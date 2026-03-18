package questflow

import (
	"fmt"
	"log"
	"sort"
	"time"

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
}

type weaponMaster struct {
	WeaponId                           int32 `json:"WeaponId"`
	WeaponStoryReleaseConditionGroupId int32 `json:"WeaponStoryReleaseConditionGroupId"`
}

type RewardGrant struct {
	PossessionType model.PossessionType
	PossessionId   int32
	Count          int32
}

type FinishOutcome struct {
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

	return outcome
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

	sceneGrants, err := utils.ReadJSON[sceneGrant]("EntityMUserQuestSceneGrantPossessionTable.json")
	if err != nil {
		panic(err)
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
	user.MainQuest.HeadQuestSceneId = max(user.MainQuest.HeadQuestSceneId, questSceneId)
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
		panic(fmt.Sprintf("unknown sceneId=%d for ApplyBootstrap", sceneId))
	}
	targetQuestId := scene.QuestId

	for _, questId := range e.orderedQuestIds {
		if questId == targetQuestId {
			break
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
			e.HandleQuestFinish(user, questId, nowMillis)
		}
	}

	e.HandleQuestStart(user, targetQuestId, false, nowMillis)
	for _, sid := range e.sceneIdsByQuestId[targetQuestId] {
		e.HandleMainFlowSceneProgress(user, sid, nowMillis)
		e.HandleMainQuestSceneProgress(user, sid)
		if sid == sceneId {
			break
		}
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

	for i := len(sceneIds) - 1; i >= 0; i-- {
		sceneId := sceneIds[i]
		scene := e.sceneById[sceneId]
		if scene.IsMainFlowQuestTarget {
			return sceneId
		}
	}

	panic(fmt.Sprintf("no main flow target scene found for questId=%d", questId))
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
	user.MainQuest.HeadQuestSceneId = max(user.MainQuest.HeadQuestSceneId, questSceneId)
	lastSceneId := e.getLastMainFlowSceneId(quest.QuestId)
	user.MainQuest.IsReachedLastQuestScene = questSceneId == lastSceneId

	if isMainQuestPlayable(quest) {
		questState := user.Quests[quest.QuestId]
		if scene.QuestResultType == QuestResultTypeHalfResult {
			nowMillis := time.Now().UnixMilli()
			e.clearQuestMissions(user, quest.QuestId, nowMillis)
			e.applyExpRewards(user, quest.QuestId, nowMillis)
		}
		if scene.QuestResultType == QuestResultTypeFullResult {
			questState.QuestStateType = store.UserQuestStateTypeCleared
			questState.ClearCount = 1
			questState.DailyClearCount = 1
		}
		user.Quests[quest.QuestId] = questState

		user.MainQuest.ProgressQuestSceneId = questSceneId
		user.MainQuest.ProgressHeadQuestSceneId = max(user.MainQuest.ProgressHeadQuestSceneId, questSceneId)
		user.MainQuest.CurrentQuestFlowType = int32(QuestFlowTypeSubFlow)
		user.MainQuest.ProgressQuestFlowType = int32(QuestFlowTypeSubFlow)
	}
}

func (e *Engine) applyExpRewards(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := e.questById[questId]
	if !ok {
		return
	}

	user.Status.Exp += questMeta.UserExp

	if questMeta.CharacterExp != 0 {
		for id, row := range user.Characters {
			row.Exp += questMeta.CharacterExp
			user.Characters[id] = row
		}
	}

	if questMeta.CostumeExp != 0 {
		for key, row := range user.Costumes {
			row.Exp += questMeta.CostumeExp
			user.Costumes[key] = row
		}
	}
}

func (e *Engine) applyQuestRewards(user *store.UserState, questId int32, nowMillis int64) {
	questMeta, ok := e.questById[questId]
	if !ok {
		return
	}

	e.applyExpRewards(user, questId, nowMillis)

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

func (e *Engine) HandleQuestFinish(user *store.UserState, questId int32, nowMillis int64) FinishOutcome {
	_, ok := e.questById[questId]
	if !ok {
		panic(fmt.Sprintf("unknown questId=%d for HandleQuestFinish", questId))
	}

	outcome := e.evaluateFinishOutcome(user, questId)

	questState := user.Quests[questId]
	if !questState.IsRewardGranted {
		e.applyQuestRewards(user, questId, nowMillis)
		e.grantWeaponStoryUnlocksForQuestScene(user, questId, QuestResultTypeHalfResult, nowMillis)
		e.grantWeaponStoryUnlocksForQuestScene(user, questId, QuestResultTypeFullResult, nowMillis)
		questState.IsRewardGranted = true
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
