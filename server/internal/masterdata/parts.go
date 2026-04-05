package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type PartsRow struct {
	PartsId                       int32            `json:"PartsId"`
	RarityType                    model.RarityType `json:"RarityType"`
	PartsGroupId                  int32            `json:"PartsGroupId"`
	PartsStatusMainLotteryGroupId int32            `json:"PartsStatusMainLotteryGroupId"`
}

type PartsRarityRow struct {
	RarityType                   model.RarityType `json:"RarityType"`
	PartsLevelUpRateGroupId      int32            `json:"PartsLevelUpRateGroupId"`
	PartsLevelUpPriceGroupId     int32            `json:"PartsLevelUpPriceGroupId"`
	SellPriceNumericalFunctionId int32            `json:"SellPriceNumericalFunctionId"`
}

type partsLevelUpRateRow struct {
	PartsLevelUpRateGroupId int32 `json:"PartsLevelUpRateGroupId"`
	LevelLowerLimit         int32 `json:"LevelLowerLimit"`
	SuccessRatePermil       int32 `json:"SuccessRatePermil"`
}

type partsLevelUpPriceRow struct {
	PartsLevelUpPriceGroupId int32 `json:"PartsLevelUpPriceGroupId"`
	LevelLowerLimit          int32 `json:"LevelLowerLimit"`
	Gold                     int32 `json:"Gold"`
}

type PartsCatalog struct {
	PartsById                            map[int32]PartsRow
	DefaultPartsStatusMainByLotteryGroup map[int32]int32
	RarityByRarityType                   map[model.RarityType]PartsRarityRow
	RateByGroupAndLevel                  map[int32]map[int32]int32
	PriceByGroupAndLevel                 map[int32]map[int32]int32
	SellPriceByRarity                    map[model.RarityType]NumericalFunc
}

func LoadPartsCatalog() (*PartsCatalog, error) {
	partsRows, err := utils.ReadJSON[PartsRow]("EntityMPartsTable.json")
	if err != nil {
		return nil, fmt.Errorf("load parts table: %w", err)
	}

	rarityRows, err := utils.ReadJSON[PartsRarityRow]("EntityMPartsRarityTable.json")
	if err != nil {
		return nil, fmt.Errorf("load parts rarity table: %w", err)
	}

	rateRows, err := utils.ReadJSON[partsLevelUpRateRow]("EntityMPartsLevelUpRateGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load parts level up rate table: %w", err)
	}

	priceRows, err := utils.ReadJSON[partsLevelUpPriceRow]("EntityMPartsLevelUpPriceGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load parts level up price table: %w", err)
	}

	partsById := make(map[int32]PartsRow, len(partsRows))
	for _, p := range partsRows {
		partsById[p.PartsId] = p
	}

	// Lottery group ID encodes tier (first digit 1-4) and stat category
	// (second digit 1-6). Formula: mainStatId = (category - 1) * 4 + tier.
	defaultPartsStatusMainByLotteryGroup := make(map[int32]int32, 24)
	for tier := int32(1); tier <= 4; tier++ {
		for cat := int32(1); cat <= 6; cat++ {
			groupId := tier*10 + cat
			mainStatId := (cat-1)*4 + tier
			defaultPartsStatusMainByLotteryGroup[groupId] = mainStatId
		}
	}

	funcResolver, err := LoadFunctionResolver()
	if err != nil {
		return nil, fmt.Errorf("load function resolver: %w", err)
	}

	rarityByRarityType := make(map[model.RarityType]PartsRarityRow, len(rarityRows))
	sellPriceByRarity := make(map[model.RarityType]NumericalFunc, len(rarityRows))
	for _, r := range rarityRows {
		rarityByRarityType[r.RarityType] = r
		if f, ok := funcResolver.Resolve(r.SellPriceNumericalFunctionId); ok {
			sellPriceByRarity[r.RarityType] = f
		}
	}

	rateByGroupAndLevel := make(map[int32]map[int32]int32)
	for _, r := range rateRows {
		if rateByGroupAndLevel[r.PartsLevelUpRateGroupId] == nil {
			rateByGroupAndLevel[r.PartsLevelUpRateGroupId] = make(map[int32]int32)
		}
		rateByGroupAndLevel[r.PartsLevelUpRateGroupId][r.LevelLowerLimit] = r.SuccessRatePermil
	}

	priceByGroupAndLevel := make(map[int32]map[int32]int32)
	for _, p := range priceRows {
		if priceByGroupAndLevel[p.PartsLevelUpPriceGroupId] == nil {
			priceByGroupAndLevel[p.PartsLevelUpPriceGroupId] = make(map[int32]int32)
		}
		priceByGroupAndLevel[p.PartsLevelUpPriceGroupId][p.LevelLowerLimit] = p.Gold
	}

	return &PartsCatalog{
		PartsById:                            partsById,
		DefaultPartsStatusMainByLotteryGroup: defaultPartsStatusMainByLotteryGroup,
		RarityByRarityType:                   rarityByRarityType,
		RateByGroupAndLevel:                  rateByGroupAndLevel,
		PriceByGroupAndLevel:                 priceByGroupAndLevel,
		SellPriceByRarity:                    sellPriceByRarity,
	}, nil
}
