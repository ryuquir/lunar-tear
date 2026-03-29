package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"

	emptypb "google.golang.org/protobuf/types/known/emptypb"
)

type FriendServiceServer struct {
	pb.UnimplementedFriendServiceServer
	users    store.UserRepository
	sessions store.SessionRepository
}

func NewFriendServiceServer(users store.UserRepository, sessions store.SessionRepository) *FriendServiceServer {
	return &FriendServiceServer{users: users, sessions: sessions}
}

func (s *FriendServiceServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
	log.Printf("[FriendService] GetUser: playerId=%d", req.PlayerId)
	return &pb.GetUserResponse{DiffUserData: userdata.EmptyDiff()}, nil
}

func (s *FriendServiceServer) GetFriendList(ctx context.Context, req *pb.GetFriendListRequest) (*pb.GetFriendListResponse, error) {
	log.Printf("[FriendService] GetFriendList")
	return &pb.GetFriendListResponse{
		FriendUser:         []*pb.FriendUser{},
		SendCheerCount:     0,
		ReceivedCheerCount: 0,
		DiffUserData:       userdata.EmptyDiff(),
	}, nil
}

func (s *FriendServiceServer) GetFriendRequestList(ctx context.Context, req *emptypb.Empty) (*pb.GetFriendRequestListResponse, error) {
	log.Printf("[FriendService] GetFriendRequestList")
	return &pb.GetFriendRequestListResponse{
		User:         []*pb.User{},
		DiffUserData: userdata.EmptyDiff(),
	}, nil
}

func (s *FriendServiceServer) SearchRecommendedUsers(ctx context.Context, req *emptypb.Empty) (*pb.SearchRecommendedUsersResponse, error) {
	log.Printf("[FriendService] SearchRecommendedUsers")
	return &pb.SearchRecommendedUsersResponse{
		Users:        []*pb.User{},
		DiffUserData: userdata.EmptyDiff(),
	}, nil
}
