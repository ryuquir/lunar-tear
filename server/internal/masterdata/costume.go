package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type CostumeMasterRow struct {
	CostumeId          int32 `json:"CostumeId"`
	CharacterId        int32 `json:"CharacterId"`
	SkillfulWeaponType int32 `json:"SkillfulWeaponType"`
	RarityType         int32 `json:"RarityType"`
}

type costumeRarityRow struct {
	RarityType                                   int32 `json:"RarityType"`
	RequiredExpForLevelUpNumericalParameterMapId int32 `json:"RequiredExpForLevelUpNumericalParameterMapId"`
	EnhancementCostByMaterialNumericalFunctionId int32 `json:"EnhancementCostByMaterialNumericalFunctionId"`
	MaxLevelNumericalFunctionId                  int32 `json:"MaxLevelNumericalFunctionId"`
}

type CostumeCatalog struct {
	Costumes            map[int32]CostumeMasterRow
	Materials           map[int32]MaterialRow
	ExpByRarity         map[int32][]int32
	EnhanceCostByRarity map[int32]NumericalFunc
	MaxLevelByRarity    map[int32]NumericalFunc
}

func LoadCostumeCatalog(matCatalog *MaterialCatalog) (*CostumeCatalog, error) {
	costumes, err := utils.ReadJSON[CostumeMasterRow]("EntityMCostumeTable.json")
	if err != nil {
		return nil, fmt.Errorf("load costume table: %w", err)
	}

	rarities, err := utils.ReadJSON[costumeRarityRow]("EntityMCostumeRarityTable.json")
	if err != nil {
		return nil, fmt.Errorf("load costume rarity table: %w", err)
	}

	paramMapRows, err := LoadParameterMap()
	if err != nil {
		return nil, err
	}

	funcResolver, err := LoadFunctionResolver()
	if err != nil {
		return nil, fmt.Errorf("load function resolver: %w", err)
	}

	catalog := &CostumeCatalog{
		Costumes:            make(map[int32]CostumeMasterRow, len(costumes)),
		Materials:           matCatalog.ByType[model.MaterialTypeCostumeEnhancement],
		ExpByRarity:         make(map[int32][]int32, len(rarities)),
		EnhanceCostByRarity: make(map[int32]NumericalFunc, len(rarities)),
		MaxLevelByRarity:    make(map[int32]NumericalFunc, len(rarities)),
	}

	for _, row := range costumes {
		catalog.Costumes[row.CostumeId] = row
	}

	for _, r := range rarities {
		if _, ok := catalog.ExpByRarity[r.RarityType]; !ok {
			catalog.ExpByRarity[r.RarityType] = BuildExpThresholds(paramMapRows, r.RequiredExpForLevelUpNumericalParameterMapId)
		}
		if _, ok := catalog.EnhanceCostByRarity[r.RarityType]; !ok {
			if f, found := funcResolver.Resolve(r.EnhancementCostByMaterialNumericalFunctionId); found {
				catalog.EnhanceCostByRarity[r.RarityType] = f
			}
		}
		if _, ok := catalog.MaxLevelByRarity[r.RarityType]; !ok {
			if f, found := funcResolver.Resolve(r.MaxLevelNumericalFunctionId); found {
				catalog.MaxLevelByRarity[r.RarityType] = f
			}
		}
	}

	return catalog, nil
}
