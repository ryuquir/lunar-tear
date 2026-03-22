package questflow

import (
	"fmt"
	"log"
	"sort"

	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/utils"
)

type QuestFlowType int32

const (
	QuestFlowTypeUnknown                QuestFlowType = 0
	QuestFlowTypeMainFlow               QuestFlowType = 1
	QuestFlowTypeSubFlow                QuestFlowType = 2
	QuestFlowTypeReplayFlow             QuestFlowType = 3
	QuestFlowTypeAnotherRouteReplayFlow QuestFlowType = 4
)

func (t QuestFlowType) String() string {
	switch t {
	case QuestFlowTypeUnknown:
		return "unknown"
	case QuestFlowTypeMainFlow:
		return "main-flow"
	case QuestFlowTypeSubFlow:
		return "sub-flow"
	case QuestFlowTypeReplayFlow:
		return "replay-flow"
	case QuestFlowTypeAnotherRouteReplayFlow:
		return "another-route-replay-flow"
	default:
		return fmt.Sprintf("unknown-quest-flow(%d)", int32(t))
	}
}

type QuestResultType int32

const (
	QuestResultTypeUnknown    QuestResultType = 0
	QuestResultTypeNone       QuestResultType = 1
	QuestResultTypeHalfResult QuestResultType = 2
	QuestResultTypeFullResult QuestResultType = 3
)

type QuestSceneType int32

const (
	QuestSceneTypeUnknown      QuestSceneType = 0
	QuestSceneTypeTower        QuestSceneType = 1
	QuestSceneTypePictureBook  QuestSceneType = 2
	QuestSceneTypeField        QuestSceneType = 3
	QuestSceneTypeNovel        QuestSceneType = 4
	QuestSceneTypeLimitContent QuestSceneType = 5
)

