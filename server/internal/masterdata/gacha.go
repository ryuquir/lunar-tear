package masterdata

import (
	"fmt"
	"sort"
	"strings"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/utils"
)

type gachaMedalRow struct {
	GachaMedalId          int32 `json:"GachaMedalId"`
	ShopTransitionGachaId int32 `json:"ShopTransitionGachaId"`
	ConsumableItemId      int32 `json:"ConsumableItemId"`
	AutoConvertDatetime   int64 `json:"AutoConvertDatetime"`
	ConversionRate        int32 `json:"ConversionRate"`
}

type momBannerRow struct {
	MomBannerId           int32  `json:"MomBannerId"`
	SortOrderDesc         int32  `json:"SortOrderDesc"`
	DestinationDomainType int32  `json:"DestinationDomainType"`
	DestinationDomainId   int32  `json:"DestinationDomainId"`
	BannerAssetName       string `json:"BannerAssetName"`
	StartDatetime         int64  `json:"StartDatetime"`
	EndDatetime           int64  `json:"EndDatetime"`
}

type GachaMedalInfo struct {
	GachaMedalId        int32
	ConsumableItemId    int32
	AutoConvertDatetime int64
	ConversionRate      int32
}

const (
	chapterGachaIdBase  int32 = 200000
	maxMainQuestChapter int32 = 38
)

func LoadGachaCatalog() ([]store.GachaCatalogEntry, map[int32]GachaMedalInfo, error) {
	medals, err := utils.ReadJSON[gachaMedalRow]("EntityMGachaMedalTable.json")
	if err != nil {
		return nil, nil, fmt.Errorf("load gacha medal table: %w", err)
	}
	banners, err := utils.ReadJSON[momBannerRow]("EntityMMomBannerTable.json")
	if err != nil {
		return nil, nil, fmt.Errorf("load mom banner table: %w", err)
	}

	gachaToMedal := make(map[int32]gachaMedalRow)
	medalInfoByGacha := make(map[int32]GachaMedalInfo)
	for _, m := range medals {
		gachaToMedal[m.ShopTransitionGachaId] = m
		medalInfoByGacha[m.ShopTransitionGachaId] = GachaMedalInfo{
			GachaMedalId:        m.GachaMedalId,
			ConsumableItemId:    m.ConsumableItemId,
			AutoConvertDatetime: m.AutoConvertDatetime,
			ConversionRate:      m.ConversionRate,
		}
	}

	stepupSteps := make(map[int32][]momBannerRow)
	var entries []store.GachaCatalogEntry

	for _, b := range banners {
		if b.DestinationDomainType != model.MomBannerDomainGacha {
			continue
		}
		gachaId := b.DestinationDomainId

		if strings.HasPrefix(b.BannerAssetName, model.BannerPrefixStepUp) {
			if _, hasMedal := gachaToMedal[gachaId]; !hasMedal {
				continue
			}
			groupId := gachaId / model.StepUpGroupDivisor
			stepupSteps[groupId] = append(stepupSteps[groupId], b)
			continue
		}

		labelType := model.GachaLabelPremium
		modeType := model.GachaModeBasic
		decoration := model.GachaDecorationNormal

		isChapter := strings.HasPrefix(b.BannerAssetName, model.BannerPrefixCommon)

		if strings.HasPrefix(b.BannerAssetName, model.BannerPrefixLimited) {
			decoration = model.GachaDecorationFestival
		}
		if isChapter {
			labelType = model.GachaLabelChapter
			modeType = model.GachaModeBox
		}

		medal, hasMedal := gachaToMedal[gachaId]
		if !hasMedal && !isChapter {
			continue
		}
		var medalId int32
		var medalConsumableId int32
		var ceilingCount int32
		if hasMedal {
			medalId = medal.GachaMedalId
			medalConsumableId = medal.ConsumableItemId
			ceilingCount = model.PityCeilingCount
		}

		var pricePhases []store.GachaPricePhaseEntry
		if isChapter {
			pricePhases = buildChapterPricePhases(gachaId)
		} else {
			pricePhases = buildPremiumBasicPricePhases(gachaId)
		}

		relMainQuest := int32(0)
		if isChapter {
			relMainQuest = gachaId - chapterGachaIdBase
			if relMainQuest < 1 || relMainQuest > maxMainQuestChapter {
				relMainQuest = 1
			}
		}

		var descriptionTextId int32
		if isChapter {
			descriptionTextId = gachaId
		}

		entries = append(entries, store.GachaCatalogEntry{
			GachaId:                   gachaId,
			GachaLabelType:            labelType,
			GachaModeType:             modeType,
			GachaAutoResetType:        model.GachaAutoResetNone,
			IsUserGachaUnlock:         true,
			StartDatetime:             b.StartDatetime,
			EndDatetime:               b.EndDatetime,
			RelatedMainQuestChapterId: relMainQuest,
			GachaMedalId:              medalId,
			MedalConsumableItemId:     medalConsumableId,
			GachaDecorationType:       decoration,
			SortOrder:                 b.SortOrderDesc,
			BannerAssetName:           b.BannerAssetName,
			GroupId:                   gachaId,
			CeilingCount:              ceilingCount,
			PricePhases:               pricePhases,
			DescriptionTextId:         descriptionTextId,
		})
	}

	for groupId, steps := range stepupSteps {
		if len(steps) == 0 {
			continue
		}
		first := steps[0]
		gachaId := groupId

		medal, hasMedal := gachaToMedal[first.DestinationDomainId]
		var medalId int32
		var medalConsumableId int32
		if hasMedal {
			medalId = medal.GachaMedalId
			medalConsumableId = medal.ConsumableItemId
		}

		pricePhases := buildStepUpPricePhases(gachaId, len(steps))

		var maxStep int32
		for _, p := range pricePhases {
			if p.StepNumber > maxStep {
				maxStep = p.StepNumber
			}
		}

		entries = append(entries, store.GachaCatalogEntry{
			GachaId:               gachaId,
			GachaLabelType:        model.GachaLabelPremium,
			GachaModeType:         model.GachaModeStepup,
			GachaAutoResetType:    model.GachaAutoResetNone,
			IsUserGachaUnlock:     true,
			StartDatetime:         first.StartDatetime,
			EndDatetime:           first.EndDatetime,
			GachaMedalId:          medalId,
			MedalConsumableItemId: medalConsumableId,
			GachaDecorationType:   model.GachaDecorationFestival,
			SortOrder:             first.SortOrderDesc,
			BannerAssetName:       first.BannerAssetName,
			GroupId:               groupId,
			CeilingCount:          model.PityCeilingCount,
			PricePhases:           pricePhases,
			MaxStepNumber:         maxStep,
		})
	}

	return entries, medalInfoByGacha, nil
}

