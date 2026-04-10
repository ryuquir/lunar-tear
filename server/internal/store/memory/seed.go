package memory

import (
	"fmt"
	"log"
	"time"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
)

const (
	defaultUUID   = "default-user"
	defaultUserId = int64(1001)

	starterMissionId         = int32(1)
	starterMainQuestRouteId  = int32(1)
	starterMainQuestSeasonId = int32(1)
	missionInProgress        = int32(1)
	giftUUIDPrefix           = "default-gift"

	defaultBirthYear            = int32(2000)
	defaultBirthMonth           = int32(1)
	defaultBackupToken          = "mock-backup-token"
	defaultChargeMoneyThisMonth = int64(0)
)

type starterItemDef struct {
	Type model.PossessionType
	Id   int32
	Qty  int32
}

var defaultStarterItems = []starterItemDef{
	{Type: model.PossessionTypeFreeGem, Id: 0, Qty: 300},
	{Type: model.PossessionTypeConsumableItem, Id: 9001, Qty: 1000},
	{Type: model.PossessionTypeConsumableItem, Id: model.ConsumableIdChapterTicket, Qty: 1000},
	{Type: model.PossessionTypeConsumableItem, Id: 5001, Qty: 1000},
	{Type: model.PossessionTypeConsumableItem, Id: 5002, Qty: 1000},
	{Type: model.PossessionTypeConsumableItem, Id: 5003, Qty: 1000},
	{Type: model.PossessionTypeConsumableItem, Id: 1009, Qty: 1000},
}

