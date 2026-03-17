package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gacha"
	"lunar-tear/server/internal/mock"
	"lunar-tear/server/internal/store"
)

type BannerServiceServer struct {
	pb.UnimplementedBannerServiceServer
	store *store.Store
}

func NewBannerServiceServer(userStore *store.Store) *BannerServiceServer {
	return &BannerServiceServer{store: userStore}
}

func (s *BannerServiceServer) GetMamaBanner(ctx context.Context, req *pb.GetMamaBannerRequest) (*pb.GetMamaBannerResponse, error) {
	log.Printf("[BannerService] GetMamaBanner")
	catalog := s.store.SnapshotGachaCatalog()
	log.Printf("[BannerService] GetMamaBanner: catalog size=%d", len(catalog))
	var termLimited []*pb.GachaBanner
	var latestChapter *pb.GachaBanner
	for _, entry := range catalog {
		log.Printf("[BannerService] GetMamaBanner: entry gachaId=%d label=%d asset=%q", entry.GachaId, entry.GachaLabelType, entry.BannerAssetName)
		b := &pb.GachaBanner{
			GachaLabelType: entry.GachaLabelType,
			GachaAssetName: entry.BannerAssetName,
			GachaId:        entry.GachaId,
		}
		switch entry.GachaLabelType {
		case gacha.GachaLabelEvent, gacha.GachaLabelPremium:
			termLimited = append(termLimited, b)
		case gacha.GachaLabelChapter:
			latestChapter = b
		}
	}
	return &pb.GetMamaBannerResponse{
		TermLimitedGacha:   termLimited,
		LatestChapterGacha: latestChapter,
		IsExistUnreadPop:   false,
		DiffUserData:       mock.EmptyDiff(),
	}, nil
}
