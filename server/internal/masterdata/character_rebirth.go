package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/utils"
)

type CharacterRebirthRow struct {
	CharacterId                 int32 `json:"CharacterId"`
	CharacterRebirthStepGroupId int32 `json:"CharacterRebirthStepGroupId"`
}

type CharacterRebirthStepRow struct {
	CharacterRebirthStepGroupId     int32 `json:"CharacterRebirthStepGroupId"`
	BeforeRebirthCount              int32 `json:"BeforeRebirthCount"`
	CostumeLevelLimitUp             int32 `json:"CostumeLevelLimitUp"`
	CharacterRebirthMaterialGroupId int32 `json:"CharacterRebirthMaterialGroupId"`
}

type CharacterRebirthMaterialRow struct {
	CharacterRebirthMaterialGroupId int32 `json:"CharacterRebirthMaterialGroupId"`
	MaterialId                      int32 `json:"MaterialId"`
	Count                           int32 `json:"Count"`
}

type StepKey struct {
	GroupId            int32
	BeforeRebirthCount int32
}

type CharacterRebirthCatalog struct {
	StepGroupByCharacterId map[int32]int32
	StepByGroupAndCount    map[StepKey]CharacterRebirthStepRow
	MaterialsByGroupId     map[int32][]CharacterRebirthMaterialRow
}

func LoadCharacterRebirthCatalog() (*CharacterRebirthCatalog, error) {
	rebirthRows, err := utils.ReadJSON[CharacterRebirthRow]("EntityMCharacterRebirthTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character rebirth table: %w", err)
	}

	stepRows, err := utils.ReadJSON[CharacterRebirthStepRow]("EntityMCharacterRebirthStepGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character rebirth step group table: %w", err)
	}

	materialRows, err := utils.ReadJSON[CharacterRebirthMaterialRow]("EntityMCharacterRebirthMaterialGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character rebirth material group table: %w", err)
	}

	stepGroupByCharacterId := make(map[int32]int32, len(rebirthRows))
	for _, r := range rebirthRows {
		stepGroupByCharacterId[r.CharacterId] = r.CharacterRebirthStepGroupId
	}

	stepByGroupAndCount := make(map[StepKey]CharacterRebirthStepRow, len(stepRows))
	for _, s := range stepRows {
		stepByGroupAndCount[StepKey{GroupId: s.CharacterRebirthStepGroupId, BeforeRebirthCount: s.BeforeRebirthCount}] = s
	}

	materialsByGroupId := make(map[int32][]CharacterRebirthMaterialRow)
	for _, m := range materialRows {
		materialsByGroupId[m.CharacterRebirthMaterialGroupId] = append(materialsByGroupId[m.CharacterRebirthMaterialGroupId], m)
	}

	return &CharacterRebirthCatalog{
		StepGroupByCharacterId: stepGroupByCharacterId,
		StepByGroupAndCount:    stepByGroupAndCount,
		MaterialsByGroupId:     materialsByGroupId,
	}, nil
}