func seedUserState(userId int64, uuid string, nowMillis int64, sceneId int32, snapshotDir string, grantStarterItems bool) *store.UserState {
	if sceneId != 0 && snapshotDir != "" {
		user, err := loadSnapshot(snapshotDir, sceneId)
		if err != nil {
			log.Fatalf("[bootstrap] no snapshot for scene=%d: %v", sceneId, err)
		}
		log.Printf("[bootstrap] loaded snapshot for scene=%d", sceneId)
		if grantStarterItems {
			applyStarterItems(user)
		}
		return user
	}

	user := &store.UserState{
		UserId:               userId,
		Uuid:                 uuid,
		PlayerId:             userId,
		OsType:               2,
		PlatformType:         2,
		UserRestrictionType:  0,
		RegisterDatetime:     nowMillis,
		GameStartDatetime:    nowMillis,
		LatestVersion:        0,
		BirthYear:            defaultBirthYear,
		BirthMonth:           defaultBirthMonth,
		BackupToken:          defaultBackupToken,
		ChargeMoneyThisMonth: defaultChargeMoneyThisMonth,
		Setting: store.UserSettingState{
			IsNotifyPurchaseAlert: false,
			LatestVersion:         0,
		},
		Status: store.UserStatusState{
			Level:                 1,
			Exp:                   0,
			StaminaMilliValue:     50000,
			StaminaUpdateDatetime: nowMillis,
			LatestVersion:         0,
		},
		Gem: store.UserGemState{
			PaidGem: 10000,
			FreeGem: 10000,
		},
		Profile: store.UserProfileState{
			Name:                            "",
			NameUpdateDatetime:              0,
			Message:                         "",
			MessageUpdateDatetime:           nowMillis,
			FavoriteCostumeId:               0,
			FavoriteCostumeIdUpdateDatetime: nowMillis,
			LatestVersion:                   0,
		},
		Login: store.UserLoginState{
			TotalLoginCount:           1,
			ContinualLoginCount:       1,
			MaxContinualLoginCount:    1,
			LastLoginDatetime:         nowMillis,
			LastComebackLoginDatetime: 0,
			LatestVersion:             0,
		},
		LoginBonus: store.UserLoginBonusState{
			LoginBonusId:                1,
			CurrentPageNumber:           1,
			CurrentStampNumber:          0,
			LatestRewardReceiveDatetime: 0,
			LatestVersion:               0,
		},
		Tutorials: map[int32]store.TutorialProgressState{
			1: {TutorialType: 1},
		},
		Battle: store.BattleState{},
		Gifts: store.GiftState{
			NotReceived: []store.NotReceivedGiftState{
				{
					GiftCommon: store.GiftCommonState{
						PossessionType: int32(model.PossessionTypeFreeGem),
						PossessionId:   0,
						Count:          300,
						GrantDatetime:  nowMillis,
					},
					ExpirationDatetime: nowMillis + int64((7*24*time.Hour)/time.Millisecond),
					UserGiftUuid:       fmt.Sprintf("%s-%d-1", giftUUIDPrefix, userId),
				},
			},
			Received: []store.ReceivedGiftState{},
		},
		Gacha: store.GachaState{
			ConvertedGachaMedal: store.ConvertedGachaMedalState{
				ConvertedMedalPossession: []store.ConsumableItemState{},
			},
			BannerStates: make(map[int32]store.GachaBannerState),
		},
		MainQuest: store.MainQuestState{
			CurrentMainQuestRouteId: starterMainQuestRouteId,
			MainQuestSeasonId:       starterMainQuestSeasonId,
		},
		Notifications: store.NotificationState{
			GiftNotReceiveCount: 1,
		},
		Characters:               make(map[int32]store.CharacterState),
		Costumes:                 make(map[string]store.CostumeState),
		Weapons:                  make(map[string]store.WeaponState),
		Companions:               make(map[string]store.CompanionState),
		DeckCharacters:           make(map[string]store.DeckCharacterState),
		Decks:                    make(map[store.DeckKey]store.DeckState),
		DeckSubWeapons:           make(map[string][]string),
		DeckParts:                make(map[string][]string),
		Quests:                   make(map[int32]store.UserQuestState),
		QuestMissions:            make(map[store.QuestMissionKey]store.UserQuestMissionState),
		SideStoryQuests:          make(map[int32]store.SideStoryQuestProgress),
		QuestLimitContentStatus:  make(map[int32]store.QuestLimitContentStatus),
		BigHuntMaxScores:         make(map[int32]store.BigHuntMaxScore),
		BigHuntStatuses:          make(map[int32]store.BigHuntStatus),
		BigHuntScheduleMaxScores: make(map[store.BigHuntScheduleScoreKey]store.BigHuntScheduleMaxScore),
		BigHuntWeeklyMaxScores:   make(map[store.BigHuntWeeklyScoreKey]store.BigHuntWeeklyMaxScore),
		BigHuntWeeklyStatuses:    make(map[int64]store.BigHuntWeeklyStatus),
		WeaponStories:            make(map[int32]store.WeaponStoryState),
		Missions: map[int32]store.UserMissionState{
			starterMissionId: {
				MissionId:                 starterMissionId,
				StartDatetime:             nowMillis,
				MissionProgressStatusType: missionInProgress,
			},
		},
		Gimmick: store.GimmickState{
			Progress:         make(map[store.GimmickKey]store.GimmickProgressState),
			OrnamentProgress: make(map[store.GimmickOrnamentKey]store.GimmickOrnamentProgressState),
			Sequences:        make(map[store.GimmickSequenceKey]store.GimmickSequenceState),
			Unlocks:          make(map[store.GimmickKey]store.GimmickUnlockState),
		},
		CageOrnamentRewards:   make(map[int32]store.CageOrnamentRewardState),
		ConsumableItems:       make(map[int32]int32),
		Materials:             make(map[int32]int32),
		Thoughts:              make(map[string]store.ThoughtState),
		Parts:                 make(map[string]store.PartsState),
		PartsGroupNotes:       make(map[int32]store.PartsGroupNoteState),
		PartsPresets:          make(map[int32]store.PartsPresetState),
		ImportantItems:        make(map[int32]int32),
		CostumeActiveSkills:   make(map[string]store.CostumeActiveSkillState),
		WeaponSkills:          make(map[string][]store.WeaponSkillState),
		WeaponAbilities:       make(map[string][]store.WeaponAbilityState),
		DeckTypeNotes:         make(map[model.DeckType]store.DeckTypeNoteState),
		WeaponNotes:           make(map[int32]store.WeaponNoteState),
		NaviCutInPlayed:       make(map[int32]bool),
		ViewedMovies:          make(map[int32]int64),
		ContentsStories:       make(map[int32]int64),
		DrawnOmikuji:          make(map[int32]int64),
		PremiumItems:          make(map[int32]int64),
		DokanConfirmed:        make(map[int32]bool),
		ShopItems:             make(map[int32]store.UserShopItemState),
		ShopReplaceableLineup: make(map[int32]store.UserShopReplaceableLineupState),
		ExploreScores:         make(map[int32]store.ExploreScoreState),

		CharacterBoards:         make(map[int32]store.CharacterBoardState),
		CharacterBoardAbilities: make(map[store.CharacterBoardAbilityKey]store.CharacterBoardAbilityState),
		CharacterBoardStatusUps: make(map[store.CharacterBoardStatusUpKey]store.CharacterBoardStatusUpState),

		CostumeAwakenStatusUps: make(map[store.CostumeAwakenStatusKey]store.CostumeAwakenStatusUpState),
		AutoSaleSettings:       make(map[int32]store.AutoSaleSettingState),
		CharacterRebirths:      make(map[int32]store.CharacterRebirthState),
	}
	store.EnsureDefaultDeck(user, nowMillis)
	if grantStarterItems {
		applyStarterItems(user)
	}
	return user
}

func applyStarterItems(user *store.UserState) {
	for _, item := range defaultStarterItems {
		switch item.Type {
		case model.PossessionTypeFreeGem:
			user.Gem.FreeGem += item.Qty
		case model.PossessionTypeConsumableItem:
			user.ConsumableItems[item.Id] += item.Qty
		case model.PossessionTypeMaterial:
			user.Materials[item.Id] += item.Qty
		}
	}
}
