package service

import (
	"context"
	"fmt"
	"log"
	"time"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/loginbonusloader"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"

	emptypb "google.golang.org/protobuf/types/known/emptypb"
)

type LoginBonusServiceServer struct {
	pb.UnimplementedLoginBonusServiceServer
	store   *store.Store
	catalog *loginbonusloader.Catalog
}

func NewLoginBonusServiceServer(userStore *store.Store, catalog *loginbonusloader.Catalog) *LoginBonusServiceServer {
	return &LoginBonusServiceServer{store: userStore, catalog: catalog}
}

func (s *LoginBonusServiceServer) ReceiveStamp(ctx context.Context, req *emptypb.Empty) (*pb.ReceiveStampResponse, error) {
	log.Printf("[LoginBonusService] ReceiveStamp")
	userId := currentUserId(ctx, s.store)

	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		now := time.Now().UnixMilli()
		nextStamp := user.LoginBonus.CurrentStampNumber + 1

		reward, ok := s.catalog.LookupStampReward(
			user.LoginBonus.LoginBonusId,
			user.LoginBonus.CurrentPageNumber,
			nextStamp,
		)
		if !ok {
			log.Fatalf("[LoginBonusService] no reward found for bonusId=%d page=%d stamp=%d",
				user.LoginBonus.LoginBonusId, user.LoginBonus.CurrentPageNumber, nextStamp)
		}

		log.Printf("[LoginBonusService] stamp %d -> possType=%d possId=%d count=%d (-> gift box)",
			nextStamp, reward.PossessionType, reward.PossessionId, reward.Count)

		user.Gifts.NotReceived = append(user.Gifts.NotReceived, store.NotReceivedGiftState{
			GiftCommon: store.GiftCommonState{
				PossessionType: reward.PossessionType,
				PossessionId:   reward.PossessionId,
				Count:          reward.Count,
				GrantDatetime:  now,
			},
			ExpirationDatetime: now + int64(30*24*time.Hour/time.Millisecond),
			UserGiftUuid:       fmt.Sprintf("login-bonus-%d-%d", userId, nextStamp),
		})
		user.Notifications.GiftNotReceiveCount = int32(len(user.Gifts.NotReceived))
		user.LoginBonus.CurrentStampNumber = nextStamp
		user.LoginBonus.LatestRewardReceiveDatetime = now
		user.LoginBonus.LatestVersion = now
	})

	diff := userdata.BuildDiffFromTables(userdata.SelectTables(
		userdata.FullClientTableMap(user),
		[]string{"IUserLoginBonus"},
	))
	setCommonResponseTrailers(ctx, diff, false)
	return &pb.ReceiveStampResponse{DiffUserData: diff}, nil
}
