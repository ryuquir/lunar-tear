package questflow

import (
	"lunar-tear/server/internal/masterdata"
	"lunar-tear/server/internal/model"
)

type RewardGrant struct {
	PossessionType model.PossessionType
	PossessionId   int32
	Count          int32
}

type FinishOutcome struct {
	DropRewards                  []RewardGrant
	FirstClearRewards            []RewardGrant
	MissionClearRewards          []RewardGrant
	MissionClearCompleteRewards  []RewardGrant
	BigWinClearedQuestMissionIds []int32
	IsBigWin                     bool
}

type QuestHandler struct {
	*masterdata.QuestCatalog
	Config *masterdata.GameConfig
}

func NewQuestHandler(catalog *masterdata.QuestCatalog, config *masterdata.GameConfig) *QuestHandler {
	return &QuestHandler{QuestCatalog: catalog, Config: config}
}
