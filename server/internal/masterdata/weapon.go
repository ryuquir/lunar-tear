package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type WeaponMasterRow struct {
	WeaponId                           int32 `json:"WeaponId"`
	WeaponType                         int32 `json:"WeaponType"`
	WeaponSpecificEnhanceId            int32 `json:"WeaponSpecificEnhanceId"`
	WeaponSkillGroupId                 int32 `json:"WeaponSkillGroupId"`
	WeaponAbilityGroupId               int32 `json:"WeaponAbilityGroupId"`
	WeaponStoryReleaseConditionGroupId int32 `json:"WeaponStoryReleaseConditionGroupId"`
}

type WeaponStoryReleaseConditionRow struct {
	WeaponStoryReleaseConditionGroupId          int32                                 `json:"WeaponStoryReleaseConditionGroupId"`
	StoryIndex                                  int32                                 `json:"StoryIndex"`
	WeaponStoryReleaseConditionType             model.WeaponStoryReleaseConditionType `json:"WeaponStoryReleaseConditionType"`
	ConditionValue                              int32                                 `json:"ConditionValue"`
	WeaponStoryReleaseConditionOperationGroupId int32                                 `json:"WeaponStoryReleaseConditionOperationGroupId"`
}

type WeaponSkillGroupRow struct {
	WeaponSkillGroupId int32 `json:"WeaponSkillGroupId"`
	SlotNumber         int32 `json:"SlotNumber"`
}

type WeaponAbilityGroupRow struct {
	WeaponAbilityGroupId int32 `json:"WeaponAbilityGroupId"`
	SlotNumber           int32 `json:"SlotNumber"`
}

type weaponSpecificEnhanceRow struct {
	WeaponSpecificEnhanceId                      int32 `json:"WeaponSpecificEnhanceId"`
	SellPriceNumericalFunctionId                 int32 `json:"SellPriceNumericalFunctionId"`
	RequiredExpForLevelUpNumericalParameterMapId int32 `json:"RequiredExpForLevelUpNumericalParameterMapId"`
	EnhancementCostByMaterialNumericalFunctionId int32 `json:"EnhancementCostByMaterialNumericalFunctionId"`
	MaxLevelNumericalFunctionId                  int32 `json:"MaxLevelNumericalFunctionId"`
}

type weaponConsumeExchangeRow struct {
	WeaponId         int32 `json:"WeaponId"`
	ConsumableItemId int32 `json:"ConsumableItemId"`
	Count            int32 `json:"Count"`
}

type WeaponCatalog struct {
	Weapons              map[int32]WeaponMasterRow
	Materials            map[int32]MaterialRow
	ExpByEnhanceId       map[int32][]int32
	GoldCostByEnhanceId  map[int32]NumericalFunc
	MaxLevelByEnhanceId  map[int32]NumericalFunc
	SellPriceByEnhanceId map[int32]NumericalFunc
	MedalsByWeaponId     map[int32]map[int32]int32 // WeaponId -> ConsumableItemId -> Count
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

	exchangeRows, err := utils.ReadJSON[weaponConsumeExchangeRow]("EntityMWeaponConsumeExchangeConsumableItemGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon consume exchange table: %w", err)
	}

	catalog := &WeaponCatalog{
		Weapons:              make(map[int32]WeaponMasterRow, len(weapons)),
		Materials:            matCatalog.ByType[model.MaterialTypeWeaponEnhancement],
		ExpByEnhanceId:       make(map[int32][]int32, len(enhanceRows)),
		GoldCostByEnhanceId:  make(map[int32]NumericalFunc, len(enhanceRows)),
		MaxLevelByEnhanceId:  make(map[int32]NumericalFunc, len(enhanceRows)),
		SellPriceByEnhanceId: make(map[int32]NumericalFunc, len(enhanceRows)),
		MedalsByWeaponId:     make(map[int32]map[int32]int32),
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
		if _, ok := catalog.SellPriceByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.SellPriceNumericalFunctionId); found {
				catalog.SellPriceByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
	}

	for _, ex := range exchangeRows {
		if catalog.MedalsByWeaponId[ex.WeaponId] == nil {
			catalog.MedalsByWeaponId[ex.WeaponId] = make(map[int32]int32)
		}
		catalog.MedalsByWeaponId[ex.WeaponId][ex.ConsumableItemId] = ex.Count
	}

	return catalog, nil
}
