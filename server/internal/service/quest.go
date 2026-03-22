package service

import (
	"context"
	"log"

	pb "lunar-tear/server/gen/proto"
	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/mock"
	"lunar-tear/server/internal/questflow"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/userdata"

	emptypb "google.golang.org/protobuf/types/known/emptypb"
)

type QuestServiceServer struct {
	pb.UnimplementedQuestServiceServer
	store  *store.Store
	engine *questflow.Engine
}

func NewQuestServiceServer(userStore *store.Store, engine *questflow.Engine) *QuestServiceServer {
	if engine == nil {
		panic("quest flow engine is required")
	}
	return &QuestServiceServer{store: userStore, engine: engine}
}

func buildSelectedQuestDiff(user store.UserState, tableNames []string) map[string]*pb.DiffData {
	tables := userdata.SelectTables(userdata.FullClientTableMap(user), tableNames)
	return userdata.BuildDiffFromTablesOrdered(tables, tableNames)
}

func logQuestState(prefix string, user store.UserState) {
	log.Printf("[QuestService] %s MainQuest=%#v Status=%#v Quests=%#v", prefix, user.MainQuest, user.Status, user.Quests)
	log.Printf("[QuestService] %s Weapons=%#v WeaponStories=%#v", prefix, user.Weapons, user.WeaponStories)
}

func (s *QuestServiceServer) UpdateMainFlowSceneProgress(ctx context.Context, req *pb.UpdateMainFlowSceneProgressRequest) (*pb.UpdateMainFlowSceneProgressResponse, error) {
	log.Printf("[QuestService] UpdateMainFlowSceneProgress: questSceneId=%d", req.QuestSceneId)

	userId := currentUserId(ctx, s.store)
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		s.engine.HandleMainFlowSceneProgress(user, req.QuestSceneId, gametime.NowMillis())
	})
	logQuestState("UpdateMainFlowSceneProgress state", user)

	return &pb.UpdateMainFlowSceneProgressResponse{
		DiffUserData: buildSelectedQuestDiff(user, []string{
			"IUserMainQuestFlowStatus",
			"IUserMainQuestMainFlowStatus",
			"IUserMainQuestProgressStatus",
			"IUserMainQuestSeasonRoute",
			"IUserCharacter",
			"IUserCostume",
			"IUserCostumeActiveSkill",
			"IUserWeapon",
			"IUserWeaponNote",
			"IUserWeaponStory",
			"IUserCompanion",
			"IUserConsumableItem",
			"IUserMaterial",
			"IUserImportantItem",
		}),
	}, nil
}

func (s *QuestServiceServer) UpdateReplayFlowSceneProgress(ctx context.Context, req *pb.UpdateReplayFlowSceneProgressRequest) (*pb.UpdateReplayFlowSceneProgressResponse, error) {
	log.Printf("[QuestService] UpdateReplayFlowSceneProgress: questSceneId=%d", req.QuestSceneId)
	return &pb.UpdateReplayFlowSceneProgressResponse{
		DiffUserData: mock.EmptyDiff(),
	}, nil
}

func (s *QuestServiceServer) UpdateMainQuestSceneProgress(ctx context.Context, req *pb.UpdateMainQuestSceneProgressRequest) (*pb.UpdateMainQuestSceneProgressResponse, error) {
	log.Printf("[QuestService] UpdateMainQuestSceneProgress: questSceneId=%d", req.QuestSceneId)

	userId := currentUserId(ctx, s.store)
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		s.engine.HandleMainQuestSceneProgress(user, req.QuestSceneId)
	})
	logQuestState("UpdateMainQuestSceneProgress state", user)
	return &pb.UpdateMainQuestSceneProgressResponse{
		DiffUserData: buildSelectedQuestDiff(user, []string{
			"IUserStatus",
			"IUserCharacter",
			"IUserQuest",
			"IUserQuestMission",
			"IUserMainQuestFlowStatus",
			"IUserMainQuestMainFlowStatus",
			"IUserMainQuestProgressStatus",
		}),
	}, nil
}

