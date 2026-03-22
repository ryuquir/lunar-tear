package userdata

import (
	"log"
	"sort"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/store"
)

func FullClientTableMap(user store.UserState) map[string]string {
	userJSON, _ := encodeJSONMaps(map[string]any{
		"userId":              user.UserId,
		"playerId":            user.PlayerId,
		"osType":              user.OsType,
		"platformType":        user.PlatformType,
		"userRestrictionType": user.UserRestrictionType,
		"registerDatetime":    user.RegisterDatetime,
		"gameStartDatetime":   user.GameStartDatetime,
		"latestVersion":       user.LatestVersion,
	})
	userSettingJSON, _ := encodeJSONRecords(&EntityIUserSetting{
		UserId:                user.UserId,
		IsNotifyPurchaseAlert: user.Setting.IsNotifyPurchaseAlert,
		LatestVersion:         user.Setting.LatestVersion,
	})
	userStatusJSON, _ := encodeJSONMaps(map[string]any{
		"userId":                user.UserId,
		"level":                 user.Status.Level,
		"exp":                   user.Status.Exp,
		"staminaMilliValue":     user.Status.StaminaMilliValue,
		"staminaUpdateDatetime": user.Status.StaminaUpdateDatetime,
		"latestVersion":         user.Status.LatestVersion,
	})
	userGemJSON, _ := encodeJSONRecords(&EntityIUserGem{
		UserId:  user.UserId,
		PaidGem: user.Gem.PaidGem,
		FreeGem: user.Gem.FreeGem,
	})
	userProfileJSON, _ := encodeJSONMaps(map[string]any{
		"userId":                          user.UserId,
		"name":                            user.Profile.Name,
		"nameUpdateDatetime":              user.Profile.NameUpdateDatetime,
		"message":                         user.Profile.Message,
		"messageUpdateDatetime":           user.Profile.MessageUpdateDatetime,
		"favoriteCostumeId":               user.Profile.FavoriteCostumeId,
		"favoriteCostumeIdUpdateDatetime": user.Profile.FavoriteCostumeIdUpdateDatetime,
		"latestVersion":                   user.Profile.LatestVersion,
	})
	userLoginJSON, _ := encodeJSONRecords(&EntityIUserLogin{
		UserId:                    user.UserId,
		TotalLoginCount:           user.Login.TotalLoginCount,
		ContinualLoginCount:       user.Login.ContinualLoginCount,
		MaxContinualLoginCount:    user.Login.MaxContinualLoginCount,
		LastLoginDatetime:         user.Login.LastLoginDatetime,
		LastComebackLoginDatetime: user.Login.LastComebackLoginDatetime,
		LatestVersion:             user.Login.LatestVersion,
	})
	userLoginBonusJSON, _ := encodeJSONRecords(&EntityIUserLoginBonus{
		UserId:                      user.UserId,
		LoginBonusId:                user.LoginBonus.LoginBonusId,
		CurrentPageNumber:           user.LoginBonus.CurrentPageNumber,
		CurrentStampNumber:          user.LoginBonus.CurrentStampNumber,
		LatestRewardReceiveDatetime: user.LoginBonus.LatestRewardReceiveDatetime,
		LatestVersion:               user.LoginBonus.LatestVersion,
	})
	userTutorialProgressJSON, _ := encodeJSONMaps(sortedTutorialRecords(user)...)
	mainQuestFlowJSON, _ := encodeJSONMaps(map[string]any{
		"userId":               user.UserId,
		"currentQuestFlowType": user.MainQuest.CurrentQuestFlowType,
		"latestVersion":        user.MainQuest.LatestVersion,
	})
	mainQuestMainFlowJSON, _ := encodeJSONMaps(map[string]any{
		"userId":                  user.UserId,
		"currentMainQuestRouteId": user.MainQuest.CurrentMainQuestRouteId,
		"currentQuestSceneId":     user.MainQuest.CurrentQuestSceneId,
		"headQuestSceneId":        user.MainQuest.HeadQuestSceneId,
		"isReachedLastQuestScene": user.MainQuest.IsReachedLastQuestScene,
		"latestVersion":           user.MainQuest.LatestVersion,
	})
	mainQuestProgressJSON, _ := encodeJSONMaps(map[string]any{
		"userId":               user.UserId,
		"currentQuestSceneId":  user.MainQuest.ProgressQuestSceneId,
		"headQuestSceneId":     user.MainQuest.ProgressHeadQuestSceneId,
		"currentQuestFlowType": user.MainQuest.ProgressQuestFlowType,
		"latestVersion":        user.MainQuest.LatestVersion,
	})
	mainQuestSeasonRouteJSON, _ := encodeJSONMaps(map[string]any{
		"userId":            user.UserId,
		"mainQuestSeasonId": user.MainQuest.MainQuestSeasonId,
		"mainQuestRouteId":  user.MainQuest.CurrentMainQuestRouteId,
		"latestVersion":     user.MainQuest.LatestVersion,
	})
	userGuerrillaFreeOpenJSON, _ := encodeJSONMaps(map[string]any{
		"userId":           user.UserId,
		"startDatetime":    user.GuerrillaFreeOpen.StartDatetime,
		"openMinutes":      user.GuerrillaFreeOpen.OpenMinutes,
		"dailyOpenedCount": user.GuerrillaFreeOpen.DailyOpenedCount,
		"latestVersion":    user.GuerrillaFreeOpen.LatestVersion,
	})
	userPortalCageStatusJSON, _ := encodeJSONMaps(map[string]any{
		"userId":                user.UserId,
		"isCurrentProgress":     user.PortalCageStatus.IsCurrentProgress,
		"dropItemStartDatetime": user.PortalCageStatus.DropItemStartDatetime,
		"currentDropItemCount":  user.PortalCageStatus.CurrentDropItemCount,
		"latestVersion":         user.PortalCageStatus.LatestVersion,
	})

	userCharacterJSON, _ := encodeJSONMaps(sortedCharacterRecords(user)...)
	userCostumeJSON, _ := encodeJSONMaps(sortedCostumeRecords(user)...)
	userWeaponJSON, _ := encodeJSONMaps(sortedWeaponRecords(user)...)
	userWeaponStoryJSON, _ := encodeJSONMaps(sortedWeaponStoryRecords(user)...)
	userCompanionJSON, _ := encodeJSONMaps(sortedCompanionRecords(user)...)
	userThoughtJSON, _ := encodeJSONMaps(sortedThoughtRecords(user)...)
	userDeckCharacterJSON, _ := encodeJSONMaps(sortedDeckCharacterRecords(user)...)
	userDeckJSON, _ := encodeJSONMaps(sortedDeckRecords(user)...)
	userQuestJSON, _ := encodeJSONMaps(sortedQuestRecords(user)...)
	userQuestMissionJSON, _ := encodeJSONMaps(sortedQuestMissionRecords(user)...)
	userMissionJSON, _ := encodeJSONMaps(sortedMissionRecords(user)...)
	userGimmickJSON, _ := encodeJSONMaps(sortedGimmickRecords(user)...)
	userGimmickOrnamentProgressJSON, _ := encodeJSONMaps(sortedGimmickOrnamentProgressRecords(user)...)
	userGimmickSequenceJSON, _ := encodeJSONMaps(sortedGimmickSequenceRecords(user)...)
	userGimmickUnlockJSON, _ := encodeJSONMaps(sortedGimmickUnlockRecords(user)...)
	userMaterialJSON, _ := encodeJSONMaps(sortedMaterialRecords(user)...)
	userConsumableItemJSON, _ := encodeJSONMaps(sortedConsumableItemRecords(user)...)
	userPartsJSON, _ := encodeJSONMaps(sortedPartsRecords(user)...)
	userImportantItemJSON, _ := encodeJSONMaps(sortedImportantItemRecords(user)...)
	userCostumeActiveSkillJSON, _ := encodeJSONMaps(sortedCostumeActiveSkillRecords(user)...)
	userDeckTypeNoteJSON, _ := encodeJSONMaps(sortedDeckTypeNoteRecords(user)...)
	userDeckSubWeaponGroupJSON, _ := encodeJSONMaps(sortedDeckSubWeaponGroupRecords(user)...)
	userWeaponNoteJSON, _ := encodeJSONMaps(sortedWeaponNoteRecords(user)...)
	userNaviCutInJSON, _ := encodeJSONMaps(sortedNaviCutInRecords(user)...)
	userDokanJSON, _ := encodeJSONMaps(sortedDokanRecords(user)...)

	return map[string]string{
		"IUser":                        userJSON,
		"IUserSetting":                 userSettingJSON,
		"IUserStatus":                  userStatusJSON,
		"IUserGem":                     userGemJSON,
		"IUserProfile":                 userProfileJSON,
		"IUserCharacter":               userCharacterJSON,
		"IUserCostume":                 userCostumeJSON,
		"IUserWeapon":                  userWeaponJSON,
		"IUserWeaponStory":             userWeaponStoryJSON,
		"IUserCompanion":               userCompanionJSON,
		"IUserThought":                 userThoughtJSON,
		"IUserDeckCharacter":           userDeckCharacterJSON,
		"IUserDeck":                    userDeckJSON,
		"IUserLogin":                   userLoginJSON,
		"IUserLoginBonus":              userLoginBonusJSON,
		"IUserMission":                 userMissionJSON,
		"IUserMainQuestFlowStatus":     mainQuestFlowJSON,
		"IUserMainQuestMainFlowStatus": mainQuestMainFlowJSON,
		"IUserMainQuestProgressStatus": mainQuestProgressJSON,
		"IUserMainQuestSeasonRoute":    mainQuestSeasonRouteJSON,
		"IUserQuest":                   userQuestJSON,
		"IUserQuestMission":            userQuestMissionJSON,
		"IUserTutorialProgress":        userTutorialProgressJSON,
		"IUserGimmick":                 userGimmickJSON,
		"IUserGimmickOrnamentProgress": userGimmickOrnamentProgressJSON,
		"IUserGimmickSequence":         userGimmickSequenceJSON,
		"IUserGimmickUnlock":           userGimmickUnlockJSON,
		"IUserMaterial":                userMaterialJSON,
		"IUserConsumableItem":          userConsumableItemJSON,
		"IUserParts":                   userPartsJSON,
		"IUserImportantItem":           userImportantItemJSON,

		// Deck-related tables needed by DeckOrganizationCache.SetupCache.
		// Empty for now (no server-side state), but must exist so the client's
		// MemoryDatabase has non-null table references during diff application.
		"IUserDeckPartsGroup":              "[]",
		"IUserDeckSubWeaponGroup":          userDeckSubWeaponGroupJSON,
		"IUserDeckCharacterDressupCostume": "[]",
		"IUserDeckTypeNote":                userDeckTypeNoteJSON,
		"IUserDeckLimitContentRestricted":  "[]",

		// Costume sub-tables accessed by CreateDataOutgameCostume.
		"IUserCostumeActiveSkill":             userCostumeActiveSkillJSON,
		"IUserCostumeAwakenStatusUp":          "[]",
		"IUserCostumeLevelBonusReleaseStatus": "[]",
		"IUserCostumeLotteryEffect":           "[]",
		"IUserCostumeLotteryEffectAbility":    "[]",
		"IUserCostumeLotteryEffectStatusUp":   "[]",
		"IUserCostumeLotteryEffectPending":    "[]",

		// Weapon sub-tables.
		"IUserWeaponNote":    userWeaponNoteJSON,
		"IUserWeaponAbility": "[]",
		"IUserWeaponSkill":   "[]",
		"IUserWeaponAwaken":  "[]",

		// Parts/memory sub-tables.
		"IUserPartsGroupNote": "[]",
		"IUserPartsPreset":    "[]",
		"IUserPartsPresetTag": "[]",
		"IUserPartsStatusSub": "[]",

		"IUserNaviCutIn":                   userNaviCutInJSON,
		"IUserDokan":                       userDokanJSON,
		"IUserPortalCageStatus":            userPortalCageStatusJSON,
		"IUserEventQuestGuerrillaFreeOpen": userGuerrillaFreeOpenJSON,
	}
}

