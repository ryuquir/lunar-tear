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

var weaponDiffTables = []string{
	"IUserWeapon",
	"IUserWeaponSkill",
	"IUserWeaponAbility",
	"IUserMaterial",
	"IUserConsumableItem",
}

type WeaponServiceServer struct {
	pb.UnimplementedWeaponServiceServer
	users    store.UserRepository
	sessions store.SessionRepository
	catalog  *masterdata.WeaponCatalog
	config   *masterdata.GameConfig
}

func NewWeaponServiceServer(users store.UserRepository, sessions store.SessionRepository, catalog *masterdata.WeaponCatalog, config *masterdata.GameConfig) *WeaponServiceServer {
	return &WeaponServiceServer{users: users, sessions: sessions, catalog: catalog, config: config}
}

func (s *WeaponServiceServer) Protect(ctx context.Context, req *pb.ProtectRequest) (*pb.ProtectResponse, error) {
	log.Printf("[WeaponService] Protect: uuids=%v", req.UserWeaponUuid)

	userId := currentUserId(ctx, s.users, s.sessions)
	nowMillis := gametime.NowMillis()

	snapshot, _ := s.users.UpdateUser(userId, func(user *store.UserState) {
		for _, uuid := range req.UserWeaponUuid {
			weapon, ok := user.Weapons[uuid]
			if !ok {
				log.Printf("[WeaponService] Protect: weapon uuid=%s not found", uuid)
				continue
			}
			weapon.IsProtected = true
			weapon.LatestVersion = nowMillis
			user.Weapons[uuid] = weapon
		}
	})

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, []string{"IUserWeapon"}))
	return &pb.ProtectResponse{DiffUserData: diff}, nil
}

func (s *WeaponServiceServer) Unprotect(ctx context.Context, req *pb.UnprotectRequest) (*pb.UnprotectResponse, error) {
	log.Printf("[WeaponService] Unprotect: uuids=%v", req.UserWeaponUuid)

	userId := currentUserId(ctx, s.users, s.sessions)
	nowMillis := gametime.NowMillis()

	snapshot, _ := s.users.UpdateUser(userId, func(user *store.UserState) {
		for _, uuid := range req.UserWeaponUuid {
			weapon, ok := user.Weapons[uuid]
			if !ok {
				log.Printf("[WeaponService] Unprotect: weapon uuid=%s not found", uuid)
				continue
			}
			weapon.IsProtected = false
			weapon.LatestVersion = nowMillis
			user.Weapons[uuid] = weapon
		}
	})

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, []string{"IUserWeapon"}))
	return &pb.UnprotectResponse{DiffUserData: diff}, nil
}

func (s *WeaponServiceServer) EnhanceByMaterial(ctx context.Context, req *pb.EnhanceByMaterialRequest) (*pb.EnhanceByMaterialResponse, error) {
	log.Printf("[WeaponService] EnhanceByMaterial: uuid=%s materials=%v", req.UserWeaponUuid, req.Materials)

	userId := currentUserId(ctx, s.users, s.sessions)
	nowMillis := gametime.NowMillis()

	snapshot, err := s.users.UpdateUser(userId, func(user *store.UserState) {
		weapon, ok := user.Weapons[req.UserWeaponUuid]
		if !ok {
			log.Printf("[WeaponService] EnhanceByMaterial: weapon uuid=%s not found", req.UserWeaponUuid)
			return
		}

		wm, ok := s.catalog.Weapons[weapon.WeaponId]
		if !ok {
			log.Printf("[WeaponService] EnhanceByMaterial: weapon master id=%d not found", weapon.WeaponId)
			return
		}

		totalExp := int32(0)
		totalMaterialCount := int32(0)
		for materialId, count := range req.Materials {
			mat, ok := s.catalog.Materials[materialId]
			if !ok {
				log.Printf("[WeaponService] EnhanceByMaterial: material id=%d not found, skipping", materialId)
				continue
			}

			cur := user.Materials[materialId]
			if cur < count {
				log.Printf("[WeaponService] EnhanceByMaterial: insufficient material id=%d have=%d need=%d", materialId, cur, count)
				continue
			}
			user.Materials[materialId] = cur - count
			totalMaterialCount += count

			expPerUnit := mat.EffectValue
			if mat.WeaponType != 0 && mat.WeaponType == wm.WeaponType {
				expPerUnit = expPerUnit * s.config.MaterialSameWeaponExpCoefficientPermil / 1000
			}
			totalExp += expPerUnit * count
		}

		if costFunc, ok := s.catalog.GoldCostByEnhanceId[wm.WeaponSpecificEnhanceId]; ok && totalMaterialCount > 0 {
			goldCost := costFunc.Evaluate(totalMaterialCount)
			user.ConsumableItems[s.config.ConsumableItemIdForGold] -= goldCost
			log.Printf("[WeaponService] EnhanceByMaterial: gold cost=%d (materials=%d)", goldCost, totalMaterialCount)
		}

		weapon.Exp += totalExp
		if thresholds, ok := s.catalog.ExpByEnhanceId[wm.WeaponSpecificEnhanceId]; ok {
			weapon.Level, weapon.Exp = gameutil.LevelAndCap(weapon.Exp, thresholds)
		}

		weapon.LatestVersion = nowMillis
		user.Weapons[req.UserWeaponUuid] = weapon
		log.Printf("[WeaponService] EnhanceByMaterial: weaponId=%d +%d exp -> total=%d level=%d", weapon.WeaponId, totalExp, weapon.Exp, weapon.Level)
	})
	if err != nil {
		return nil, fmt.Errorf("weapon enhance by material: %w", err)
	}

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, weaponDiffTables))

	return &pb.EnhanceByMaterialResponse{
		IsGreatSuccess:         false,
		SurplusEnhanceMaterial: map[int32]int32{},
		DiffUserData:           diff,
	}, nil
}
