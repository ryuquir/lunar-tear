package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type evaluateCondition struct {
	EvaluateConditionId           int32                               `json:"EvaluateConditionId"`
	EvaluateConditionFunctionType model.EvaluateConditionFunctionType `json:"EvaluateConditionFunctionType"`
	EvaluateConditionEvaluateType model.EvaluateConditionEvaluateType `json:"EvaluateConditionEvaluateType"`
	EvaluateConditionValueGroupId int32                               `json:"EvaluateConditionValueGroupId"`
}

type evaluateConditionValueGroup struct {
	EvaluateConditionValueGroupId int32 `json:"EvaluateConditionValueGroupId"`
	GroupIndex                    int32 `json:"GroupIndex"`
	Value                         int64 `json:"Value"`
}

const defaultGroupIndex = 1

type ConditionResolver struct {
	requiredQuestByCondId map[int32]int32
}

func LoadConditionResolver() (*ConditionResolver, error) {
	conditions, err := utils.ReadJSON[evaluateCondition]("EntityMEvaluateConditionTable.json")
	if err != nil {
		return nil, fmt.Errorf("load evaluate condition table: %w", err)
	}
	valueGroups, err := utils.ReadJSON[evaluateConditionValueGroup]("EntityMEvaluateConditionValueGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load evaluate condition value group table: %w", err)
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

	resolved := make(map[int32]int32)
	for _, c := range conditions {
		if c.EvaluateConditionFunctionType == model.EvaluateConditionFunctionTypeQuestClear &&
			c.EvaluateConditionEvaluateType == model.EvaluateConditionEvaluateTypeIdContain {
			if questId, ok := vgByKey[vgKey{c.EvaluateConditionValueGroupId, defaultGroupIndex}]; ok {
				resolved[c.EvaluateConditionId] = int32(questId)
			}
		}
	}

	return &ConditionResolver{requiredQuestByCondId: resolved}, nil
}

func (r *ConditionResolver) RequiredQuestId(conditionId int32) (int32, bool) {
	qid, ok := r.requiredQuestByCondId[conditionId]
	return qid, ok
}
