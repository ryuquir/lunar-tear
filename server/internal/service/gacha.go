package service

import (
	"context"
	"log"
	"sort"
	"time"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gacha"
	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/mock"
	"lunar-tear/server/internal/store"

	emptypb "google.golang.org/protobuf/types/known/emptypb"
	"google.golang.org/protobuf/types/known/timestamppb"
)

type GachaServiceServer struct {
	pb.UnimplementedGachaServiceServer
	store *store.Store
}

func NewGachaServiceServer(userStore *store.Store) *GachaServiceServer {
	return &GachaServiceServer{store: userStore}
}

func (s *GachaServiceServer) GetGachaList(ctx context.Context, req *pb.GetGachaListRequest) (*pb.GetGachaListResponse, error) {
	log.Printf("[GachaService] GetGachaList: labels=%v", req.GachaLabelType)

	catalog := s.store.SnapshotGachaCatalog()
	sort.Slice(catalog, func(i, j int) bool {
		if catalog[i].SortOrder != catalog[j].SortOrder {
			return catalog[i].SortOrder < catalog[j].SortOrder
		}
		return catalog[i].GachaId < catalog[j].GachaId
	})

	userId := currentUserId(ctx, s.store)
	user, ok := s.store.SnapshotUser(userId)
	if !ok {
		user = s.store.EnsureUser("")
	}

	gachaList := make([]*pb.Gacha, 0, len(catalog))
	for _, entry := range catalog {
		if !matchesGachaLabel(req.GachaLabelType, entry.GachaLabelType) {
			continue
		}
		gachaList = append(gachaList, toProtoGacha(entry))
	}
	log.Printf("[GachaService] GetGachaList: returning gachas: %#v", gachaList)

	return &pb.GetGachaListResponse{
		Gacha:               gachaList,
		ConvertedGachaMedal: toProtoConvertedGachaMedal(user.Gacha.ConvertedGachaMedal),
		DiffUserData:        mock.EmptyDiff(),
	}, nil
}

func (s *GachaServiceServer) GetGacha(ctx context.Context, req *pb.GetGachaRequest) (*pb.GetGachaResponse, error) {
	log.Printf("[GachaService] GetGacha: ids=%v", req.GachaId)

	catalog := s.store.SnapshotGachaCatalog()
	byId := make(map[int32]*pb.Gacha, len(req.GachaId))
	for _, wantedId := range req.GachaId {
		for _, entry := range catalog {
			if entry.GachaId == wantedId {
				byId[wantedId] = toProtoGacha(entry)
				break
			}
		}
	}

	return &pb.GetGachaResponse{
		Gacha:        byId,
		DiffUserData: mock.EmptyDiff(),
	}, nil
}

func (s *GachaServiceServer) Draw(ctx context.Context, req *pb.DrawRequest) (*pb.DrawResponse, error) {
	log.Printf("[GachaService] Draw: gachaId=%d phaseId=%d execCount=%d", req.GachaId, req.GachaPricePhaseId, req.ExecCount)
	return &pb.DrawResponse{
		NextGacha:          nil,
		GachaResult:        []*pb.DrawGachaOddsItem{},
		GachaBonus:         []*pb.GachaBonus{},
		MenuGachaBadgeInfo: []*pb.MenuGachaBadgeInfo{},
		DiffUserData:       mock.EmptyDiff(),
	}, nil
}

func (s *GachaServiceServer) ResetBoxGacha(ctx context.Context, req *pb.ResetBoxGachaRequest) (*pb.ResetBoxGachaResponse, error) {
	log.Printf("[GachaService] ResetBoxGacha: gachaId=%d", req.GachaId)
	return &pb.ResetBoxGachaResponse{
		Gacha:        nil,
		DiffUserData: mock.EmptyDiff(),
	}, nil
}

func (s *GachaServiceServer) GetRewardGacha(ctx context.Context, req *emptypb.Empty) (*pb.GetRewardGachaResponse, error) {
	log.Printf("[GachaService] GetRewardGacha")
	userId := currentUserId(ctx, s.store)
	user, ok := s.store.SnapshotUser(userId)
	if !ok {
		user = s.store.EnsureUser("")
	}

	return &pb.GetRewardGachaResponse{
		Available:              user.Gacha.RewardAvailable,
		TodaysCurrentDrawCount: user.Gacha.TodaysCurrentDrawCount,
		DailyMaxCount:          user.Gacha.DailyMaxCount,
		DiffUserData:           mock.EmptyDiff(),
	}, nil
}

func (s *GachaServiceServer) RewardDraw(ctx context.Context, req *pb.RewardDrawRequest) (*pb.RewardDrawResponse, error) {
	log.Printf("[GachaService] RewardDraw: placement=%q reward=%q amount=%q", req.PlacementName, req.RewardName, req.RewardAmount)
	return &pb.RewardDrawResponse{
		RewardGachaResult: []*pb.RewardGachaItem{},
		DiffUserData:      mock.EmptyDiff(),
	}, nil
}

func matchesGachaLabel(labels []int32, label int32) bool {
	if len(labels) == 0 {
		return true
	}
	for _, candidate := range labels {
		if candidate == label {
			return true
		}
	}
	return false
}

var featuredCostumes = []int32{
	31000, 31001, 31002, 31004, 31005, 31006, 31007, 31008, 31009, 31010,
	31011, 31012, 31013, 31014, 31015, 31016, 31017, 31018, 31019, 31020,
}

var featuredWeapons = []int32{
	210002, 210022, 210032, 210042, 210062, 210072, 210082, 210102,
	210112, 210122, 210142, 210152, 210162, 210172, 210182, 210192,
}

