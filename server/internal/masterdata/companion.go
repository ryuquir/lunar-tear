package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/utils"
)

type companionRow struct {
	CompanionId           int32 `json:"CompanionId"`
	CompanionCategoryType int32 `json:"CompanionCategoryType"`
}

type companionCategoryRow struct {
	CompanionCategoryType              int32 `json:"CompanionCategoryType"`
	EnhancementCostNumericalFunctionId int32 `json:"EnhancementCostNumericalFunctionId"`
}

type companionEnhancementMaterialRow struct {
	CompanionCategoryType int32 `json:"CompanionCategoryType"`
	Level                 int32 `json:"Level"`
	MaterialId            int32 `json:"MaterialId"`
	Count                 int32 `json:"Count"`
}

type CompanionLevelKey struct {
	CategoryType int32
	Level        int32
}

type CompanionMaterialCost struct {
	MaterialId int32
	Count      int32
}

type CompanionCatalog struct {
	CompanionById      map[int32]companionRow
	GoldCostByCategory map[int32]NumericalFunc
	MaterialsByKey     map[CompanionLevelKey]CompanionMaterialCost
}

func LoadCompanionCatalog() (*CompanionCatalog, error) {
	companions, err := utils.ReadJSON[companionRow]("EntityMCompanionTable.json")
	if err != nil {
		return nil, fmt.Errorf("load companion table: %w", err)
	}

	categories, err := utils.ReadJSON[companionCategoryRow]("EntityMCompanionCategoryTable.json")
	if err != nil {
		return nil, fmt.Errorf("load companion category table: %w", err)
	}

	materials, err := utils.ReadJSON[companionEnhancementMaterialRow]("EntityMCompanionEnhancementMaterialTable.json")
	if err != nil {
		return nil, fmt.Errorf("load companion enhancement material table: %w", err)
	}

	funcResolver, err := LoadFunctionResolver()
	if err != nil {
		return nil, fmt.Errorf("load function resolver: %w", err)
	}

	companionById := make(map[int32]companionRow, len(companions))
	for _, c := range companions {
		companionById[c.CompanionId] = c
	}

	goldCostByCategory := make(map[int32]NumericalFunc, len(categories))
	for _, cat := range categories {
		if f, ok := funcResolver.Resolve(cat.EnhancementCostNumericalFunctionId); ok {
			goldCostByCategory[cat.CompanionCategoryType] = f
		}
	}

	materialsByKey := make(map[CompanionLevelKey]CompanionMaterialCost, len(materials))
	for _, m := range materials {
		key := CompanionLevelKey{CategoryType: m.CompanionCategoryType, Level: m.Level}
		materialsByKey[key] = CompanionMaterialCost{MaterialId: m.MaterialId, Count: m.Count}
	}

	return &CompanionCatalog{
		CompanionById:      companionById,
		GoldCostByCategory: goldCostByCategory,
		MaterialsByKey:     materialsByKey,
	}, nil
}
