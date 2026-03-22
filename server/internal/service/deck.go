package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

type DeckServiceServer struct {
	pb.UnimplementedDeckServiceServer
	store *store.Store
}

func NewDeckServiceServer(userStore *store.Store) *DeckServiceServer {
	return &DeckServiceServer{store: userStore}
}

func (s *DeckServiceServer) UpdateName(ctx context.Context, req *pb.UpdateNameRequest) (*pb.UpdateNameResponse, error) {
	log.Printf("[DeckService] UpdateName: deckType=%d deckNumber=%d name=%q", req.DeckType, req.UserDeckNumber, req.Name)
	userId := currentUserId(ctx, s.store)

	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		deckKey := store.DeckKey{DeckType: req.DeckType, UserDeckNumber: req.UserDeckNumber}
		deck := user.Decks[deckKey]
		deck.Name = req.Name
		user.Decks[deckKey] = deck
	})

	result := userdata.SelectTables(userdata.FullClientTableMap(user), []string{"IUserDeck"})
	return &pb.UpdateNameResponse{
		DiffUserData: userdata.BuildDiffFromTables(result),
	}, nil
}

func (s *DeckServiceServer) RefreshDeckPower(ctx context.Context, req *pb.RefreshDeckPowerRequest) (*pb.RefreshDeckPowerResponse, error) {
	log.Printf("[DeckService] RefreshDeckPower: deckType=%d deckNumber=%d", req.DeckType, req.UserDeckNumber)
	userId := currentUserId(ctx, s.store)

	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		if req.DeckPower == nil {
			log.Printf("[DeckService] RefreshDeckPower: deckPower is nil")
			return
		}

		deckKey := store.DeckKey{DeckType: req.DeckType, UserDeckNumber: req.UserDeckNumber}
		deck, ok := user.Decks[deckKey]
		if !ok {
			log.Fatalf("[DeckService] RefreshDeckPower: deck not found")
		}

		deck.Power = req.DeckPower.Power
		user.Decks[deckKey] = deck

		for _, cp := range []*pb.DeckCharacterPower{
			req.DeckPower.DeckCharacterPower01,
			req.DeckPower.DeckCharacterPower02,
			req.DeckPower.DeckCharacterPower03,
		} {
			if cp == nil || cp.UserDeckCharacterUuid == "" {
				continue
			}

			if dc, ok := user.DeckCharacters[cp.UserDeckCharacterUuid]; ok {
				dc.Power = cp.Power
				user.DeckCharacters[cp.UserDeckCharacterUuid] = dc
			}
		}

		note := user.DeckTypeNotes[req.DeckType]
		if req.DeckPower.Power > note.MaxDeckPower {
			note.DeckType = req.DeckType
			note.MaxDeckPower = req.DeckPower.Power
			user.DeckTypeNotes[req.DeckType] = note
		}
	})

	result := userdata.SelectTables(userdata.FullClientTableMap(user), []string{
		"IUserDeck", "IUserDeckCharacter", "IUserDeckTypeNote",
	})
	return &pb.RefreshDeckPowerResponse{
		DiffUserData: userdata.BuildDiffFromTables(result),
	}, nil
}

func deckSlotsFromProto(deck *pb.Deck) []store.DeckCharacterInput {
	slots := make([]store.DeckCharacterInput, 3)
	for i, ch := range []*pb.DeckCharacter{deck.Character01, deck.Character02, deck.Character03} {
		if ch == nil {
			continue
		}
		slots[i] = store.DeckCharacterInput{
			UserCostumeUuid:    ch.UserCostumeUuid,
			MainUserWeaponUuid: ch.MainUserWeaponUuid,
			SubWeaponUuids:     ch.SubUserWeaponUuid,
			UserCompanionUuid:  ch.UserCompanionUuid,
			UserThoughtUuid:    ch.UserThoughtUuid,
		}
	}
	return slots
}

func (s *DeckServiceServer) ReplaceDeck(ctx context.Context, req *pb.ReplaceDeckRequest) (*pb.ReplaceDeckResponse, error) {
	log.Printf("[DeckService] ReplaceDeck: deckType=%d deckNumber=%d", req.DeckType, req.UserDeckNumber)
	if req.Deck != nil {
		for i, ch := range []*pb.DeckCharacter{req.Deck.Character01, req.Deck.Character02, req.Deck.Character03} {
			if ch == nil {
				continue
			}
			log.Printf("[DeckService] ReplaceDeck slot %d: costume=%s mainWeapon=%s subWeapons=%v companion=%s thought=%s",
				i+1, ch.UserCostumeUuid, ch.MainUserWeaponUuid, ch.SubUserWeaponUuid, ch.UserCompanionUuid, ch.UserThoughtUuid)
		}
	}
	userId := currentUserId(ctx, s.store)

	oldUser, _ := s.store.SnapshotUser(userId)
	oldSubWeapons := userdata.DeckSubWeaponRecords(oldUser)

	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		if req.Deck == nil {
			return
		}
		store.ApplyDeckReplacement(user, req.DeckType, req.UserDeckNumber, deckSlotsFromProto(req.Deck), gametime.NowMillis())
	})

	newSubWeapons := userdata.DeckSubWeaponRecords(user)
	subWeaponDeleteKeys := userdata.ComputeDeleteKeys(oldSubWeapons, newSubWeapons,
		[]string{"userId", "userDeckCharacterUuid", "sortOrder"})

	result := userdata.SelectTables(userdata.FullClientTableMap(user), []string{
		"IUserDeck", "IUserDeckCharacter", "IUserDeckSubWeaponGroup",
	})
	log.Printf("[DeckService] ReplaceDeck response IUserDeckSubWeaponGroup: %s deleteKeys: %s",
		result["IUserDeckSubWeaponGroup"], subWeaponDeleteKeys)
	return &pb.ReplaceDeckResponse{
		DiffUserData: userdata.NewDiffSet(result).
			WithDeletes("IUserDeckSubWeaponGroup", subWeaponDeleteKeys).
			Build(),
	}, nil
}
