package userdata

import (
	"sort"

	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/store"
)

func init() {
	register("IUser", func(user store.UserState) string {
		s, _ := encodeJSONMaps(map[string]any{
			"userId":              user.UserId,
			"playerId":            user.PlayerId,
			"osType":              user.OsType,
			"platformType":        user.PlatformType,
			"userRestrictionType": user.UserRestrictionType,
			"registerDatetime":    user.RegisterDatetime,
			"gameStartDatetime":   user.GameStartDatetime,
			"latestVersion":       user.LatestVersion,
		})
		return s
	})
	register("IUserSetting", func(user store.UserState) string {
		s, _ := encodeJSONRecords(&EntityIUserSetting{
			UserId:                user.UserId,
			IsNotifyPurchaseAlert: user.Setting.IsNotifyPurchaseAlert,
			LatestVersion:         user.Setting.LatestVersion,
		})
		return s
	})
	register("IUserStatus", func(user store.UserState) string {
		s, _ := encodeJSONMaps(map[string]any{
			"userId":                user.UserId,
			"level":                 user.Status.Level,
			"exp":                   user.Status.Exp,
			"staminaMilliValue":     user.Status.StaminaMilliValue,
			"staminaUpdateDatetime": user.Status.StaminaUpdateDatetime,
			"latestVersion":         user.Status.LatestVersion,
		})
		return s
	})
	register("IUserGem", func(user store.UserState) string {
		s, _ := encodeJSONRecords(&EntityIUserGem{
			UserId:  user.UserId,
			PaidGem: user.Gem.PaidGem,
			FreeGem: user.Gem.FreeGem,
		})
		return s
	})
	register("IUserProfile", func(user store.UserState) string {
		s, _ := encodeJSONMaps(map[string]any{
			"userId":                          user.UserId,
			"name":                            user.Profile.Name,
			"nameUpdateDatetime":              user.Profile.NameUpdateDatetime,
			"message":                         user.Profile.Message,
			"messageUpdateDatetime":           user.Profile.MessageUpdateDatetime,
			"favoriteCostumeId":               user.Profile.FavoriteCostumeId,
			"favoriteCostumeIdUpdateDatetime": user.Profile.FavoriteCostumeIdUpdateDatetime,
			"latestVersion":                   user.Profile.LatestVersion,
		})
		return s
	})
	register("IUserLogin", func(user store.UserState) string {
		s, _ := encodeJSONRecords(&EntityIUserLogin{
			UserId:                    user.UserId,
			TotalLoginCount:           user.Login.TotalLoginCount,
			ContinualLoginCount:       user.Login.ContinualLoginCount,
			MaxContinualLoginCount:    user.Login.MaxContinualLoginCount,
			LastLoginDatetime:         user.Login.LastLoginDatetime,
			LastComebackLoginDatetime: user.Login.LastComebackLoginDatetime,
			LatestVersion:             user.Login.LatestVersion,
		})
		return s
	})
	register("IUserLoginBonus", func(user store.UserState) string {
		s, _ := encodeJSONRecords(&EntityIUserLoginBonus{
			UserId:                      user.UserId,
			LoginBonusId:                user.LoginBonus.LoginBonusId,
			CurrentPageNumber:           user.LoginBonus.CurrentPageNumber,
			CurrentStampNumber:          user.LoginBonus.CurrentStampNumber,
			LatestRewardReceiveDatetime: user.LoginBonus.LatestRewardReceiveDatetime,
			LatestVersion:               user.LoginBonus.LatestVersion,
		})
		return s
	})
	register("IUserTutorialProgress", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedTutorialRecords(user)...)
		return s
	})
	register("IUserMission", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedMissionRecords(user)...)
		return s
	})
	register("IUserNaviCutIn", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedNaviCutInRecords(user)...)
		return s
	})
	register("IUserMovie", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedMovieRecords(user)...)
		return s
	})
	register("IUserContentsStory", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedContentsStoryRecords(user)...)
		return s
	})
	register("IUserOmikuji", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedOmikujiRecords(user)...)
		return s
	})
	register("IUserDokan", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedDokanRecords(user)...)
		return s
	})
	register("IUserPortalCageStatus", func(user store.UserState) string {
		s, _ := encodeJSONMaps(map[string]any{
			"userId":                user.UserId,
			"isCurrentProgress":     user.PortalCageStatus.IsCurrentProgress,
			"dropItemStartDatetime": user.PortalCageStatus.DropItemStartDatetime,
			"currentDropItemCount":  user.PortalCageStatus.CurrentDropItemCount,
			"latestVersion":         user.PortalCageStatus.LatestVersion,
		})
		return s
	})
	register("IUserEventQuestGuerrillaFreeOpen", func(user store.UserState) string {
		s, _ := encodeJSONMaps(map[string]any{
			"userId":           user.UserId,
			"startDatetime":    user.GuerrillaFreeOpen.StartDatetime,
			"openMinutes":      user.GuerrillaFreeOpen.OpenMinutes,
			"dailyOpenedCount": user.GuerrillaFreeOpen.DailyOpenedCount,
			"latestVersion":    user.GuerrillaFreeOpen.LatestVersion,
		})
		return s
	})

	register("IUserShopItem", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedShopItemRecords(user)...)
		return s
	})
	register("IUserShopReplaceable", func(user store.UserState) string {
		s, _ := encodeJSONMaps(map[string]any{
			"userId":                     user.UserId,
			"lineupUpdateCount":          user.ShopReplaceable.LineupUpdateCount,
			"latestLineupUpdateDatetime": user.ShopReplaceable.LatestLineupUpdateDatetime,
			"latestVersion":              user.ShopReplaceable.LatestVersion,
		})
		return s
	})
	register("IUserShopReplaceableLineup", func(user store.UserState) string {
		s, _ := encodeJSONMaps(sortedShopReplaceableLineupRecords(user)...)
		return s
	})

	registerStatic()
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
			"latestVersion": now,
		})
	}
	return records
}