func (s *QuestServiceServer) StartMainQuest(ctx context.Context, req *pb.StartMainQuestRequest) (*pb.StartMainQuestResponse, error) {
	log.Printf("[QuestService] StartMainQuest: %+v", req)

	userId := currentUserId(ctx, s.store)
	nowMillis := gametime.NowMillis()
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		s.engine.HandleQuestStart(user, req.QuestId, req.IsBattleOnly, nowMillis)
	})
	logQuestState("StartMainQuest state", user)

	drops := s.engine.BattleDropRewards(req.QuestId)
	pbDrops := make([]*pb.BattleDropReward, len(drops))
	for i, d := range drops {
		pbDrops[i] = &pb.BattleDropReward{
			QuestSceneId:         d.QuestSceneId,
			BattleDropCategoryId: d.BattleDropCategoryId,
			BattleDropEffectId:   1,
		}
	}

	return &pb.StartMainQuestResponse{
		BattleDropReward: pbDrops,
		DiffUserData: buildSelectedQuestDiff(user, []string{
			"IUserStatus",
			"IUserQuest",
			"IUserQuestMission",
			"IUserMainQuestFlowStatus",
			"IUserMainQuestMainFlowStatus",
			"IUserMainQuestProgressStatus",
			"IUserMainQuestSeasonRoute",
		}),
	}, nil
}

func toProtoRewards(grants []questflow.RewardGrant) []*pb.QuestReward {
	if len(grants) == 0 {
		return []*pb.QuestReward{}
	}
	out := make([]*pb.QuestReward, len(grants))
	for i, g := range grants {
		out[i] = &pb.QuestReward{
			PossessionType: int32(g.PossessionType),
			PossessionId:   g.PossessionId,
			Count:          g.Count,
		}
	}
	return out
}

func (s *QuestServiceServer) FinishMainQuest(ctx context.Context, req *pb.FinishMainQuestRequest) (*pb.FinishMainQuestResponse, error) {
	log.Printf("[QuestService] FinishMainQuest: questId=%d isMainFlow=%v isRetired=%v storySkipType=%d",
		req.QuestId, req.IsMainFlow, req.IsRetired, req.StorySkipType)

	nowMillis := gametime.NowMillis()
	userId := currentUserId(ctx, s.store)
	var outcome questflow.FinishOutcome
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		outcome = s.engine.HandleQuestFinish(user, req.QuestId, req.IsRetired, nowMillis)
	})
	logQuestState("FinishMainQuest state", user)

	return &pb.FinishMainQuestResponse{
		DropReward:                      toProtoRewards(outcome.DropRewards),
		FirstClearReward:                toProtoRewards(outcome.FirstClearRewards),
		MissionClearReward:              toProtoRewards(outcome.MissionClearRewards),
		MissionClearCompleteReward:      toProtoRewards(outcome.MissionClearCompleteRewards),
		AutoOrbitResult:                 []*pb.QuestReward{},
		IsBigWin:                        outcome.IsBigWin,
		BigWinClearedQuestMissionIdList: outcome.BigWinClearedQuestMissionIds,
		ReplayFlowFirstClearReward:      []*pb.QuestReward{},
		UserStatusCampaignReward:        []*pb.QuestReward{},
		DiffUserData: buildSelectedQuestDiff(user, []string{
			"IUserQuest",
			"IUserQuestMission",
			"IUserMainQuestFlowStatus",
			"IUserMainQuestMainFlowStatus",
			"IUserMainQuestProgressStatus",
			"IUserMainQuestSeasonRoute",
			"IUserStatus",
			"IUserGem",
			"IUserCharacter",
			"IUserCostume",
			"IUserCostumeActiveSkill",
			"IUserWeapon",
			"IUserWeaponNote",
			"IUserWeaponStory",
			"IUserCompanion",
			"IUserConsumableItem",
			"IUserMaterial",
			"IUserImportantItem",
		}),
	}, nil
}