func FirstEntranceClientTableMap(user store.UserState) map[string]string {
	tables := FullClientTableMap(user)
	for _, table := range []string{
		"IUserCharacter",
		"IUserCostume",
		"IUserWeapon",
		"IUserCompanion",
		"IUserDeckCharacter",
		"IUserDeck",
		"IUserTutorialProgress",
		"IUserParts",
		"IUserWeaponNote",
		"IUserWeaponStory",
		"IUserCostumeActiveSkill",
		"IUserDeckTypeNote",
	} {
		tables[table] = "[]"
	}
	return tables
}

func SelectTables(all map[string]string, requested []string) map[string]string {
	selected := make(map[string]string, len(requested))
	for _, table := range requested {
		if payload, ok := all[table]; ok && payload != "" {
			selected[table] = payload
			continue
		}
		selected[table] = "[]"
	}
	return selected
}

func BuildDiffFromTables(tables map[string]string) map[string]*pb.DiffData {
	diff := make(map[string]*pb.DiffData, len(tables))
	for table, payload := range tables {
		if payload == "" {
			payload = "[]"
		}
		diff[table] = &pb.DiffData{
			UpdateRecordsJson: payload,
			DeleteKeysJson:    "[]",
		}
	}
	return diff
}

// BuildDiffFromTablesOrdered builds a diff map with tables in the given order.
// Use when client applies tables in received order and order matters (e.g. IUserWeapon before IUserWeaponStory).
// Protobuf map serialization order is implementation-defined; this at least ensures we only include
// the requested tables in the specified sequence when building the map.
func BuildDiffFromTablesOrdered(tables map[string]string, order []string) map[string]*pb.DiffData {
	diff := make(map[string]*pb.DiffData, len(order))
	for _, table := range order {
		payload, ok := tables[table]
		if !ok {
			payload = "[]"
		}
		if payload == "" {
			payload = "[]"
		}
		diff[table] = &pb.DiffData{
			UpdateRecordsJson: payload,
			DeleteKeysJson:    "[]",
		}
	}
	return diff
}

func sortedTutorialRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.Tutorials))
	for id := range user.Tutorials {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		row := user.Tutorials[int32(id)]
		records = append(records, map[string]any{
			"userId":        user.UserId,
			"tutorialType":  row.TutorialType,
			"progressPhase": row.ProgressPhase,
			"choiceId":      row.ChoiceId,
			"latestVersion": row.LatestVersion,
		})
	}
	return records
}

func sortedCharacterRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.Characters))
	for id := range user.Characters {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		row := user.Characters[int32(id)]
		records = append(records, map[string]any{
			"userId":        user.UserId,
			"characterId":   row.CharacterId,
			"level":         row.Level,
			"exp":           row.Exp,
			"latestVersion": row.LatestVersion,
		})
	}
	return records
}

func sortedCostumeRecords(user store.UserState) []map[string]any {
	keys := sortedStringKeys(user.Costumes)
	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Costumes[key]
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"userCostumeUuid":     row.UserCostumeUuid,
			"costumeId":           row.CostumeId,
			"limitBreakCount":     row.LimitBreakCount,
			"level":               row.Level,
			"exp":                 row.Exp,
			"headupDisplayViewId": row.HeadupDisplayViewId,
			"acquisitionDatetime": row.AcquisitionDatetime,
			"awakenCount":         row.AwakenCount,
			"latestVersion":       row.LatestVersion,
		})
	}
	return records
}