type questScene struct {
	QuestSceneId          int32           `json:"QuestSceneId"`
	QuestId               int32           `json:"QuestId"`
	SortOrder             int32           `json:"SortOrder"`
	QuestSceneType        QuestSceneType  `json:"QuestSceneType"`
	AssetBackgroundId     int32           `json:"AssetBackgroundId"`
	EventMapNumberUpper   int32           `json:"EventMapNumberUpper"`
	EventMapNumberLower   int32           `json:"EventMapNumberLower"`
	IsMainFlowQuestTarget bool            `json:"IsMainFlowQuestTarget"`
	IsBattleOnlyTarget    bool            `json:"IsBattleOnlyTarget"`
	QuestResultType       QuestResultType `json:"QuestResultType"`
	IsStorySkipTarget     bool            `json:"IsStorySkipTarget"`
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

type QuestMissionConditionType int

const (
	QuestMissionConditionTypeUnknown                                   QuestMissionConditionType = 0
	QuestMissionConditionTypeLessThanOrEqualXPeopleNotAlive            QuestMissionConditionType = 1
	QuestMissionConditionTypeMaxDamage                                 QuestMissionConditionType = 2
	QuestMissionConditionTypeSpecifiedCostumeIsInDeck                  QuestMissionConditionType = 3
	QuestMissionConditionTypeSpecifiedCharacterIsInDeck                QuestMissionConditionType = 4
	QuestMissionConditionTypeSpecifiedAttributeMainWeaponIsInDeck      QuestMissionConditionType = 5
	QuestMissionConditionTypeGreaterThanOrEqualXCostumeSkillUseCount   QuestMissionConditionType = 6
	QuestMissionConditionTypeGreaterThanOrEqualXWeaponSkillUseCount    QuestMissionConditionType = 7
	QuestMissionConditionTypeGreaterThanOrEqualXCompanionSkillUseCount QuestMissionConditionType = 8
	QuestMissionConditionTypeCostumeSkillfulWeaponAllCharacter         QuestMissionConditionType = 9
	QuestMissionConditionTypeCostumeSkillfulWeaponAnyCharacter         QuestMissionConditionType = 10
	QuestMissionConditionTypeCostumeRarityEqAllCharacter               QuestMissionConditionType = 11
	QuestMissionConditionTypeCostumeRarityGeAllCharacter               QuestMissionConditionType = 12
	QuestMissionConditionTypeCostumeRarityLeAllCharacter               QuestMissionConditionType = 13
	QuestMissionConditionTypeCostumeRarityEqAnyCharacter               QuestMissionConditionType = 14
	QuestMissionConditionTypeCostumeRarityGeAnyCharacter               QuestMissionConditionType = 15
	QuestMissionConditionTypeCostumeRarityLeAnyCharacter               QuestMissionConditionType = 16
	QuestMissionConditionTypeWeaponEvolutionGroupId                    QuestMissionConditionType = 17
	QuestMissionConditionTypeSpecifiedAttributeWeaponIsInDeck          QuestMissionConditionType = 18
	QuestMissionConditionTypeSpecifiedAttributeMainWeaponAllCharacter  QuestMissionConditionType = 19
	QuestMissionConditionTypeSpecifiedAttributeWeaponAllCharacter      QuestMissionConditionType = 20
	QuestMissionConditionTypeWeaponManSkillfulWeaponAllCharacter       QuestMissionConditionType = 21
	QuestMissionConditionTypeWeaponSkillfulWeaponAllCharacter          QuestMissionConditionType = 22
	QuestMissionConditionTypeWeaponManSkillfulWeaponAnyCharacter       QuestMissionConditionType = 23
	QuestMissionConditionTypeWeaponSkillfulWeaponAnyCharacter          QuestMissionConditionType = 24
	QuestMissionConditionTypeWeaponRarityEqAllCharacter                QuestMissionConditionType = 25
	QuestMissionConditionTypeWeaponRarityGeAllCharacter                QuestMissionConditionType = 26
	QuestMissionConditionTypeWeaponRarityLeAllCharacter                QuestMissionConditionType = 27
	QuestMissionConditionTypeWeaponMainRarityEqAllCharacter            QuestMissionConditionType = 28
	QuestMissionConditionTypeWeaponMainRarityGeAllCharacter            QuestMissionConditionType = 29
	QuestMissionConditionTypeWeaponMainRarityLeAllCharacter            QuestMissionConditionType = 30
	QuestMissionConditionTypeWeaponRarityEqAnyCharacter                QuestMissionConditionType = 31
	QuestMissionConditionTypeWeaponRarityGeAnyCharacter                QuestMissionConditionType = 32
	QuestMissionConditionTypeWeaponRarityLeAnyCharacter                QuestMissionConditionType = 33
	QuestMissionConditionTypeWeaponMainRarityEqAnyCharacter            QuestMissionConditionType = 34
	QuestMissionConditionTypeWeaponMainRarityGeAnyCharacter            QuestMissionConditionType = 35
	QuestMissionConditionTypeWeaponMainRarityLeAnyCharacter            QuestMissionConditionType = 36
	QuestMissionConditionTypeCompanionId                               QuestMissionConditionType = 37
	QuestMissionConditionTypeCompanionAttribute                        QuestMissionConditionType = 38
	QuestMissionConditionTypeCompanionCategory                         QuestMissionConditionType = 39
	QuestMissionConditionTypePartsId                                   QuestMissionConditionType = 40
	QuestMissionConditionTypePartsGroupId                              QuestMissionConditionType = 41
	QuestMissionConditionTypePartsRarityEq                             QuestMissionConditionType = 42
	QuestMissionConditionTypePartsRarityGe                             QuestMissionConditionType = 43
	QuestMissionConditionTypePartsRarityLe                             QuestMissionConditionType = 44
	QuestMissionConditionTypeDeckPowerGe                               QuestMissionConditionType = 45
	QuestMissionConditionTypeDeckPowerLe                               QuestMissionConditionType = 46
	QuestMissionConditionTypeDeckCostumeNumEq                          QuestMissionConditionType = 47
	QuestMissionConditionTypeDeckCostumeNumGe                          QuestMissionConditionType = 48
	QuestMissionConditionTypeDeckCostumeNumLe                          QuestMissionConditionType = 49
	QuestMissionConditionTypeCriticalCountGe                           QuestMissionConditionType = 50
	QuestMissionConditionTypeMinHpPercentageGe                         QuestMissionConditionType = 51
	QuestMissionConditionTypeComboCountGe                              QuestMissionConditionType = 52
	QuestMissionConditionTypeComboMaxDamageGe                          QuestMissionConditionType = 53
	QuestMissionConditionTypeLessThanOrEqualXCostumeSkillUseCount      QuestMissionConditionType = 54
	QuestMissionConditionTypeLessThanOrEqualXWeaponSkillUseCount       QuestMissionConditionType = 55
	QuestMissionConditionTypeLessThanOrEqualXCompanionSkillUseCount    QuestMissionConditionType = 56
	QuestMissionConditionTypeWithoutRecoverySkill                      QuestMissionConditionType = 57
	QuestMissionConditionTypeWithoutCostumeSkill                       QuestMissionConditionType = 58
	QuestMissionConditionTypeWithoutWeaponSkill                        QuestMissionConditionType = 59
	QuestMissionConditionTypeWithoutCompanionSkill                     QuestMissionConditionType = 60
	QuestMissionConditionTypeCharacterContainAll                       QuestMissionConditionType = 61
	QuestMissionConditionTypeCharacterContainAny                       QuestMissionConditionType = 62
	QuestMissionConditionTypeCostumeContainAll                         QuestMissionConditionType = 63
	QuestMissionConditionTypeCostumeContainAny                         QuestMissionConditionType = 64
	QuestMissionConditionTypeCostumeSkillfulWeaponContainAll           QuestMissionConditionType = 65
	QuestMissionConditionTypeCostumeSkillfulWeaponContainAny           QuestMissionConditionType = 66
	QuestMissionConditionTypeAttributeMainWeaponContainAll             QuestMissionConditionType = 67
	QuestMissionConditionTypeAttributeMainWeaponContainAny             QuestMissionConditionType = 68
	QuestMissionConditionTypeAttributeWeaponContainAll                 QuestMissionConditionType = 69
	QuestMissionConditionTypeAttributeWeaponContainAny                 QuestMissionConditionType = 70
	QuestMissionConditionTypeWeaponManSkillfulWeaponContainAll         QuestMissionConditionType = 71
	QuestMissionConditionTypeWeaponManSkillfulWeaponContainAny         QuestMissionConditionType = 72
	QuestMissionConditionTypeWeaponSkillfulWeaponContainAll            QuestMissionConditionType = 73
	QuestMissionConditionTypeWeaponSkillfulWeaponContainAny            QuestMissionConditionType = 74
	QuestMissionConditionTypeComplete                                  QuestMissionConditionType = 9999
)

type mission struct {
	QuestMissionId                    int32                     `json:"QuestMissionId"`
	QuestMissionConditionType         QuestMissionConditionType `json:"QuestMissionConditionType"`
	QuestMissionRewardId              int32                     `json:"QuestMissionRewardId"`
	QuestMissionConditionValueGroupId int32                     `json:"QuestMissionConditionValueGroupId"`
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

type WeaponStoryReleaseConditionType int32

const (
	WeaponStoryReleaseConditionTypeUnknown                      = 0
	WeaponStoryReleaseConditionTypeAcquisition                  = 1
	WeaponStoryReleaseConditionTypeReachSpecifiedLevel          = 2
	WeaponStoryReleaseConditionTypeReachInitialMaxLevel         = 3
	WeaponStoryReleaseConditionTypeReachOnceEvolvedMaxLevel     = 4
	WeaponStoryReleaseConditionTypeReachSpecifiedEvolutionCount = 5
	WeaponStoryReleaseConditionTypeQuestClear                   = 6
	WeaponStoryReleaseConditionTypeMainFlowSceneProgress        = 7
)

type weaponStoryReleaseCondition struct {
	WeaponStoryReleaseConditionGroupId          int32                           `json:"WeaponStoryReleaseConditionGroupId"`
	StoryIndex                                  int32                           `json:"StoryIndex"`
	WeaponStoryReleaseConditionType             WeaponStoryReleaseConditionType `json:"WeaponStoryReleaseConditionType"`
	ConditionValue                              int32                           `json:"ConditionValue"`
	WeaponStoryReleaseConditionOperationGroupId int32                           `json:"WeaponStoryReleaseConditionOperationGroupId"`
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
	WeaponStoryReleaseConditionGroupId int32 `json:"WeaponStoryReleaseConditionGroupId"`
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
	BattleId            int32 `json:"BattleId"`
	BattleNpcId         int32 `json:"BattleNpcId"`
	DeckType            int32 `json:"DeckType"`
	BattleNpcDeckNumber int32 `json:"BattleNpcDeckNumber"`
}

type battleNpcDeck struct {
	BattleNpcId                  int32  `json:"BattleNpcId"`
	DeckType                     int32  `json:"DeckType"`
	BattleNpcDeckNumber          int32  `json:"BattleNpcDeckNumber"`
	BattleNpcDeckCharacterUuid01 string `json:"BattleNpcDeckCharacterUuid01"`
	BattleNpcDeckCharacterUuid02 string `json:"BattleNpcDeckCharacterUuid02"`
	BattleNpcDeckCharacterUuid03 string `json:"BattleNpcDeckCharacterUuid03"`
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

func (e *Engine) isQuestCleared(user *store.UserState, questId int32) bool {
	quest, ok := user.Quests[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for isQuestCleared", questId))
	}

	return quest.QuestStateType == store.UserQuestStateTypeCleared
}

func appendMissionRewards(dst []RewardGrant, src []missionReward) []RewardGrant {
	for _, r := range src {
		dst = append(dst, RewardGrant{
			PossessionType: r.PossessionType,
			PossessionId:   r.PossessionId,
			Count:          r.Count,
		})
	}
	return dst
}

func (e *Engine) firstClearRewardGroupId(user *store.UserState, questMeta quest) int32 {
	rewardGroupId := questMeta.QuestFirstClearRewardGroupId
	for _, switchRow := range e.firstClearRewardSwitchesByQuestId[questMeta.QuestId] {
		if e.isQuestCleared(user, switchRow.SwitchConditionClearQuestId) {
			rewardGroupId = switchRow.QuestFirstClearRewardGroupId
			break
		}
	}
	return rewardGroupId
}

func (e *Engine) evaluateFinishOutcome(user *store.UserState, questId int32) FinishOutcome {
	outcome := FinishOutcome{}
	quest, ok := user.Quests[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for evaluateFinishOutcome", questId))
	}
	questMeta, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for evaluateFinishOutcome", questId))
	}

	if !quest.IsRewardGranted {
		rewardGroupId := e.firstClearRewardGroupId(user, questMeta)
		for _, reward := range e.firstClearRewardsByGroupId[rewardGroupId] {
			outcome.FirstClearRewards = append(outcome.FirstClearRewards, RewardGrant{
				PossessionType: reward.PossessionType,
				PossessionId:   reward.PossessionId,
				Count:          reward.Count,
			})
		}
	}

	newlyClearedCount := 0
	totalNon9999 := 0
	for _, questMissionId := range e.missionIdsByQuestId[questId] {
		missionMaster, ok := e.missionById[questMissionId]
		if !ok || missionMaster.QuestMissionConditionType == QuestMissionConditionTypeComplete {
			continue
		}
		totalNon9999++

		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: questMissionId}
		mission := user.QuestMissions[key]

		if !mission.IsClear {
			newlyClearedCount++
			outcome.MissionClearRewards = appendMissionRewards(
				outcome.MissionClearRewards,
				e.missionRewardsByMissionId[missionMaster.QuestMissionRewardId],
			)
		}
	}

	alreadyClearedCount := totalNon9999 - newlyClearedCount
	allWillBeClear := totalNon9999 > 0 && (alreadyClearedCount+newlyClearedCount) == totalNon9999
	if allWillBeClear {
		for _, questMissionId := range e.missionIdsByQuestId[questId] {
			missionMaster, ok := e.missionById[questMissionId]
			if !ok || missionMaster.QuestMissionConditionType != QuestMissionConditionTypeComplete {
				continue
			}
			key := store.QuestMissionKey{QuestId: questId, QuestMissionId: questMissionId}
			if !user.QuestMissions[key].IsClear {
				outcome.MissionClearCompleteRewards = appendMissionRewards(
					outcome.MissionClearCompleteRewards,
					e.missionRewardsByMissionId[missionMaster.QuestMissionRewardId],
				)
				outcome.BigWinClearedQuestMissionIds = append(outcome.BigWinClearedQuestMissionIds, questMissionId)
			}
		}
		outcome.IsBigWin = len(outcome.BigWinClearedQuestMissionIds) > 0
	}

	if questMeta.QuestPickupRewardGroupId != 0 {
		for _, dropId := range e.pickupRewardIdsByGroupId[questMeta.QuestPickupRewardGroupId] {
			if bdr, ok := e.battleDropRewardById[dropId]; ok {
				outcome.DropRewards = append(outcome.DropRewards, RewardGrant{
					PossessionType: bdr.PossessionType,
					PossessionId:   bdr.PossessionId,
					Count:          bdr.Count,
				})
			}
		}
	}

	return outcome
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
	tutorialUnlockConditions           []tutorialUnlockCondition
	userExpThresholds                  []int32
	characterExpThresholds             []int32
	costumeExpByRarity                 map[int32][]int32
	maxStaminaByLevel                  map[int32]int32
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
	}

	for _, scene := range scenes {
		engine.sceneById[scene.QuestSceneId] = scene
		engine.sceneIdsByQuestId[scene.QuestId] = append(
			engine.sceneIdsByQuestId[scene.QuestId],
			scene.QuestSceneId,
		)
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
			missionIdsByGroupId[missionGroup.QuestMissionGroupId],
			missionGroup.QuestMissionId,
		)
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
		sequencesByGroupId[seq.MainQuestSequenceId] = append(
			sequencesByGroupId[seq.MainQuestSequenceId], seq,
		)
	}
	for _, chapter := range mainQuestChapters {
		for _, seq := range sequencesByGroupId[chapter.MainQuestSequenceGroupId] {
			engine.orderedQuestIds = append(engine.orderedQuestIds, seq.QuestId)
		}
	}

	for _, reward := range firstClearRewards {
		engine.firstClearRewardsByGroupId[reward.QuestFirstClearRewardGroupId] = append(
			engine.firstClearRewardsByGroupId[reward.QuestFirstClearRewardGroupId],
			reward,
		)
	}

	for _, switchRow := range firstClearRewardSwitches {
		engine.firstClearRewardSwitchesByQuestId[switchRow.QuestId] = append(
			engine.firstClearRewardSwitchesByQuestId[switchRow.QuestId],
			switchRow,
		)
	}

	for _, reward := range missionRewards {
		engine.missionRewardsByMissionId[reward.QuestMissionRewardId] = append(
			engine.missionRewardsByMissionId[reward.QuestMissionRewardId],
			reward,
		)
	}

	for _, w := range weapons {
		engine.weaponById[w.WeaponId] = w
		if w.WeaponStoryReleaseConditionGroupId != 0 {
			engine.weaponIdsByReleaseConditionGroupId[w.WeaponStoryReleaseConditionGroupId] = append(
				engine.weaponIdsByReleaseConditionGroupId[w.WeaponStoryReleaseConditionGroupId],
				w.WeaponId,
			)
		}
	}

	for _, c := range releaseConditions {
		engine.releaseConditionsByGroupId[c.WeaponStoryReleaseConditionGroupId] = append(
			engine.releaseConditionsByGroupId[c.WeaponStoryReleaseConditionGroupId],
			c,
		)
	}

	for _, cm := range costumeMasters {
		engine.costumeById[cm.CostumeId] = cm
	}

	for _, sg := range sceneGrants {
		engine.sceneGrantsBySceneId[sg.QuestSceneId] = append(
			engine.sceneGrantsBySceneId[sg.QuestSceneId],
			sg,
		)
	}

	for _, bdr := range battleDropRewards {
		engine.battleDropRewardById[bdr.BattleDropRewardId] = bdr
	}

	for _, pg := range pickupRewardGroups {
		engine.pickupRewardIdsByGroupId[pg.QuestPickupRewardGroupId] = append(
			engine.pickupRewardIdsByGroupId[pg.QuestPickupRewardGroupId],
			pg.BattleDropRewardId,
		)
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
		DeckType            int32
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

	return engine
}

