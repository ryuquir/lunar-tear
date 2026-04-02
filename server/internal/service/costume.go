package service

import (
	"context"
	"fmt"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/gameutil"
	"lunar-tear/server/internal/masterdata"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"
)

var costumeDiffTables = []string{
	"IUserCostume",
	"IUserMaterial",
	"IUserConsumableItem",
}

const (
	sameWeaponExpCoefficientPermil = 1500
	goldConsumableItemId           = int32(1)
)

type CostumeServiceServer struct {
	pb.UnimplementedCostumeServiceServer
	users    store.UserRepository
	sessions store.SessionRepository
	catalog  *masterdata.CostumeCatalog
}

func NewCostumeServiceServer(users store.UserRepository, sessions store.SessionRepository, catalog *masterdata.CostumeCatalog) *CostumeServiceServer {
	return &CostumeServiceServer{users: users, sessions: sessions, catalog: catalog}
}

func (s *CostumeServiceServer) Enhance(ctx context.Context, req *pb.EnhanceRequest) (*pb.EnhanceResponse, error) {
	log.Printf("[CostumeService] Enhance: uuid=%s materials=%v", req.UserCostumeUuid, req.Materials)

	userId := currentUserId(ctx, s.users, s.sessions)
	nowMillis := gametime.NowMillis()

	snapshot, err := s.users.UpdateUser(userId, func(user *store.UserState) {
		costume, ok := user.Costumes[req.UserCostumeUuid]
		if !ok {
			log.Printf("[CostumeService] Enhance: costume uuid=%s not found", req.UserCostumeUuid)
			return
		}

		cm, ok := s.catalog.Costumes[costume.CostumeId]
		if !ok {
			log.Printf("[CostumeService] Enhance: costume master id=%d not found", costume.CostumeId)
			return
		}

		totalExp := int32(0)
		totalMaterialCount := int32(0)
		for materialId, count := range req.Materials {
			mat, ok := s.catalog.Materials[materialId]
			if !ok {
				log.Printf("[CostumeService] Enhance: material id=%d not found, skipping", materialId)
				continue
			}

			cur := user.Materials[materialId]
			if cur < count {
				log.Printf("[CostumeService] Enhance: insufficient material id=%d have=%d need=%d", materialId, cur, count)
				continue
			}
			user.Materials[materialId] = cur - count
			totalMaterialCount += count

			expPerUnit := mat.EffectValue
			if mat.WeaponType != 0 && mat.WeaponType == cm.SkillfulWeaponType {
				expPerUnit = expPerUnit * sameWeaponExpCoefficientPermil / 1000
			}
			totalExp += expPerUnit * count
		}

		if costFunc, ok := s.catalog.EnhanceCostByRarity[cm.RarityType]; ok && totalMaterialCount > 0 {
			goldCost := costFunc.Evaluate(totalMaterialCount)
			user.ConsumableItems[goldConsumableItemId] -= goldCost
			log.Printf("[CostumeService] Enhance: gold cost=%d (materials=%d)", goldCost, totalMaterialCount)
		}

		costume.Exp += totalExp

		if thresholds, ok := s.catalog.ExpByRarity[cm.RarityType]; ok {
			costume.Level, costume.Exp = gameutil.LevelAndCap(costume.Exp, thresholds)
		}

		costume.LatestVersion = nowMillis
		user.Costumes[req.UserCostumeUuid] = costume
		log.Printf("[CostumeService] Enhance: costumeId=%d +%d exp -> total=%d level=%d", costume.CostumeId, totalExp, costume.Exp, costume.Level)
	})
	if err != nil {
		return nil, fmt.Errorf("costume enhance: %w", err)
	}

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, costumeDiffTables))

	return &pb.EnhanceResponse{
		IsGreatSuccess:         false,
		SurplusEnhanceMaterial: map[int32]int32{},
		DiffUserData:           diff,
	}, nil
}
