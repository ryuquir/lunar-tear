package questflow

import (
	"sort"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type questScene struct {
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

type missionGroup struct {
	QuestMissionGroupId int32 `json:"QuestMissionGroupId"`
	SortOrder           int32 `json:"SortOrder"`
	QuestMissionId      int32 `json:"QuestMissionId"`
}

type quest struct {
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

type mission struct {
	QuestMissionId                    int32                           `json:"QuestMissionId"`
	QuestMissionConditionType         model.QuestMissionConditionType `json:"QuestMissionConditionType"`
	QuestMissionRewardId              int32                           `json:"QuestMissionRewardId"`
	QuestMissionConditionValueGroupId int32                           `json:"QuestMissionConditionValueGroupId"`
}

type missionReward struct {
	QuestMissionRewardId int32                `json:"QuestMissionRewardId"`
	PossessionType       model.PossessionType `json:"PossessionType"`
	PossessionId         int32                `json:"PossessionId"`
	Count                int32                `json:"Count"`
}

type mainQuestSequence struct {
	MainQuestSequenceId int32 `json:"MainQuestSequenceId"`
	SortOrder           int32 `json:"SortOrder"`
	QuestId             int32 `json:"QuestId"`
}

type mainQuestChapter struct {
	MainQuestChapterId         int32 `json:"MainQuestChapterId"`
	MainQuestRouteId           int32 `json:"MainQuestRouteId"`
	SortOrder                  int32 `json:"SortOrder"`
	MainQuestSequenceGroupId   int32 `json:"MainQuestSequenceGroupId"`
	PortalCageCharacterGroupId int32 `json:"PortalCageCharacterGroupId"`
	StartDatetime              int64 `json:"StartDatetime"`
	IsInvisibleInLibrary       bool  `json:"IsInvisibleInLibrary"`
	JoinLibraryChapterId       int32 `json:"JoinLibraryChapterId"`
}

type questFirstClearRewardSwitch struct {
	QuestId                      int32 `json:"QuestId"`
	QuestFirstClearRewardGroupId int32 `json:"QuestFirstClearRewardGroupId"`
	SwitchConditionClearQuestId  int32 `json:"SwitchConditionClearQuestId"`
}

type questFirstClearRewardGroup struct {
	QuestFirstClearRewardGroupId int32                `json:"QuestFirstClearRewardGroupId"`
	QuestFirstClearRewardType    int32                `json:"QuestFirstClearRewardType"`
	SortOrder                    int32                `json:"SortOrder"`
	PossessionType               model.PossessionType `json:"PossessionType"`
	PossessionId                 int32                `json:"PossessionId"`
	Count                        int32                `json:"Count"`
	IsPickup                     bool                 `json:"IsPickup"`
}

type weaponStoryReleaseCondition struct {
	WeaponStoryReleaseConditionGroupId          int32                                 `json:"WeaponStoryReleaseConditionGroupId"`
	StoryIndex                                  int32                                 `json:"StoryIndex"`
	WeaponStoryReleaseConditionType             model.WeaponStoryReleaseConditionType `json:"WeaponStoryReleaseConditionType"`
	ConditionValue                              int32                                 `json:"ConditionValue"`
	WeaponStoryReleaseConditionOperationGroupId int32                                 `json:"WeaponStoryReleaseConditionOperationGroupId"`
}

type sceneGrant struct {
	QuestSceneId   int32                `json:"QuestSceneId"`
	PossessionType model.PossessionType `json:"PossessionType"`
	PossessionId   int32                `json:"PossessionId"`
	Count          int32                `json:"Count"`
}

type costumeMaster struct {
	CostumeId   int32 `json:"CostumeId"`
	CharacterId int32 `json:"CharacterId"`
	RarityType  int32 `json:"RarityType"`
}

type costumeRarityRow struct {
	RarityType                                   int32 `json:"RarityType"`
	RequiredExpForLevelUpNumericalParameterMapId int32 `json:"RequiredExpForLevelUpNumericalParameterMapId"`
}

type weaponMaster struct {
	WeaponId                           int32 `json:"WeaponId"`
	WeaponSkillGroupId                 int32 `json:"WeaponSkillGroupId"`
	WeaponAbilityGroupId               int32 `json:"WeaponAbilityGroupId"`
	WeaponStoryReleaseConditionGroupId int32 `json:"WeaponStoryReleaseConditionGroupId"`
}

type weaponSkillGroupRow struct {
	WeaponSkillGroupId int32 `json:"WeaponSkillGroupId"`
	SlotNumber         int32 `json:"SlotNumber"`
}

type weaponAbilityGroupRow struct {
	WeaponAbilityGroupId int32 `json:"WeaponAbilityGroupId"`
	SlotNumber           int32 `json:"SlotNumber"`
}

type battleDropReward struct {
	BattleDropRewardId int32                `json:"BattleDropRewardId"`
	PossessionType     model.PossessionType `json:"PossessionType"`
	PossessionId       int32                `json:"PossessionId"`
	Count              int32                `json:"Count"`
}

type questPickupRewardGroup struct {
	QuestPickupRewardGroupId int32 `json:"QuestPickupRewardGroupId"`
	SortOrder                int32 `json:"SortOrder"`
	BattleDropRewardId       int32 `json:"BattleDropRewardId"`
}

type questSceneBattle struct {
	QuestSceneId  int32 `json:"QuestSceneId"`
	BattleGroupId int32 `json:"BattleGroupId"`
}

type battleGroup struct {
	BattleGroupId int32 `json:"BattleGroupId"`
	WaveNumber    int32 `json:"WaveNumber"`
	BattleId      int32 `json:"BattleId"`
}

type battle struct {
	BattleId            int32          `json:"BattleId"`
	BattleNpcId         int32          `json:"BattleNpcId"`
	DeckType            model.DeckType `json:"DeckType"`
	BattleNpcDeckNumber int32          `json:"BattleNpcDeckNumber"`
}

type battleNpcDeck struct {
	BattleNpcId                  int32          `json:"BattleNpcId"`
	DeckType                     model.DeckType `json:"DeckType"`
	BattleNpcDeckNumber          int32          `json:"BattleNpcDeckNumber"`
	BattleNpcDeckCharacterUuid01 string         `json:"BattleNpcDeckCharacterUuid01"`
	BattleNpcDeckCharacterUuid02 string         `json:"BattleNpcDeckCharacterUuid02"`
	BattleNpcDeckCharacterUuid03 string         `json:"BattleNpcDeckCharacterUuid03"`
}

type battleNpcDropCategory struct {
	BattleNpcId                int32  `json:"BattleNpcId"`
	BattleNpcDeckCharacterUuid string `json:"BattleNpcDeckCharacterUuid"`
	BattleDropCategoryId       int32  `json:"BattleDropCategoryId"`
}

type BattleDropInfo struct {
	QuestSceneId         int32
	BattleDropCategoryId int32
}

type numericalParameterMapRow struct {
	NumericalParameterMapId int32 `json:"NumericalParameterMapId"`
	ParameterKey            int32 `json:"ParameterKey"`
	ParameterValue          int32 `json:"ParameterValue"`
}

type RewardGrant struct {
	PossessionType model.PossessionType
	PossessionId   int32
	Count          int32
}

type FinishOutcome struct {
	DropRewards                  []RewardGrant
	FirstClearRewards            []RewardGrant
	MissionClearRewards          []RewardGrant
	MissionClearCompleteRewards  []RewardGrant
	BigWinClearedQuestMissionIds []int32
	IsBigWin                     bool
}

type tutorialUnlockCondition struct {
	TutorialType                int32 `json:"TutorialType"`
	TutorialUnlockConditionType int32 `json:"TutorialUnlockConditionType"`
	ConditionValue              int32 `json:"ConditionValue"`
}

const (
	tutorialUnlockFunctionReleased         = 1
	tutorialUnlockReachSpecifiedQuestScene = 2
	tutorialUnlockUntilReachSpecifiedScene = 3
)

type rentalDeck struct {
	BattleGroupId int32 `json:"BattleGroupId"`
}

type Engine struct {
	sceneById                          map[int32]questScene
	missionById                        map[int32]mission
	questById                          map[int32]quest
	missionIdsByQuestId                map[int32][]int32
	routeIdByQuestId                   map[int32]int32
	sceneIdsByQuestId                  map[int32][]int32
	orderedQuestIds                    []int32
	firstClearRewardsByGroupId         map[int32][]questFirstClearRewardGroup
	firstClearRewardSwitchesByQuestId  map[int32][]questFirstClearRewardSwitch
	missionRewardsByMissionId          map[int32][]missionReward
	weaponById                         map[int32]weaponMaster
	weaponIdsByReleaseConditionGroupId map[int32][]int32
	releaseConditionsByGroupId         map[int32][]weaponStoryReleaseCondition
	costumeById                        map[int32]costumeMaster
	sceneGrantsBySceneId               map[int32][]sceneGrant
	battleDropRewardById               map[int32]battleDropReward
	pickupRewardIdsByGroupId           map[int32][]int32
	battleDropsByQuestId               map[int32][]BattleDropInfo
	rentalQuestIds                     map[int32]bool
	tutorialUnlockConditions           []tutorialUnlockCondition
	userExpThresholds                  []int32
	characterExpThresholds             []int32
	costumeExpByRarity                 map[int32][]int32
	maxStaminaByLevel                  map[int32]int32
	skillGroupSlots                    map[int32][]int32 // groupId -> slot numbers
	abilityGroupSlots                  map[int32][]int32 // groupId -> slot numbers
}

type userLevelEntry struct {
	UserLevel  int32 `json:"UserLevel"`
	MaxStamina int32 `json:"MaxStamina"`
}

func MakeEngine() *Engine {
	scenes, err := utils.ReadJSON[questScene]("EntityMQuestSceneTable.json")
	if err != nil {
		panic(err)
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

	missions, err := utils.ReadJSON[mission]("EntityMQuestMissionTable.json")
	if err != nil {
		panic(err)
	}

	quests, err := utils.ReadJSON[quest]("EntityMQuestTable.json")
	if err != nil {
		panic(err)
	}

	missionGroups, err := utils.ReadJSON[missionGroup]("EntityMQuestMissionGroupTable.json")
	if err != nil {
		panic(err)
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

	sequences, err := utils.ReadJSON[mainQuestSequence]("EntityMMainQuestSequenceTable.json")
	if err != nil {
		panic(err)
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

	mainQuestChapters, err := utils.ReadJSON[mainQuestChapter]("EntityMMainQuestChapterTable.json")
	if err != nil {
		panic(err)
	}

	firstClearRewardSwitches, err := utils.ReadJSON[questFirstClearRewardSwitch]("EntityMQuestFirstClearRewardSwitchTable.json")
	if err != nil {
		panic(err)
	}

	firstClearRewards, err := utils.ReadJSON[questFirstClearRewardGroup]("EntityMQuestFirstClearRewardGroupTable.json")
	if err != nil {
		panic(err)
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

	missionRewards, err := utils.ReadJSON[missionReward]("EntityMQuestMissionRewardTable.json")
	if err != nil {
		panic(err)
	}

	weapons, err := utils.ReadJSON[weaponMaster]("EntityMWeaponTable.json")
	if err != nil {
		panic(err)
	}

	weaponSkillGroups, err := utils.ReadJSON[weaponSkillGroupRow]("EntityMWeaponSkillGroupTable.json")
	if err != nil {
		panic(err)
	}

	weaponAbilityGroups, err := utils.ReadJSON[weaponAbilityGroupRow]("EntityMWeaponAbilityGroupTable.json")
	if err != nil {
		panic(err)
	}

	releaseConditions, err := utils.ReadJSON[weaponStoryReleaseCondition]("EntityMWeaponStoryReleaseConditionGroupTable.json")
	if err != nil {
		panic(err)
	}

	costumeMasters, err := utils.ReadJSON[costumeMaster]("EntityMCostumeTable.json")
	if err != nil {
		panic(err)
	}

	costumeRarities, err := utils.ReadJSON[costumeRarityRow]("EntityMCostumeRarityTable.json")
	if err != nil {
		panic(err)
	}

	sceneGrants, err := utils.ReadJSON[sceneGrant]("EntityMUserQuestSceneGrantPossessionTable.json")
	if err != nil {
		panic(err)
	}

	battleDropRewards, err := utils.ReadJSON[battleDropReward]("EntityMBattleDropRewardTable.json")
	if err != nil {
		panic(err)
	}

	pickupRewardGroups, err := utils.ReadJSON[questPickupRewardGroup]("EntityMQuestPickupRewardGroupTable.json")
	if err != nil {
		panic(err)
	}
	sort.Slice(pickupRewardGroups, func(i, j int) bool {
		if pickupRewardGroups[i].QuestPickupRewardGroupId != pickupRewardGroups[j].QuestPickupRewardGroupId {
			return pickupRewardGroups[i].QuestPickupRewardGroupId < pickupRewardGroups[j].QuestPickupRewardGroupId
		}
		return pickupRewardGroups[i].SortOrder < pickupRewardGroups[j].SortOrder
	})

	sceneBattles, err := utils.ReadJSON[questSceneBattle]("EntityMQuestSceneBattleTable.json")
	if err != nil {
		panic(err)
	}

	battleGroups, err := utils.ReadJSON[battleGroup]("EntityMBattleGroupTable.json")
	if err != nil {
		panic(err)
	}

	battles, err := utils.ReadJSON[battle]("EntityMBattleTable.json")
	if err != nil {
		panic(err)
	}

	npcDecks, err := utils.ReadJSON[battleNpcDeck]("EntityMBattleNpcDeckTable.json")
	if err != nil {
		panic(err)
	}

	npcDropCategories, err := utils.ReadJSON[battleNpcDropCategory]("EntityMBattleNpcDeckCharacterDropCategoryTable.json")
	if err != nil {
		panic(err)
	}

	rentalDecks, err := utils.ReadJSON[rentalDeck]("EntityMBattleRentalDeckTable.json")
	if err != nil {
		panic(err)
	}

	tutorialUnlockConds, err := utils.ReadJSON[tutorialUnlockCondition]("EntityMTutorialUnlockConditionTable.json")
	if err != nil {
		panic(err)
	}

	paramMapRows, err := utils.ReadJSON[numericalParameterMapRow]("EntityMNumericalParameterMapTable.json")
	if err != nil {
		panic(err)
	}

	userLevels, err := utils.ReadJSON[userLevelEntry]("EntityMUserLevelTable.json")
	if err != nil {
		panic(err)
	}
	maxStaminaByLevel := make(map[int32]int32, len(userLevels))
	for _, ul := range userLevels {
		maxStaminaByLevel[ul.UserLevel] = ul.MaxStamina
	}
	buildExpThresholds := func(mapId int32) []int32 {
		maxKey := int32(0)
		for _, r := range paramMapRows {
			if r.NumericalParameterMapId == mapId && r.ParameterKey > maxKey {
				maxKey = r.ParameterKey
			}
		}
		thresholds := make([]int32, maxKey+1)
		for _, r := range paramMapRows {
			if r.NumericalParameterMapId == mapId {
				thresholds[r.ParameterKey] = r.ParameterValue
			}
		}
		return thresholds
	}

	skillSlots := make(map[int32][]int32)
	for _, row := range weaponSkillGroups {
		skillSlots[row.WeaponSkillGroupId] = append(skillSlots[row.WeaponSkillGroupId], row.SlotNumber)
	}
	abilitySlots := make(map[int32][]int32)
	for _, row := range weaponAbilityGroups {
		abilitySlots[row.WeaponAbilityGroupId] = append(abilitySlots[row.WeaponAbilityGroupId], row.SlotNumber)
	}

	engine := &Engine{
		sceneById:                          make(map[int32]questScene, len(scenes)),
		missionById:                        make(map[int32]mission, len(missions)),
		questById:                          make(map[int32]quest, len(quests)),
		missionIdsByQuestId:                make(map[int32][]int32),
		routeIdByQuestId:                   make(map[int32]int32),
		sceneIdsByQuestId:                  make(map[int32][]int32),
		firstClearRewardSwitchesByQuestId:  make(map[int32][]questFirstClearRewardSwitch, len(firstClearRewardSwitches)),
		missionRewardsByMissionId:          make(map[int32][]missionReward, len(missionRewards)),
		firstClearRewardsByGroupId:         make(map[int32][]questFirstClearRewardGroup, len(firstClearRewards)),
		weaponById:                         make(map[int32]weaponMaster, len(weapons)),
		weaponIdsByReleaseConditionGroupId: make(map[int32][]int32),
		releaseConditionsByGroupId:         make(map[int32][]weaponStoryReleaseCondition),
		costumeById:                        make(map[int32]costumeMaster, len(costumeMasters)),
		sceneGrantsBySceneId:               make(map[int32][]sceneGrant),
		battleDropRewardById:               make(map[int32]battleDropReward, len(battleDropRewards)),
		pickupRewardIdsByGroupId:           make(map[int32][]int32),
		battleDropsByQuestId:               make(map[int32][]BattleDropInfo),
		tutorialUnlockConditions:           tutorialUnlockConds,
		userExpThresholds:                  buildExpThresholds(1),
		characterExpThresholds:             buildExpThresholds(31),
		costumeExpByRarity:                 buildCostumeExpByRarity(costumeRarities, buildExpThresholds),
		maxStaminaByLevel:                  maxStaminaByLevel,
		skillGroupSlots:                    skillSlots,
		abilityGroupSlots:                  abilitySlots,
	}

	for _, scene := range scenes {
		engine.sceneById[scene.QuestSceneId] = scene
		engine.sceneIdsByQuestId[scene.QuestId] = append(engine.sceneIdsByQuestId[scene.QuestId], scene.QuestSceneId)
	}

	for _, mission := range missions {
		engine.missionById[mission.QuestMissionId] = mission
	}

	for _, quest := range quests {
		engine.questById[quest.QuestId] = quest
	}

	missionIdsByGroupId := make(map[int32][]int32, len(missionGroups))
	for _, missionGroup := range missionGroups {
		missionIdsByGroupId[missionGroup.QuestMissionGroupId] = append(
			missionIdsByGroupId[missionGroup.QuestMissionGroupId], missionGroup.QuestMissionId)
	}
	for questId, quest := range engine.questById {
		missionIds := missionIdsByGroupId[quest.QuestMissionGroupId]
		if len(missionIds) == 0 {
			continue
		}
		engine.missionIdsByQuestId[questId] = append([]int32(nil), missionIds...)
	}

	chapterBySequenceId := make(map[int32]mainQuestChapter, len(mainQuestChapters))
	for _, chapter := range mainQuestChapters {
		chapterBySequenceId[chapter.MainQuestSequenceGroupId] = chapter
	}
	for _, sequence := range sequences {
		if chapter, ok := chapterBySequenceId[sequence.MainQuestSequenceId]; ok {
			engine.routeIdByQuestId[sequence.QuestId] = chapter.MainQuestRouteId
		}
	}

	sort.Slice(mainQuestChapters, func(i, j int) bool {
		return mainQuestChapters[i].SortOrder < mainQuestChapters[j].SortOrder
	})
	sequencesByGroupId := make(map[int32][]mainQuestSequence)
	for _, seq := range sequences {
		sequencesByGroupId[seq.MainQuestSequenceId] = append(sequencesByGroupId[seq.MainQuestSequenceId], seq)
	}
	for _, chapter := range mainQuestChapters {
		for _, seq := range sequencesByGroupId[chapter.MainQuestSequenceGroupId] {
			engine.orderedQuestIds = append(engine.orderedQuestIds, seq.QuestId)
		}
	}

	for _, reward := range firstClearRewards {
		engine.firstClearRewardsByGroupId[reward.QuestFirstClearRewardGroupId] = append(
			engine.firstClearRewardsByGroupId[reward.QuestFirstClearRewardGroupId], reward)
	}

	for _, switchRow := range firstClearRewardSwitches {
		engine.firstClearRewardSwitchesByQuestId[switchRow.QuestId] = append(
			engine.firstClearRewardSwitchesByQuestId[switchRow.QuestId], switchRow)
	}

	for _, reward := range missionRewards {
		engine.missionRewardsByMissionId[reward.QuestMissionRewardId] = append(
			engine.missionRewardsByMissionId[reward.QuestMissionRewardId], reward)
	}

	for _, w := range weapons {
		engine.weaponById[w.WeaponId] = w
		if w.WeaponStoryReleaseConditionGroupId != 0 {
			engine.weaponIdsByReleaseConditionGroupId[w.WeaponStoryReleaseConditionGroupId] = append(
				engine.weaponIdsByReleaseConditionGroupId[w.WeaponStoryReleaseConditionGroupId], w.WeaponId)
		}
	}

	for _, c := range releaseConditions {
		engine.releaseConditionsByGroupId[c.WeaponStoryReleaseConditionGroupId] = append(
			engine.releaseConditionsByGroupId[c.WeaponStoryReleaseConditionGroupId], c)
	}

	for _, cm := range costumeMasters {
		engine.costumeById[cm.CostumeId] = cm
	}

	for _, sg := range sceneGrants {
		engine.sceneGrantsBySceneId[sg.QuestSceneId] = append(engine.sceneGrantsBySceneId[sg.QuestSceneId], sg)
	}

	for _, bdr := range battleDropRewards {
		engine.battleDropRewardById[bdr.BattleDropRewardId] = bdr
	}

	for _, pg := range pickupRewardGroups {
		engine.pickupRewardIdsByGroupId[pg.QuestPickupRewardGroupId] = append(
			engine.pickupRewardIdsByGroupId[pg.QuestPickupRewardGroupId], pg.BattleDropRewardId)
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
	npcDeckByKey := make(map[npcDeckKey]battleNpcDeck, len(npcDecks))
	for _, d := range npcDecks {
		npcDeckByKey[npcDeckKey{d.BattleNpcId, d.DeckType, d.BattleNpcDeckNumber}] = d
	}

	battleById := make(map[int32]battle, len(battles))
	for _, b := range battles {
		battleById[b.BattleId] = b
	}

	type dropCatKey struct {
		BattleNpcId int32
		Uuid        string
	}
	dropCategoryByKey := make(map[dropCatKey]int32, len(npcDropCategories))
	for _, dc := range npcDropCategories {
		dropCategoryByKey[dropCatKey{dc.BattleNpcId, dc.BattleNpcDeckCharacterUuid}] = dc.BattleDropCategoryId
	}

	for questId := range engine.questById {
		sceneIds := engine.sceneIdsByQuestId[questId]
		seen := make(map[BattleDropInfo]bool)
		var drops []BattleDropInfo
		for _, sceneId := range sceneIds {
			groupId, ok := battleGroupBySceneId[sceneId]
			if !ok {
				continue
			}
			for _, battleId := range battleIdsByGroupId[groupId] {
				b, ok := battleById[battleId]
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
			engine.battleDropsByQuestId[questId] = drops
		}
	}

	rentalBattleGroups := make(map[int32]bool, len(rentalDecks))
	for _, rd := range rentalDecks {
		rentalBattleGroups[rd.BattleGroupId] = true
	}
	engine.rentalQuestIds = make(map[int32]bool)
	for questId := range engine.questById {
		for _, sceneId := range engine.sceneIdsByQuestId[questId] {
			if groupId, ok := battleGroupBySceneId[sceneId]; ok && rentalBattleGroups[groupId] {
				engine.rentalQuestIds[questId] = true
				break
			}
		}
	}

	return engine
}

func buildCostumeExpByRarity(rarities []costumeRarityRow, buildThresholds func(int32) []int32) map[int32][]int32 {
	m := make(map[int32][]int32, len(rarities))
	for _, r := range rarities {
		if _, ok := m[r.RarityType]; !ok {
			m[r.RarityType] = buildThresholds(r.RequiredExpForLevelUpNumericalParameterMapId)
		}
	}
	return m
}
