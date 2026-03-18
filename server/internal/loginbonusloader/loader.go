package loginbonusloader

import (
	"log"

	"lunar-tear/server/internal/utils"
)

type stamp struct {
	LoginBonusId         int32 `json:"LoginBonusId"`
	LowerPageNumber      int32 `json:"LowerPageNumber"`
	StampNumber          int32 `json:"StampNumber"`
	RewardPossessionType int32 `json:"RewardPossessionType"`
	RewardPossessionId   int32 `json:"RewardPossessionId"`
	RewardCount          int32 `json:"RewardCount"`
}

type stampKey struct {
	LoginBonusId    int32
	LowerPageNumber int32
	StampNumber     int32
}

type RewardEntry struct {
	PossessionType int32
	PossessionId   int32
	Count          int32
}

type Catalog struct {
	stamps map[stampKey]RewardEntry
}

func (c *Catalog) LookupStampReward(loginBonusId, pageNumber, stampNumber int32) (RewardEntry, bool) {
	entry, ok := c.stamps[stampKey{loginBonusId, pageNumber, stampNumber}]
	return entry, ok
}

func LoadCatalog() *Catalog {
	stamps, err := utils.ReadJSON[stamp]("EntityMLoginBonusStampTable.json")
	if err != nil {
		log.Fatalf("load login bonus stamp table: %v", err)
	}

	cat := &Catalog{
		stamps: make(map[stampKey]RewardEntry, len(stamps)),
	}
	for _, s := range stamps {
		cat.stamps[stampKey{s.LoginBonusId, s.LowerPageNumber, s.StampNumber}] = RewardEntry{
			PossessionType: s.RewardPossessionType,
			PossessionId:   s.RewardPossessionId,
			Count:          s.RewardCount,
		}
	}
	return cat
}
