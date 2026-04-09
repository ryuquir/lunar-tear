package masterdata

import (
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type costumeDupRow struct {
	CostumeId      int32 `json:"CostumeId"`
	PossessionType int32 `json:"PossessionType"`
	PossessionId   int32 `json:"PossessionId"`
	Count          int32 `json:"Count"`
}

func LoadDupExchange() (map[int32][]model.DupExchangeEntry, error) {
	result := make(map[int32][]model.DupExchangeEntry)

	costumeRows, err := utils.ReadJSON[costumeDupRow]("EntityMCostumeDuplicationExchangePossessionGroupTable.json")
	if err != nil {
		return nil, err
	}
	for _, r := range costumeRows {
		result[r.CostumeId] = append(result[r.CostumeId], model.DupExchangeEntry{
			PossessionType: r.PossessionType,
			PossessionId:   r.PossessionId,
			Count:          r.Count,
		})
	}

	return result, nil
}

type lbMaterialRow struct {
	CostumeLimitBreakMaterialGroupId int32 `json:"CostumeLimitBreakMaterialGroupId"`
	MaterialId                       int32 `json:"MaterialId"`
}

type costumeLBRef struct {
	CostumeId                        int32 `json:"CostumeId"`
	CostumeLimitBreakMaterialGroupId int32 `json:"CostumeLimitBreakMaterialGroupId"`
}

const dupExchangeFallbackCount int32 = 10

func EnrichDupExchange(dupMap map[int32][]model.DupExchangeEntry, pool *GachaCatalog) (int, error) {
	lbRows, err := utils.ReadJSON[lbMaterialRow]("EntityMCostumeLimitBreakMaterialGroupTable.json")
	if err != nil {
		return 0, err
	}
	groupToMaterial := make(map[int32]int32, len(lbRows))
	for _, r := range lbRows {
		groupToMaterial[r.CostumeLimitBreakMaterialGroupId] = r.MaterialId
	}

	costumeRows, err := utils.ReadJSON[costumeLBRef]("EntityMCostumeTable.json")
	if err != nil {
		return 0, err
	}
	costumeLBGroup := make(map[int32]int32, len(costumeRows))
	for _, r := range costumeRows {
		costumeLBGroup[r.CostumeId] = r.CostumeLimitBreakMaterialGroupId
	}

	added := 0
	for costumeId := range pool.CostumeById {
		if _, exists := dupMap[costumeId]; exists {
			continue
		}
		matId := groupToMaterial[costumeLBGroup[costumeId]]
		if matId == 0 {
			continue
		}
		dupMap[costumeId] = []model.DupExchangeEntry{{
			PossessionType: int32(model.PossessionTypeMaterial),
			PossessionId:   matId,
			Count:          dupExchangeFallbackCount,
		}}
		added++
	}
	return added, nil
}