func sortedWeaponRecords(user store.UserState) []map[string]any {
	keys := sortedStringKeys(user.Weapons)
	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Weapons[key]
		uuid := row.UserWeaponUuid
		if uuid == "" {
			log.Printf("[state_projection] sortedWeaponRecords: using key as fallback for weapon key=%q (empty userWeaponUuid)", key)
			uuid = key // Defensive: map key IS the userWeaponUuid by design
		}
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"userWeaponUuid":      uuid,
			"weaponId":            row.WeaponId,
			"level":               row.Level,
			"exp":                 row.Exp,
			"limitBreakCount":     row.LimitBreakCount,
			"isProtected":         row.IsProtected,
			"acquisitionDatetime": row.AcquisitionDatetime,
			"latestVersion":       row.LatestVersion,
		})
	}
	return records
}

func sortedWeaponStoryRecords(user store.UserState) []map[string]any {
	if user.WeaponStories == nil {
		return []map[string]any{}
	}
	// Build set of weaponIds that exist in IUserWeapon - never send IUserWeaponStory
	// for a weapon not in IUserWeapon (client may crash on null lookup).
	// Aligned with sortedWeaponRecords: we emit all weapons (key-as-fallback when UserWeaponUuid empty).
	weaponIdsInWeapons := make(map[int32]bool)
	for _, row := range user.Weapons {
		weaponIdsInWeapons[row.WeaponId] = true
	}
	weaponIds := make([]int32, 0, len(user.WeaponStories))
	for weaponId := range user.WeaponStories {
		if weaponIdsInWeapons[weaponId] {
			weaponIds = append(weaponIds, weaponId)
		}
	}
	sort.Slice(weaponIds, func(i, j int) bool { return weaponIds[i] < weaponIds[j] })
	records := make([]map[string]any, 0, len(weaponIds))
	for _, weaponId := range weaponIds {
		row := user.WeaponStories[weaponId]
		records = append(records, map[string]any{
			"userId":                user.UserId,
			"weaponId":              row.WeaponId,
			"releasedMaxStoryIndex": row.ReleasedMaxStoryIndex,
			"latestVersion":         row.LatestVersion,
		})
	}
	return records
}

