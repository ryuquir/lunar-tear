package service

import (
	"context"
	"fmt"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/masterdata"
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

var shopDiffTables = []string{
	"IUserShopItem",
	"IUserShopReplaceable",
	"IUserShopReplaceableLineup",
	"IUserGem",
	"IUserConsumableItem",
	"IUserMaterial",
	"IUserImportantItem",
}

type ShopServiceServer struct {
	pb.UnimplementedShopServiceServer
	users    store.UserRepository
	sessions store.SessionRepository
	catalog  *masterdata.ShopCatalog
}

func NewShopServiceServer(users store.UserRepository, sessions store.SessionRepository, catalog *masterdata.ShopCatalog) *ShopServiceServer {
	return &ShopServiceServer{users: users, sessions: sessions, catalog: catalog}
}

func (s *ShopServiceServer) Buy(ctx context.Context, req *pb.BuyRequest) (*pb.BuyResponse, error) {
	log.Printf("[ShopService] Buy: shopId=%d items=%v", req.ShopId, req.ShopItems)

	userId := currentUserId(ctx, s.users, s.sessions)
	nowMillis := gametime.NowMillis()

	snapshot, err := s.users.UpdateUser(userId, func(user *store.UserState) {
		for shopItemId, qty := range req.ShopItems {
			item, ok := s.catalog.Items[shopItemId]
			if !ok {
				log.Printf("[ShopService] Buy: unknown shopItemId=%d, skipping", shopItemId)
				continue
			}

			totalPrice := item.Price * qty
			if err := store.DeductPrice(user, item.PriceType, item.PriceId, totalPrice); err != nil {
				log.Printf("[ShopService] Buy: deduct failed shopItemId=%d: %v", shopItemId, err)
				continue
			}

			for _, content := range s.catalog.Contents[shopItemId] {
				store.GrantPossession(user,
					model.PossessionType(content.PossessionType),
					content.PossessionId,
					content.Count*qty,
				)
			}

			si := user.ShopItems[shopItemId]
			si.ShopItemId = shopItemId
			si.BoughtCount += qty
			si.LatestBoughtCountChangedDatetime = nowMillis
			si.LatestVersion = nowMillis
			user.ShopItems[shopItemId] = si
		}
	})
	if err != nil {
		return nil, fmt.Errorf("shop buy: %w", err)
	}

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, shopDiffTables))

	return &pb.BuyResponse{
		OverflowPossession: []*pb.Possession{},
		DiffUserData:       diff,
	}, nil
}

func (s *ShopServiceServer) RefreshUserData(ctx context.Context, req *pb.RefreshRequest) (*pb.RefreshResponse, error) {
	log.Printf("[ShopService] RefreshUserData: isGemUsed=%v", req.IsGemUsed)

	userId := currentUserId(ctx, s.users, s.sessions)

	var snapshot store.UserState
	var err error

	if req.IsGemUsed {
		snapshot, err = s.users.UpdateUser(userId, func(user *store.UserState) {
			user.ShopReplaceable.LineupUpdateCount++
			user.ShopReplaceable.LatestLineupUpdateDatetime = gametime.NowMillis()
		})
	} else {
		snapshot, err = s.users.SnapshotUser(userId)
	}
	if err != nil {
		return nil, fmt.Errorf("shop refresh: %w", err)
	}

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, shopDiffTables))

	return &pb.RefreshResponse{
		DiffUserData: diff,
	}, nil
}
