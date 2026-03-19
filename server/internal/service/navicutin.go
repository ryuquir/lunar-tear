package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

type NaviCutInServiceServer struct {
	pb.UnimplementedNaviCutInServiceServer
	store *store.Store
}

func NewNaviCutInServiceServer(userStore *store.Store) *NaviCutInServiceServer {
	return &NaviCutInServiceServer{store: userStore}
}

func (s *NaviCutInServiceServer) RegisterPlayed(ctx context.Context, req *pb.RegisterPlayedRequest) (*pb.RegisterPlayedResponse, error) {
	log.Printf("[NaviCutInService] RegisterPlayed: naviCutId=%d", req.NaviCutId)

	userId := currentUserId(ctx, s.store)
	snapshot, ok := s.store.UpdateUser(userId, func(user *store.UserState) {
		user.NaviCutInPlayed[req.NaviCutId] = true
	})
	if !ok {
		snapshot = s.store.EnsureUser("")
	}

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, []string{"IUserNaviCutIn"}))

	return &pb.RegisterPlayedResponse{
		DiffUserData: diff,
	}, nil
}
