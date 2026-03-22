package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gametime"
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
		user.Tutorials[req.TutorialType] = store.TutorialProgressState{
			TutorialType:  req.TutorialType,
			ProgressPhase: req.ProgressPhase,
			ChoiceId:      req.ChoiceId,
		}
		if req.TutorialType == int32(model.TutorialTypeMenuFirst) ||
			req.TutorialType == int32(model.TutorialTypeMenuSecond) {
			store.EnsureDefaultDeck(user, gametime.NowMillis())
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
		user.Tutorials[req.TutorialType] = store.TutorialProgressState{
			TutorialType:  req.TutorialType,
			ProgressPhase: req.ProgressPhase,
		}
		if req.Deck != nil {
			store.ApplyDeckReplacement(user, req.DeckType, req.UserDeckNumber, deckSlotsFromProto(req.Deck), gametime.NowMillis())
		}
	})
	return &pb.SetTutorialProgressAndReplaceDeckResponse{
		DiffUserData: userdata.BuildDiffFromTables(userdata.SelectTables(userdata.FullClientTableMap(user), []string{
			"IUserTutorialProgress",
			"IUserDeck",
			"IUserDeckCharacter",
			"IUserDeckSubWeaponGroup",
		})),
	}, nil
}
