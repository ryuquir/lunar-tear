package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/masterdata"
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

type CageOrnamentServiceServer struct {
	pb.UnimplementedCageOrnamentServiceServer
	users    store.UserRepository
	sessions store.SessionRepository
	catalog  *masterdata.CageOrnamentCatalog
}

func NewCageOrnamentServiceServer(users store.UserRepository, sessions store.SessionRepository, catalog *masterdata.CageOrnamentCatalog) *CageOrnamentServiceServer {
	return &CageOrnamentServiceServer{users: users, sessions: sessions, catalog: catalog}
}

func (s *CageOrnamentServiceServer) ReceiveReward(ctx context.Context, req *pb.ReceiveRewardRequest) (*pb.ReceiveRewardResponse, error) {
	log.Printf("[CageOrnamentService] ReceiveReward: cageOrnamentId=%d", req.CageOrnamentId)

	reward, ok := s.catalog.LookupReward(req.CageOrnamentId)
	if !ok {
		log.Fatalf("[CageOrnamentService] ReceiveReward: no reward for cageOrnamentId=%d", req.CageOrnamentId)
	}

	userId := currentUserId(ctx, s.users, s.sessions)
	user, _ := s.users.UpdateUser(userId, func(user *store.UserState) {
		user.CageOrnamentRewards[req.CageOrnamentId] = store.CageOrnamentRewardState{
			CageOrnamentId: req.CageOrnamentId,
		}
		store.GrantPossession(user, model.PossessionType(reward.PossessionType), reward.PossessionId, reward.Count)
	})

	diff := userdata.BuildDiffFromTables(userdata.SelectTables(
		userdata.FullClientTableMap(user),
		[]string{"IUserMaterial", "IUserConsumableItem", "IUserGem"},
	))

	return &pb.ReceiveRewardResponse{
		CageOrnamentReward: []*pb.CageOrnamentReward{
			{
				PossessionType: reward.PossessionType,
				PossessionId:   reward.PossessionId,
				Count:          reward.Count,
			},
		},
		DiffUserData: diff,
	}, nil
}

func (s *CageOrnamentServiceServer) RecordAccess(ctx context.Context, req *pb.RecordAccessRequest) (*pb.RecordAccessResponse, error) {
	log.Printf("[CageOrnamentService] RecordAccess: cageOrnamentId=%d", req.CageOrnamentId)
	return &pb.RecordAccessResponse{
		DiffUserData: userdata.EmptyDiff(),
	}, nil
}
