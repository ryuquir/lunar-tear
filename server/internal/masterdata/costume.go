package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/utils"
)

type CostumeMasterRow struct {
	CostumeId          int32 `json:"CostumeId"`
	CharacterId        int32 `json:"CharacterId"`
	SkillfulWeaponType int32 `json:"SkillfulWeaponType"`
	RarityType         int32 `json:"RarityType"`
}

type MaterialRow struct {
	MaterialId   int32 `json:"MaterialId"`
	MaterialType int32 `json:"MaterialType"`
	WeaponType   int32 `json:"WeaponType"`
	EffectValue  int32 `json:"EffectValue"`
}

type costumeRarityRow struct {
	RarityType                                   int32 `json:"RarityType"`
	RequiredExpForLevelUpNumericalParameterMapId int32 `json:"RequiredExpForLevelUpNumericalParameterMapId"`
	EnhancementCostByMaterialNumericalFunctionId int32 `json:"EnhancementCostByMaterialNumericalFunctionId"`
}

type numericalParameterMapRow struct {
	NumericalParameterMapId int32 `json:"NumericalParameterMapId"`
	ParameterKey            int32 `json:"ParameterKey"`
	ParameterValue          int32 `json:"ParameterValue"`
}

const materialTypeCostumeEnhancement = 20

type CostumeCatalog struct {
	Costumes            map[int32]CostumeMasterRow
	Materials           map[int32]MaterialRow
	ExpByRarity         map[int32][]int32
	EnhanceCostByRarity map[int32]NumericalFunc
}

func LoadCostumeCatalog() (*CostumeCatalog, error) {
	costumes, err := utils.ReadJSON[CostumeMasterRow]("EntityMCostumeTable.json")
	if err != nil {
		return nil, fmt.Errorf("load costume table: %w", err)
	}

	allMaterials, err := utils.ReadJSON[MaterialRow]("EntityMMaterialTable.json")
	if err != nil {
		return nil, fmt.Errorf("load material table: %w", err)
	}

	rarities, err := utils.ReadJSON[costumeRarityRow]("EntityMCostumeRarityTable.json")
	if err != nil {
		return nil, fmt.Errorf("load costume rarity table: %w", err)
	}

	paramMapRows, err := utils.ReadJSON[numericalParameterMapRow]("EntityMNumericalParameterMapTable.json")
	if err != nil {
		return nil, fmt.Errorf("load numerical parameter map table: %w", err)
	}

	funcResolver, err := LoadFunctionResolver()
	if err != nil {
		return nil, fmt.Errorf("load function resolver: %w", err)
	}

	catalog := &CostumeCatalog{
		Costumes:            make(map[int32]CostumeMasterRow, len(costumes)),
		Materials:           make(map[int32]MaterialRow),
		ExpByRarity:         make(map[int32][]int32, len(rarities)),
		EnhanceCostByRarity: make(map[int32]NumericalFunc, len(rarities)),
	}

	for _, row := range costumes {
		catalog.Costumes[row.CostumeId] = row
	}

	for _, row := range allMaterials {
		if row.MaterialType == materialTypeCostumeEnhancement {
			catalog.Materials[row.MaterialId] = row
		}
	}

	buildExpThresholds := func(mapId int32) []int32 {
		maxKey := int32(0)
		for _, r := range paramMapRows {
			if r.NumericalParameterMapId == mapId && r.ParameterKey > maxKey {
				maxKey = r.ParameterKey
			}
		}
		thresholds := make([]int32, maxKey+1)
		for _, r := range paramMapRows {
			if r.NumericalParameterMapId == mapId {
				thresholds[r.ParameterKey] = r.ParameterValue
			}
		}
		return thresholds
	}

	for _, r := range rarities {
		if _, ok := catalog.ExpByRarity[r.RarityType]; !ok {
			catalog.ExpByRarity[r.RarityType] = buildExpThresholds(r.RequiredExpForLevelUpNumericalParameterMapId)
		}
		if _, ok := catalog.EnhanceCostByRarity[r.RarityType]; !ok {
			if f, found := funcResolver.Resolve(r.EnhancementCostByMaterialNumericalFunctionId); found {
				catalog.EnhanceCostByRarity[r.RarityType] = f
			}
		}
	}

	return catalog, nil
}
