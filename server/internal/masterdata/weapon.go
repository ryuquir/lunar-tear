package masterdata

import (
	"fmt"
	"sort"

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
	WeaponEvolutionMaterialGroupId     int32 `json:"WeaponEvolutionMaterialGroupId"`
}

type WeaponStoryReleaseConditionRow struct {
	WeaponStoryReleaseConditionGroupId          int32                                 `json:"WeaponStoryReleaseConditionGroupId"`
	StoryIndex                                  int32                                 `json:"StoryIndex"`
	WeaponStoryReleaseConditionType             model.WeaponStoryReleaseConditionType `json:"WeaponStoryReleaseConditionType"`
	ConditionValue                              int32                                 `json:"ConditionValue"`
	WeaponStoryReleaseConditionOperationGroupId int32                                 `json:"WeaponStoryReleaseConditionOperationGroupId"`
}

type WeaponSkillGroupRow struct {
	WeaponSkillGroupId               int32 `json:"WeaponSkillGroupId"`
	SlotNumber                       int32 `json:"SlotNumber"`
	SkillId                          int32 `json:"SkillId"`
	WeaponSkillEnhancementMaterialId int32 `json:"WeaponSkillEnhancementMaterialId"`
}

type WeaponAbilityGroupRow struct {
	WeaponAbilityGroupId               int32 `json:"WeaponAbilityGroupId"`
	SlotNumber                         int32 `json:"SlotNumber"`
	AbilityId                          int32 `json:"AbilityId"`
	WeaponAbilityEnhancementMaterialId int32 `json:"WeaponAbilityEnhancementMaterialId"`
}

type weaponSpecificEnhanceRow struct {
	WeaponSpecificEnhanceId                      int32 `json:"WeaponSpecificEnhanceId"`
	BaseEnhancementObtainedExp                   int32 `json:"BaseEnhancementObtainedExp"`
	SellPriceNumericalFunctionId                 int32 `json:"SellPriceNumericalFunctionId"`
	RequiredExpForLevelUpNumericalParameterMapId int32 `json:"RequiredExpForLevelUpNumericalParameterMapId"`
	EnhancementCostByWeaponNumericalFunctionId   int32 `json:"EnhancementCostByWeaponNumericalFunctionId"`
	EnhancementCostByMaterialNumericalFunctionId int32 `json:"EnhancementCostByMaterialNumericalFunctionId"`
	MaxLevelNumericalFunctionId                  int32 `json:"MaxLevelNumericalFunctionId"`
	EvolutionCostNumericalFunctionId             int32 `json:"EvolutionCostNumericalFunctionId"`
	LimitBreakCostByWeaponNumericalFunctionId    int32 `json:"LimitBreakCostByWeaponNumericalFunctionId"`
	LimitBreakCostByMaterialNumericalFunctionId  int32 `json:"LimitBreakCostByMaterialNumericalFunctionId"`
	MaxSkillLevelNumericalFunctionId             int32 `json:"MaxSkillLevelNumericalFunctionId"`
	SkillEnhancementCostNumericalFunctionId      int32 `json:"SkillEnhancementCostNumericalFunctionId"`
	MaxAbilityLevelNumericalFunctionId           int32 `json:"MaxAbilityLevelNumericalFunctionId"`
	AbilityEnhancementCostNumericalFunctionId    int32 `json:"AbilityEnhancementCostNumericalFunctionId"`
}

type weaponConsumeExchangeRow struct {
	WeaponId         int32 `json:"WeaponId"`
	ConsumableItemId int32 `json:"ConsumableItemId"`
	Count            int32 `json:"Count"`
}

type WeaponEvolutionGroupRow struct {
	WeaponEvolutionGroupId int32 `json:"WeaponEvolutionGroupId"`
	EvolutionOrder         int32 `json:"EvolutionOrder"`
	WeaponId               int32 `json:"WeaponId"`
}

type WeaponEvolutionMaterialRow struct {
	WeaponEvolutionMaterialGroupId int32 `json:"WeaponEvolutionMaterialGroupId"`
	MaterialId                     int32 `json:"MaterialId"`
	Count                          int32 `json:"Count"`
	SortOrder                      int32 `json:"SortOrder"`
}

type WeaponSkillEnhanceMaterialRow struct {
	WeaponSkillEnhancementMaterialId int32 `json:"WeaponSkillEnhancementMaterialId"`
	SkillLevel                       int32 `json:"SkillLevel"`
	MaterialId                       int32 `json:"MaterialId"`
	Count                            int32 `json:"Count"`
	SortOrder                        int32 `json:"SortOrder"`
}