func sortedWeaponNoteRecords(user store.UserState) []map[string]any {
	weaponIds := make([]int32, 0, len(user.WeaponNotes))
	for id := range user.WeaponNotes {
		weaponIds = append(weaponIds, id)
	}
	sort.Slice(weaponIds, func(i, j int) bool { return weaponIds[i] < weaponIds[j] })
	records := make([]map[string]any, 0, len(weaponIds))
	for _, id := range weaponIds {
		row := user.WeaponNotes[id]
		records = append(records, map[string]any{
			"userId":                   user.UserId,
			"weaponId":                 row.WeaponId,
			"maxLevel":                 row.MaxLevel,
			"maxLimitBreakCount":       row.MaxLimitBreakCount,
			"firstAcquisitionDatetime": row.FirstAcquisitionDatetime,
			"latestVersion":            row.LatestVersion,
		})
	}
	return records
}

func sortedNaviCutInRecords(user store.UserState) []map[string]any {
	ids := make([]int32, 0, len(user.NaviCutInPlayed))
	for id := range user.NaviCutInPlayed {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { return ids[i] < ids[j] })
	now := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		records = append(records, map[string]any{
			"userId":        user.UserId,
			"naviCutInId":   id,
			"playDatetime":  now,
			"latestVersion": 0,
		})
	}
	return records
}

func sortedDokanRecords(user store.UserState) []map[string]any {
	ids := make([]int32, 0, len(user.DokanConfirmed))
	for id := range user.DokanConfirmed {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { return ids[i] < ids[j] })
	now := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		records = append(records, map[string]any{
			"userId":          user.UserId,
			"dokanId":         id,
			"displayDatetime": now,
			"latestVersion":   0,
		})
	}
	return records
}

func sortedCompanionRecords(user store.UserState) []map[string]any {
	keys := sortedStringKeys(user.Companions)
	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Companions[key]
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"userCompanionUuid":   row.UserCompanionUuid,
			"companionId":         row.CompanionId,
			"headupDisplayViewId": row.HeadupDisplayViewId,
			"level":               row.Level,
			"acquisitionDatetime": row.AcquisitionDatetime,
			"latestVersion":       row.LatestVersion,
		})
	}
	return records
}

func sortedThoughtRecords(user store.UserState) []map[string]any {
	keys := sortedStringKeys(user.Thoughts)
	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Thoughts[key]
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"userThoughtUuid":     row.UserThoughtUuid,
			"thoughtId":           row.ThoughtId,
			"acquisitionDatetime": row.AcquisitionDatetime,
			"latestVersion":       row.LatestVersion,
		})
	}
	return records
}

