package userdata

import (
	"log"
	"sort"

	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/store"
)

func init() {
	register("IUserCharacter", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedCharacterRecords(user)...)
		return s
	})
	register("IUserCostume", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedCostumeRecords(user)...)
		return s
	})
	register("IUserWeapon", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedWeaponRecords(user)...)
		return s
	})
	register("IUserWeaponStory", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedWeaponStoryRecords(user)...)
		return s
	})
	register("IUserWeaponNote", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedWeaponNoteRecords(user)...)
		return s
	})
	register("IUserCompanion", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedCompanionRecords(user)...)
		return s
	})
	register("IUserThought", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedThoughtRecords(user)...)
		return s
	})
	register("IUserConsumableItem", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedConsumableItemRecords(user)...)
		return s
	})
	register("IUserMaterial", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedMaterialRecords(user)...)
		return s
	})
	register("IUserImportantItem", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedImportantItemRecords(user)...)
		return s
	})
	register("IUserPremiumItem", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedPremiumItemRecords(user)...)
		return s
	})
	register("IUserParts", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedPartsRecords(user)...)
		return s
	})
	register("IUserCostumeActiveSkill", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedCostumeActiveSkillRecords(user)...)
		return s
	})
	registerStatic(
		"IUserCostumeAwakenStatusUp",
		"IUserCostumeLevelBonusReleaseStatus",
		"IUserCostumeLotteryEffect",
		"IUserCostumeLotteryEffectAbility",
		"IUserCostumeLotteryEffectStatusUp",
		"IUserCostumeLotteryEffectPending",
		"IUserWeaponAbility",
		"IUserWeaponSkill",
		"IUserWeaponAwaken",
		"IUserPartsGroupNote",
		"IUserPartsPreset",
		"IUserPartsPresetTag",
		"IUserPartsStatusSub",
	)
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
			log.Printf("[userdata] sortedWeaponRecords: using key as fallback for weapon key=%q (empty userWeaponUuid)", key)
			uuid = key
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

func sortedPremiumItemRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.PremiumItems))
	for id := range user.PremiumItems {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)

	nowMillis := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		acqTime := user.PremiumItems[int32(id)]
		if acqTime == 0 {
			acqTime = nowMillis
		}
		records = append(records, map[string]any{
			"userId":              user.UserId,
			"premiumItemId":       int32(id),
			"acquisitionDatetime": acqTime,
			"latestVersion":       nowMillis,
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
