package service

import (
	"context"
	"fmt"
	"log"
	"time"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

type TutorialServiceServer struct {
	pb.UnimplementedTutorialServiceServer
	store *store.Store
}

func NewTutorialServiceServer(userStore *store.Store) *TutorialServiceServer {
	return &TutorialServiceServer{store: userStore}
}

func (s *TutorialServiceServer) SetTutorialProgress(ctx context.Context, req *pb.SetTutorialProgressRequest) (*pb.SetTutorialProgressResponse, error) {
	log.Printf("[TutorialService] SetTutorialProgress: type=%d phase=%d choice=%d", req.TutorialType, req.ProgressPhase, req.ChoiceId)
	userId := currentUserId(ctx, s.store)
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		user.Tutorial.TutorialType = req.TutorialType
		user.Tutorial.ProgressPhase = req.ProgressPhase
		user.Tutorial.ChoiceId = req.ChoiceId
		if req.TutorialType == int32(model.TutorialTypeMenuFirst) ||
			req.TutorialType == int32(model.TutorialTypeMenuSecond) {
			store.EnsureDefaultDeck(user, time.Now().UnixMilli())
		}
	})
	tables := []string{"IUserTutorialProgress"}
	if req.TutorialType == int32(model.TutorialTypeMenuFirst) ||
		req.TutorialType == int32(model.TutorialTypeMenuSecond) {
		tables = append(tables,
			"IUserCharacter", "IUserCostume", "IUserWeapon",
			"IUserCompanion", "IUserDeckCharacter", "IUserDeck",
		)
	}
	result := userdata.SelectTables(userdata.FullClientTableMap(user), tables)
	for _, t := range tables {
		log.Printf("[TutorialService] DiffTable %s -> %s", t, result[t])
	}
	return &pb.SetTutorialProgressResponse{
		TutorialChoiceReward: []*pb.TutorialChoiceReward{},
		DiffUserData:         userdata.BuildDiffFromTables(result),
	}, nil
}

func (s *TutorialServiceServer) SetTutorialProgressAndReplaceDeck(ctx context.Context, req *pb.SetTutorialProgressAndReplaceDeckRequest) (*pb.SetTutorialProgressAndReplaceDeckResponse, error) {
	log.Printf("[TutorialService] SetTutorialProgressAndReplaceDeck: type=%d phase=%d deckType=%d deckNumber=%d", req.TutorialType, req.ProgressPhase, req.DeckType, req.UserDeckNumber)
	userId := currentUserId(ctx, s.store)
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		user.Tutorial.TutorialType = req.TutorialType
		user.Tutorial.ProgressPhase = req.ProgressPhase

		nowMillis := time.Now().UnixMilli()
		deckKey := store.DeckKey{DeckType: req.DeckType, UserDeckNumber: req.UserDeckNumber}
		deck := user.Decks[deckKey]
		deck.DeckType = req.DeckType
		deck.UserDeckNumber = req.UserDeckNumber
		if deck.Name == "" {
			deck.Name = "Deck 1"
		}
		if deck.Power == 0 {
			deck.Power = 100
		}

		if req.Deck != nil {
			slots := []*pb.DeckCharacter{req.Deck.Character01, req.Deck.Character02, req.Deck.Character03}
			uuids := []*string{&deck.UserDeckCharacterUuid01, &deck.UserDeckCharacterUuid02, &deck.UserDeckCharacterUuid03}
			for i, slot := range slots {
				if slot == nil || slot.UserCostumeUuid == "" {
					*uuids[i] = ""
					continue
				}
				dcUuid := fmt.Sprintf("deck-%d-%d-%d", req.DeckType, req.UserDeckNumber, i+1)
				dc := user.DeckCharacters[dcUuid]
				dc.UserDeckCharacterUuid = dcUuid
				dc.UserCostumeUuid = slot.UserCostumeUuid
				dc.MainUserWeaponUuid = slot.MainUserWeaponUuid
				dc.UserCompanionUuid = slot.UserCompanionUuid
				dc.UserThoughtUuid = slot.UserThoughtUuid
				dc.LatestVersion = nowMillis
				user.DeckCharacters[dcUuid] = dc
				*uuids[i] = dcUuid
			}
		} else if deck.UserDeckCharacterUuid01 == "" {
			for dcId := range user.DeckCharacters {
				deck.UserDeckCharacterUuid01 = dcId
				break
			}
		}

		deck.LatestVersion = nowMillis
		user.Decks[deckKey] = deck
	})
	return &pb.SetTutorialProgressAndReplaceDeckResponse{
		DiffUserData: userdata.BuildDiffFromTables(userdata.SelectTables(userdata.FullClientTableMap(user), []string{
			"IUserTutorialProgress",
			"IUserDeck",
			"IUserDeckCharacter",
		})),
	}, nil
}
