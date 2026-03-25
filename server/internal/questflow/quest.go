package questflow

import (
	"fmt"
	"log"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

func (e *Engine) initQuestState(user *store.UserState, questId int32) {
	quest := user.Quests[questId]
	quest.QuestId = questId
	user.Quests[questId] = quest

	for _, missionId := range e.missionIdsByQuestId[questId] {
		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: missionId}
		mission := user.QuestMissions[key]
		mission.QuestId = questId
		mission.QuestMissionId = missionId
		user.QuestMissions[key] = mission
	}
}

func isMainQuestPlayable(quest quest) bool {
	return !quest.IsRunInTheBackground && quest.IsCountedAsQuest
}

func (e *Engine) clearQuestMissions(user *store.UserState, questId int32, nowMillis int64) {
	for _, missionId := range e.missionIdsByQuestId[questId] {
		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: missionId}
		mission := user.QuestMissions[key]
		mission.IsClear = true
		mission.ProgressValue = 1
		mission.LatestClearDatetime = nowMillis
		user.QuestMissions[key] = mission
	}
}

func (e *Engine) HandleQuestStart(user *store.UserState, questId int32, isBattleOnly bool, userDeckNumber int32, nowMillis int64) {
	quest, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleQuestStart", questId))
	}

	e.initQuestState(user, questId)

	if quest.Stamina > 0 {
		user.Status.StaminaMilliValue = max(user.Status.StaminaMilliValue-quest.Stamina*1000, 0)
		user.Status.StaminaUpdateDatetime = nowMillis
		log.Printf("[HandleQuestStart] questId=%d stamina cost=%d -> remaining=%d", questId, quest.Stamina, user.Status.StaminaMilliValue)
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
	}
	user.Quests[questId] = questState
}

func (e *Engine) HandleQuestFinish(user *store.UserState, questId int32, isRetired bool, nowMillis int64) FinishOutcome {
	_, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleQuestFinish", questId))
	}

	outcome := e.evaluateFinishOutcome(user, questId)

	questState := user.Quests[questId]
	if !questState.IsRewardGranted && !isRetired {
		e.applyQuestRewards(user, questId, nowMillis)
		e.grantWeaponStoryUnlocksForQuestScene(user, questId, model.QuestResultTypeHalfResult, nowMillis)
		e.grantWeaponStoryUnlocksForQuestScene(user, questId, model.QuestResultTypeFullResult, nowMillis)
		questState.IsRewardGranted = true
	}
	if !isRetired {
		for _, drop := range outcome.DropRewards {
			e.applyRewardPossession(user, drop.PossessionType, drop.PossessionId, drop.Count, nowMillis)
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

	e.clearQuestMissions(user, questId, nowMillis)

	return outcome
}

func (e *Engine) HandleQuestRestart(user *store.UserState, questId int32, nowMillis int64) {
	quest := user.Quests[questId]
	quest.QuestId = questId
	quest.QuestStateType = model.UserQuestStateTypeActive
	quest.IsBattleOnly = false
	quest.LatestStartDatetime = nowMillis
	user.Quests[questId] = quest

	for _, missionId := range e.missionIdsByQuestId[questId] {
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