func stubPromotionItems(gachaId int32) []*pb.GachaOddsItem {
	idx := int(gachaId) % len(featuredCostumes)
	wIdx := int(gachaId) % len(featuredWeapons)
	return []*pb.GachaOddsItem{
		{
			GachaItem: &pb.GachaItem{PossessionType: 1, PossessionId: featuredCostumes[idx], Count: 1, PromotionOrder: 1},
			IsTarget:  true,
		},
		{
			GachaItem: &pb.GachaItem{PossessionType: 1, PossessionId: featuredCostumes[(idx+1)%len(featuredCostumes)], Count: 1, PromotionOrder: 2},
			IsTarget:  true,
		},
		{
			GachaItem: &pb.GachaItem{PossessionType: 2, PossessionId: featuredWeapons[wIdx], Count: 1, PromotionOrder: 3},
			IsTarget:  true,
		},
	}
}

func stubGachaPricePhases(gachaId, modeType int32) []*pb.GachaPricePhase {
	phaseId := gachaId*10 + 1

	price := int32(3000)
	drawCount := int32(10)
	if modeType == gacha.GachaModeStepup {
		price = 1500
		drawCount = 10
	}

	return []*pb.GachaPricePhase{{
		GachaPricePhaseId: phaseId,
		IsEnabled:         true,
		EndDatetime:       timestamppb.New(gametime.Now().AddDate(0, 0, 30)),
		PriceType:         gacha.PriceTypeGem,
		Price:             price,
		RegularPrice:      3000,
		DrawCount:         drawCount,
		GachaOddsFixedRarity: &pb.GachaOddsFixedRarity{
			FixedRarityTypeLowerLimit: 0,
			FixedCount:                0,
		},
	}}
}

func toProtoGacha(entry store.GachaCatalogEntry) *pb.Gacha {
	g := &pb.Gacha{
		GachaId:                    entry.GachaId,
		GachaLabelType:             entry.GachaLabelType,
		GachaModeType:              entry.GachaModeType,
		GachaAutoResetType:         entry.GachaAutoResetType,
		GachaAutoResetPeriod:       entry.GachaAutoResetPeriod,
		NextAutoResetDatetime:      safeTimestamp(entry.NextAutoResetDatetime),
		GachaUnlockCondition:       []*pb.GachaUnlockCondition{{GachaUnlockConditionType: gacha.GachaUnlockNone, ConditionValue: 0}},
		IsUserGachaUnlock:          entry.IsUserGachaUnlock,
		StartDatetime:              safeTimestamp(entry.StartDatetime),
		EndDatetime:                safeTimestamp(entry.EndDatetime),
		GachaPricePhase:            stubGachaPricePhases(entry.GachaId, entry.GachaModeType),
		RelatedMainQuestChapterId:  entry.RelatedMainQuestChapterId,
		RelatedEventQuestChapterId: entry.RelatedEventQuestChapterId,
		PromotionMovieAssetId:      entry.PromotionMovieAssetId,
		GachaMedalId:               entry.GachaMedalId,
		GachaDecorationType:        entry.GachaDecorationType,
		SortOrder:                  entry.SortOrder,
		IsInactive:                 entry.IsInactive,
		InformationId:              entry.InformationId,
	}

	phaseId := entry.GachaId*10 + 1

	switch entry.GachaModeType {
	case gacha.GachaModeBox:
		g.GachaMode = &pb.Gacha_GachaModeBoxComposition{
			GachaModeBoxComposition: &pb.GachaModeBoxComposition{
				GachaBoxGroupId:        entry.StepupGroupId,
				BoxNumber:              1,
				CurrentBoxNumber:       1,
				GachaAssetName:         entry.BannerAssetName,
				GachaPricePhaseId:      phaseId,
				PromotionGachaOddsItem: stubPromotionItems(entry.GachaId),
			},
		}
	case gacha.GachaModeStepup:
		g.GachaMode = &pb.Gacha_GachaModeStepupComposition{
			GachaModeStepupComposition: &pb.GachaModeStepupComposition{
				GachaStepGroupId:              entry.StepupGroupId,
				StepNumber:                    1,
				CurrentStepNumber:             1,
				NaviCharacterCommentAssetName: "",
				GachaAssetName:                entry.BannerAssetName,
				CurrentLoopCount:              0,
			},
		}
	default:
		g.GachaMode = &pb.Gacha_GachaModeBasic{
			GachaModeBasic: &pb.GachaModeBasic{
				GachaAssetName: entry.BannerAssetName,
			},
		}
	}

	return g
}

func toProtoConvertedGachaMedal(state store.ConvertedGachaMedalState) *pb.ConvertedGachaMedal {
	items := make([]*pb.ConsumableItemPossession, 0, len(state.ConvertedMedalPossession))
	for _, item := range state.ConvertedMedalPossession {
		items = append(items, &pb.ConsumableItemPossession{
			ConsumableItemId: item.ConsumableItemId,
			Count:            item.Count,
		})
	}

	obtain := &pb.ConsumableItemPossession{
		ConsumableItemId: 0,
		Count:            0,
	}
	if state.ObtainPossession != nil {
		obtain.ConsumableItemId = state.ObtainPossession.ConsumableItemId
		obtain.Count = state.ObtainPossession.Count
	}

	return &pb.ConvertedGachaMedal{
		ConvertedMedalPossession: items,
		ObtainPossession:         obtain,
	}
}

func safeTimestamp(unixMillis int64) *timestamppb.Timestamp {
	if unixMillis == 0 {
		return &timestamppb.Timestamp{Seconds: 0}
	}
	return timestamppb.New(time.UnixMilli(unixMillis))
}
