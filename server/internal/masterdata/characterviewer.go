package masterdata

import (
	"log"
	"sort"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/utils"
)

type characterViewerField struct {
	CharacterViewerFieldId     int32 `json:"CharacterViewerFieldId"`
	ReleaseEvaluateConditionId int32 `json:"ReleaseEvaluateConditionId"`
}

type evaluateCondition struct {
	EvaluateConditionId             int32 `json:"EvaluateConditionId"`
	EvaluateConditionFunctionType   int32 `json:"EvaluateConditionFunctionType"`
	EvaluateConditionEvaluateType   int32 `json:"EvaluateConditionEvaluateType"`
	EvaluateConditionValueGroupId   int32 `json:"EvaluateConditionValueGroupId"`
}

type evaluateConditionValueGroup struct {
	EvaluateConditionValueGroupId int32 `json:"EvaluateConditionValueGroupId"`
	GroupIndex                    int32 `json:"GroupIndex"`
	Value                         int64 `json:"Value"`
}

const (
	evaluateConditionFunctionTypeQuestClear = 4
	evaluateConditionEvaluateTypeIDContain  = 4
	defaultGroupIndex                       = 1
)

type characterViewerFieldEntry struct {
	FieldId         int32
	RequiredQuestId int32
}

type CharacterViewerCatalog struct {
	fields []characterViewerFieldEntry
}

func (c *CharacterViewerCatalog) ReleasedFieldIds(user store.UserState) []int32 {
	var released []int32
	for _, f := range c.fields {
		if f.RequiredQuestId == 0 {
			released = append(released, f.FieldId)
			continue
		}
		q, ok := user.Quests[f.RequiredQuestId]
		if ok && q.QuestStateType == model.UserQuestStateTypeCleared {
			released = append(released, f.FieldId)
		}
	}
	return released
}

func LoadCharacterViewerCatalog() *CharacterViewerCatalog {
	fields, err := utils.ReadJSON[characterViewerField]("EntityMCharacterViewerFieldTable.json")
	if err != nil {
		log.Fatalf("load character viewer field table: %v", err)
	}
	conditions, err := utils.ReadJSON[evaluateCondition]("EntityMEvaluateConditionTable.json")
	if err != nil {
		log.Fatalf("load evaluate condition table: %v", err)
	}
	valueGroups, err := utils.ReadJSON[evaluateConditionValueGroup]("EntityMEvaluateConditionValueGroupTable.json")
	if err != nil {
		log.Fatalf("load evaluate condition value group table: %v", err)
	}

	condById := make(map[int32]evaluateCondition, len(conditions))
	for _, c := range conditions {
		condById[c.EvaluateConditionId] = c
	}

	type vgKey struct {
		GroupId    int32
		GroupIndex int32
	}
	vgByKey := make(map[vgKey]int64, len(valueGroups))
	for _, vg := range valueGroups {
		vgByKey[vgKey{vg.EvaluateConditionValueGroupId, vg.GroupIndex}] = vg.Value
	}

	cat := &CharacterViewerCatalog{}
	for _, f := range fields {
		entry := characterViewerFieldEntry{FieldId: f.CharacterViewerFieldId}
		if cond, ok := condById[f.ReleaseEvaluateConditionId]; ok &&
			cond.EvaluateConditionFunctionType == evaluateConditionFunctionTypeQuestClear &&
			cond.EvaluateConditionEvaluateType == evaluateConditionEvaluateTypeIDContain {
			if questId, ok := vgByKey[vgKey{cond.EvaluateConditionValueGroupId, defaultGroupIndex}]; ok {
				entry.RequiredQuestId = int32(questId)
			}
		}
		cat.fields = append(cat.fields, entry)
	}

	sort.Slice(cat.fields, func(i, j int) bool {
		return cat.fields[i].FieldId < cat.fields[j].FieldId
	})

	log.Printf("character viewer catalog loaded: %d fields", len(cat.fields))
	return cat
}
