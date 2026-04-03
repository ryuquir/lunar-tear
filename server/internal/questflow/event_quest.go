package questflow

import (
	"fmt"
	"log"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

func (h *QuestHandler) HandleEventQuestStart(user *store.UserState, eventQuestChapterId, questId int32, isBattleOnly bool, userDeckNumber int32, nowMillis int64) {
	quest, ok := h.QuestById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleEventQuestStart", questId))
	}

	h.initQuestState(user, questId)

	if quest.Stamina > 0 {
		maxMillis := h.MaxStaminaByLevel[user.Status.Level] * 1000
		store.ConsumeStamina(user, quest.Stamina, maxMillis, nowMillis)
	}

	questState := user.Quests[questId]
	questState.IsBattleOnly = isBattleOnly
	questState.UserDeckNumber = userDeckNumber
	questState.QuestStateType = model.UserQuestStateTypeActive
	questState.LatestStartDatetime = nowMillis
	user.Quests[questId] = questState

	user.EventQuest.CurrentEventQuestChapterId = eventQuestChapterId
	user.EventQuest.CurrentQuestId = questId
	if sceneIds := h.SceneIdsByQuestId[questId]; len(sceneIds) > 0 {
		user.EventQuest.CurrentQuestSceneId = sceneIds[0]
		user.EventQuest.HeadQuestSceneId = sceneIds[0]
	}
}

func (h *QuestHandler) HandleEventQuestFinish(user *store.UserState, eventQuestChapterId, questId int32, isRetired bool, nowMillis int64) FinishOutcome {
	_, ok := h.QuestById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleEventQuestFinish", questId))
	}

	outcome := h.evaluateFinishOutcome(user, questId)

	questState := user.Quests[questId]
	if !questState.IsRewardGranted && !isRetired {
		h.applyQuestRewards(user, questId, nowMillis)
		h.grantWeaponStoryUnlocksForQuestScene(user, questId, model.QuestResultTypeHalfResult, nowMillis)
		h.grantWeaponStoryUnlocksForQuestScene(user, questId, model.QuestResultTypeFullResult, nowMillis)
		questState.IsRewardGranted = true
	}
	if !isRetired {
		for _, drop := range outcome.DropRewards {
			h.applyRewardPossession(user, drop.PossessionType, drop.PossessionId, drop.Count, nowMillis)
		}
	}
	questState.QuestStateType = model.UserQuestStateTypeCleared
	questState.ClearCount++
	questState.DailyClearCount++
	questState.LastClearDatetime = nowMillis
	user.Quests[questId] = questState

	user.EventQuest.CurrentQuestId = 0
	user.EventQuest.CurrentQuestSceneId = 0
	user.EventQuest.HeadQuestSceneId = 0

	h.clearQuestMissions(user, questId, nowMillis)

	return outcome
}

func (h *QuestHandler) HandleEventQuestRestart(user *store.UserState, eventQuestChapterId, questId int32, nowMillis int64) {
	h.HandleQuestRestart(user, questId, nowMillis)

	user.EventQuest.CurrentEventQuestChapterId = eventQuestChapterId
	user.EventQuest.CurrentQuestId = questId
}

func (h *QuestHandler) HandleEventQuestSceneProgress(user *store.UserState, questSceneId int32, nowMillis int64) {
	scene, ok := h.SceneById[questSceneId]
	if !ok {
		log.Printf("[HandleEventQuestSceneProgress] unknown sceneId=%d, skipping", questSceneId)
		return
	}

	user.EventQuest.CurrentQuestSceneId = questSceneId
	if h.isSceneAhead(questSceneId, user.EventQuest.HeadQuestSceneId) {
		user.EventQuest.HeadQuestSceneId = questSceneId
	}

	h.applySceneGrants(user, questSceneId, nowMillis)

	if scene.QuestResultType == model.QuestResultTypeHalfResult {
		h.clearQuestMissions(user, scene.QuestId, nowMillis)
	}
}