func sortedDeckCharacterRecords(user store.UserState) []map[string]any {
	keys := sortedStringKeys(user.DeckCharacters)
	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.DeckCharacters[key]
		records = append(records, map[string]any{
			"userId":                user.UserId,
			"userDeckCharacterUuid": row.UserDeckCharacterUuid,
			"userCostumeUuid":       row.UserCostumeUuid,
			"mainUserWeaponUuid":    row.MainUserWeaponUuid,
			"userCompanionUuid":     row.UserCompanionUuid,
			"power":                 row.Power,
			"userThoughtUuid":       row.UserThoughtUuid,
			"latestVersion":         row.LatestVersion,
		})
	}
	return records
}

func sortedDeckRecords(user store.UserState) []map[string]any {
	keys := make([]store.DeckKey, 0, len(user.Decks))
	for key := range user.Decks {
		keys = append(keys, key)
	}
	sort.Slice(keys, func(i, j int) bool {
		if keys[i].DeckType != keys[j].DeckType {
			return keys[i].DeckType < keys[j].DeckType
		}
		return keys[i].UserDeckNumber < keys[j].UserDeckNumber
	})

	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Decks[key]
		records = append(records, map[string]any{
			"userId":                  user.UserId,
			"deckType":                row.DeckType,
			"userDeckNumber":          row.UserDeckNumber,
			"userDeckCharacterUuid01": row.UserDeckCharacterUuid01,
			"userDeckCharacterUuid02": row.UserDeckCharacterUuid02,
			"userDeckCharacterUuid03": row.UserDeckCharacterUuid03,
			"name":                    row.Name,
			"power":                   row.Power,
			"latestVersion":           row.LatestVersion,
		})
	}
	return records
}

func sortedQuestRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.Quests))
	for id := range user.Quests {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		row := user.Quests[int32(id)]
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"questId":             row.QuestId,
			"questStateType":      row.QuestStateType,
			"isBattleOnly":        row.IsBattleOnly,
			"latestStartDatetime": row.LatestStartDatetime,
			"clearCount":          row.ClearCount,
			"dailyClearCount":     row.DailyClearCount,
			"lastClearDatetime":   row.LastClearDatetime,
			"shortestClearFrames": row.ShortestClearFrames,
			"latestVersion":       row.LatestVersion,
		})
	}
	return records
}

func sortedQuestMissionRecords(user store.UserState) []map[string]any {
	keys := make([]store.QuestMissionKey, 0, len(user.QuestMissions))
	for key := range user.QuestMissions {
		keys = append(keys, key)
	}
	sort.Slice(keys, func(i, j int) bool {
		if keys[i].QuestId != keys[j].QuestId {
			return keys[i].QuestId < keys[j].QuestId
		}
		return keys[i].QuestMissionId < keys[j].QuestMissionId
	})

	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.QuestMissions[key]
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"questId":             row.QuestId,
			"questMissionId":      row.QuestMissionId,
			"progressValue":       row.ProgressValue,
			"isClear":             row.IsClear,
			"latestClearDatetime": row.LatestClearDatetime,
			"latestVersion":       row.LatestVersion,
		})
	}
	return records
}

func sortedMissionRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.Missions))
	for id := range user.Missions {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		row := user.Missions[int32(id)]
		records = append(records, map[string]any{
			"userId":                    user.UserId,
			"missionId":                 row.MissionId,
			"startDatetime":             row.StartDatetime,
			"progressValue":             row.ProgressValue,
			"missionProgressStatusType": row.MissionProgressStatusType,
			"clearDatetime":             row.ClearDatetime,
			"latestVersion":             row.LatestVersion,
		})
	}
	return records
}

func sortedGimmickRecords(user store.UserState) []map[string]any {
	keys := make([]store.GimmickKey, 0, len(user.Gimmick.Progress))
	for key := range user.Gimmick.Progress {
		keys = append(keys, key)
	}
	sort.Slice(keys, func(i, j int) bool {
		return compareGimmickKey(keys[i], keys[j]) < 0
	})

	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Gimmick.Progress[key]
		records = append(records, map[string]any{
			"userId":                    user.UserId,
			"gimmickSequenceScheduleId": row.Key.GimmickSequenceScheduleId,
			"gimmickSequenceId":         row.Key.GimmickSequenceId,
			"gimmickId":                 row.Key.GimmickId,
			"isGimmickCleared":          row.IsGimmickCleared,
			"startDatetime":             row.StartDatetime,
			"latestVersion":             row.LatestVersion,
		})
	}
	return records
}

