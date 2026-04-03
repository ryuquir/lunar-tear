package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/utils"
)

type CharacterBoardPanelRow struct {
	CharacterBoardPanelId                       int32 `json:"CharacterBoardPanelId"`
	CharacterBoardId                            int32 `json:"CharacterBoardId"`
	CharacterBoardPanelUnlockConditionGroupId   int32 `json:"CharacterBoardPanelUnlockConditionGroupId"`
	CharacterBoardPanelReleasePossessionGroupId int32 `json:"CharacterBoardPanelReleasePossessionGroupId"`
	CharacterBoardPanelReleaseRewardGroupId     int32 `json:"CharacterBoardPanelReleaseRewardGroupId"`
	CharacterBoardPanelReleaseEffectGroupId     int32 `json:"CharacterBoardPanelReleaseEffectGroupId"`
	SortOrder                                   int32 `json:"SortOrder"`
	ParentCharacterBoardPanelId                 int32 `json:"ParentCharacterBoardPanelId"`
	PlaceIndex                                  int32 `json:"PlaceIndex"`
}

type CharacterBoardReleasePossessionRow struct {
	CharacterBoardPanelReleasePossessionGroupId int32 `json:"CharacterBoardPanelReleasePossessionGroupId"`
	PossessionType                              int32 `json:"PossessionType"`
	PossessionId                                int32 `json:"PossessionId"`
	Count                                       int32 `json:"Count"`
	SortOrder                                   int32 `json:"SortOrder"`
}

type CharacterBoardReleaseEffectRow struct {
	CharacterBoardPanelReleaseEffectGroupId int32 `json:"CharacterBoardPanelReleaseEffectGroupId"`
	SortOrder                               int32 `json:"SortOrder"`
	CharacterBoardEffectType                int32 `json:"CharacterBoardEffectType"`
	CharacterBoardEffectId                  int32 `json:"CharacterBoardEffectId"`
	EffectValue                             int32 `json:"EffectValue"`
}

type CharacterBoardRow struct {
	CharacterBoardId                     int32 `json:"CharacterBoardId"`
	CharacterBoardGroupId                int32 `json:"CharacterBoardGroupId"`
	CharacterBoardUnlockConditionGroupId int32 `json:"CharacterBoardUnlockConditionGroupId"`
	ReleaseRank                          int32 `json:"ReleaseRank"`
}

type CharacterBoardStatusUpRow struct {
	CharacterBoardStatusUpId          int32 `json:"CharacterBoardStatusUpId"`
	CharacterBoardStatusUpType        int32 `json:"CharacterBoardStatusUpType"`
	CharacterBoardEffectTargetGroupId int32 `json:"CharacterBoardEffectTargetGroupId"`
}

type CharacterBoardAbilityRow struct {
	CharacterBoardAbilityId           int32 `json:"CharacterBoardAbilityId"`
	CharacterBoardEffectTargetGroupId int32 `json:"CharacterBoardEffectTargetGroupId"`
	AbilityId                         int32 `json:"AbilityId"`
}

type CharacterBoardAbilityMaxLevelRow struct {
	CharacterId int32 `json:"CharacterId"`
	AbilityId   int32 `json:"AbilityId"`
	MaxLevel    int32 `json:"MaxLevel"`
}

type CharacterBoardEffectTargetRow struct {
	CharacterBoardEffectTargetGroupId int32 `json:"CharacterBoardEffectTargetGroupId"`
	GroupIndex                        int32 `json:"GroupIndex"`
	CharacterBoardEffectTargetType    int32 `json:"CharacterBoardEffectTargetType"`
	TargetValue                       int32 `json:"TargetValue"`
}

type CharacterBoardAssignmentRow struct {
	CharacterId                  int32 `json:"CharacterId"`
	CharacterBoardCategoryId     int32 `json:"CharacterBoardCategoryId"`
	SortOrder                    int32 `json:"SortOrder"`
	CharacterBoardAssignmentType int32 `json:"CharacterBoardAssignmentType"`
}

type CharacterBoardGroupRow struct {
	CharacterBoardGroupId    int32 `json:"CharacterBoardGroupId"`
	CharacterBoardCategoryId int32 `json:"CharacterBoardCategoryId"`
	SortOrder                int32 `json:"SortOrder"`
	CharacterBoardGroupType  int32 `json:"CharacterBoardGroupType"`
	TextAssetId              int32 `json:"TextAssetId"`
}