func (s *QuestServiceServer) RestartMainQuest(ctx context.Context, req *pb.RestartMainQuestRequest) (*pb.RestartMainQuestResponse, error) {
	log.Printf("[QuestService] RestartMainQuest: questId=%d isMainFlow=%v", req.QuestId, req.IsMainFlow)

	userId := currentUserId(ctx, s.store)
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		s.engine.HandleQuestRestart(user, req.QuestId, gametime.NowMillis())
	})
	logQuestState("RestartMainQuest state", user)

	return &pb.RestartMainQuestResponse{
		BattleDropReward: []*pb.BattleDropReward{},
		DiffUserData:     buildSelectedQuestDiff(user, []string{"IUserQuest", "IUserQuestMission"}),
	}, nil
}

func (s *QuestServiceServer) FinishAutoOrbit(ctx context.Context, req *emptypb.Empty) (*pb.FinishAutoOrbitResponse, error) {
	log.Printf("[QuestService] FinishAutoOrbit")
	return &pb.FinishAutoOrbitResponse{
		DiffUserData: mock.EmptyDiff(),
	}, nil
}

func (s *QuestServiceServer) SetQuestSceneChoice(ctx context.Context, req *pb.SetQuestSceneChoiceRequest) (*pb.SetQuestSceneChoiceResponse, error) {
	log.Printf("[QuestService] SetQuestSceneChoice: questSceneId=%d choiceNumber=%d",
		req.QuestSceneId, req.ChoiceNumber)
	return &pb.SetQuestSceneChoiceResponse{
		DiffUserData: mock.EmptyDiff(),
	}, nil
}

func (s *QuestServiceServer) StartEventQuest(ctx context.Context, req *pb.StartEventQuestRequest) (*pb.StartEventQuestResponse, error) {
	log.Printf("[QuestService] StartEventQuest: chapterId=%d questId=%d isBattleOnly=%v", req.EventQuestChapterId, req.QuestId, req.IsBattleOnly)

	userId := currentUserId(ctx, s.store)
	nowMillis := gametime.NowMillis()
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		s.engine.HandleEventQuestStart(user, req.EventQuestChapterId, req.QuestId, req.IsBattleOnly, nowMillis)
	})

	drops := s.engine.BattleDropRewards(req.QuestId)
	pbDrops := make([]*pb.BattleDropReward, len(drops))
	for i, d := range drops {
		pbDrops[i] = &pb.BattleDropReward{
			QuestSceneId:         d.QuestSceneId,
			BattleDropCategoryId: d.BattleDropCategoryId,
			BattleDropEffectId:   1,
		}
	}

	return &pb.StartEventQuestResponse{
		BattleDropReward: pbDrops,
		DiffUserData: buildSelectedQuestDiff(user, []string{
			"IUserStatus",
			"IUserQuest",
			"IUserQuestMission",
			"IUserEventQuestProgressStatus",
		}),
	}, nil
}

