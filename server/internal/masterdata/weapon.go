package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type WeaponMasterRow struct {
	WeaponId               int32 `json:"WeaponId"`
	WeaponType             int32 `json:"WeaponType"`
	WeaponSpecificEnhanceId int32 `json:"WeaponSpecificEnhanceId"`
}

type weaponSpecificEnhanceRow struct {
	WeaponSpecificEnhanceId                     int32 `json:"WeaponSpecificEnhanceId"`
	RequiredExpForLevelUpNumericalParameterMapId int32 `json:"RequiredExpForLevelUpNumericalParameterMapId"`
	EnhancementCostByMaterialNumericalFunctionId int32 `json:"EnhancementCostByMaterialNumericalFunctionId"`
	MaxLevelNumericalFunctionId                  int32 `json:"MaxLevelNumericalFunctionId"`
}

type WeaponCatalog struct {
	Weapons             map[int32]WeaponMasterRow
	Materials           map[int32]MaterialRow
	ExpByEnhanceId      map[int32][]int32
	GoldCostByEnhanceId map[int32]NumericalFunc
	MaxLevelByEnhanceId map[int32]NumericalFunc
}

func LoadWeaponCatalog(matCatalog *MaterialCatalog) (*WeaponCatalog, error) {
	weapons, err := utils.ReadJSON[WeaponMasterRow]("EntityMWeaponTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon table: %w", err)
	}

	enhanceRows, err := utils.ReadJSON[weaponSpecificEnhanceRow]("EntityMWeaponSpecificEnhanceTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon specific enhance table: %w", err)
	}

	paramMapRows, err := LoadParameterMap()
	if err != nil {
		return nil, err
	}

	funcResolver, err := LoadFunctionResolver()
	if err != nil {
		return nil, fmt.Errorf("load function resolver: %w", err)
	}

	catalog := &WeaponCatalog{
		Weapons:             make(map[int32]WeaponMasterRow, len(weapons)),
		Materials:           matCatalog.ByType[model.MaterialTypeWeaponEnhancement],
		ExpByEnhanceId:      make(map[int32][]int32, len(enhanceRows)),
		GoldCostByEnhanceId: make(map[int32]NumericalFunc, len(enhanceRows)),
		MaxLevelByEnhanceId: make(map[int32]NumericalFunc, len(enhanceRows)),
	}

	for _, w := range weapons {
		catalog.Weapons[w.WeaponId] = w
	}

	for _, r := range enhanceRows {
		if _, ok := catalog.ExpByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			catalog.ExpByEnhanceId[r.WeaponSpecificEnhanceId] = BuildExpThresholds(paramMapRows, r.RequiredExpForLevelUpNumericalParameterMapId)
		}
		if _, ok := catalog.GoldCostByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.EnhancementCostByMaterialNumericalFunctionId); found {
				catalog.GoldCostByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.MaxLevelByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.MaxLevelNumericalFunctionId); found {
				catalog.MaxLevelByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
	}

	return catalog, nil
}