type WeaponAbilityEnhanceMaterialRow struct {
	WeaponAbilityEnhancementMaterialId int32 `json:"WeaponAbilityEnhancementMaterialId"`
	AbilityLevel                       int32 `json:"AbilityLevel"`
	MaterialId                         int32 `json:"MaterialId"`
	Count                              int32 `json:"Count"`
	SortOrder                          int32 `json:"SortOrder"`
}

type WeaponCatalog struct {
	Weapons                             map[int32]WeaponMasterRow
	Materials                           map[int32]MaterialRow
	ExpByEnhanceId                      map[int32][]int32
	GoldCostByEnhanceId                 map[int32]NumericalFunc
	MaxLevelByEnhanceId                 map[int32]NumericalFunc
	SellPriceByEnhanceId                map[int32]NumericalFunc
	MedalsByWeaponId                    map[int32]map[int32]int32 // WeaponId -> ConsumableItemId -> Count
	EvolutionNextWeaponId               map[int32]int32
	EvolutionMaterials                  map[int32][]WeaponEvolutionMaterialRow // WeaponEvolutionMaterialGroupId -> materials
	EvolutionCostByEnhanceId            map[int32]NumericalFunc
	AbilitySlots                        map[int32][]int32 // WeaponAbilityGroupId -> slot numbers
	SkillGroupsByGroupId                map[int32][]WeaponSkillGroupRow
	SkillEnhanceMats                    map[[2]int32][]WeaponSkillEnhanceMaterialRow // key: [enhancementMaterialId, skillLevel]
	SkillMaxLevelByEnhanceId            map[int32]NumericalFunc
	SkillCostByEnhanceId                map[int32]NumericalFunc
	AbilityGroupsByGroupId              map[int32][]WeaponAbilityGroupRow
	AbilityEnhanceMats                  map[[2]int32][]WeaponAbilityEnhanceMaterialRow // key: [enhancementMaterialId, abilityLevel]
	AbilityMaxLevelByEnhanceId          map[int32]NumericalFunc
	AbilityCostByEnhanceId              map[int32]NumericalFunc
	EnhanceCostByWeaponByEnhanceId      map[int32]NumericalFunc
	LimitBreakCostByWeaponByEnhanceId   map[int32]NumericalFunc
	LimitBreakCostByMaterialByEnhanceId map[int32]NumericalFunc
	BaseExpByEnhanceId                  map[int32]int32
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

	evoGroupRows, err := utils.ReadJSON[WeaponEvolutionGroupRow]("EntityMWeaponEvolutionGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon evolution group table: %w", err)
	}
	evoMatRows, err := utils.ReadJSON[WeaponEvolutionMaterialRow]("EntityMWeaponEvolutionMaterialGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon evolution material group table: %w", err)
	}
	abilityGroupRows, err := utils.ReadJSON[WeaponAbilityGroupRow]("EntityMWeaponAbilityGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon ability group table: %w", err)
	}
	skillGroupRows, err := utils.ReadJSON[WeaponSkillGroupRow]("EntityMWeaponSkillGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon skill group table: %w", err)
	}
	skillMatRows, err := utils.ReadJSON[WeaponSkillEnhanceMaterialRow]("EntityMWeaponSkillEnhancementMaterialTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon skill enhancement material table: %w", err)
	}
	abilityMatRows, err := utils.ReadJSON[WeaponAbilityEnhanceMaterialRow]("EntityMWeaponAbilityEnhancementMaterialTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon ability enhancement material table: %w", err)
	}

	catalog := &WeaponCatalog{
		Weapons:                             make(map[int32]WeaponMasterRow, len(weapons)),
		Materials:                           matCatalog.ByType[model.MaterialTypeWeaponEnhancement],
		ExpByEnhanceId:                      make(map[int32][]int32, len(enhanceRows)),
		GoldCostByEnhanceId:                 make(map[int32]NumericalFunc, len(enhanceRows)),
		MaxLevelByEnhanceId:                 make(map[int32]NumericalFunc, len(enhanceRows)),
		SellPriceByEnhanceId:                make(map[int32]NumericalFunc, len(enhanceRows)),
		MedalsByWeaponId:                    make(map[int32]map[int32]int32),
		EvolutionNextWeaponId:               make(map[int32]int32),
		EvolutionMaterials:                  make(map[int32][]WeaponEvolutionMaterialRow),
		EvolutionCostByEnhanceId:            make(map[int32]NumericalFunc, len(enhanceRows)),
		AbilitySlots:                        make(map[int32][]int32),
		SkillGroupsByGroupId:                make(map[int32][]WeaponSkillGroupRow),
		SkillEnhanceMats:                    make(map[[2]int32][]WeaponSkillEnhanceMaterialRow),
		SkillMaxLevelByEnhanceId:            make(map[int32]NumericalFunc, len(enhanceRows)),
		SkillCostByEnhanceId:                make(map[int32]NumericalFunc, len(enhanceRows)),
		AbilityGroupsByGroupId:              make(map[int32][]WeaponAbilityGroupRow),
		AbilityEnhanceMats:                  make(map[[2]int32][]WeaponAbilityEnhanceMaterialRow),
		AbilityMaxLevelByEnhanceId:          make(map[int32]NumericalFunc, len(enhanceRows)),
		AbilityCostByEnhanceId:              make(map[int32]NumericalFunc, len(enhanceRows)),
		EnhanceCostByWeaponByEnhanceId:      make(map[int32]NumericalFunc, len(enhanceRows)),
		LimitBreakCostByWeaponByEnhanceId:   make(map[int32]NumericalFunc, len(enhanceRows)),
		LimitBreakCostByMaterialByEnhanceId: make(map[int32]NumericalFunc, len(enhanceRows)),
		BaseExpByEnhanceId:                  make(map[int32]int32, len(enhanceRows)),
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
		if _, ok := catalog.EvolutionCostByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.EvolutionCostNumericalFunctionId); found {
				catalog.EvolutionCostByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.SkillMaxLevelByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.MaxSkillLevelNumericalFunctionId); found {
				catalog.SkillMaxLevelByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.SkillCostByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.SkillEnhancementCostNumericalFunctionId); found {
				catalog.SkillCostByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.AbilityMaxLevelByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.MaxAbilityLevelNumericalFunctionId); found {
				catalog.AbilityMaxLevelByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.AbilityCostByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.AbilityEnhancementCostNumericalFunctionId); found {
				catalog.AbilityCostByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.EnhanceCostByWeaponByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.EnhancementCostByWeaponNumericalFunctionId); found {
				catalog.EnhanceCostByWeaponByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.LimitBreakCostByWeaponByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.LimitBreakCostByWeaponNumericalFunctionId); found {
				catalog.LimitBreakCostByWeaponByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.LimitBreakCostByMaterialByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			if f, found := funcResolver.Resolve(r.LimitBreakCostByMaterialNumericalFunctionId); found {
				catalog.LimitBreakCostByMaterialByEnhanceId[r.WeaponSpecificEnhanceId] = f
			}
		}
		if _, ok := catalog.BaseExpByEnhanceId[r.WeaponSpecificEnhanceId]; !ok {
			catalog.BaseExpByEnhanceId[r.WeaponSpecificEnhanceId] = r.BaseEnhancementObtainedExp
		}
	}

	for _, ex := range exchangeRows {
		if catalog.MedalsByWeaponId[ex.WeaponId] == nil {
			catalog.MedalsByWeaponId[ex.WeaponId] = make(map[int32]int32)
		}
		catalog.MedalsByWeaponId[ex.WeaponId][ex.ConsumableItemId] = ex.Count
	}

	grouped := make(map[int32][]WeaponEvolutionGroupRow)
	for _, row := range evoGroupRows {
		grouped[row.WeaponEvolutionGroupId] = append(grouped[row.WeaponEvolutionGroupId], row)
	}
	for _, rows := range grouped {
		sort.Slice(rows, func(i, j int) bool {
			return rows[i].EvolutionOrder < rows[j].EvolutionOrder
		})
		for i := 0; i < len(rows)-1; i++ {
			catalog.EvolutionNextWeaponId[rows[i].WeaponId] = rows[i+1].WeaponId
		}
	}

	for _, row := range evoMatRows {
		catalog.EvolutionMaterials[row.WeaponEvolutionMaterialGroupId] = append(
			catalog.EvolutionMaterials[row.WeaponEvolutionMaterialGroupId], row)
	}

	for _, row := range abilityGroupRows {
		catalog.AbilitySlots[row.WeaponAbilityGroupId] = append(
			catalog.AbilitySlots[row.WeaponAbilityGroupId], row.SlotNumber)
	}

	for _, row := range skillGroupRows {
		catalog.SkillGroupsByGroupId[row.WeaponSkillGroupId] = append(
			catalog.SkillGroupsByGroupId[row.WeaponSkillGroupId], row)
	}

	for _, row := range skillMatRows {
		key := [2]int32{row.WeaponSkillEnhancementMaterialId, row.SkillLevel}
		catalog.SkillEnhanceMats[key] = append(catalog.SkillEnhanceMats[key], row)
	}

	for _, row := range abilityGroupRows {
		catalog.AbilityGroupsByGroupId[row.WeaponAbilityGroupId] = append(
			catalog.AbilityGroupsByGroupId[row.WeaponAbilityGroupId], row)
	}

	for _, row := range abilityMatRows {
		key := [2]int32{row.WeaponAbilityEnhancementMaterialId, row.AbilityLevel}
		catalog.AbilityEnhanceMats[key] = append(catalog.AbilityEnhanceMats[key], row)
	}

	return catalog, nil
}
