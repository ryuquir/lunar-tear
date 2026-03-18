package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
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