func (e *Engine) initQuestState(user *store.UserState, questId int32) {
	quest := user.Quests[questId]
	quest.QuestId = questId
	user.Quests[questId] = quest

	for _, missionId := range e.missionIdsByQuestId[questId] {
		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: missionId}
		mission := user.QuestMissions[key]
		mission.QuestId = questId
		mission.QuestMissionId = missionId
		user.QuestMissions[key] = mission
	}
}

func isMainQuestPlayable(quest quest) bool {
	return !quest.IsRunInTheBackground && quest.IsCountedAsQuest
}

func (e *Engine) clearQuestMissions(user *store.UserState, questId int32, nowMillis int64) {
	for _, missionId := range e.missionIdsByQuestId[questId] {
		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: missionId}
		mission := user.QuestMissions[key]
		mission.IsClear = true
		mission.ProgressValue = 1
		mission.LatestClearDatetime = nowMillis
		user.QuestMissions[key] = mission
	}
}

func (e *Engine) HandleQuestStart(user *store.UserState, questId int32, isBattleOnly bool, nowMillis int64) {
	quest, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleQuestStart", questId))
	}

	e.initQuestState(user, questId)

	if quest.Stamina > 0 {
		user.Status.StaminaMilliValue = max(user.Status.StaminaMilliValue-quest.Stamina*1000, 0)
		user.Status.StaminaUpdateDatetime = nowMillis
		log.Printf("[HandleQuestStart] questId=%d stamina cost=%d -> remaining=%d", questId, quest.Stamina, user.Status.StaminaMilliValue)
	}

	questState := user.Quests[questId]
	if questState.QuestStateType == store.UserQuestStateTypeCleared {
		return
	}

	questState.IsBattleOnly = isBattleOnly
	if isMainQuestPlayable(quest) {
		user.MainQuest.CurrentQuestFlowType = int32(QuestFlowTypeMainFlow)
		questState.QuestStateType = store.UserQuestStateTypeActive
		questState.LatestStartDatetime = nowMillis
	} else {
		questState.QuestStateType = store.UserQuestStateTypeCleared
		questState.ClearCount = 1
		questState.DailyClearCount = 1
		questState.LastClearDatetime = nowMillis
	}
	user.Quests[questId] = questState
}

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

