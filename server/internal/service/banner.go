package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

type BannerServiceServer struct {
	pb.UnimplementedBannerServiceServer
	gacha store.GachaRepository
}

func NewBannerServiceServer(gacha store.GachaRepository) *BannerServiceServer {
	return &BannerServiceServer{gacha: gacha}
}

func (s *BannerServiceServer) GetMamaBanner(ctx context.Context, req *pb.GetMamaBannerRequest) (*pb.GetMamaBannerResponse, error) {
	log.Printf("[BannerService] GetMamaBanner")
	catalog, _ := s.gacha.SnapshotCatalog()
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
		case model.GachaLabelEvent, model.GachaLabelPremium:
			termLimited = append(termLimited, b)
		case model.GachaLabelChapter:
			latestChapter = b
		}
	}
	return &pb.GetMamaBannerResponse{
		TermLimitedGacha:   termLimited,
		LatestChapterGacha: latestChapter,
		IsExistUnreadPop:   false,
		DiffUserData:       userdata.EmptyDiff(),
	}, nil
}
