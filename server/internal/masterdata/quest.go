package masterdata

import (
	"fmt"
	"sort"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type QuestSceneRow struct {
	QuestSceneId          int32                 `json:"QuestSceneId"`
	QuestId               int32                 `json:"QuestId"`
	SortOrder             int32                 `json:"SortOrder"`
	QuestSceneType        model.QuestSceneType  `json:"QuestSceneType"`
	AssetBackgroundId     int32                 `json:"AssetBackgroundId"`
	EventMapNumberUpper   int32                 `json:"EventMapNumberUpper"`
	EventMapNumberLower   int32                 `json:"EventMapNumberLower"`
	IsMainFlowQuestTarget bool                  `json:"IsMainFlowQuestTarget"`
	IsBattleOnlyTarget    bool                  `json:"IsBattleOnlyTarget"`
	QuestResultType       model.QuestResultType `json:"QuestResultType"`
	IsStorySkipTarget     bool                  `json:"IsStorySkipTarget"`
}

type QuestRow struct {
	QuestId                      int32 `json:"QuestId"`
	NameQuestTextId              int32 `json:"NameQuestTextId"`
	PictureBookNameQuestTextId   int32 `json:"PictureBookNameQuestTextId"`
	QuestReleaseConditionListId  int32 `json:"QuestReleaseConditionListId"`
	StoryQuestTextId             int32 `json:"StoryQuestTextId"`
	QuestDisplayAttributeGroupId int32 `json:"QuestDisplayAttributeGroupId"`
	RecommendedDeckPower         int32 `json:"RecommendedDeckPower"`
	QuestFirstClearRewardGroupId int32 `json:"QuestFirstClearRewardGroupId"`
	QuestPickupRewardGroupId     int32 `json:"QuestPickupRewardGroupId"`
	QuestDeckRestrictionGroupId  int32 `json:"QuestDeckRestrictionGroupId"`
	QuestMissionGroupId          int32 `json:"QuestMissionGroupId"`
	Stamina                      int32 `json:"Stamina"`
	UserExp                      int32 `json:"UserExp"`
	CharacterExp                 int32 `json:"CharacterExp"`
	CostumeExp                   int32 `json:"CostumeExp"`
	Gold                         int32 `json:"Gold"`
	DailyClearableCount          int32 `json:"DailyClearableCount"`
	IsRunInTheBackground         bool  `json:"IsRunInTheBackground"`
	IsCountedAsQuest             bool  `json:"IsCountedAsQuest"`
	QuestBonusId                 int32 `json:"QuestBonusId"`
	IsNotShowAfterClear          bool  `json:"IsNotShowAfterClear"`
	IsBigWinTarget               bool  `json:"IsBigWinTarget"`
	IsUsableSkipTicket           bool  `json:"IsUsableSkipTicket"`
	QuestReplayFlowRewardGroupId int32 `json:"QuestReplayFlowRewardGroupId"`
	InvisibleQuestMissionGroupId int32 `json:"InvisibleQuestMissionGroupId"`
	FieldEffectGroupId           int32 `json:"FieldEffectGroupId"`
}

type QuestMissionRow struct {
	QuestMissionId                    int32                           `json:"QuestMissionId"`
	QuestMissionConditionType         model.QuestMissionConditionType `json:"QuestMissionConditionType"`
	QuestMissionRewardId              int32                           `json:"QuestMissionRewardId"`
	QuestMissionConditionValueGroupId int32                           `json:"QuestMissionConditionValueGroupId"`
}

type QuestMissionGroupRow struct {
	QuestMissionGroupId int32 `json:"QuestMissionGroupId"`
	SortOrder           int32 `json:"SortOrder"`
	QuestMissionId      int32 `json:"QuestMissionId"`
}

type QuestMissionRewardRow struct {
	QuestMissionRewardId int32                `json:"QuestMissionRewardId"`
	PossessionType       model.PossessionType `json:"PossessionType"`
	PossessionId         int32                `json:"PossessionId"`
	Count                int32                `json:"Count"`
}

type MainQuestSequenceRow struct {
	MainQuestSequenceId int32 `json:"MainQuestSequenceId"`
	SortOrder           int32 `json:"SortOrder"`
	QuestId             int32 `json:"QuestId"`
}

type MainQuestRouteRow struct {
	MainQuestRouteId  int32 `json:"MainQuestRouteId"`
	MainQuestSeasonId int32 `json:"MainQuestSeasonId"`
	SortOrder         int32 `json:"SortOrder"`
	CharacterId       int32 `json:"CharacterId"`
}

type MainQuestChapterRow struct {
	MainQuestChapterId         int32 `json:"MainQuestChapterId"`
	MainQuestRouteId           int32 `json:"MainQuestRouteId"`
	SortOrder                  int32 `json:"SortOrder"`
	MainQuestSequenceGroupId   int32 `json:"MainQuestSequenceGroupId"`
	PortalCageCharacterGroupId int32 `json:"PortalCageCharacterGroupId"`
	StartDatetime              int64 `json:"StartDatetime"`
	IsInvisibleInLibrary       bool  `json:"IsInvisibleInLibrary"`
	JoinLibraryChapterId       int32 `json:"JoinLibraryChapterId"`
}

type QuestFirstClearRewardSwitchRow struct {
	QuestId                      int32 `json:"QuestId"`
	QuestFirstClearRewardGroupId int32 `json:"QuestFirstClearRewardGroupId"`
	SwitchConditionClearQuestId  int32 `json:"SwitchConditionClearQuestId"`
}

type QuestFirstClearRewardGroupRow struct {
	QuestFirstClearRewardGroupId int32                `json:"QuestFirstClearRewardGroupId"`
	QuestFirstClearRewardType    int32                `json:"QuestFirstClearRewardType"`
	SortOrder                    int32                `json:"SortOrder"`
	PossessionType               model.PossessionType `json:"PossessionType"`
	PossessionId                 int32                `json:"PossessionId"`
	Count                        int32                `json:"Count"`
	IsPickup                     bool                 `json:"IsPickup"`
}

type QuestReplayFlowRewardGroupRow struct {
	QuestReplayFlowRewardGroupId int32                `json:"QuestReplayFlowRewardGroupId"`
	SortOrder                    int32                `json:"SortOrder"`
	PossessionType               model.PossessionType `json:"PossessionType"`
	PossessionId                 int32                `json:"PossessionId"`
	Count                        int32                `json:"Count"`
}

type QuestSceneGrantRow struct {
	QuestSceneId   int32                `json:"QuestSceneId"`
	PossessionType model.PossessionType `json:"PossessionType"`
	PossessionId   int32                `json:"PossessionId"`
	Count          int32                `json:"Count"`
}

type QuestPickupRewardGroupRow struct {
	QuestPickupRewardGroupId int32 `json:"QuestPickupRewardGroupId"`
	SortOrder                int32 `json:"SortOrder"`
	BattleDropRewardId       int32 `json:"BattleDropRewardId"`
}

type BattleDropRewardRow struct {
	BattleDropRewardId int32                `json:"BattleDropRewardId"`
	PossessionType     model.PossessionType `json:"PossessionType"`
	PossessionId       int32                `json:"PossessionId"`
	Count              int32                `json:"Count"`
}

type QuestSceneBattleRow struct {
	QuestSceneId  int32 `json:"QuestSceneId"`
	BattleGroupId int32 `json:"BattleGroupId"`
}

type BattleGroupRow struct {
	BattleGroupId int32 `json:"BattleGroupId"`
	WaveNumber    int32 `json:"WaveNumber"`
	BattleId      int32 `json:"BattleId"`
}

type BattleRow struct {
	BattleId            int32          `json:"BattleId"`
	BattleNpcId         int32          `json:"BattleNpcId"`
	DeckType            model.DeckType `json:"DeckType"`
	BattleNpcDeckNumber int32          `json:"BattleNpcDeckNumber"`
}

type BattleNpcDeckRow struct {
	BattleNpcId                  int32          `json:"BattleNpcId"`
	DeckType                     model.DeckType `json:"DeckType"`
	BattleNpcDeckNumber          int32          `json:"BattleNpcDeckNumber"`
	BattleNpcDeckCharacterUuid01 string         `json:"BattleNpcDeckCharacterUuid01"`
	BattleNpcDeckCharacterUuid02 string         `json:"BattleNpcDeckCharacterUuid02"`
	BattleNpcDeckCharacterUuid03 string         `json:"BattleNpcDeckCharacterUuid03"`
}

type BattleNpcDropCategoryRow struct {
	BattleNpcId                int32  `json:"BattleNpcId"`
	BattleNpcDeckCharacterUuid string `json:"BattleNpcDeckCharacterUuid"`
	BattleDropCategoryId       int32  `json:"BattleDropCategoryId"`
}

type BattleDropInfo struct {
	QuestSceneId         int32
	BattleDropCategoryId int32
}

type TutorialUnlockConditionRow struct {
	TutorialType                int32 `json:"TutorialType"`
	TutorialUnlockConditionType int32 `json:"TutorialUnlockConditionType"`
	ConditionValue              int32 `json:"ConditionValue"`
}

type RentalDeckRow struct {
	BattleGroupId int32 `json:"BattleGroupId"`
}

type UserLevelRow struct {
	UserLevel  int32 `json:"UserLevel"`
	MaxStamina int32 `json:"MaxStamina"`
}

type QuestCatalog struct {
	SceneById                          map[int32]QuestSceneRow
	MissionById                        map[int32]QuestMissionRow
	QuestById                          map[int32]QuestRow
	MissionIdsByQuestId                map[int32][]int32
	RouteIdByQuestId                   map[int32]int32
	SceneIdsByQuestId                  map[int32][]int32
	OrderedQuestIds                    []int32
	FirstClearRewardsByGroupId         map[int32][]QuestFirstClearRewardGroupRow
	FirstClearRewardSwitchesByQuestId  map[int32][]QuestFirstClearRewardSwitchRow
	MissionRewardsByMissionId          map[int32][]QuestMissionRewardRow
	WeaponIdsByReleaseConditionGroupId map[int32][]int32
	ReleaseConditionsByGroupId         map[int32][]WeaponStoryReleaseConditionRow
	SceneGrantsBySceneId               map[int32][]QuestSceneGrantRow
	BattleDropRewardById               map[int32]BattleDropRewardRow
	PickupRewardIdsByGroupId           map[int32][]int32
	BattleDropsByQuestId               map[int32][]BattleDropInfo
	ReplayFlowRewardsByGroupId         map[int32][]QuestReplayFlowRewardGroupRow
	RentalQuestIds                     map[int32]bool
	TutorialUnlockConditions           []TutorialUnlockConditionRow
	ChapterLastSceneByQuestId          map[int32]int32
	SeasonIdByRouteId                  map[int32]int32

	UserExpThresholds       []int32
	CharacterExpThresholds  []int32
	CostumeExpByRarity      map[int32][]int32
	CostumeMaxLevelByRarity map[int32]NumericalFunc
	MaxStaminaByLevel       map[int32]int32

	CostumeById map[int32]CostumeMasterRow
	WeaponById  map[int32]WeaponMasterRow

	WeaponSkillSlots   map[int32][]int32
	WeaponAbilitySlots map[int32][]int32

	*PartsCatalog
}

func LoadQuestCatalog(partsCatalog *PartsCatalog) (*QuestCatalog, error) {
	scenes, err := utils.ReadJSON[QuestSceneRow]("EntityMQuestSceneTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest scene table: %w", err)
	}
	sort.Slice(scenes, func(i, j int) bool {
		if scenes[i].QuestId != scenes[j].QuestId {
			return scenes[i].QuestId < scenes[j].QuestId
		}
		if scenes[i].SortOrder != scenes[j].SortOrder {
			return scenes[i].SortOrder < scenes[j].SortOrder
		}
		return scenes[i].QuestSceneId < scenes[j].QuestSceneId
	})

	missions, err := utils.ReadJSON[QuestMissionRow]("EntityMQuestMissionTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest mission table: %w", err)
	}

	quests, err := utils.ReadJSON[QuestRow]("EntityMQuestTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest table: %w", err)
	}

	missionGroups, err := utils.ReadJSON[QuestMissionGroupRow]("EntityMQuestMissionGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest mission group table: %w", err)
	}
	sort.Slice(missionGroups, func(i, j int) bool {
		if missionGroups[i].QuestMissionGroupId != missionGroups[j].QuestMissionGroupId {
			return missionGroups[i].QuestMissionGroupId < missionGroups[j].QuestMissionGroupId
		}
		if missionGroups[i].SortOrder != missionGroups[j].SortOrder {
			return missionGroups[i].SortOrder < missionGroups[j].SortOrder
		}
		return missionGroups[i].QuestMissionId < missionGroups[j].QuestMissionId
	})

	sequences, err := utils.ReadJSON[MainQuestSequenceRow]("EntityMMainQuestSequenceTable.json")
	if err != nil {
		return nil, fmt.Errorf("load main quest sequence table: %w", err)
	}
	sort.Slice(sequences, func(i, j int) bool {
		if sequences[i].MainQuestSequenceId != sequences[j].MainQuestSequenceId {
			return sequences[i].MainQuestSequenceId < sequences[j].MainQuestSequenceId
		}
		if sequences[i].SortOrder != sequences[j].SortOrder {
			return sequences[i].SortOrder < sequences[j].SortOrder
		}
		return sequences[i].QuestId < sequences[j].QuestId
	})

	chapters, err := utils.ReadJSON[MainQuestChapterRow]("EntityMMainQuestChapterTable.json")
	if err != nil {
		return nil, fmt.Errorf("load main quest chapter table: %w", err)
	}

	routes, err := utils.ReadJSON[MainQuestRouteRow]("EntityMMainQuestRouteTable.json")
	if err != nil {
		return nil, fmt.Errorf("load main quest route table: %w", err)
	}
	seasonIdByRouteId := make(map[int32]int32, len(routes))
	for _, r := range routes {
		seasonIdByRouteId[r.MainQuestRouteId] = r.MainQuestSeasonId
	}

	firstClearSwitches, err := utils.ReadJSON[QuestFirstClearRewardSwitchRow]("EntityMQuestFirstClearRewardSwitchTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest first clear reward switch table: %w", err)
	}

	firstClearRewards, err := utils.ReadJSON[QuestFirstClearRewardGroupRow]("EntityMQuestFirstClearRewardGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest first clear reward group table: %w", err)
	}
	sort.Slice(firstClearRewards, func(i, j int) bool {
		if firstClearRewards[i].QuestFirstClearRewardGroupId != firstClearRewards[j].QuestFirstClearRewardGroupId {
			return firstClearRewards[i].QuestFirstClearRewardGroupId < firstClearRewards[j].QuestFirstClearRewardGroupId
		}
		if firstClearRewards[i].SortOrder != firstClearRewards[j].SortOrder {
			return firstClearRewards[i].SortOrder < firstClearRewards[j].SortOrder
		}
		return firstClearRewards[i].QuestFirstClearRewardType < firstClearRewards[j].QuestFirstClearRewardType
	})

	replayFlowRewards, err := utils.ReadJSON[QuestReplayFlowRewardGroupRow]("EntityMQuestReplayFlowRewardGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest replay flow reward group table: %w", err)
	}
	sort.Slice(replayFlowRewards, func(i, j int) bool {
		if replayFlowRewards[i].QuestReplayFlowRewardGroupId != replayFlowRewards[j].QuestReplayFlowRewardGroupId {
			return replayFlowRewards[i].QuestReplayFlowRewardGroupId < replayFlowRewards[j].QuestReplayFlowRewardGroupId
		}
		return replayFlowRewards[i].SortOrder < replayFlowRewards[j].SortOrder
	})

	missionRewards, err := utils.ReadJSON[QuestMissionRewardRow]("EntityMQuestMissionRewardTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest mission reward table: %w", err)
	}

	weapons, err := utils.ReadJSON[WeaponMasterRow]("EntityMWeaponTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon table: %w", err)
	}

	weaponSkillGroups, err := utils.ReadJSON[WeaponSkillGroupRow]("EntityMWeaponSkillGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon skill group table: %w", err)
	}

	weaponAbilityGroups, err := utils.ReadJSON[WeaponAbilityGroupRow]("EntityMWeaponAbilityGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon ability group table: %w", err)
	}

	releaseConditions, err := utils.ReadJSON[WeaponStoryReleaseConditionRow]("EntityMWeaponStoryReleaseConditionGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon story release condition table: %w", err)
	}

	costumeMasters, err := utils.ReadJSON[CostumeMasterRow]("EntityMCostumeTable.json")
	if err != nil {
		return nil, fmt.Errorf("load costume table: %w", err)
	}

	costumeRarities, err := utils.ReadJSON[costumeRarityRow]("EntityMCostumeRarityTable.json")
	if err != nil {
		return nil, fmt.Errorf("load costume rarity table: %w", err)
	}

	sceneGrants, err := utils.ReadJSON[QuestSceneGrantRow]("EntityMUserQuestSceneGrantPossessionTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest scene grant table: %w", err)
	}

	battleDropRewards, err := utils.ReadJSON[BattleDropRewardRow]("EntityMBattleDropRewardTable.json")
	if err != nil {
		return nil, fmt.Errorf("load battle drop reward table: %w", err)
	}

	pickupRewardGroups, err := utils.ReadJSON[QuestPickupRewardGroupRow]("EntityMQuestPickupRewardGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest pickup reward group table: %w", err)
	}
	sort.Slice(pickupRewardGroups, func(i, j int) bool {
		if pickupRewardGroups[i].QuestPickupRewardGroupId != pickupRewardGroups[j].QuestPickupRewardGroupId {
			return pickupRewardGroups[i].QuestPickupRewardGroupId < pickupRewardGroups[j].QuestPickupRewardGroupId
		}
		return pickupRewardGroups[i].SortOrder < pickupRewardGroups[j].SortOrder
	})

	sceneBattles, err := utils.ReadJSON[QuestSceneBattleRow]("EntityMQuestSceneBattleTable.json")
	if err != nil {
		return nil, fmt.Errorf("load quest scene battle table: %w", err)
	}

	battleGroups, err := utils.ReadJSON[BattleGroupRow]("EntityMBattleGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load battle group table: %w", err)
	}

	battles, err := utils.ReadJSON[BattleRow]("EntityMBattleTable.json")
	if err != nil {
		return nil, fmt.Errorf("load battle table: %w", err)
	}

	npcDecks, err := utils.ReadJSON[BattleNpcDeckRow]("EntityMBattleNpcDeckTable.json")
	if err != nil {
		return nil, fmt.Errorf("load battle npc deck table: %w", err)
	}

	npcDropCategories, err := utils.ReadJSON[BattleNpcDropCategoryRow]("EntityMBattleNpcDeckCharacterDropCategoryTable.json")
	if err != nil {
		return nil, fmt.Errorf("load battle npc drop category table: %w", err)
	}

	rentalDecks, err := utils.ReadJSON[RentalDeckRow]("EntityMBattleRentalDeckTable.json")
	if err != nil {
		return nil, fmt.Errorf("load battle rental deck table: %w", err)
	}

	tutorialUnlockConds, err := utils.ReadJSON[TutorialUnlockConditionRow]("EntityMTutorialUnlockConditionTable.json")
	if err != nil {
		return nil, fmt.Errorf("load tutorial unlock condition table: %w", err)
	}

	paramMapRows, err := LoadParameterMap()
	if err != nil {
		return nil, err
	}

	userLevels, err := utils.ReadJSON[UserLevelRow]("EntityMUserLevelTable.json")
	if err != nil {
		return nil, fmt.Errorf("load user level table: %w", err)
	}
	maxStaminaByLevel := make(map[int32]int32, len(userLevels))
	for _, ul := range userLevels {
		maxStaminaByLevel[ul.UserLevel] = ul.MaxStamina
	}

	funcResolver, err := LoadFunctionResolver()
	if err != nil {
		return nil, fmt.Errorf("load function resolver: %w", err)
	}

	costumeExpByRarity := make(map[int32][]int32, len(costumeRarities))
	costumeMaxLevelByRarity := make(map[int32]NumericalFunc, len(costumeRarities))
	for _, r := range costumeRarities {
		if _, ok := costumeExpByRarity[r.RarityType]; !ok {
			costumeExpByRarity[r.RarityType] = BuildExpThresholds(paramMapRows, r.RequiredExpForLevelUpNumericalParameterMapId)
		}
		if _, ok := costumeMaxLevelByRarity[r.RarityType]; !ok {
			if f, found := funcResolver.Resolve(r.MaxLevelNumericalFunctionId); found {
				costumeMaxLevelByRarity[r.RarityType] = f
			}
		}
	}

	costumeById := make(map[int32]CostumeMasterRow, len(costumeMasters))
	for _, cm := range costumeMasters {
		costumeById[cm.CostumeId] = cm
	}

	weaponById := make(map[int32]WeaponMasterRow, len(weapons))
	for _, w := range weapons {
		weaponById[w.WeaponId] = w
	}

	skillSlots := make(map[int32][]int32)
	for _, row := range weaponSkillGroups {
		skillSlots[row.WeaponSkillGroupId] = append(skillSlots[row.WeaponSkillGroupId], row.SlotNumber)
	}
	abilitySlots := make(map[int32][]int32)
	for _, row := range weaponAbilityGroups {
		abilitySlots[row.WeaponAbilityGroupId] = append(abilitySlots[row.WeaponAbilityGroupId], row.SlotNumber)
	}

	sceneById := make(map[int32]QuestSceneRow, len(scenes))
	sceneIdsByQuestId := make(map[int32][]int32)
	for _, scene := range scenes {
		sceneById[scene.QuestSceneId] = scene
		sceneIdsByQuestId[scene.QuestId] = append(sceneIdsByQuestId[scene.QuestId], scene.QuestSceneId)
	}

	missionById := make(map[int32]QuestMissionRow, len(missions))
	for _, mission := range missions {
		missionById[mission.QuestMissionId] = mission
	}

	questById := make(map[int32]QuestRow, len(quests))
	for _, quest := range quests {
		questById[quest.QuestId] = quest
	}

	missionIdsByGroupId := make(map[int32][]int32, len(missionGroups))
	for _, mg := range missionGroups {
		missionIdsByGroupId[mg.QuestMissionGroupId] = append(
			missionIdsByGroupId[mg.QuestMissionGroupId], mg.QuestMissionId)
	}
	missionIdsByQuestId := make(map[int32][]int32)
	for questId, quest := range questById {
		missionIds := missionIdsByGroupId[quest.QuestMissionGroupId]
		if len(missionIds) == 0 {
			continue
		}
		missionIdsByQuestId[questId] = append([]int32(nil), missionIds...)
	}

	chapterBySequenceId := make(map[int32]MainQuestChapterRow, len(chapters))
	for _, chapter := range chapters {
		chapterBySequenceId[chapter.MainQuestSequenceGroupId] = chapter
	}
	routeIdByQuestId := make(map[int32]int32)
	for _, sequence := range sequences {
		if chapter, ok := chapterBySequenceId[sequence.MainQuestSequenceId]; ok {
			routeIdByQuestId[sequence.QuestId] = chapter.MainQuestRouteId
		}
	}

	sortedChapters := make([]MainQuestChapterRow, len(chapters))
	copy(sortedChapters, chapters)
	sort.Slice(sortedChapters, func(i, j int) bool {
		return sortedChapters[i].SortOrder < sortedChapters[j].SortOrder
	})
	sequencesByGroupId := make(map[int32][]MainQuestSequenceRow)
	for _, seq := range sequences {
		sequencesByGroupId[seq.MainQuestSequenceId] = append(sequencesByGroupId[seq.MainQuestSequenceId], seq)
	}
	var orderedQuestIds []int32
	for _, chapter := range sortedChapters {
		for _, seq := range sequencesByGroupId[chapter.MainQuestSequenceGroupId] {
			orderedQuestIds = append(orderedQuestIds, seq.QuestId)
		}
	}

	chapterLastSceneByQuestId := make(map[int32]int32)
	for _, chapter := range sortedChapters {
		seqs := sequencesByGroupId[chapter.MainQuestSequenceGroupId]
		var chapterLastScene int32
		for i := len(seqs) - 1; i >= 0; i-- {
			if sids := sceneIdsByQuestId[seqs[i].QuestId]; len(sids) > 0 {
				chapterLastScene = sids[len(sids)-1]
				break
			}
		}
		if chapterLastScene != 0 {
			for _, seq := range seqs {
				chapterLastSceneByQuestId[seq.QuestId] = chapterLastScene
			}
		}
	}

	firstClearRewardsByGroupId := make(map[int32][]QuestFirstClearRewardGroupRow, len(firstClearRewards))
	for _, reward := range firstClearRewards {
		firstClearRewardsByGroupId[reward.QuestFirstClearRewardGroupId] = append(
			firstClearRewardsByGroupId[reward.QuestFirstClearRewardGroupId], reward)
	}

	replayFlowRewardsByGroupId := make(map[int32][]QuestReplayFlowRewardGroupRow, len(replayFlowRewards))
	for _, reward := range replayFlowRewards {
		replayFlowRewardsByGroupId[reward.QuestReplayFlowRewardGroupId] = append(
			replayFlowRewardsByGroupId[reward.QuestReplayFlowRewardGroupId], reward)
	}

	firstClearRewardSwitchesByQuestId := make(map[int32][]QuestFirstClearRewardSwitchRow, len(firstClearSwitches))
	for _, switchRow := range firstClearSwitches {
		firstClearRewardSwitchesByQuestId[switchRow.QuestId] = append(
			firstClearRewardSwitchesByQuestId[switchRow.QuestId], switchRow)
	}

	missionRewardsByMissionId := make(map[int32][]QuestMissionRewardRow, len(missionRewards))
	for _, reward := range missionRewards {
		missionRewardsByMissionId[reward.QuestMissionRewardId] = append(
			missionRewardsByMissionId[reward.QuestMissionRewardId], reward)
	}

	weaponIdsByReleaseConditionGroupId := make(map[int32][]int32)
	for _, w := range weaponById {
		if w.WeaponStoryReleaseConditionGroupId != 0 {
			weaponIdsByReleaseConditionGroupId[w.WeaponStoryReleaseConditionGroupId] = append(
				weaponIdsByReleaseConditionGroupId[w.WeaponStoryReleaseConditionGroupId], w.WeaponId)
		}
	}

	releaseConditionsByGroupId := make(map[int32][]WeaponStoryReleaseConditionRow)
	for _, c := range releaseConditions {
		releaseConditionsByGroupId[c.WeaponStoryReleaseConditionGroupId] = append(
			releaseConditionsByGroupId[c.WeaponStoryReleaseConditionGroupId], c)
	}

	sceneGrantsBySceneId := make(map[int32][]QuestSceneGrantRow)
	for _, sg := range sceneGrants {
		sceneGrantsBySceneId[sg.QuestSceneId] = append(sceneGrantsBySceneId[sg.QuestSceneId], sg)
	}

	battleDropRewardById := make(map[int32]BattleDropRewardRow, len(battleDropRewards))
	for _, bdr := range battleDropRewards {
		battleDropRewardById[bdr.BattleDropRewardId] = bdr
	}

	pickupRewardIdsByGroupId := make(map[int32][]int32)
	for _, pg := range pickupRewardGroups {
		pickupRewardIdsByGroupId[pg.QuestPickupRewardGroupId] = append(
			pickupRewardIdsByGroupId[pg.QuestPickupRewardGroupId], pg.BattleDropRewardId)
	}

	battleGroupBySceneId := make(map[int32]int32, len(sceneBattles))
	for _, sb := range sceneBattles {
		battleGroupBySceneId[sb.QuestSceneId] = sb.BattleGroupId
	}

	battleIdsByGroupId := make(map[int32][]int32)
	for _, bg := range battleGroups {
		battleIdsByGroupId[bg.BattleGroupId] = append(battleIdsByGroupId[bg.BattleGroupId], bg.BattleId)
	}

	type npcDeckKey struct {
		BattleNpcId         int32
		DeckType            model.DeckType
		BattleNpcDeckNumber int32
	}
	npcDeckByKey := make(map[npcDeckKey]BattleNpcDeckRow, len(npcDecks))
	for _, d := range npcDecks {
		npcDeckByKey[npcDeckKey{d.BattleNpcId, d.DeckType, d.BattleNpcDeckNumber}] = d
	}

	battleByIdMap := make(map[int32]BattleRow, len(battles))
	for _, b := range battles {
		battleByIdMap[b.BattleId] = b
	}

	type dropCatKey struct {
		BattleNpcId int32
		Uuid        string
	}
	dropCategoryByKey := make(map[dropCatKey]int32, len(npcDropCategories))
	for _, dc := range npcDropCategories {
		dropCategoryByKey[dropCatKey{dc.BattleNpcId, dc.BattleNpcDeckCharacterUuid}] = dc.BattleDropCategoryId
	}

	battleDropsByQuestId := make(map[int32][]BattleDropInfo)
	for questId := range questById {
		sids := sceneIdsByQuestId[questId]
		seen := make(map[BattleDropInfo]bool)
		var drops []BattleDropInfo
		for _, sceneId := range sids {
			groupId, ok := battleGroupBySceneId[sceneId]
			if !ok {
				continue
			}
			for _, battleId := range battleIdsByGroupId[groupId] {
				b, ok := battleByIdMap[battleId]
				if !ok {
					continue
				}
				dk := npcDeckKey{b.BattleNpcId, b.DeckType, b.BattleNpcDeckNumber}
				deck, ok := npcDeckByKey[dk]
				if !ok {
					continue
				}
				for _, uuid := range []string{deck.BattleNpcDeckCharacterUuid01, deck.BattleNpcDeckCharacterUuid02, deck.BattleNpcDeckCharacterUuid03} {
					if uuid == "" {
						continue
					}
					catId, ok := dropCategoryByKey[dropCatKey{b.BattleNpcId, uuid}]
					if !ok {
						continue
					}
					info := BattleDropInfo{QuestSceneId: sceneId, BattleDropCategoryId: catId}
					if !seen[info] {
						seen[info] = true
						drops = append(drops, info)
					}
				}
			}
		}
		if len(drops) > 0 {
			battleDropsByQuestId[questId] = drops
		}
	}

	rentalBattleGroups := make(map[int32]bool, len(rentalDecks))
	for _, rd := range rentalDecks {
		rentalBattleGroups[rd.BattleGroupId] = true
	}
	rentalQuestIds := make(map[int32]bool)
	for questId := range questById {
		for _, sceneId := range sceneIdsByQuestId[questId] {
			if groupId, ok := battleGroupBySceneId[sceneId]; ok && rentalBattleGroups[groupId] {
				rentalQuestIds[questId] = true
				break
			}
		}
	}

	return &QuestCatalog{
		SceneById:                          sceneById,
		MissionById:                        missionById,
		QuestById:                          questById,
		MissionIdsByQuestId:                missionIdsByQuestId,
		RouteIdByQuestId:                   routeIdByQuestId,
		SceneIdsByQuestId:                  sceneIdsByQuestId,
		OrderedQuestIds:                    orderedQuestIds,
		FirstClearRewardsByGroupId:         firstClearRewardsByGroupId,
		FirstClearRewardSwitchesByQuestId:  firstClearRewardSwitchesByQuestId,
		MissionRewardsByMissionId:          missionRewardsByMissionId,
		WeaponIdsByReleaseConditionGroupId: weaponIdsByReleaseConditionGroupId,
		ReleaseConditionsByGroupId:         releaseConditionsByGroupId,
		SceneGrantsBySceneId:               sceneGrantsBySceneId,
		BattleDropRewardById:               battleDropRewardById,
		PickupRewardIdsByGroupId:           pickupRewardIdsByGroupId,
		BattleDropsByQuestId:               battleDropsByQuestId,
		ReplayFlowRewardsByGroupId:         replayFlowRewardsByGroupId,
		RentalQuestIds:                     rentalQuestIds,
		TutorialUnlockConditions:           tutorialUnlockConds,
		ChapterLastSceneByQuestId:          chapterLastSceneByQuestId,
		SeasonIdByRouteId:                  seasonIdByRouteId,

		UserExpThresholds:       BuildExpThresholds(paramMapRows, 1),
		CharacterExpThresholds:  BuildExpThresholds(paramMapRows, 31),
		CostumeExpByRarity:      costumeExpByRarity,
		CostumeMaxLevelByRarity: costumeMaxLevelByRarity,
		MaxStaminaByLevel:       maxStaminaByLevel,

		CostumeById: costumeById,
		WeaponById:  weaponById,

		WeaponSkillSlots:   skillSlots,
		WeaponAbilitySlots: abilitySlots,

		PartsCatalog: partsCatalog,
	}, nil
}