const chapterPromoMaxItems = 4

func EnrichCatalogPromotions(entries []store.GachaCatalogEntry, pool *GachaCatalog) {
	ssrCostumes := pool.CostumesByRarity[model.RaritySSRare]
	ssrWeapons := pool.WeaponsByRarity[model.RaritySSRare]

	for i := range entries {
		if len(entries[i].PromotionItems) > 0 {
			continue
		}

		if entries[i].GachaLabelType == model.GachaLabelChapter {
			entries[i].PromotionItems = buildChapterPromotionItems(pool.Materials)
			continue
		}

		isMaterialBanner := model.IsMaterialBanner(entries[i].GachaLabelType)

		var items []store.GachaPromotionItem

		if featured, ok := pool.FeaturedByGacha[entries[i].GachaId]; ok {
			maxCostumes := 2
			if isMaterialBanner {
				maxCostumes = 1
			}
			for _, c := range featured.Costumes[:min(maxCostumes, len(featured.Costumes))] {
				items = append(items, toPromoItem(c))
			}
			if !isMaterialBanner {
				for _, w := range featured.Weapons[:min(1, len(featured.Weapons))] {
					items = append(items, toPromoItem(w))
				}
			}
		}

		if len(items) == 0 {
			items = buildFallbackPromotionItems(entries[i].GachaId, isMaterialBanner, ssrCostumes, ssrWeapons)
		}

		entries[i].PromotionItems = items
	}

	sort.Slice(entries, func(i, j int) bool {
		if entries[i].SortOrder != entries[j].SortOrder {
			return entries[i].SortOrder < entries[j].SortOrder
		}
		return entries[i].GachaId < entries[j].GachaId
	})
}

