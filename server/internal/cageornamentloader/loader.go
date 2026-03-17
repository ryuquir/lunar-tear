package cageornamentloader

import (
	"log"

	"lunar-tear/server/internal/utils"
)

type ornament struct {
	CageOrnamentId       int32 `json:"CageOrnamentId"`
	CageOrnamentRewardId int32 `json:"CageOrnamentRewardId"`
}

type reward struct {
	CageOrnamentRewardId int32 `json:"CageOrnamentRewardId"`
	PossessionType       int32 `json:"PossessionType"`
	PossessionId         int32 `json:"PossessionId"`
	Count                int32 `json:"Count"`
}

type RewardEntry struct {
	PossessionType int32
	PossessionId   int32
	Count          int32
}

type Catalog struct {
	ornamentToRewardId map[int32]int32
	rewards            map[int32]RewardEntry
}

func (c *Catalog) LookupReward(cageOrnamentId int32) (RewardEntry, bool) {
	rewardId, ok := c.ornamentToRewardId[cageOrnamentId]
	if !ok || rewardId == 0 {
		return RewardEntry{}, false
	}
	entry, ok := c.rewards[rewardId]
	return entry, ok
}

func LoadCatalog() *Catalog {
	ornaments, err := utils.ReadJSON[ornament]("EntityMCageOrnamentTable.json")
	if err != nil {
		log.Fatalf("load cage ornament table: %v", err)
	}
	rewards, err := utils.ReadJSON[reward]("EntityMCageOrnamentRewardTable.json")
	if err != nil {
		log.Fatalf("load cage ornament reward table: %v", err)
	}

	cat := &Catalog{
		ornamentToRewardId: make(map[int32]int32, len(ornaments)),
		rewards:            make(map[int32]RewardEntry, len(rewards)),
	}
	for _, o := range ornaments {
		cat.ornamentToRewardId[o.CageOrnamentId] = o.CageOrnamentRewardId
	}
	for _, r := range rewards {
		cat.rewards[r.CageOrnamentRewardId] = RewardEntry{
			PossessionType: r.PossessionType,
			PossessionId:   r.PossessionId,
			Count:          r.Count,
		}
	}
	return cat
}
