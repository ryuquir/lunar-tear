package questflow

import (
	"fmt"
	"log"

	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

func (e *Engine) applySceneGrants(user *store.UserState, questSceneId int32, nowMillis int64) {
	grants, ok := e.sceneGrantsBySceneId[questSceneId]
	if !ok {
		return
	}
	for _, g := range grants {
		e.applyRewardPossession(user, g.PossessionType, g.PossessionId, g.Count, nowMillis)
	}
}

func (e *Engine) isSceneAhead(newSceneId, currentHeadId int32) bool {
	if currentHeadId == 0 {
		return true
	}
	return e.sceneById[newSceneId].SortOrder > e.sceneById[currentHeadId].SortOrder
}

func (e *Engine) HandleMainFlowSceneProgress(user *store.UserState, questSceneId int32, nowMillis int64) {
	scene, ok := e.sceneById[questSceneId]
	if !ok {
		panic(fmt.Sprintf("unknown sceneId=%d for HandleMainFlowSceneProgress", questSceneId))
	}

	quest, ok := e.questById[scene.QuestId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleMainFlowSceneProgress", questSceneId))
	}

	user.MainQuest.CurrentQuestSceneId = questSceneId
	if e.isSceneAhead(questSceneId, user.MainQuest.HeadQuestSceneId) {
		user.MainQuest.HeadQuestSceneId = questSceneId
	}
	user.MainQuest.CurrentQuestFlowType = int32(model.QuestFlowTypeMainFlow)

	lastSceneId := e.getLastMainFlowSceneId(scene.QuestId)
	user.MainQuest.IsReachedLastQuestScene = questSceneId == lastSceneId

	routeId, ok := e.routeIdByQuestId[quest.QuestId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleMainFlowSceneProgress setting currentMainQuestRouteId", quest.QuestId))
	}
	user.MainQuest.CurrentMainQuestRouteId = routeId

	user.PortalCageStatus.IsCurrentProgress = false
	user.PortalCageStatus.LatestVersion = nowMillis

	e.applySceneGrants(user, questSceneId, nowMillis)
}

func (e *Engine) advanceTutorialsForScene(user *store.UserState, sceneId int32) {
	currentScene, ok := e.sceneById[sceneId]
	if !ok {
		log.Printf("[advanceTutorialsForScene] unknown sceneId=%d", sceneId)
		return
	}
	for _, cond := range e.tutorialUnlockConditions {
		condScene, ok := e.sceneById[cond.ConditionValue]
		if !ok {
			log.Printf("[advanceTutorialsForScene] unknown conditionValue=%d", cond.ConditionValue)
			continue
		}
		if currentScene.SortOrder >= condScene.SortOrder {
			if _, exists := user.Tutorials[cond.TutorialType]; !exists {
				user.Tutorials[cond.TutorialType] = store.TutorialProgressState{
					TutorialType:  cond.TutorialType,
					ProgressPhase: 99999,
				}
			}
		}
	}
}

func (e *Engine) getLastMainFlowSceneId(questId int32) int32 {
	sceneIds := e.sceneIdsByQuestId[questId]
	if len(sceneIds) == 0 {
		panic(fmt.Sprintf("no scenes found for questId=%d", questId))
	}
	return sceneIds[len(sceneIds)-1]
}

func (e *Engine) HandleMainQuestSceneProgress(user *store.UserState, questSceneId int32) {
	scene, ok := e.sceneById[questSceneId]
	if !ok {
		panic(fmt.Sprintf("unknown sceneId=%d for HandleMainQuestSceneProgress", questSceneId))
	}

	quest, ok := e.questById[scene.QuestId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleMainQuestSceneProgress", questSceneId))
	}

	user.MainQuest.CurrentQuestSceneId = questSceneId
	if e.isSceneAhead(questSceneId, user.MainQuest.HeadQuestSceneId) {
		user.MainQuest.HeadQuestSceneId = questSceneId
	}
	lastSceneId := e.getLastMainFlowSceneId(quest.QuestId)
	user.MainQuest.IsReachedLastQuestScene = questSceneId == lastSceneId

	if isMainQuestPlayable(quest) {
		if scene.QuestResultType == model.QuestResultTypeHalfResult {
			nowMillis := gametime.NowMillis()
			e.clearQuestMissions(user, quest.QuestId, nowMillis)
		}

		user.MainQuest.ProgressQuestSceneId = questSceneId
		if e.isSceneAhead(questSceneId, user.MainQuest.ProgressHeadQuestSceneId) {
			user.MainQuest.ProgressHeadQuestSceneId = questSceneId
		}
		user.MainQuest.CurrentQuestFlowType = int32(model.QuestFlowTypeSubFlow)
		user.MainQuest.ProgressQuestFlowType = int32(model.QuestFlowTypeSubFlow)
	}
}
