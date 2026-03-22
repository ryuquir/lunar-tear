package masterdata

import (
	"log"
	"lunar-tear/server/internal/utils"
)

type cageOrnament struct {
	CageOrnamentId       int32 `json:"CageOrnamentId"`
	CageOrnamentRewardId int32 `json:"CageOrnamentRewardId"`
}

type cageOrnamentRewardRow struct {
	CageOrnamentRewardId int32 `json:"CageOrnamentRewardId"`
	PossessionType       int32 `json:"PossessionType"`
	PossessionId         int32 `json:"PossessionId"`
	Count                int32 `json:"Count"`
}

type CageOrnamentReward struct {
	PossessionType int32
	PossessionId   int32
	Count          int32
}

type CageOrnamentCatalog struct {
	ornamentToRewardId map[int32]int32
	rewards            map[int32]CageOrnamentReward
}

func (c *CageOrnamentCatalog) LookupReward(cageOrnamentId int32) (CageOrnamentReward, bool) {
	rewardId, ok := c.ornamentToRewardId[cageOrnamentId]
	if !ok || rewardId == 0 {
		return CageOrnamentReward{}, false
	}
	entry, ok := c.rewards[rewardId]
	return entry, ok
}

func LoadCageOrnamentCatalog() *CageOrnamentCatalog {
	ornaments, err := utils.ReadJSON[cageOrnament]("EntityMCageOrnamentTable.json")
	if err != nil {
		log.Fatalf("load cage ornament table: %v", err)
	}
	rewards, err := utils.ReadJSON[cageOrnamentRewardRow]("EntityMCageOrnamentRewardTable.json")
	if err != nil {
		log.Fatalf("load cage ornament reward table: %v", err)
	}

	cat := &CageOrnamentCatalog{
		ornamentToRewardId: make(map[int32]int32, len(ornaments)),
		rewards:            make(map[int32]CageOrnamentReward, len(rewards)),
	}
	for _, o := range ornaments {
		cat.ornamentToRewardId[o.CageOrnamentId] = o.CageOrnamentRewardId
	}
	for _, r := range rewards {
		cat.rewards[r.CageOrnamentRewardId] = CageOrnamentReward{
			PossessionType: r.PossessionType,
			PossessionId:   r.PossessionId,
			Count:          r.Count,
		}
	}
	return cat
}
