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

	bestByLabel := make(map[int32]store.GachaCatalogEntry)
	for gachaID, banner := range gachaToBanner {
		medal, hasMedal := gachaToMedal[gachaID]
		if !hasMedal {
			continue
		}
		sortOrder := banner.SortOrderDesc
		gachaLabelType := gacha.GachaLabelPremium
		if strings.Contains(strings.ToLower(banner.BannerAssetName), "limited") {
			gachaLabelType = gacha.GachaLabelEvent
		} else if strings.Contains(strings.ToLower(banner.BannerAssetName), "chapter") {
			gachaLabelType = gacha.GachaLabelChapter
		}
		entry := store.GachaCatalogEntry{
			GachaID:                    gachaID,
			GachaLabelType:             gachaLabelType,
			GachaModeType:              gacha.GachaModeBasic,
			GachaAutoResetType:         0,
			GachaAutoResetPeriod:       0,
			NextAutoResetDatetime:      0,
			IsUserGachaUnlock:          true,
			StartDatetime:              startDt,
			EndDatetime:                endDt,
			RelatedMainQuestChapterID:  0,
			RelatedEventQuestChapterID: 0,
			PromotionMovieAssetID:      0,
			GachaMedalID:               medal.GachaMedalId,
			GachaDecorationType:        0,
			SortOrder:                  sortOrder,
			IsInactive:                 false,
			InformationID:              0,
			GachaMode:                  nil,
			BannerAssetName:            banner.BannerAssetName,
		}
		if existing, ok := bestByLabel[gachaLabelType]; !ok || sortOrder > existing.SortOrder {
			bestByLabel[gachaLabelType] = entry
		}
	}
	entries := make([]store.GachaCatalogEntry, 0, len(bestByLabel))
	for _, entry := range bestByLabel {
		entries = append(entries, entry)
	}
	return entries, nil
}