func (e *Engine) BattleDropRewards(questId int32) []BattleDropInfo {
	return e.battleDropsByQuestId[questId]
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
	user.MainQuest.CurrentQuestFlowType = int32(QuestFlowTypeMainFlow)

	routeId, ok := e.routeIdByQuestId[quest.QuestId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleMainFlowSceneProgress setting currentMainQuestRouteId", quest.QuestId))
	}
	user.MainQuest.CurrentMainQuestRouteId = routeId

	e.applySceneGrants(user, questSceneId, nowMillis)
}

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

	e.advanceTutorialForBootstrap(user, sceneId)
}

func (e *Engine) advanceTutorialForBootstrap(user *store.UserState, bootstrapSceneId int32) {
	added := 0
	for _, cond := range e.tutorialUnlockConditions {
		satisfied := false
		switch cond.TutorialUnlockConditionType {
		case tutorialUnlockReachSpecifiedQuestScene:
			satisfied = bootstrapSceneId >= cond.ConditionValue
		case tutorialUnlockUntilReachSpecifiedScene:
			satisfied = bootstrapSceneId >= cond.ConditionValue
		}
		if satisfied {
			if _, exists := user.Tutorials[cond.TutorialType]; !exists {
				user.Tutorials[cond.TutorialType] = store.TutorialProgressState{
					TutorialType:  cond.TutorialType,
					ProgressPhase: 99999,
				}
				added++
			}
		}
	}
	if added > 0 {
		log.Printf("[ApplyBootstrap] marked %d tutorials as completed for scene=%d", added, bootstrapSceneId)
	}
}