func buildFallbackPromotionItems(gachaId int32, isMaterial bool, ssrCostumes, ssrWeapons []GachaPoolItem) []store.GachaPromotionItem {
	if len(ssrCostumes) == 0 {
		return nil
	}
	var items []store.GachaPromotionItem
	idx := int(gachaId) % len(ssrCostumes)
	items = append(items, toPromoItem(ssrCostumes[idx]))

	if !isMaterial && len(ssrCostumes) > 1 {
		items = append(items, toPromoItem(ssrCostumes[(idx+1)%len(ssrCostumes)]))
	}
	if !isMaterial && len(ssrWeapons) > 0 {
		items = append(items, toPromoItem(ssrWeapons[int(gachaId)%len(ssrWeapons)]))
	}
	return items
}

func toPromoItem(item GachaPoolItem) store.GachaPromotionItem {
	return store.GachaPromotionItem{
		PossessionType: item.PossessionType,
		PossessionId:   item.PossessionId,
		IsTarget:       true,
	}
}

func buildChapterPromotionItems(materials []GachaPoolItem) []store.GachaPromotionItem {
	limit := min(chapterPromoMaxItems, len(materials))
	items := make([]store.GachaPromotionItem, 0, limit)
	for _, m := range materials[:limit] {
		items = append(items, toPromoItem(m))
	}
	return items
}

func buildPremiumBasicPricePhases(gachaId int32) []store.GachaPricePhaseEntry {
	return []store.GachaPricePhaseEntry{
		{
			PhaseId:      gachaId*model.PhaseIdMultiplier + 1,
			PriceType:    model.PriceTypeGem,
			Price:        model.PremiumSinglePullPrice,
			RegularPrice: model.PremiumSinglePullPrice,
			DrawCount:    1,
		},
		{
			PhaseId:        gachaId*model.PhaseIdMultiplier + 2,
			PriceType:      model.PriceTypeGem,
			Price:          model.PremiumMultiPullPrice,
			RegularPrice:   model.PremiumMultiPullPrice,
			DrawCount:      model.PremiumMultiPullCount,
			FixedRarityMin: model.RaritySRare,
			FixedCount:     1,
		},
		{
			PhaseId:      gachaId*model.PhaseIdMultiplier + 3,
			PriceType:    model.PriceTypeConsumableItem,
			PriceId:      model.ConsumableIdPremiumTicket,
			Price:        1,
			RegularPrice: 1,
			DrawCount:    1,
		},
	}
}

func buildStepUpPricePhases(gachaId int32, totalSteps int) []store.GachaPricePhaseEntry {
	stepCosts := []int32{model.StepUpStep1Cost, model.StepUpFreeCost, model.StepUpStep3Cost, model.StepUpFreeCost, model.StepUpStep5Cost}
	stepCosts = stepCosts[:min(totalSteps, len(stepCosts))]

	var phases []store.GachaPricePhaseEntry
	for i, cost := range stepCosts {
		step := int32(i + 1)
		priceType := model.PriceTypePaidGem
		if cost == 0 {
			priceType = model.PriceTypeGem
		}

		fixedRarityMin := int32(0)
		fixedCount := int32(0)
		if step == int32(len(stepCosts)) {
			fixedRarityMin = model.RaritySSRare
			fixedCount = 1
		}

		phases = append(phases, store.GachaPricePhaseEntry{
			PhaseId:        gachaId*model.PhaseIdMultiplier + step,
			PriceType:      priceType,
			Price:          cost,
			RegularPrice:   model.PremiumMultiPullPrice,
			DrawCount:      model.PremiumMultiPullCount,
			FixedRarityMin: fixedRarityMin,
			FixedCount:     fixedCount,
			LimitExecCount: 1,
			StepNumber:     step,
		})
	}
	return phases
}

func buildChapterPricePhases(gachaId int32) []store.GachaPricePhaseEntry {
	return []store.GachaPricePhaseEntry{
		{
			PhaseId:      gachaId*model.PhaseIdMultiplier + 1,
			PriceType:    model.PriceTypeConsumableItem,
			PriceId:      model.ConsumableIdChapterTicket,
			Price:        1,
			RegularPrice: 1,
			DrawCount:    1,
		},
		{
			PhaseId:      gachaId*model.PhaseIdMultiplier + 2,
			PriceType:    model.PriceTypeConsumableItem,
			PriceId:      model.ConsumableIdChapterTicket,
			Price:        10,
			RegularPrice: 10,
			DrawCount:    model.PremiumMultiPullCount,
		},
	}
}

