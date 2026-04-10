package masterdata

import (
	"log"
	"lunar-tear/server/internal/utils"
)

type sideStorySceneRow struct {
	SideStoryQuestId      int32 `json:"SideStoryQuestId"`
	SideStoryQuestSceneId int32 `json:"SideStoryQuestSceneId"`
	SortOrder             int32 `json:"SortOrder"`
}

type SideStoryCatalog struct {
	FirstSceneByQuestId map[int32]int32
}

func LoadSideStoryCatalog() *SideStoryCatalog {
	scenes, err := utils.ReadJSON[sideStorySceneRow]("EntityMSideStoryQuestSceneTable.json")
	if err != nil {
		log.Fatalf("load side story quest scene table: %v", err)
	}

	firstScene := make(map[int32]int32, len(scenes)/7)
	for _, s := range scenes {
		if s.SortOrder == 1 {
			firstScene[s.SideStoryQuestId] = s.SideStoryQuestSceneId
		}
	}

	log.Printf("side story catalog loaded: %d quests", len(firstScene))
	return &SideStoryCatalog{FirstSceneByQuestId: firstScene}
}