func sortedContentsStoryRecords(user store.UserState) []map[string]any {
	ids := make([]int32, 0, len(user.ContentsStories))
	for id := range user.ContentsStories {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { return ids[i] < ids[j] })
	now := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		records = append(records, map[string]any{
			"userId":          user.UserId,
			"contentsStoryId": id,
			"playDatetime":    user.ContentsStories[id],
			"latestVersion":   now,
		})
	}
	return records
}

func sortedMovieRecords(user store.UserState) []map[string]any {
	ids := make([]int32, 0, len(user.ViewedMovies))
	for id := range user.ViewedMovies {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { return ids[i] < ids[j] })
	now := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		records = append(records, map[string]any{
			"userId":               user.UserId,
			"movieId":              id,
			"latestViewedDatetime": user.ViewedMovies[id],
			"latestVersion":        now,
		})
	}
	return records
}

func sortedOmikujiRecords(user store.UserState) []map[string]any {
	ids := make([]int32, 0, len(user.DrawnOmikuji))
	for id := range user.DrawnOmikuji {
		ids = append(ids, id)
	}
	sort.Slice(ids, func(i, j int) bool { return ids[i] < ids[j] })
	now := gametime.NowMillis()
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		records = append(records, map[string]any{
			"userId":             user.UserId,
			"omikujiId":          id,
			"latestDrawDatetime": user.DrawnOmikuji[id],
			"latestVersion":      now,
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
			"latestVersion":   now,
		})
	}
	return records
}

func sortedShopItemRecords(user store.UserState) []map[string]any {
	ids := make([]int, 0, len(user.ShopItems))
	for id := range user.ShopItems {
		ids = append(ids, int(id))
	}
	sort.Ints(ids)
	records := make([]map[string]any, 0, len(ids))
	for _, id := range ids {
		row := user.ShopItems[int32(id)]
		records = append(records, map[string]any{
			"userId":                           user.UserId,
			"shopItemId":                       row.ShopItemId,
			"boughtCount":                      row.BoughtCount,
			"latestBoughtCountChangedDatetime": row.LatestBoughtCountChangedDatetime,
			"latestVersion":                    row.LatestVersion,
		})
	}
	return records
}

func sortedShopReplaceableLineupRecords(user store.UserState) []map[string]any {
	slots := make([]int, 0, len(user.ShopReplaceableLineup))
	for slot := range user.ShopReplaceableLineup {
		slots = append(slots, int(slot))
	}
	sort.Ints(slots)
	records := make([]map[string]any, 0, len(slots))
	for _, slot := range slots {
		row := user.ShopReplaceableLineup[int32(slot)]
		records = append(records, map[string]any{
			"userId":        user.UserId,
			"slotNumber":    row.SlotNumber,
			"shopItemId":    row.ShopItemId,
			"latestVersion": row.LatestVersion,
		})
	}
	return records
}
