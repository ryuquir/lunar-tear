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

func (s *WeaponServiceServer) Sell(ctx context.Context, req *pb.SellRequest) (*pb.SellResponse, error) {
	log.Printf("[WeaponService] Sell: uuids=%v", req.UserWeaponUuid)

	userId := currentUserId(ctx, s.users, s.sessions)

	oldUser, _ := s.users.SnapshotUser(userId)
	tracker := userdata.NewDeleteTracker().
		Track("IUserWeapon", oldUser, userdata.SortedWeaponRecords, []string{"userId", "userWeaponUuid"}).
		Track("IUserWeaponSkill", oldUser, userdata.SortedWeaponSkillRecords, []string{"userId", "userWeaponUuid", "slotNumber"}).
		Track("IUserWeaponAbility", oldUser, userdata.SortedWeaponAbilityRecords, []string{"userId", "userWeaponUuid", "slotNumber"})

	snapshot, err := s.users.UpdateUser(userId, func(user *store.UserState) {
		totalGold := int32(0)
		for _, uuid := range req.UserWeaponUuid {
			weapon, ok := user.Weapons[uuid]
			if !ok {
				log.Printf("[WeaponService] Sell: weapon uuid=%s not found, skipping", uuid)
				continue
			}

			wm, ok := s.catalog.Weapons[weapon.WeaponId]
			if !ok {
				log.Printf("[WeaponService] Sell: weapon master id=%d not found, skipping", weapon.WeaponId)
				continue
			}

			if sellFunc, ok := s.catalog.SellPriceByEnhanceId[wm.WeaponSpecificEnhanceId]; ok {
				totalGold += sellFunc.Evaluate(weapon.Level)
			}

			if medals, ok := s.catalog.MedalsByWeaponId[weapon.WeaponId]; ok {
				for itemId, count := range medals {
					user.ConsumableItems[itemId] += count
				}
			}

			delete(user.Weapons, uuid)
			delete(user.WeaponSkills, uuid)
			delete(user.WeaponAbilities, uuid)
		}

		if totalGold > 0 {
			user.ConsumableItems[s.config.ConsumableItemIdForGold] += totalGold
			log.Printf("[WeaponService] Sell: granted %d gold", totalGold)
		}
	})
	if err != nil {
		return nil, fmt.Errorf("weapon sell: %w", err)
	}

	sellDiffTables := []string{"IUserWeapon", "IUserWeaponSkill", "IUserWeaponAbility", "IUserConsumableItem"}
	tables := userdata.SelectTables(userdata.FullClientTableMap(snapshot), sellDiffTables)
	diff := tracker.Apply(snapshot, tables)

	return &pb.SellResponse{DiffUserData: diff}, nil
}

func (s *WeaponServiceServer) Evolve(ctx context.Context, req *pb.EvolveRequest) (*pb.EvolveResponse, error) {
	log.Printf("[WeaponService] Evolve: uuid=%s", req.UserWeaponUuid)

	userId := currentUserId(ctx, s.users, s.sessions)
	nowMillis := gametime.NowMillis()

	snapshot, err := s.users.UpdateUser(userId, func(user *store.UserState) {
		weapon, ok := user.Weapons[req.UserWeaponUuid]
		if !ok {
			log.Printf("[WeaponService] Evolve: weapon uuid=%s not found", req.UserWeaponUuid)
			return
		}

		wm, ok := s.catalog.Weapons[weapon.WeaponId]
		if !ok {
			log.Printf("[WeaponService] Evolve: weapon master id=%d not found", weapon.WeaponId)
			return
		}

		evolvedId, ok := s.catalog.EvolutionNextWeaponId[weapon.WeaponId]
		if !ok {
			log.Printf("[WeaponService] Evolve: no evolution for weaponId=%d", weapon.WeaponId)
			return
		}

		totalMaterialCount := int32(0)
		mats := s.catalog.EvolutionMaterials[wm.WeaponEvolutionMaterialGroupId]
		for _, mat := range mats {
			cur := user.Materials[mat.MaterialId]
			cost := mat.Count
			if cur < cost {
				log.Printf("[WeaponService] Evolve: insufficient material id=%d have=%d need=%d", mat.MaterialId, cur, cost)
				cost = cur
			}
			user.Materials[mat.MaterialId] = cur - cost
			totalMaterialCount += cost
		}

		if costFunc, ok := s.catalog.EvolutionCostByEnhanceId[wm.WeaponSpecificEnhanceId]; ok && totalMaterialCount > 0 {
			goldCost := costFunc.Evaluate(totalMaterialCount)
			user.ConsumableItems[s.config.ConsumableItemIdForGold] -= goldCost
			log.Printf("[WeaponService] Evolve: gold cost=%d", goldCost)
		}

		weapon.WeaponId = evolvedId
		weapon.LatestVersion = nowMillis
		user.Weapons[req.UserWeaponUuid] = weapon

		evolvedMaster, ok := s.catalog.Weapons[evolvedId]
		if ok {
			if slots, ok := s.catalog.AbilitySlots[evolvedMaster.WeaponAbilityGroupId]; ok {
				abilities := make([]store.WeaponAbilityState, len(slots))
				for i, slot := range slots {
					abilities[i] = store.WeaponAbilityState{
						UserWeaponUuid: req.UserWeaponUuid,
						SlotNumber:     slot,
						Level:          1,
					}
				}
				user.WeaponAbilities[req.UserWeaponUuid] = abilities
			}
		}

		log.Printf("[WeaponService] Evolve: weaponId %d -> %d", wm.WeaponId, evolvedId)
	})
	if err != nil {
		return nil, fmt.Errorf("weapon evolve: %w", err)
	}

	tables := userdata.FullClientTableMap(snapshot)
	diff := userdata.BuildDiffFromTables(userdata.SelectTables(tables, weaponDiffTables))

	return &pb.EvolveResponse{DiffUserData: diff}, nil
}