func sortedGimmickOrnamentProgressRecords(user store.UserState) []map[string]any {
	keys := make([]store.GimmickOrnamentKey, 0, len(user.Gimmick.OrnamentProgress))
	for key := range user.Gimmick.OrnamentProgress {
		keys = append(keys, key)
	}
	sort.Slice(keys, func(i, j int) bool {
		return compareGimmickOrnamentKey(keys[i], keys[j]) < 0
	})

	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Gimmick.OrnamentProgress[key]
		records = append(records, map[string]any{
			"userId":                    user.UserId,
			"gimmickSequenceScheduleId": row.Key.GimmickSequenceScheduleId,
			"gimmickSequenceId":         row.Key.GimmickSequenceId,
			"gimmickId":                 row.Key.GimmickId,
			"gimmickOrnamentIndex":      row.Key.GimmickOrnamentIndex,
			"progressValueBit":          row.ProgressValueBit,
			"baseDatetime":              row.BaseDatetime,
			"latestVersion":             row.LatestVersion,
		})
	}
	return records
}

func sortedGimmickSequenceRecords(user store.UserState) []map[string]any {
	keys := make([]store.GimmickSequenceKey, 0, len(user.Gimmick.Sequences))
	for key := range user.Gimmick.Sequences {
		keys = append(keys, key)
	}
	sort.Slice(keys, func(i, j int) bool {
		if keys[i].GimmickSequenceScheduleId != keys[j].GimmickSequenceScheduleId {
			return keys[i].GimmickSequenceScheduleId < keys[j].GimmickSequenceScheduleId
		}
		return keys[i].GimmickSequenceId < keys[j].GimmickSequenceId
	})

	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Gimmick.Sequences[key]
		records = append(records, map[string]any{
			"userId":                    user.UserId,
			"gimmickSequenceScheduleId": row.Key.GimmickSequenceScheduleId,
			"gimmickSequenceId":         row.Key.GimmickSequenceId,
			"isGimmickSequenceCleared":  row.IsGimmickSequenceCleared,
			"clearDatetime":             row.ClearDatetime,
			"latestVersion":             row.LatestVersion,
		})
	}
	return records
}

func sortedGimmickUnlockRecords(user store.UserState) []map[string]any {
	keys := make([]store.GimmickKey, 0, len(user.Gimmick.Unlocks))
	for key := range user.Gimmick.Unlocks {
		keys = append(keys, key)
	}
	sort.Slice(keys, func(i, j int) bool {
		return compareGimmickKey(keys[i], keys[j]) < 0
	})

	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Gimmick.Unlocks[key]
		records = append(records, map[string]any{
			"userId":                    user.UserId,
			"gimmickSequenceScheduleId": row.Key.GimmickSequenceScheduleId,
			"gimmickSequenceId":         row.Key.GimmickSequenceId,
			"gimmickId":                 row.Key.GimmickId,
			"isUnlocked":                row.IsUnlocked,
			"latestVersion":             row.LatestVersion,
		})
	}
	return records
}

func sortedMaterialRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.Materials))
	for id := range user.Materials {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	nowMillis := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		records = append(records, map[string]any{
			"userId":                   user.UserId,
			"materialId":               int32(id),
			"count":                    user.Materials[int32(id)],
			"firstAcquisitionDatetime": nowMillis,
			"latestVersion":            nowMillis,
		})
	}
	return records
}

func sortedConsumableItemRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.ConsumableItems))
	for id := range user.ConsumableItems {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	nowMillis := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		records = append(records, map[string]any{
			"userId":                   user.UserId,
			"consumableItemId":         int32(id),
			"count":                    user.ConsumableItems[int32(id)],
			"firstAcquisitionDatetime": nowMillis,
			"latestVersion":            nowMillis,
		})
	}
	return records
}

