package store

import (
	"fmt"
	"log"
	"sort"

	"lunar-tear/server/internal/model"
)

func DeductPrice(user *UserState, priceType, priceId, amount int32) error {
	switch priceType {
	case model.PriceTypeConsumableItem:
		cur := user.ConsumableItems[priceId]
		if cur < amount {
			return fmt.Errorf("insufficient consumable %d: have %d, need %d", priceId, cur, amount)
		}
		user.ConsumableItems[priceId] = cur - amount
	case model.PriceTypeGem:
		total := user.Gem.FreeGem + user.Gem.PaidGem
		if total < amount {
			return fmt.Errorf("insufficient gems: have %d, need %d", total, amount)
		}
		if user.Gem.FreeGem >= amount {
			user.Gem.FreeGem -= amount
		} else {
			amount -= user.Gem.FreeGem
			user.Gem.FreeGem = 0
			user.Gem.PaidGem -= amount
		}
	case model.PriceTypePaidGem:
		if user.Gem.PaidGem < amount {
			return fmt.Errorf("insufficient paid gems: have %d, need %d", user.Gem.PaidGem, amount)
		}
		user.Gem.PaidGem -= amount
	case model.PriceTypePlatformPayment:
		// real-money purchase -- treat as free on private server
	default:
		log.Printf("[DeductPrice] unhandled priceType=%d priceId=%d amount=%d", priceType, priceId, amount)
	}
	return nil
}

func GrantPossession(user *UserState, possessionType model.PossessionType, possessionId, count int32) {
	switch possessionType {
	case model.PossessionTypeMaterial:
		user.Materials[possessionId] += count
	case model.PossessionTypeConsumableItem:
		user.ConsumableItems[possessionId] += count
	case model.PossessionTypePaidGem:
		user.Gem.PaidGem += count
	case model.PossessionTypeFreeGem:
		user.Gem.FreeGem += count
	case model.PossessionTypeImportantItem:
		user.ImportantItems[possessionId] += count
	default:
		log.Printf("[GrantPossession] unhandled type=%d id=%d count=%d", possessionType, possessionId, count)
	}
}

func EnsureDefaultDeck(user *UserState, nowMillis int64) {
	if len(user.Costumes) == 0 || len(user.Decks) > 0 {
		return
	}

	costumeUuid := FirstSortedKey(user.Costumes)
	weaponUuid := FirstSortedKey(user.Weapons)
	companionUuid := FirstSortedKey(user.Companions)

	dcUuid := "default-deck-character-0001"
	user.DeckCharacters[dcUuid] = DeckCharacterState{
		UserDeckCharacterUuid: dcUuid,
		UserCostumeUuid:       costumeUuid,
		MainUserWeaponUuid:    weaponUuid,
		UserCompanionUuid:     companionUuid,
		Power:                 100,
		LatestVersion:         nowMillis,
	}
	user.Decks[DeckKey{DeckType: model.DeckTypeQuest, UserDeckNumber: 1}] = DeckState{
		DeckType:                model.DeckTypeQuest,
		UserDeckNumber:          1,
		UserDeckCharacterUuid01: dcUuid,
		Name:                    "Deck 1",
		Power:                   100,
		LatestVersion:           nowMillis,
	}

	if _, exists := user.DeckTypeNotes[model.DeckTypeQuest]; !exists {
		user.DeckTypeNotes[model.DeckTypeQuest] = DeckTypeNoteState{
			DeckType:      model.DeckTypeQuest,
			MaxDeckPower:  100,
			LatestVersion: nowMillis,
		}
	}
}

func FirstSortedKey[V any](m map[string]V) string {
	if len(m) == 0 {
		return ""
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys[0]
}

func ApplyDeckReplacement(user *UserState, deckType model.DeckType, userDeckNumber int32, slots []DeckCharacterInput, nowMillis int64) {
	deckKey := DeckKey{DeckType: deckType, UserDeckNumber: userDeckNumber}
	deck := user.Decks[deckKey]
	deck.DeckType = deckType
	deck.UserDeckNumber = userDeckNumber
	if deck.Name == "" {
		deck.Name = fmt.Sprintf("Deck %d", userDeckNumber)
	}
	if deck.Power == 0 {
		deck.Power = 100
	}

	uuids := []*string{&deck.UserDeckCharacterUuid01, &deck.UserDeckCharacterUuid02, &deck.UserDeckCharacterUuid03}
	for i, uuid := range uuids {
		if i >= len(slots) || slots[i].UserCostumeUuid == "" {
			*uuid = ""
			continue
		}
		slot := slots[i]
		dcUuid := fmt.Sprintf("deck-%d-%d-%d", deckType, userDeckNumber, i+1)
		dc := user.DeckCharacters[dcUuid]
		dc.UserDeckCharacterUuid = dcUuid
		dc.UserCostumeUuid = slot.UserCostumeUuid
		dc.MainUserWeaponUuid = slot.MainUserWeaponUuid
		dc.UserCompanionUuid = slot.UserCompanionUuid
		dc.UserThoughtUuid = slot.UserThoughtUuid
		dc.LatestVersion = nowMillis
		user.DeckCharacters[dcUuid] = dc
		user.DeckSubWeapons[dcUuid] = slot.SubWeaponUuids
		*uuid = dcUuid
	}

	deck.LatestVersion = nowMillis
	user.Decks[deckKey] = deck
}
