package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

type PortalCageServiceServer struct {
	pb.UnimplementedPortalCageServiceServer
	store *store.Store
}

func NewPortalCageServiceServer(userStore *store.Store) *PortalCageServiceServer {
	return &PortalCageServiceServer{store: userStore}
}

func (s *PortalCageServiceServer) UpdatePortalCageSceneProgress(ctx context.Context, req *pb.UpdatePortalCageSceneProgressRequest) (*pb.UpdatePortalCageSceneProgressResponse, error) {
	log.Printf("[PortalCageService] UpdatePortalCageSceneProgress: portalCageSceneId=%d", req.PortalCageSceneId)

	userId := currentUserId(ctx, s.store)
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		now := gametime.NowMillis()
		user.PortalCageStatus.IsCurrentProgress = true
		user.PortalCageStatus.LatestVersion = now
	})

	tables := userdata.SelectTables(
		userdata.FullClientTableMap(user),
		[]string{"IUserPortalCageStatus"},
	)
	return &pb.UpdatePortalCageSceneProgressResponse{
		DiffUserData: userdata.BuildDiffFromTablesOrdered(tables, []string{"IUserPortalCageStatus"}),
	}, nil
}