func (e *Engine) HandleQuestRestart(user *store.UserState, questId int32, nowMillis int64) {
	quest := user.Quests[questId]
	quest.QuestId = questId
	quest.QuestStateType = store.UserQuestStateTypeActive
	quest.IsBattleOnly = false
	quest.LatestStartDatetime = nowMillis
	user.Quests[questId] = quest

	for _, missionId := range e.missionIdsByQuestId[questId] {
		key := store.QuestMissionKey{QuestId: questId, QuestMissionId: missionId}
		m := user.QuestMissions[key]
		m.QuestId = questId
		m.QuestMissionId = missionId
		m.IsClear = false
		m.ProgressValue = 0
		m.LatestClearDatetime = 0
		user.QuestMissions[key] = m
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
		if scene.QuestResultType == QuestResultTypeHalfResult {
			nowMillis := gametime.NowMillis()
			e.clearQuestMissions(user, quest.QuestId, nowMillis)
		}

		user.MainQuest.ProgressQuestSceneId = questSceneId
		if e.isSceneAhead(questSceneId, user.MainQuest.ProgressHeadQuestSceneId) {
			user.MainQuest.ProgressHeadQuestSceneId = questSceneId
		}
		user.MainQuest.CurrentQuestFlowType = int32(QuestFlowTypeSubFlow)
		user.MainQuest.ProgressQuestFlowType = int32(QuestFlowTypeSubFlow)
	}
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

func levelFromExp(exp int32, thresholds []int32) int32 {
	level := int32(1)
	for lvl := 1; lvl < len(thresholds); lvl++ {
		if exp >= thresholds[lvl] {
			level = int32(lvl)
		} else {
			break
		}
	}
	return level
}

func (e *Engine) applyExpRewards(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := e.questById[questId]
	if !ok {
		return
	}

	oldLevel := user.Status.Level
	user.Status.Exp += questMeta.UserExp
	user.Status.Level = levelFromExp(user.Status.Exp, e.userExpThresholds)
	log.Printf("[applyExpRewards] questId=%d user: +%d exp -> total=%d level=%d", questId, questMeta.UserExp, user.Status.Exp, user.Status.Level)

	if user.Status.Level > oldLevel {
		if maxStamina, ok := e.maxStaminaByLevel[user.Status.Level]; ok {
			user.Status.StaminaMilliValue = maxStamina * 1000
			user.Status.StaminaUpdateDatetime = nowMillis
			log.Printf("[applyExpRewards] level-up %d->%d, stamina replenished to %d", oldLevel, user.Status.Level, maxStamina)
		}
	}

	if questMeta.CharacterExp != 0 {
		for id, row := range user.Characters {
			row.Exp += questMeta.CharacterExp
			row.Level = levelFromExp(row.Exp, e.characterExpThresholds)
			user.Characters[id] = row
			log.Printf("[applyExpRewards] questId=%d character=%d: +%d exp -> total=%d level=%d", questId, id, questMeta.CharacterExp, row.Exp, row.Level)
		}
	}

	if questMeta.CostumeExp != 0 {
		for key, row := range user.Costumes {
			row.Exp += questMeta.CostumeExp
			cm, ok := e.costumeById[row.CostumeId]
			if ok {
				if thresholds, ok := e.costumeExpByRarity[cm.RarityType]; ok {
					row.Level = levelFromExp(row.Exp, thresholds)
				}
			}
			user.Costumes[key] = row
			log.Printf("[applyExpRewards] questId=%d costume=%d (key=%s): +%d exp -> total=%d level=%d", questId, row.CostumeId, key, questMeta.CostumeExp, row.Exp, row.Level)
		}
	}
}

const goldConsumableItemId int32 = 1

func (e *Engine) applyQuestRewards(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := e.questById[questId]
	if !ok {
		return
	}

	e.applyExpRewards(user, questId, nowMillis)

	if questMeta.Gold != 0 {
		user.ConsumableItems[goldConsumableItemId] += questMeta.Gold
		log.Printf("[applyQuestRewards] questId=%d gold: +%d -> total=%d", questId, questMeta.Gold, user.ConsumableItems[goldConsumableItemId])
	}

	rewardGroupId := e.firstClearRewardGroupId(user, questMeta)
	for _, reward := range e.firstClearRewardsByGroupId[rewardGroupId] {
		e.applyRewardPossession(user, reward.PossessionType, reward.PossessionId, reward.Count, nowMillis)
	}
}

func (e *Engine) applyRewardPossession(user *store.UserState, possType model.PossessionType, possId, count int32, nowMillis int64) {
	switch possType {
	case model.PossessionTypeFreeGem:
		user.Gem.FreeGem += count
	case model.PossessionTypePaidGem:
		user.Gem.PaidGem += count
	case model.PossessionTypeCostume:
		e.grantCostume(user, possId, nowMillis)
	case model.PossessionTypeWeapon:
		e.grantWeapon(user, possId, nowMillis)
	case model.PossessionTypeCompanion:
		e.grantCompanion(user, possId, nowMillis)
	case model.PossessionTypeParts:
		e.grantParts(user, possId, nowMillis)
	case model.PossessionTypeCostumeEnhanced:
		e.grantCostume(user, possId, nowMillis)
	case model.PossessionTypeMaterial, model.PossessionTypeConsumableItem, model.PossessionTypeImportantItem:
		store.GrantPossession(user, possType, possId, count)
	default:
		log.Printf("[Engine] unsupported reward possession: type=%d id=%d count=%d", possType, possId, count)
	}
}

func (e *Engine) grantCostume(user *store.UserState, costumeId int32, nowMillis int64) {
	for _, row := range user.Costumes {
		if row.CostumeId == costumeId {
			return
		}
	}
	if cm, ok := e.costumeById[costumeId]; ok {
		if _, exists := user.Characters[cm.CharacterId]; !exists {
			user.Characters[cm.CharacterId] = store.CharacterState{
				CharacterId: cm.CharacterId,
				Level:       1,
			}
		}
	}
	key := fmt.Sprintf("reward-costume-%d", costumeId)
	user.Costumes[key] = store.CostumeState{
		UserCostumeUuid:     key,
		CostumeId:           costumeId,
		Level:               1,
		HeadupDisplayViewId: 1,
		AcquisitionDatetime: nowMillis,
	}
	user.CostumeActiveSkills[key] = store.CostumeActiveSkillState{
		UserCostumeUuid:     key,
		Level:               1,
		AcquisitionDatetime: nowMillis,
	}
}

func (e *Engine) grantWeapon(user *store.UserState, weaponId int32, nowMillis int64) {
	for _, row := range user.Weapons {
		if row.WeaponId == weaponId {
			return
		}
	}
	key := fmt.Sprintf("reward-weapon-%d", weaponId)
	user.Weapons[key] = store.WeaponState{
		UserWeaponUuid:      key,
		WeaponId:            weaponId,
		Level:               1,
		AcquisitionDatetime: nowMillis,
	}
	if _, exists := user.WeaponNotes[weaponId]; !exists {
		user.WeaponNotes[weaponId] = store.WeaponNoteState{
			WeaponId:                 weaponId,
			MaxLevel:                 1,
			MaxLimitBreakCount:       0,
			FirstAcquisitionDatetime: nowMillis,
			LatestVersion:            nowMillis,
		}
	}
	weapon, ok := e.weaponById[weaponId]
	if ok && weapon.WeaponStoryReleaseConditionGroupId != 0 {
		for _, cond := range e.releaseConditionsByGroupId[weapon.WeaponStoryReleaseConditionGroupId] {
			if cond.WeaponStoryReleaseConditionType == WeaponStoryReleaseConditionTypeAcquisition {
				e.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
			}
		}
	}
}

func (e *Engine) grantCompanion(user *store.UserState, companionId int32, nowMillis int64) {
	for _, row := range user.Companions {
		if row.CompanionId == companionId {
			return
		}
	}
	key := fmt.Sprintf("reward-companion-%d", companionId)
	user.Companions[key] = store.CompanionState{
		UserCompanionUuid:   key,
		CompanionId:         companionId,
		Level:               1,
		HeadupDisplayViewId: 1,
		AcquisitionDatetime: nowMillis,
	}
}

func (e *Engine) grantParts(user *store.UserState, partsId int32, nowMillis int64) {
	for _, row := range user.Parts {
		if row.PartsId == partsId {
			return
		}
	}
	key := fmt.Sprintf("reward-parts-%d", partsId)
	user.Parts[key] = store.PartsState{
		UserPartsUuid:       key,
		PartsId:             partsId,
		Level:               1,
		AcquisitionDatetime: nowMillis,
	}
}

func (e *Engine) grantWeaponStoryUnlock(user *store.UserState, weaponId, storyIndex int32, nowMillis int64) {
	// Consistency guard: only grant story if weapon exists in IUserWeapon.
	// Client's GetUnlockWeaponStoryWeapons iterates IUserWeapon; if we send IUserWeaponStory
	// for a weapon not in IUserWeapon, the client may crash on null lookup.
	hasWeapon := false
	for _, row := range user.Weapons {
		if row.WeaponId == weaponId {
			hasWeapon = true
			break
		}
	}
	if !hasWeapon {
		log.Printf("[Engine] grantWeaponStoryUnlock: skipping weaponId=%d (weapon not in user.Weapons)", weaponId)
		return
	}
	if user.WeaponStories == nil {
		user.WeaponStories = make(map[int32]store.WeaponStoryState)
	}
	cur := user.WeaponStories[weaponId]
	if storyIndex <= cur.ReleasedMaxStoryIndex {
		return
	}
	user.WeaponStories[weaponId] = store.WeaponStoryState{
		WeaponId:              weaponId,
		ReleasedMaxStoryIndex: storyIndex,
		LatestVersion:         nowMillis,
	}
}

func (e *Engine) grantWeaponStoryUnlocksForQuestScene(user *store.UserState, questId int32, resultType QuestResultType, nowMillis int64) {
	if resultType == QuestResultTypeHalfResult {
		questMeta, ok := e.questById[questId]
		if !ok {
			return
		}
		rewardGroupId := e.firstClearRewardGroupId(user, questMeta)
		for _, reward := range e.firstClearRewardsByGroupId[rewardGroupId] {
			if reward.PossessionType != model.PossessionTypeWeapon {
				continue
			}
			weaponId := reward.PossessionId
			weapon, ok := e.weaponById[weaponId]
			if !ok || weapon.WeaponStoryReleaseConditionGroupId == 0 {
				continue
			}
			groupId := weapon.WeaponStoryReleaseConditionGroupId
			for _, cond := range e.releaseConditionsByGroupId[groupId] {
				if cond.WeaponStoryReleaseConditionType == WeaponStoryReleaseConditionTypeAcquisition && cond.ConditionValue == 0 {
					e.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
				}
			}
		}
		return
	}
	if resultType == QuestResultTypeFullResult {
		for groupId, conditions := range e.releaseConditionsByGroupId {
			for _, cond := range conditions {
				if cond.WeaponStoryReleaseConditionType == WeaponStoryReleaseConditionTypeQuestClear && cond.ConditionValue == questId {
					for _, weaponId := range e.weaponIdsByReleaseConditionGroupId[groupId] {
						e.grantWeaponStoryUnlock(user, weaponId, cond.StoryIndex, nowMillis)
					}
					break
				}
			}
		}
	}
}

func (e *Engine) HandleQuestFinish(user *store.UserState, questId int32, isRetired bool, nowMillis int64) FinishOutcome {
	_, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleQuestFinish", questId))
	}

	outcome := e.evaluateFinishOutcome(user, questId)

	questState := user.Quests[questId]
	if !questState.IsRewardGranted && !isRetired {
		e.applyQuestRewards(user, questId, nowMillis)
		e.grantWeaponStoryUnlocksForQuestScene(user, questId, QuestResultTypeHalfResult, nowMillis)
		e.grantWeaponStoryUnlocksForQuestScene(user, questId, QuestResultTypeFullResult, nowMillis)
		questState.IsRewardGranted = true
	}
	if !isRetired {
		for _, drop := range outcome.DropRewards {
			e.applyRewardPossession(user, drop.PossessionType, drop.PossessionId, drop.Count, nowMillis)
		}
	}
	questState.QuestStateType = store.UserQuestStateTypeCleared
	questState.ClearCount = 1
	questState.DailyClearCount = 1
	questState.LastClearDatetime = nowMillis

	user.MainQuest.ProgressQuestSceneId = 0
	user.MainQuest.ProgressHeadQuestSceneId = 0
	user.MainQuest.ProgressQuestFlowType = 0
	user.MainQuest.CurrentQuestFlowType = int32(QuestFlowTypeUnknown)
	user.Quests[questId] = questState

	e.clearQuestMissions(user, questId, nowMillis)

	return outcome
}
