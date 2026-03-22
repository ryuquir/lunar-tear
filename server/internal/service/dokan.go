package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

type DokanServiceServer struct {
	pb.UnimplementedDokanServiceServer
	store *store.Store
}

func NewDokanServiceServer(userStore *store.Store) *DokanServiceServer {
	return &DokanServiceServer{store: userStore}
}

func (s *DokanServiceServer) RegisterDokanConfirmed(ctx context.Context, req *pb.RegisterDokanConfirmedRequest) (*pb.RegisterDokanConfirmedResponse, error) {
	log.Printf("[DokanService] RegisterDokanConfirmed: dokanIds=%v", req.DokanId)

	userId := currentUserId(ctx, s.store)
	snapshot, ok := s.store.UpdateUser(userId, func(user *store.UserState) {
		for _, id := range req.DokanId {
			user.DokanConfirmed[id] = true
		}
	})
	if !ok {
		snapshot = s.store.EnsureUser("")
	}

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, []string{"IUserDokan"}))

	return &pb.RegisterDokanConfirmedResponse{
		DiffUserData: diff,
	}, nil
}
