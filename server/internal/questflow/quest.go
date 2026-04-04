package questflow

import (
	"fmt"
	"log"

	"lunar-tear/server/internal/masterdata"
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

func (h *QuestHandler) initQuestState(user *store.UserState, questId int32) {
	quest := user.Quests[questId]
	quest.QuestId = questId
	user.Quests[questId] = quest

	for _, missionId := range h.MissionIdsByQuestId[questId] {
		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: missionId}
		mission := user.QuestMissions[key]
		mission.QuestId = questId
		mission.QuestMissionId = missionId
		user.QuestMissions[key] = mission
	}
}

func isMainQuestPlayable(quest masterdata.QuestRow) bool {
	return !quest.IsRunInTheBackground && quest.IsCountedAsQuest
}

func (h *QuestHandler) clearQuestMissions(user *store.UserState, questId int32, nowMillis int64) {
	for _, missionId := range h.MissionIdsByQuestId[questId] {
		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: missionId}
		mission := user.QuestMissions[key]
		mission.IsClear = true
		mission.ProgressValue = 1
		mission.LatestClearDatetime = nowMillis
		user.QuestMissions[key] = mission
	}
}

func (h *QuestHandler) HandleQuestStart(user *store.UserState, questId int32, isBattleOnly bool, userDeckNumber int32, nowMillis int64) {
	quest, ok := h.QuestById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleQuestStart", questId))
	}

	h.initQuestState(user, questId)

	if quest.Stamina > 0 {
		maxMillis := h.MaxStaminaByLevel[user.Status.Level] * 1000
		store.ConsumeStamina(user, quest.Stamina, maxMillis, nowMillis)
	}

	questState := user.Quests[questId]
	if questState.QuestStateType == model.UserQuestStateTypeCleared {
		return
	}

	questState.IsBattleOnly = isBattleOnly
	questState.UserDeckNumber = userDeckNumber
	if isMainQuestPlayable(quest) {
		user.MainQuest.CurrentQuestFlowType = int32(model.QuestFlowTypeMainFlow)
		questState.QuestStateType = model.UserQuestStateTypeActive
		questState.LatestStartDatetime = nowMillis
	} else {
		questState.QuestStateType = model.UserQuestStateTypeCleared
		questState.ClearCount = 1
		questState.DailyClearCount = 1
		questState.LastClearDatetime = nowMillis

		if sceneIds := h.SceneIdsByQuestId[questId]; len(sceneIds) > 0 {
			firstSceneId := sceneIds[0]
			prevSceneId := user.MainQuest.CurrentQuestSceneId
			user.MainQuest.CurrentQuestSceneId = firstSceneId
			if h.isSceneAhead(firstSceneId, user.MainQuest.HeadQuestSceneId) {
				user.MainQuest.HeadQuestSceneId = firstSceneId
			}
			user.MainQuest.CurrentQuestFlowType = int32(model.QuestFlowTypeMainFlow)
			lastSceneId := h.getLastMainFlowSceneId(questId)
			user.MainQuest.IsReachedLastQuestScene = firstSceneId == lastSceneId
			log.Printf("[HandleQuestStart] background quest %d auto-cleared, scene %d -> %d", questId, prevSceneId, firstSceneId)
		}
	}
	user.Quests[questId] = questState
}

func (h *QuestHandler) HandleQuestFinish(user *store.UserState, questId int32, isRetired bool, nowMillis int64) FinishOutcome {
	_, ok := h.QuestById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleQuestFinish", questId))
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
	questState.ClearCount = 1
	questState.DailyClearCount = 1
	questState.LastClearDatetime = nowMillis

	user.MainQuest.ProgressQuestSceneId = 0
	user.MainQuest.ProgressHeadQuestSceneId = 0
	user.MainQuest.ProgressQuestFlowType = 0
	user.MainQuest.CurrentQuestFlowType = int32(model.QuestFlowTypeUnknown)
	user.Quests[questId] = questState

	h.clearQuestMissions(user, questId, nowMillis)

	return outcome
}

func (h *QuestHandler) HandleQuestSkip(user *store.UserState, questId, skipCount int32, nowMillis int64) FinishOutcome {
	questMeta, ok := h.QuestById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleQuestSkip", questId))
	}

	maxMillis := h.MaxStaminaByLevel[user.Status.Level] * 1000
	store.ConsumeStamina(user, skipCount, maxMillis, nowMillis)

	user.ConsumableItems[skipTicketConsumableItemId] -= skipCount
	if user.ConsumableItems[skipTicketConsumableItemId] < 0 {
		user.ConsumableItems[skipTicketConsumableItemId] = 0
	}

	var allDrops []RewardGrant
	for range skipCount {
		drops := h.computeDropRewards(questMeta)
		for _, drop := range drops {
			h.applyRewardPossession(user, drop.PossessionType, drop.PossessionId, drop.Count, nowMillis)
		}
		allDrops = append(allDrops, drops...)

		if questMeta.Gold != 0 {
			user.ConsumableItems[goldConsumableItemId] += questMeta.Gold
		}
		h.applyExpRewards(user, questId, nowMillis)
	}

	questState := user.Quests[questId]
	questState.ClearCount += skipCount
	questState.DailyClearCount += skipCount
	questState.LastClearDatetime = nowMillis
	user.Quests[questId] = questState

	log.Printf("[HandleQuestSkip] questId=%d skipCount=%d drops=%d gold=%d", questId, skipCount, len(allDrops), questMeta.Gold*skipCount)
	return FinishOutcome{DropRewards: allDrops}
}

func (h *QuestHandler) HandleQuestRestart(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := h.QuestById[questId]
	if ok && isMainQuestPlayable(questMeta) {
		user.MainQuest.CurrentQuestFlowType = int32(model.QuestFlowTypeMainFlow)
	}

	quest := user.Quests[questId]
	quest.QuestId = questId
	quest.QuestStateType = model.UserQuestStateTypeActive
	quest.IsBattleOnly = false
	quest.LatestStartDatetime = nowMillis
	user.Quests[questId] = quest

	for _, missionId := range h.MissionIdsByQuestId[questId] {
		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: missionId}
		m := user.QuestMissions[key]
		m.QuestId = questId
		m.QuestMissionId = missionId
		m.IsClear = false
		m.ProgressValue = 0
		m.LatestClearDatetime = 0
		user.QuestMissions[key] = m
	}
}
