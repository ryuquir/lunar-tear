package questflow

import (
	"log"

	"lunar-tear/server/internal/store"
)

func (e *Engine) ApplyBootstrap(user *store.UserState, sceneId int32, nowMillis int64) {
	if sceneId == 0 {
		return
	}
	scene, ok := e.sceneById[sceneId]
	if !ok {
		log.Fatalf("[ApplyBootstrap] unknown sceneId=%d for ApplyBootstrap", sceneId)
	}
	targetQuestId := scene.QuestId
	targetRouteId := e.routeIdByQuestId[targetQuestId]

	for _, questId := range e.orderedQuestIds {
		if questId == targetQuestId {
			break
		}
		if e.routeIdByQuestId[questId] != targetRouteId {
			continue
		}

		quest, ok := e.questById[questId]
		if !ok {
			continue
		}

		e.HandleQuestStart(user, questId, false, nowMillis)
		for _, sid := range e.sceneIdsByQuestId[questId] {
			e.HandleMainFlowSceneProgress(user, sid, nowMillis)
			e.HandleMainQuestSceneProgress(user, sid)
		}
		if isMainQuestPlayable(quest) {
			e.HandleQuestFinish(user, questId, false, nowMillis)
		}
	}

	e.initQuestState(user, targetQuestId)
	for _, sid := range e.sceneIdsByQuestId[targetQuestId] {
		e.HandleMainFlowSceneProgress(user, sid, nowMillis)
		if sid == sceneId {
			break
		}
	}

	user.Profile.Name = "Lunar Tear"

	e.advanceTutorialForBootstrap(user, sceneId)
}

func (e *Engine) advanceTutorialForBootstrap(user *store.UserState, bootstrapSceneId int32) {
	before := len(user.Tutorials)
	e.advanceTutorialsForScene(user, bootstrapSceneId)
	added := len(user.Tutorials) - before
	if added > 0 {
		log.Printf("[ApplyBootstrap] marked %d tutorials as completed for scene=%d", added, bootstrapSceneId)
	}
}
