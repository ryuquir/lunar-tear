package questflow

import (
	"fmt"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

func (h *QuestHandler) HandleBigHuntQuestStart(user *store.UserState, questId, userDeckNumber int32, nowMillis int64) {
	quest, ok := h.QuestById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleBigHuntQuestStart", questId))
	}

	h.initQuestState(user, questId)

	if quest.Stamina > 0 {
		maxMillis := h.MaxStaminaByLevel[user.Status.Level] * 1000
		store.ConsumeStamina(user, quest.Stamina, maxMillis, nowMillis)
	}

	questState := user.Quests[questId]
	questState.UserDeckNumber = userDeckNumber
	questState.QuestStateType = model.UserQuestStateTypeActive
	questState.LatestStartDatetime = nowMillis
	user.Quests[questId] = questState
}

func (h *QuestHandler) HandleBigHuntQuestFinish(user *store.UserState, questId int32, isRetired, isAnnihilated bool, nowMillis int64) FinishOutcome {
	quest, ok := h.QuestById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleBigHuntQuestFinish", questId))
	}

	outcome := h.evaluateFinishOutcome(user, questId)
	if !isRetired {
		h.applyQuestVictory(user, questId, outcome, nowMillis)
	}

	if isRetired && !isAnnihilated && quest.Stamina > 1 {
		refund := quest.Stamina - 1
		maxMillis := h.MaxStaminaByLevel[user.Status.Level] * 1000
		store.RecoverStamina(user, refund*1000, maxMillis, nowMillis)
	}

	h.clearQuestMissions(user, questId, nowMillis)

	return outcome
}