type CharacterBoardCatalog struct {
	PanelById               map[int32]CharacterBoardPanelRow
	PanelsByBoardId         map[int32][]CharacterBoardPanelRow
	ReleaseCostsByGroupId   map[int32][]CharacterBoardReleasePossessionRow
	ReleaseEffectsByGroupId map[int32][]CharacterBoardReleaseEffectRow
	StatusUpById            map[int32]CharacterBoardStatusUpRow
	AbilityById             map[int32]CharacterBoardAbilityRow
	AbilityMaxLevel         map[store.CharacterBoardAbilityKey]int32
	EffectTargetsByGroupId  map[int32][]CharacterBoardEffectTargetRow
	BoardById               map[int32]CharacterBoardRow
}

func LoadCharacterBoardCatalog() (*CharacterBoardCatalog, error) {
	panels, err := utils.ReadJSON[CharacterBoardPanelRow]("EntityMCharacterBoardPanelTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character board panel table: %w", err)
	}

	costs, err := utils.ReadJSON[CharacterBoardReleasePossessionRow]("EntityMCharacterBoardPanelReleasePossessionGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character board release possession table: %w", err)
	}

	effects, err := utils.ReadJSON[CharacterBoardReleaseEffectRow]("EntityMCharacterBoardPanelReleaseEffectGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character board release effect table: %w", err)
	}

	boards, err := utils.ReadJSON[CharacterBoardRow]("EntityMCharacterBoardTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character board table: %w", err)
	}

	statusUps, err := utils.ReadJSON[CharacterBoardStatusUpRow]("EntityMCharacterBoardStatusUpTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character board status up table: %w", err)
	}

	abilities, err := utils.ReadJSON[CharacterBoardAbilityRow]("EntityMCharacterBoardAbilityTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character board ability table: %w", err)
	}

	abilityMaxLevels, err := utils.ReadJSON[CharacterBoardAbilityMaxLevelRow]("EntityMCharacterBoardAbilityMaxLevelTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character board ability max level table: %w", err)
	}

	targets, err := utils.ReadJSON[CharacterBoardEffectTargetRow]("EntityMCharacterBoardEffectTargetGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load character board effect target table: %w", err)
	}

	catalog := &CharacterBoardCatalog{
		PanelById:               make(map[int32]CharacterBoardPanelRow, len(panels)),
		PanelsByBoardId:         make(map[int32][]CharacterBoardPanelRow),
		ReleaseCostsByGroupId:   make(map[int32][]CharacterBoardReleasePossessionRow),
		ReleaseEffectsByGroupId: make(map[int32][]CharacterBoardReleaseEffectRow),
		StatusUpById:            make(map[int32]CharacterBoardStatusUpRow, len(statusUps)),
		AbilityById:             make(map[int32]CharacterBoardAbilityRow, len(abilities)),
		AbilityMaxLevel:         make(map[store.CharacterBoardAbilityKey]int32, len(abilityMaxLevels)),
		EffectTargetsByGroupId:  make(map[int32][]CharacterBoardEffectTargetRow),
		BoardById:               make(map[int32]CharacterBoardRow, len(boards)),
	}

	for _, p := range panels {
		catalog.PanelById[p.CharacterBoardPanelId] = p
		catalog.PanelsByBoardId[p.CharacterBoardId] = append(catalog.PanelsByBoardId[p.CharacterBoardId], p)
	}
	for _, c := range costs {
		catalog.ReleaseCostsByGroupId[c.CharacterBoardPanelReleasePossessionGroupId] = append(
			catalog.ReleaseCostsByGroupId[c.CharacterBoardPanelReleasePossessionGroupId], c)
	}
	for _, e := range effects {
		catalog.ReleaseEffectsByGroupId[e.CharacterBoardPanelReleaseEffectGroupId] = append(
			catalog.ReleaseEffectsByGroupId[e.CharacterBoardPanelReleaseEffectGroupId], e)
	}
	for _, b := range boards {
		catalog.BoardById[b.CharacterBoardId] = b
	}
	for _, s := range statusUps {
		catalog.StatusUpById[s.CharacterBoardStatusUpId] = s
	}
	for _, a := range abilities {
		catalog.AbilityById[a.CharacterBoardAbilityId] = a
	}
	for _, m := range abilityMaxLevels {
		catalog.AbilityMaxLevel[store.CharacterBoardAbilityKey{
			CharacterId: m.CharacterId,
			AbilityId:   m.AbilityId,
		}] = m.MaxLevel
	}
	for _, t := range targets {
		catalog.EffectTargetsByGroupId[t.CharacterBoardEffectTargetGroupId] = append(
			catalog.EffectTargetsByGroupId[t.CharacterBoardEffectTargetGroupId], t)
	}

	return catalog, nil
}
