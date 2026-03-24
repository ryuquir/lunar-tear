package memory

import (
	"fmt"
	"time"

	"lunar-tear/server/internal/store"
)

const (
	defaultUUID   = "default-user"
	defaultUserId = int64(1001)

	starterMissionId          = int32(1)
	starterMainQuestRouteId   = int32(1)
	starterMainQuestSeasonId  = int32(1)
	missionInProgress         = int32(1)
	giftPossessionTypeFreeGem = int32(12)
	giftDefaultCount          = int32(300)
	giftUUIDPrefix            = "default-gift"

	defaultBirthYear            = int32(2000)
	defaultBirthMonth           = int32(1)
	defaultBackupToken          = "mock-backup-token"
	defaultChargeMoneyThisMonth = int64(0)
)

func seedUserState(userId int64, uuid string, nowMillis int64, sceneId int32, bootstrapper store.Bootstrapper) *store.UserState {
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
						PossessionType: giftPossessionTypeFreeGem,
						PossessionId:   0,
						Count:          giftDefaultCount,
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
		},
		MainQuest: store.MainQuestState{
			CurrentMainQuestRouteId: starterMainQuestRouteId,
			MainQuestSeasonId:       starterMainQuestSeasonId,
		},
		Notifications: store.NotificationState{
			GiftNotReceiveCount: 1,
		},
		Characters:     make(map[int32]store.CharacterState),
		Costumes:       make(map[string]store.CostumeState),
		Weapons:        make(map[string]store.WeaponState),
		Companions:     make(map[string]store.CompanionState),
		DeckCharacters: make(map[string]store.DeckCharacterState),
		Decks:          make(map[store.DeckKey]store.DeckState),
		DeckSubWeapons: make(map[string][]string),
		Quests:         make(map[int32]store.UserQuestState),
		QuestMissions:  make(map[store.QuestMissionKey]store.UserQuestMissionState),
		WeaponStories:  make(map[int32]store.WeaponStoryState),
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
		CageOrnamentRewards: make(map[int32]store.CageOrnamentRewardState),
		ConsumableItems:     make(map[int32]int32),
		Materials:           make(map[int32]int32),
		Thoughts:            make(map[string]store.ThoughtState),
		Parts:               make(map[string]store.PartsState),
		ImportantItems:      make(map[int32]int32),
		CostumeActiveSkills: make(map[string]store.CostumeActiveSkillState),
		DeckTypeNotes:       make(map[int32]store.DeckTypeNoteState),
		WeaponNotes:         make(map[int32]store.WeaponNoteState),
		NaviCutInPlayed:     make(map[int32]bool),
		DokanConfirmed:      make(map[int32]bool),
	}
	if bootstrapper != nil {
		bootstrapper.ApplyBootstrap(user, sceneId, nowMillis)
	}
	store.EnsureDefaultDeck(user, nowMillis)
	return user
}
