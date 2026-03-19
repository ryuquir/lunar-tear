package service

import (
	"context"

	"lunar-tear/server/internal/store"

	"google.golang.org/grpc/metadata"
)

var startedGameStartTables = []string{
	"IUserProfile",
	"IUserCharacter",
	"IUserCostume",
	"IUserWeapon",
	"IUserCompanion",
	"IUserDeckCharacter",
	"IUserDeck",
	"IUserGem",
	"IUserMission",
	"IUserMainQuestFlowStatus",
	"IUserMainQuestMainFlowStatus",
	"IUserMainQuestProgressStatus",
	"IUserMainQuestSeasonRoute",
	"IUserQuest",
	"IUserQuestMission",
	"IUserTutorialProgress",
	"IUserWeaponNote",
	"IUserWeaponStory",
	"IUserCostumeActiveSkill",
	"IUserDeckTypeNote",
	"IUserDeckSubWeaponGroup",
	"IUserDeckPartsGroup",
	"IUserConsumableItem",
	"IUserMaterial",
	"IUserImportantItem",
}

var gimmickDiffTables = []string{
	"IUserGimmick",
	"IUserGimmickOrnamentProgress",
	"IUserGimmickSequence",
	"IUserGimmickUnlock",
}

func currentUserId(ctx context.Context, userStore *store.Store) int64 {
	if userStore == nil {
		return 0
	}
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if vals := md.Get("x-session-key"); len(vals) > 0 {
			if userId, ok := userStore.ResolveUserId(vals[0]); ok {
				return userId
			}
		}
	}

	defaultUserId := userStore.DefaultUserId()
	if _, ok := userStore.SnapshotUser(defaultUserId); ok {
		return defaultUserId
	}
	return userStore.EnsureUser("").UserId
}
