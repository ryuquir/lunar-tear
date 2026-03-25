package questflow

import (
	"fmt"
	"log"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

func (e *Engine) HandleEventQuestStart(user *store.UserState, eventQuestChapterId, questId int32, isBattleOnly bool, userDeckNumber int32, nowMillis int64) {
	quest, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleEventQuestStart", questId))
	}

	e.initQuestState(user, questId)

	if quest.Stamina > 0 {
		user.Status.StaminaMilliValue = max(user.Status.StaminaMilliValue-quest.Stamina*1000, 0)
		user.Status.StaminaUpdateDatetime = nowMillis
		log.Printf("[HandleEventQuestStart] questId=%d stamina cost=%d -> remaining=%d", questId, quest.Stamina, user.Status.StaminaMilliValue)
	}

	questState := user.Quests[questId]
	questState.IsBattleOnly = isBattleOnly
	questState.UserDeckNumber = userDeckNumber
	questState.QuestStateType = model.UserQuestStateTypeActive
	questState.LatestStartDatetime = nowMillis
	user.Quests[questId] = questState

	user.EventQuest.CurrentEventQuestChapterId = eventQuestChapterId
	user.EventQuest.CurrentQuestId = questId
	if sceneIds := e.sceneIdsByQuestId[questId]; len(sceneIds) > 0 {
		user.EventQuest.CurrentQuestSceneId = sceneIds[0]
		user.EventQuest.HeadQuestSceneId = sceneIds[0]
	}
}

func (e *Engine) HandleEventQuestFinish(user *store.UserState, eventQuestChapterId, questId int32, isRetired bool, nowMillis int64) FinishOutcome {
	_, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleEventQuestFinish", questId))
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
	questState.ClearCount++
	questState.DailyClearCount++
	questState.LastClearDatetime = nowMillis
	user.Quests[questId] = questState

	user.EventQuest.CurrentQuestId = 0
	user.EventQuest.CurrentQuestSceneId = 0
	user.EventQuest.HeadQuestSceneId = 0

	e.clearQuestMissions(user, questId, nowMillis)

	return outcome
}

func (e *Engine) HandleEventQuestRestart(user *store.UserState, eventQuestChapterId, questId int32, nowMillis int64) {
	e.HandleQuestRestart(user, questId, nowMillis)

	user.EventQuest.CurrentEventQuestChapterId = eventQuestChapterId
	user.EventQuest.CurrentQuestId = questId
}

func (e *Engine) HandleEventQuestSceneProgress(user *store.UserState, questSceneId int32, nowMillis int64) {
	scene, ok := e.sceneById[questSceneId]
	if !ok {
		log.Printf("[HandleEventQuestSceneProgress] unknown sceneId=%d, skipping", questSceneId)
		return
	}

	user.EventQuest.CurrentQuestSceneId = questSceneId
	if e.isSceneAhead(questSceneId, user.EventQuest.HeadQuestSceneId) {
		user.EventQuest.HeadQuestSceneId = questSceneId
	}

	e.applySceneGrants(user, questSceneId, nowMillis)

	if scene.QuestResultType == model.QuestResultTypeHalfResult {
		e.clearQuestMissions(user, scene.QuestId, nowMillis)
	}
}
