package memory

import (
	"maps"

	"lunar-tear/server/internal/store"
)

func cloneUserState(u store.UserState) store.UserState {
	out := u
	out.Tutorials = maps.Clone(u.Tutorials)
	out.Characters = maps.Clone(u.Characters)
	out.Costumes = maps.Clone(u.Costumes)
	out.Weapons = maps.Clone(u.Weapons)
	out.Companions = maps.Clone(u.Companions)
	out.Thoughts = maps.Clone(u.Thoughts)
	out.DeckCharacters = maps.Clone(u.DeckCharacters)
	out.DeckSubWeapons = maps.Clone(u.DeckSubWeapons)
	out.DeckParts = cloneSliceMap(u.DeckParts)
	out.Decks = maps.Clone(u.Decks)
	out.Quests = maps.Clone(u.Quests)
	out.QuestMissions = maps.Clone(u.QuestMissions)
	out.WeaponStories = maps.Clone(u.WeaponStories)
	out.Missions = maps.Clone(u.Missions)
	out.Gimmick = store.GimmickState{
		Progress:         maps.Clone(u.Gimmick.Progress),
		OrnamentProgress: maps.Clone(u.Gimmick.OrnamentProgress),
		Sequences:        maps.Clone(u.Gimmick.Sequences),
		Unlocks:          maps.Clone(u.Gimmick.Unlocks),
	}
	out.CageOrnamentRewards = maps.Clone(u.CageOrnamentRewards)
	out.ConsumableItems = maps.Clone(u.ConsumableItems)
	out.Materials = maps.Clone(u.Materials)
	out.Parts = maps.Clone(u.Parts)
	out.PartsGroupNotes = maps.Clone(u.PartsGroupNotes)
	out.PartsPresets = maps.Clone(u.PartsPresets)
	out.ImportantItems = maps.Clone(u.ImportantItems)
	out.CostumeActiveSkills = maps.Clone(u.CostumeActiveSkills)
	out.WeaponSkills = cloneSliceMap(u.WeaponSkills)
	out.WeaponAbilities = cloneSliceMap(u.WeaponAbilities)
	out.DeckTypeNotes = maps.Clone(u.DeckTypeNotes)
	out.WeaponNotes = maps.Clone(u.WeaponNotes)
	out.NaviCutInPlayed = maps.Clone(u.NaviCutInPlayed)
	out.ViewedMovies = maps.Clone(u.ViewedMovies)
	out.ContentsStories = maps.Clone(u.ContentsStories)
	out.DrawnOmikuji = maps.Clone(u.DrawnOmikuji)
	out.PremiumItems = maps.Clone(u.PremiumItems)
	out.DokanConfirmed = maps.Clone(u.DokanConfirmed)
	out.ShopItems = maps.Clone(u.ShopItems)
	out.ShopReplaceableLineup = maps.Clone(u.ShopReplaceableLineup)
	out.Explore = u.Explore
	out.ExploreScores = maps.Clone(u.ExploreScores)
	out.Gacha = store.GachaState{
		RewardAvailable:        u.Gacha.RewardAvailable,
		TodaysCurrentDrawCount: u.Gacha.TodaysCurrentDrawCount,
		DailyMaxCount:          u.Gacha.DailyMaxCount,
		LastRewardDrawDate:     u.Gacha.LastRewardDrawDate,
		ConvertedGachaMedal: store.ConvertedGachaMedalState{
			ConvertedMedalPossession: append([]store.ConsumableItemState(nil), u.Gacha.ConvertedGachaMedal.ConvertedMedalPossession...),
			ObtainPossession:         cloneConsumableItemPtr(u.Gacha.ConvertedGachaMedal.ObtainPossession),
		},
		BannerStates: cloneBannerStates(u.Gacha.BannerStates),
	}
	out.Gifts = store.GiftState{
		NotReceived: cloneNotReceivedGifts(u.Gifts.NotReceived),
		Received:    cloneReceivedGifts(u.Gifts.Received),
	}
	out.Battle = u.Battle
	out.CostumeAwakenStatusUps = maps.Clone(u.CostumeAwakenStatusUps)
	out.AutoSaleSettings = maps.Clone(u.AutoSaleSettings)
	out.CharacterRebirths = maps.Clone(u.CharacterRebirths)
	return out
}

func cloneGachaCatalogEntry(entry store.GachaCatalogEntry) store.GachaCatalogEntry {
	out := entry
	out.PricePhases = append([]store.GachaPricePhaseEntry(nil), entry.PricePhases...)
	out.PromotionItems = append([]store.GachaPromotionItem(nil), entry.PromotionItems...)
	return out
}

func cloneBannerStates(m map[int32]store.GachaBannerState) map[int32]store.GachaBannerState {
	if m == nil {
		return nil
	}
	out := make(map[int32]store.GachaBannerState, len(m))
	for k, v := range m {
		bs := v
		bs.BoxDrewCounts = maps.Clone(v.BoxDrewCounts)
		out[k] = bs
	}
	return out
}

func cloneConsumableItemPtr(item *store.ConsumableItemState) *store.ConsumableItemState {
	if item == nil {
		return nil
	}
	out := *item
	return &out
}

func cloneNotReceivedGifts(gifts []store.NotReceivedGiftState) []store.NotReceivedGiftState {
	out := make([]store.NotReceivedGiftState, len(gifts))
	for i, gift := range gifts {
		out[i] = store.NotReceivedGiftState{
			GiftCommon: store.GiftCommonState{
				PossessionType:        gift.GiftCommon.PossessionType,
				PossessionId:          gift.GiftCommon.PossessionId,
				Count:                 gift.GiftCommon.Count,
				GrantDatetime:         gift.GiftCommon.GrantDatetime,
				DescriptionGiftTextId: gift.GiftCommon.DescriptionGiftTextId,
				EquipmentData:         append([]byte(nil), gift.GiftCommon.EquipmentData...),
			},
			ExpirationDatetime: gift.ExpirationDatetime,
			UserGiftUuid:       gift.UserGiftUuid,
		}
	}
	return out
}

func cloneSliceMap[T any](m map[string][]T) map[string][]T {
	if m == nil {
		return nil
	}
	out := make(map[string][]T, len(m))
	for k, v := range m {
		out[k] = append([]T(nil), v...)
	}
	return out
}

func cloneReceivedGifts(gifts []store.ReceivedGiftState) []store.ReceivedGiftState {
	out := make([]store.ReceivedGiftState, len(gifts))
	for i, gift := range gifts {
		out[i] = store.ReceivedGiftState{
			GiftCommon: store.GiftCommonState{
				PossessionType:        gift.GiftCommon.PossessionType,
				PossessionId:          gift.GiftCommon.PossessionId,
				Count:                 gift.GiftCommon.Count,
				GrantDatetime:         gift.GiftCommon.GrantDatetime,
				DescriptionGiftTextId: gift.GiftCommon.DescriptionGiftTextId,
				EquipmentData:         append([]byte(nil), gift.GiftCommon.EquipmentData...),
			},
			ReceivedDatetime: gift.ReceivedDatetime,
		}
	}
	return out
}