func (s *QuestServiceServer) FinishEventQuest(ctx context.Context, req *pb.FinishEventQuestRequest) (*pb.FinishEventQuestResponse, error) {
	log.Printf("[QuestService] FinishEventQuest: chapterId=%d questId=%d isRetired=%v", req.EventQuestChapterId, req.QuestId, req.IsRetired)

	nowMillis := gametime.NowMillis()
	userId := currentUserId(ctx, s.store)
	var outcome questflow.FinishOutcome
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		outcome = s.engine.HandleEventQuestFinish(user, req.EventQuestChapterId, req.QuestId, req.IsRetired, nowMillis)
	})

	return &pb.FinishEventQuestResponse{
		DropReward:                      toProtoRewards(outcome.DropRewards),
		FirstClearReward:                toProtoRewards(outcome.FirstClearRewards),
		MissionClearReward:              toProtoRewards(outcome.MissionClearRewards),
		MissionClearCompleteReward:      toProtoRewards(outcome.MissionClearCompleteRewards),
		AutoOrbitResult:                 []*pb.QuestReward{},
		IsBigWin:                        outcome.IsBigWin,
		BigWinClearedQuestMissionIdList: outcome.BigWinClearedQuestMissionIds,
		UserStatusCampaignReward:        []*pb.QuestReward{},
		DiffUserData: buildSelectedQuestDiff(user, []string{
			"IUserQuest",
			"IUserQuestMission",
			"IUserEventQuestProgressStatus",
			"IUserStatus",
			"IUserGem",
			"IUserCharacter",
			"IUserCostume",
			"IUserCostumeActiveSkill",
			"IUserWeapon",
			"IUserWeaponNote",
			"IUserWeaponStory",
			"IUserCompanion",
			"IUserConsumableItem",
			"IUserMaterial",
			"IUserImportantItem",
		}),
	}, nil
}

func (s *QuestServiceServer) RestartEventQuest(ctx context.Context, req *pb.RestartEventQuestRequest) (*pb.RestartEventQuestResponse, error) {
	log.Printf("[QuestService] RestartEventQuest: chapterId=%d questId=%d", req.EventQuestChapterId, req.QuestId)

	userId := currentUserId(ctx, s.store)
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		s.engine.HandleEventQuestRestart(user, req.EventQuestChapterId, req.QuestId, gametime.NowMillis())
	})

	return &pb.RestartEventQuestResponse{
		BattleDropReward: []*pb.BattleDropReward{},
		DiffUserData: buildSelectedQuestDiff(user, []string{
			"IUserQuest",
			"IUserQuestMission",
			"IUserEventQuestProgressStatus",
		}),
	}, nil
}

func (s *QuestServiceServer) UpdateEventQuestSceneProgress(ctx context.Context, req *pb.UpdateEventQuestSceneProgressRequest) (*pb.UpdateEventQuestSceneProgressResponse, error) {
	log.Printf("[QuestService] UpdateEventQuestSceneProgress: questSceneId=%d", req.QuestSceneId)

	userId := currentUserId(ctx, s.store)
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		s.engine.HandleEventQuestSceneProgress(user, req.QuestSceneId, gametime.NowMillis())
	})

	return &pb.UpdateEventQuestSceneProgressResponse{
		DiffUserData: buildSelectedQuestDiff(user, []string{
			"IUserEventQuestProgressStatus",
			"IUserCharacter",
			"IUserCostume",
			"IUserWeapon",
			"IUserCompanion",
			"IUserConsumableItem",
			"IUserMaterial",
			"IUserImportantItem",
		}),
	}, nil
}

const defaultGuerrillaFreeOpenMinutes = int32(60)

func (s *QuestServiceServer) StartGuerrillaFreeOpen(ctx context.Context, req *emptypb.Empty) (*pb.StartGuerrillaFreeOpenResponse, error) {
	log.Printf("[QuestService] StartGuerrillaFreeOpen")

	userId := currentUserId(ctx, s.store)
	nowMillis := gametime.NowMillis()
	user, _ := s.store.UpdateUser(userId, func(user *store.UserState) {
		user.GuerrillaFreeOpen.StartDatetime = nowMillis
		user.GuerrillaFreeOpen.OpenMinutes = defaultGuerrillaFreeOpenMinutes
		user.GuerrillaFreeOpen.DailyOpenedCount++
		user.GuerrillaFreeOpen.LatestVersion = nowMillis
	})

	return &pb.StartGuerrillaFreeOpenResponse{
		DiffUserData: buildSelectedQuestDiff(user, []string{"IUserEventQuestGuerrillaFreeOpen"}),
	}, nil
}
