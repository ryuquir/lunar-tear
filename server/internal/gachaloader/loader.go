package gachaloader

import (
	"fmt"
	"strings"
	"time"

	"lunar-tear/server/internal/gacha"
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

func LoadGachaCatalog() ([]store.GachaCatalogEntry, error) {
	medals, err := utils.ReadJSON[gachaMedalRow]("EntityMGachaMedalTable.json")
	if err != nil {
		return nil, fmt.Errorf("load gacha medal table: %w", err)
	}
	banners, err := utils.ReadJSON[momBannerRow]("EntityMMomBannerTable.json")
	if err != nil {
		return nil, fmt.Errorf("load mom banner table: %w", err)
	}

	gachaToMedal := make(map[int32]gachaMedalRow)
	for _, m := range medals {
		gachaToMedal[m.ShopTransitionGachaId] = m
	}

	gachaToBanner := make(map[int32]momBannerRow)
	for _, b := range banners {
		if b.DestinationDomainType != 1 {
			continue
		}
		gachaToBanner[b.DestinationDomainId] = b
	}

	now := time.Now()
	startDt := now.AddDate(0, 0, -3).UnixMilli()
	endDt := now.AddDate(0, 0, 3).UnixMilli()

	var entries []store.GachaCatalogEntry
	for gachaId, banner := range gachaToBanner {
		medal, hasMedal := gachaToMedal[gachaId]
		if !hasMedal {
			continue
		}

		labelType := gacha.GachaLabelEvent
		modeType := gacha.GachaModeBox
		stepupGroupId := gachaId

		// TODO(krettsy): this is a single-step stub; real step-ups need
		// multiple Gacha entries per group with per-step prices/rewards.
		if strings.HasPrefix(banner.BannerAssetName, "step_up_") {
			labelType = gacha.GachaLabelPremium
			stepupGroupId = gachaId / 1000
		}

		entries = append(entries, store.GachaCatalogEntry{
			GachaId:                    gachaId,
			GachaLabelType:             labelType,
			GachaModeType:              modeType,
			GachaAutoResetType:         gacha.GachaAutoResetNone,
			GachaAutoResetPeriod:       0,
			NextAutoResetDatetime:      0,
			IsUserGachaUnlock:          true,
			StartDatetime:              startDt,
			EndDatetime:                endDt,
			RelatedMainQuestChapterId:  0,
			RelatedEventQuestChapterId: 0,
			PromotionMovieAssetId:      0,
			GachaMedalId:               medal.GachaMedalId,
			GachaDecorationType:        gacha.GachaDecorationNormal,
			SortOrder:                  banner.SortOrderDesc,
			IsInactive:                 false,
			InformationId:              0,
			GachaMode:                  nil,
			BannerAssetName:            banner.BannerAssetName,
			StepupGroupId:              stepupGroupId,
		})
	}
	return entries, nil
}