func sortedPartsRecords(user store.UserState) []map[string]any {
	keys := sortedStringKeys(user.Parts)
	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.Parts[key]
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"userPartsUuid":       row.UserPartsUuid,
			"partsId":             row.PartsId,
			"level":               row.Level,
			"acquisitionDatetime": row.AcquisitionDatetime,
			"latestVersion":       row.LatestVersion,
		})
	}
	return records
}

func sortedImportantItemRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.ImportantItems))
	for id := range user.ImportantItems {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	nowMillis := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		records = append(records, map[string]any{
			"userId":                   user.UserId,
			"importantItemId":          int32(id),
			"count":                    user.ImportantItems[int32(id)],
			"firstAcquisitionDatetime": nowMillis,
			"latestVersion":            nowMillis,
		})
	}
	return records
}

func sortedCostumeActiveSkillRecords(user store.UserState) []map[string]any {
	keys := sortedStringKeys(user.CostumeActiveSkills)
	records := make([]map[string]any, 0, len(keys))
	for _, key := range keys {
		row := user.CostumeActiveSkills[key]
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"userCostumeUuid":     row.UserCostumeUuid,
			"level":               row.Level,
			"acquisitionDatetime": row.AcquisitionDatetime,
			"latestVersion":       row.LatestVersion,
		})
	}
	return records
}

func sortedDeckTypeNoteRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.DeckTypeNotes))
	for id := range user.DeckTypeNotes {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		row := user.DeckTypeNotes[int32(id)]
		records = append(records, map[string]any{
			"userId":        user.UserId,
			"deckType":      row.DeckType,
			"maxDeckPower":  row.MaxDeckPower,
			"latestVersion": row.LatestVersion,
		})
	}
	return records
}

func DeckSubWeaponRecords(user store.UserState) []map[string]any {
	return sortedDeckSubWeaponGroupRecords(user)
}

func sortedDeckSubWeaponGroupRecords(user store.UserState) []map[string]any {
	keys := sortedStringKeys(user.DeckSubWeapons)
	records := make([]map[string]any, 0)
	for _, dcUuid := range keys {
		for sortOrder, weaponUuid := range user.DeckSubWeapons[dcUuid] {
			records = append(records, map[string]any{
				"userId":                user.UserId,
				"userDeckCharacterUuid": dcUuid,
				"userWeaponUuid":        weaponUuid,
				"sortOrder":             int32(sortOrder + 1),
				"latestVersion":         user.DeckCharacters[dcUuid].LatestVersion,
			})
		}
	}
	return records
}

func sortedStringKeys[T any](rows map[string]T) []string {
	keys := make([]string, 0, len(rows))
	for key := range rows {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

func compareGimmickKey(a, b store.GimmickKey) int {
	if a.GimmickSequenceScheduleId != b.GimmickSequenceScheduleId {
		if a.GimmickSequenceScheduleId < b.GimmickSequenceScheduleId {
			return -1
		}
		return 1
	}
	if a.GimmickSequenceId != b.GimmickSequenceId {
		if a.GimmickSequenceId < b.GimmickSequenceId {
			return -1
		}
		return 1
	}
	if a.GimmickId < b.GimmickId {
		return -1
	}
	if a.GimmickId > b.GimmickId {
		return 1
	}
	return 0
}

func compareGimmickOrnamentKey(a, b store.GimmickOrnamentKey) int {
	if cmp := compareGimmickKey(
		store.GimmickKey{
			GimmickSequenceScheduleId: a.GimmickSequenceScheduleId,
			GimmickSequenceId:         a.GimmickSequenceId,
			GimmickId:                 a.GimmickId,
		},
		store.GimmickKey{
			GimmickSequenceScheduleId: b.GimmickSequenceScheduleId,
			GimmickSequenceId:         b.GimmickSequenceId,
			GimmickId:                 b.GimmickId,
		},
	); cmp != 0 {
		return cmp
	}
	if a.GimmickOrnamentIndex < b.GimmickOrnamentIndex {
		return -1
	}
	if a.GimmickOrnamentIndex > b.GimmickOrnamentIndex {
		return 1
	}
	return 0
}
