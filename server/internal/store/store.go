package store

import (
	"fmt"
	"log"
	"maps"
	"sort"
	"strings"
	"sync"
	"time"

	"lunar-tear/server/internal/model"
)

const (
	defaultUUId   = "default-user"
	defaultUserId = int64(1001)

	starterMissionId          = int32(1)
	starterMainQuestRouteId   = int32(1)
	starterMainQuestSeasonId  = int32(1)
	missionInProgress         = int32(1)
	defaultGiftPossessionType = int32(12) // FREE_GEM
	defaultGiftCount          = int32(300)

	defaultGiftUUIdPrefix = "default-gift"

	defaultRegisteredName = "Un-regist User Name"
	startedProfileName    = "Lunar Tear"

	defaultBirthYear            = int32(2000)
	defaultBirthMonth           = int32(1)
	defaultBackupToken          = "mock-backup-token"
	defaultChargeMoneyThisMonth = int64(0)
)

type Clock func() time.Time

type Option func(*Store)

type Bootstrapper interface {
	ApplyBootstrap(user *UserState, sceneId int32, nowMillis int64)
}

type Store struct {
	mu               sync.RWMutex
	clock            Clock
	bootstrapSceneId int32
	bootstrapper     Bootstrapper
	nextUserId       int64
	users            map[int64]*UserState
	userIdsByUuid    map[string]int64
	sessionToUserId  map[string]int64
	sessions         map[string]SessionState
	gachaCatalog     map[int32]GachaCatalogEntry
}

func WithBootstrap(sceneId int32, bootstrapper Bootstrapper) Option {
	return func(s *Store) {
		s.bootstrapSceneId = sceneId
		s.bootstrapper = bootstrapper
	}
}

type SessionState struct {
	SessionKey string
	UserId     int64
	Uuid       string
	ExpireAt   time.Time
}

type UserState struct {
	UserId              int64
	Uuid                string
	PlayerId            int64
	OsType              int32
	PlatformType        int32
	UserRestrictionType int32
	RegisterDatetime    int64
	GameStartDatetime   int64
	LatestVersion       int64

	BirthYear            int32
	BirthMonth           int32
	BackupToken          string
	ChargeMoneyThisMonth int64

	Setting       UserSettingState
	Status        UserStatusState
	Gem           UserGemState
	Profile       UserProfileState
	Login         UserLoginState
	LoginBonus    UserLoginBonusState
	Tutorial      TutorialProgressState
	MainQuest     MainQuestState
	Battle        BattleState
	Gifts         GiftState
	Gacha         GachaState
	Notifications NotificationState

	Characters          map[int32]CharacterState
	Costumes            map[string]CostumeState
	Weapons             map[string]WeaponState
	Companions          map[string]CompanionState
	Thoughts            map[string]ThoughtState
	DeckCharacters      map[string]DeckCharacterState
	Decks               map[DeckKey]DeckState
	Quests              map[int32]UserQuestState
	QuestMissions       map[QuestMissionKey]UserQuestMissionState
	Missions            map[int32]UserMissionState
	WeaponStories       map[int32]WeaponStoryState
	Gimmick             GimmickState
	CageOrnamentRewards map[int32]CageOrnamentRewardState
	ConsumableItems     map[int32]int32
	Materials           map[int32]int32
	Parts               map[string]PartsState
	ImportantItems      map[int32]int32
	CostumeActiveSkills map[string]CostumeActiveSkillState
	DeckTypeNotes       map[int32]DeckTypeNoteState
	WeaponNotes         map[int32]WeaponNoteState
	DeckSubWeapons      map[string][]string // userDeckCharacterUuid -> ordered sub-weapon UUIDs
	NaviCutInPlayed     map[int32]bool
}

func GrantPossession(user *UserState, possessionType model.PossessionType, possessionId, count int32) {
	switch possessionType {
	case model.PossessionTypeMaterial:
		user.Materials[possessionId] += count
	case model.PossessionTypeConsumableItem:
		user.ConsumableItems[possessionId] += count
	case model.PossessionTypePaidGem:
		user.Gem.PaidGem += count
	case model.PossessionTypeFreeGem:
		user.Gem.FreeGem += count
	case model.PossessionTypeImportantItem:
		user.ImportantItems[possessionId] += count
	default:
		log.Printf("[GrantPossession] unhandled type=%d id=%d count=%d", possessionType, possessionId, count)
	}
}

func EnsureDefaultDeck(user *UserState, nowMillis int64) {
	if len(user.Costumes) == 0 || len(user.Decks) > 0 {
		return
	}

	costumeUuid := firstSortedKey(user.Costumes)
	weaponUuid := firstSortedKey(user.Weapons)
	companionUuid := firstSortedKey(user.Companions)

	dcUuid := "default-deck-character-0001"
	user.DeckCharacters[dcUuid] = DeckCharacterState{
		UserDeckCharacterUuid: dcUuid,
		UserCostumeUuid:       costumeUuid,
		MainUserWeaponUuid:    weaponUuid,
		UserCompanionUuid:     companionUuid,
		Power:                 100,
		LatestVersion:         nowMillis,
	}
	user.Decks[DeckKey{DeckType: 1, UserDeckNumber: 1}] = DeckState{
		DeckType:                1,
		UserDeckNumber:          1,
		UserDeckCharacterUuid01: dcUuid,
		Name:                    "Deck 1",
		Power:                   100,
		LatestVersion:           nowMillis,
	}

	if _, exists := user.DeckTypeNotes[int32(1)]; !exists {
		user.DeckTypeNotes[int32(1)] = DeckTypeNoteState{
			DeckType:      1,
			MaxDeckPower:  100,
			LatestVersion: nowMillis,
		}
	}
}

func firstSortedKey[V any](m map[string]V) string {
	if len(m) == 0 {
		return ""
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys[0]
}

type WeaponStoryState struct {
	WeaponId              int32
	ReleasedMaxStoryIndex int32
	LatestVersion         int64
}

type WeaponNoteState struct {
	WeaponId                 int32
	MaxLevel                 int32
	MaxLimitBreakCount       int32
	FirstAcquisitionDatetime int64
	LatestVersion            int64
}

type UserSettingState struct {
	IsNotifyPurchaseAlert bool
	LatestVersion         int64
}

type UserStatusState struct {
	Level                 int32
	Exp                   int32
	StaminaMilliValue     int32
	StaminaUpdateDatetime int64
	LatestVersion         int64
}

type UserGemState struct {
	PaidGem int32
	FreeGem int32
}

type UserProfileState struct {
	Name                            string
	NameUpdateDatetime              int64
	Message                         string
	MessageUpdateDatetime           int64
	FavoriteCostumeId               int32
	FavoriteCostumeIdUpdateDatetime int64
	LatestVersion                   int64
}

type UserLoginState struct {
	TotalLoginCount           int32
	ContinualLoginCount       int32
	MaxContinualLoginCount    int32
	LastLoginDatetime         int64
	LastComebackLoginDatetime int64
	LatestVersion             int64
}

type UserLoginBonusState struct {
	LoginBonusId                int32
	CurrentPageNumber           int32
	CurrentStampNumber          int32
	LatestRewardReceiveDatetime int64
	LatestVersion               int64
}

type CharacterState struct {
	CharacterId   int32
	Level         int32
	Exp           int32
	LatestVersion int64
}

type CostumeState struct {
	UserCostumeUuid     string
	CostumeId           int32
	LimitBreakCount     int32
	Level               int32
	Exp                 int32
	HeadupDisplayViewId int32
	AcquisitionDatetime int64
	AwakenCount         int32
	LatestVersion       int64
}

type WeaponState struct {
	UserWeaponUuid      string
	WeaponId            int32
	Level               int32
	Exp                 int32
	LimitBreakCount     int32
	IsProtected         bool
	AcquisitionDatetime int64
	LatestVersion       int64
}

type CompanionState struct {
	UserCompanionUuid   string
	CompanionId         int32
	HeadupDisplayViewId int32
	Level               int32
	AcquisitionDatetime int64
	LatestVersion       int64
}

type ThoughtState struct {
	UserThoughtUuid     string
	ThoughtId           int32
	AcquisitionDatetime int64
	LatestVersion       int64
}

type DeckCharacterState struct {
	UserDeckCharacterUuid string
	UserCostumeUuid       string
	MainUserWeaponUuid    string
	UserCompanionUuid     string
	Power                 int32
	UserThoughtUuid       string
	LatestVersion         int64
}

type DeckKey struct {
	DeckType       int32
	UserDeckNumber int32
}

type DeckState struct {
	DeckType                int32
	UserDeckNumber          int32
	UserDeckCharacterUuid01 string
	UserDeckCharacterUuid02 string
	UserDeckCharacterUuid03 string
	Name                    string
	Power                   int32
	LatestVersion           int64
}

type DeckCharacterInput struct {
	UserCostumeUuid    string
	MainUserWeaponUuid string
	SubWeaponUuids     []string
	UserCompanionUuid  string
	UserThoughtUuid    string
}

type CostumeActiveSkillState struct {
	UserCostumeUuid     string
	Level               int32
	AcquisitionDatetime int64
	LatestVersion       int64
}

type DeckTypeNoteState struct {
	DeckType      int32
	MaxDeckPower  int32
	LatestVersion int64
}

type TutorialProgressState struct {
	TutorialType  int32
	ProgressPhase int32
	ChoiceId      int32
	LatestVersion int64
}

type MainQuestState struct {
	CurrentQuestFlowType     int32
	CurrentMainQuestRouteId  int32
	CurrentQuestSceneId      int32
	HeadQuestSceneId         int32
	IsReachedLastQuestScene  bool
	ProgressQuestSceneId     int32
	ProgressHeadQuestSceneId int32
	ProgressQuestFlowType    int32
	MainQuestSeasonId        int32
	LatestVersion            int64
}

type BattleState struct {
	IsActive              bool
	StartCount            int32
	FinishCount           int32
	LastStartedAt         int64
	LastFinishedAt        int64
	LastUserPartyCount    int32
	LastNpcPartyCount     int32
	LastBattleBinarySize  int32
	LastElapsedFrameCount int64
}

type UserQuestStateType int32

const (
	UserQuestStateTypeUnknown UserQuestStateType = 0
	UserQuestStateTypeActive  UserQuestStateType = 1
	UserQuestStateTypeCleared UserQuestStateType = 2
)

type UserQuestState struct {
	QuestId             int32
	QuestStateType      UserQuestStateType
	IsBattleOnly        bool
	LatestStartDatetime int64
	ClearCount          int32
	DailyClearCount     int32
	LastClearDatetime   int64
	ShortestClearFrames int32
	IsRewardGranted     bool
	LatestVersion       int64
}

type QuestMissionKey struct {
	QuestId        int32
	QuestMissionId int32
}

type UserQuestMissionState struct {
	QuestId             int32
	QuestMissionId      int32
	ProgressValue       int32
	IsClear             bool
	LatestClearDatetime int64
	LatestVersion       int64
}

type UserMissionState struct {
	MissionId                 int32
	StartDatetime             int64
	ProgressValue             int32
	MissionProgressStatusType int32
	ClearDatetime             int64
	LatestVersion             int64
}

type GimmickSequenceKey struct {
	GimmickSequenceScheduleId int32
	GimmickSequenceId         int32
}

type GimmickKey struct {
	GimmickSequenceScheduleId int32
	GimmickSequenceId         int32
	GimmickId                 int32
}

type GimmickOrnamentKey struct {
	GimmickSequenceScheduleId int32
	GimmickSequenceId         int32
	GimmickId                 int32
	GimmickOrnamentIndex      int32
}

type GimmickState struct {
	Progress         map[GimmickKey]GimmickProgressState
	OrnamentProgress map[GimmickOrnamentKey]GimmickOrnamentProgressState
	Sequences        map[GimmickSequenceKey]GimmickSequenceState
	Unlocks          map[GimmickKey]GimmickUnlockState
}

type GimmickProgressState struct {
	Key              GimmickKey
	IsGimmickCleared bool
	StartDatetime    int64
	LatestVersion    int64
}

type GimmickOrnamentProgressState struct {
	Key              GimmickOrnamentKey
	ProgressValueBit int32
	BaseDatetime     int64
	LatestVersion    int64
}

type GimmickSequenceState struct {
	Key                      GimmickSequenceKey
	IsGimmickSequenceCleared bool
	ClearDatetime            int64
	LatestVersion            int64
}

type GimmickUnlockState struct {
	Key           GimmickKey
	IsUnlocked    bool
	LatestVersion int64
}

type CageOrnamentRewardState struct {
	CageOrnamentId int32
	LatestVersion  int64
}

type PartsState struct {
	UserPartsUuid       string
	PartsId             int32
	Level               int32
	AcquisitionDatetime int64
	LatestVersion       int64
}

type NotificationState struct {
	GiftNotReceiveCount       int32
	FriendRequestReceiveCount int32
	IsExistUnreadInformation  bool
}

type GiftState struct {
	NotReceived []NotReceivedGiftState
	Received    []ReceivedGiftState
}

type GiftCommonState struct {
	PossessionType        int32
	PossessionId          int32
	Count                 int32
	GrantDatetime         int64
	DescriptionGiftTextId int32
	EquipmentData         []byte
}

type NotReceivedGiftState struct {
	GiftCommon         GiftCommonState
	ExpirationDatetime int64
	UserGiftUuid       string
}

type ReceivedGiftState struct {
	GiftCommon       GiftCommonState
	ReceivedDatetime int64
}

type GachaState struct {
	RewardAvailable        bool
	TodaysCurrentDrawCount int32
	DailyMaxCount          int32
	ConvertedGachaMedal    ConvertedGachaMedalState
}

type ConvertedGachaMedalState struct {
	ConvertedMedalPossession []ConsumableItemState
	ObtainPossession         *ConsumableItemState
}

type ConsumableItemState struct {
	ConsumableItemId int32
	Count            int32
}

type GachaCatalogEntry struct {
	GachaId                    int32
	GachaLabelType             int32
	GachaModeType              int32
	GachaAutoResetType         int32
	GachaAutoResetPeriod       int32
	NextAutoResetDatetime      int64
	IsUserGachaUnlock          bool
	StartDatetime              int64
	EndDatetime                int64
	RelatedMainQuestChapterId  int32
	RelatedEventQuestChapterId int32
	PromotionMovieAssetId      int32
	GachaMedalId               int32
	GachaDecorationType        int32
	SortOrder                  int32
	IsInactive                 bool
	InformationId              int32
	GachaMode                  []byte
	BannerAssetName            string
	StepupGroupId              int32
}

func New(clock Clock, options ...Option) *Store {
	if clock == nil {
		clock = time.Now
	}

	store := &Store{
		clock:           clock,
		nextUserId:      defaultUserId,
		users:           make(map[int64]*UserState),
		userIdsByUuid:   make(map[string]int64),
		sessionToUserId: make(map[string]int64),
		sessions:        make(map[string]SessionState),
		gachaCatalog:    make(map[int32]GachaCatalogEntry),
	}
	for _, option := range options {
		option(store)
	}
	return store
}

func (s *Store) EnsureUser(uuid string) UserState {
	s.mu.Lock()
	defer s.mu.Unlock()

	return s.getOrCreateLocked(normalizeUUId(uuid)).clone()
}

func (s *Store) CreateSession(uuid string, ttl time.Duration) (UserState, SessionState) {
	s.mu.Lock()
	defer s.mu.Unlock()

	user := s.getOrCreateLocked(normalizeUUId(uuid))
	now := s.clock()
	session := SessionState{
		SessionKey: fmt.Sprintf("session_%d_%d", user.UserId, now.UnixNano()),
		UserId:     user.UserId,
		Uuid:       user.Uuid,
		ExpireAt:   now.Add(ttl),
	}

	s.sessionToUserId[session.SessionKey] = user.UserId
	s.sessions[session.SessionKey] = session

	return user.clone(), session
}

func (s *Store) ResolveUserId(sessionKey string) (int64, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	userId, ok := s.sessionToUserId[sessionKey]
	return userId, ok
}

func (s *Store) SnapshotUser(userId int64) (UserState, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	user, ok := s.users[userId]
	if !ok {
		return UserState{}, false
	}
	return user.clone(), true
}

func (s *Store) UpdateUser(userId int64, mutate func(*UserState)) (UserState, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	user, ok := s.users[userId]
	if !ok {
		return UserState{}, false
	}
	mutate(user)
	return user.clone(), true
}

func (s *Store) DefaultUserId() int64 {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if _, ok := s.users[defaultUserId]; ok {
		return defaultUserId
	}
	if len(s.users) == 0 {
		return defaultUserId
	}

	var minUserId int64
	for userId := range s.users {
		if minUserId == 0 || userId < minUserId {
			minUserId = userId
		}
	}
	return minUserId
}

func (s *Store) SnapshotGachaCatalog() []GachaCatalogEntry {
	s.mu.RLock()
	defer s.mu.RUnlock()

	out := make([]GachaCatalogEntry, 0, len(s.gachaCatalog))
	for _, entry := range s.gachaCatalog {
		out = append(out, cloneGachaCatalogEntry(entry))
	}
	return out
}

func (s *Store) ReplaceGachaCatalog(entries []GachaCatalogEntry) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.gachaCatalog = make(map[int32]GachaCatalogEntry, len(entries))
	for _, entry := range entries {
		s.gachaCatalog[entry.GachaId] = cloneGachaCatalogEntry(entry)
	}
}

func normalizeUUId(uuid string) string {
	uuid = strings.TrimSpace(uuid)
	if uuid == "" {
		return defaultUUId
	}
	return uuid
}

func (s *Store) getOrCreateLocked(uuid string) *UserState {
	if userId, ok := s.userIdsByUuid[uuid]; ok {
		return s.users[userId]
	}

	userId := s.nextUserId
	s.nextUserId++

	user := seedUserState(userId, uuid, s.clock().UnixMilli(), s.bootstrapSceneId, s.bootstrapper)
	s.users[userId] = user
	s.userIdsByUuid[uuid] = userId
	return user
}

func seedUserState(userId int64, uuid string, nowMillis int64, sceneId int32, bootstrapper Bootstrapper) *UserState {
	user := &UserState{
		UserId:               userId,
		Uuid:                 uuid,
		PlayerId:             userId,
		OsType:               2,
		PlatformType:         2,
		UserRestrictionType:  0,
		RegisterDatetime:     nowMillis,
		GameStartDatetime:    nowMillis,
		LatestVersion:        0,
		BirthYear:            defaultBirthYear,
		BirthMonth:           defaultBirthMonth,
		BackupToken:          defaultBackupToken,
		ChargeMoneyThisMonth: defaultChargeMoneyThisMonth,
		Setting: UserSettingState{
			IsNotifyPurchaseAlert: false,
			LatestVersion:         0,
		},
		Status: UserStatusState{
			Level:                 1,
			Exp:                   0,
			StaminaMilliValue:     60000,
			StaminaUpdateDatetime: nowMillis,
			LatestVersion:         0,
		},
		Gem: UserGemState{
			PaidGem: 10000,
			FreeGem: 10000,
		},
		Profile: UserProfileState{
			Name:                            defaultRegisteredName,
			NameUpdateDatetime:              nowMillis,
			Message:                         "",
			MessageUpdateDatetime:           nowMillis,
			FavoriteCostumeId:               0,
			FavoriteCostumeIdUpdateDatetime: nowMillis,
			LatestVersion:                   0,
		},
		Login: UserLoginState{
			TotalLoginCount:           1,
			ContinualLoginCount:       1,
			MaxContinualLoginCount:    1,
			LastLoginDatetime:         nowMillis,
			LastComebackLoginDatetime: 0,
			LatestVersion:             0,
		},
		LoginBonus: UserLoginBonusState{
			LoginBonusId:                1,
			CurrentPageNumber:           1,
			CurrentStampNumber:          0,
			LatestRewardReceiveDatetime: 0,
			LatestVersion:               0,
		},
		Tutorial: TutorialProgressState{
			TutorialType:  1,
			ProgressPhase: 0,
			ChoiceId:      0,
			LatestVersion: 0,
		},
		Battle: BattleState{
			IsActive:              false,
			StartCount:            0,
			FinishCount:           0,
			LastStartedAt:         0,
			LastFinishedAt:        0,
			LastUserPartyCount:    0,
			LastNpcPartyCount:     0,
			LastBattleBinarySize:  0,
			LastElapsedFrameCount: 0,
		},
		Gifts: GiftState{
			NotReceived: []NotReceivedGiftState{
				{
					GiftCommon: GiftCommonState{
						PossessionType:        defaultGiftPossessionType,
						PossessionId:          0,
						Count:                 defaultGiftCount,
						GrantDatetime:         nowMillis,
						DescriptionGiftTextId: 0,
						EquipmentData:         nil,
					},
					ExpirationDatetime: nowMillis + int64((7*24*time.Hour)/time.Millisecond),
					UserGiftUuid:       fmt.Sprintf("%s-%d-1", defaultGiftUUIdPrefix, userId),
				},
			},
			Received: []ReceivedGiftState{},
		},
		Gacha: GachaState{
			RewardAvailable:        false,
			TodaysCurrentDrawCount: 0,
			DailyMaxCount:          0,
			ConvertedGachaMedal: ConvertedGachaMedalState{
				ConvertedMedalPossession: []ConsumableItemState{},
				ObtainPossession:         nil,
			},
		},
		MainQuest: MainQuestState{
			CurrentQuestFlowType:     0,
			CurrentMainQuestRouteId:  starterMainQuestRouteId,
			CurrentQuestSceneId:      0,
			HeadQuestSceneId:         0,
			IsReachedLastQuestScene:  false,
			ProgressQuestSceneId:     0,
			ProgressHeadQuestSceneId: 0,
			ProgressQuestFlowType:    0,
			MainQuestSeasonId:        starterMainQuestSeasonId,
			LatestVersion:            0,
		},
		Notifications: NotificationState{
			GiftNotReceiveCount:       1,
			FriendRequestReceiveCount: 0,
			IsExistUnreadInformation:  false,
		},
		Characters: make(map[int32]CharacterState),
		Costumes:   make(map[string]CostumeState),
		Weapons:    make(map[string]WeaponState),
		Companions: make(map[string]CompanionState),
		DeckCharacters: make(map[string]DeckCharacterState),
		Decks:          make(map[DeckKey]DeckState),
		DeckSubWeapons: make(map[string][]string),
		Quests:         make(map[int32]UserQuestState),
		QuestMissions:  make(map[QuestMissionKey]UserQuestMissionState),
		WeaponStories:  make(map[int32]WeaponStoryState),
		Missions: map[int32]UserMissionState{
			starterMissionId: {
				MissionId:                 starterMissionId,
				StartDatetime:             nowMillis,
				ProgressValue:             0,
				MissionProgressStatusType: missionInProgress,
				ClearDatetime:             0,
				LatestVersion:             0,
			},
		},
		Gimmick: GimmickState{
			Progress:         make(map[GimmickKey]GimmickProgressState),
			OrnamentProgress: make(map[GimmickOrnamentKey]GimmickOrnamentProgressState),
			Sequences:        make(map[GimmickSequenceKey]GimmickSequenceState),
			Unlocks:          make(map[GimmickKey]GimmickUnlockState),
		},
		CageOrnamentRewards: make(map[int32]CageOrnamentRewardState),
		ConsumableItems:     make(map[int32]int32),
		Materials:           make(map[int32]int32),
		Thoughts:            make(map[string]ThoughtState),
		Parts:               make(map[string]PartsState),
		ImportantItems:      make(map[int32]int32),
		CostumeActiveSkills: make(map[string]CostumeActiveSkillState),
		DeckTypeNotes:       make(map[int32]DeckTypeNoteState),
		WeaponNotes:         make(map[int32]WeaponNoteState),
		NaviCutInPlayed:     make(map[int32]bool),
	}
	if bootstrapper != nil {
		bootstrapper.ApplyBootstrap(user, sceneId, nowMillis)
	}
	EnsureDefaultDeck(user, nowMillis)
	return user
}

func (u UserState) clone() UserState {
	out := u
	out.Characters = maps.Clone(u.Characters)
	out.Costumes = maps.Clone(u.Costumes)
	out.Weapons = maps.Clone(u.Weapons)
	out.Companions = maps.Clone(u.Companions)
	out.Thoughts = maps.Clone(u.Thoughts)
	out.DeckCharacters = maps.Clone(u.DeckCharacters)
	out.DeckSubWeapons = maps.Clone(u.DeckSubWeapons)
	out.Decks = maps.Clone(u.Decks)
	out.Quests = maps.Clone(u.Quests)
	out.QuestMissions = maps.Clone(u.QuestMissions)
	out.WeaponStories = maps.Clone(u.WeaponStories)
	out.Missions = maps.Clone(u.Missions)
	out.Gimmick = GimmickState{
		Progress:         maps.Clone(u.Gimmick.Progress),
		OrnamentProgress: maps.Clone(u.Gimmick.OrnamentProgress),
		Sequences:        maps.Clone(u.Gimmick.Sequences),
		Unlocks:          maps.Clone(u.Gimmick.Unlocks),
	}
	out.CageOrnamentRewards = maps.Clone(u.CageOrnamentRewards)
	out.ConsumableItems = maps.Clone(u.ConsumableItems)
	out.Materials = maps.Clone(u.Materials)
	out.Parts = maps.Clone(u.Parts)
	out.ImportantItems = maps.Clone(u.ImportantItems)
	out.CostumeActiveSkills = maps.Clone(u.CostumeActiveSkills)
	out.DeckTypeNotes = maps.Clone(u.DeckTypeNotes)
	out.WeaponNotes = maps.Clone(u.WeaponNotes)
	out.NaviCutInPlayed = maps.Clone(u.NaviCutInPlayed)
	out.Gacha = GachaState{
		RewardAvailable:        u.Gacha.RewardAvailable,
		TodaysCurrentDrawCount: u.Gacha.TodaysCurrentDrawCount,
		DailyMaxCount:          u.Gacha.DailyMaxCount,
		ConvertedGachaMedal: ConvertedGachaMedalState{
			ConvertedMedalPossession: append([]ConsumableItemState(nil), u.Gacha.ConvertedGachaMedal.ConvertedMedalPossession...),
			ObtainPossession:         cloneConsumableItemPtr(u.Gacha.ConvertedGachaMedal.ObtainPossession),
		},
	}
	out.Gifts = GiftState{
		NotReceived: cloneNotReceivedGifts(u.Gifts.NotReceived),
		Received:    cloneReceivedGifts(u.Gifts.Received),
	}
	out.Battle = BattleState{
		IsActive:              u.Battle.IsActive,
		StartCount:            u.Battle.StartCount,
		FinishCount:           u.Battle.FinishCount,
		LastStartedAt:         u.Battle.LastStartedAt,
		LastFinishedAt:        u.Battle.LastFinishedAt,
		LastUserPartyCount:    u.Battle.LastUserPartyCount,
		LastNpcPartyCount:     u.Battle.LastNpcPartyCount,
		LastBattleBinarySize:  u.Battle.LastBattleBinarySize,
		LastElapsedFrameCount: u.Battle.LastElapsedFrameCount,
	}
	return out
}

func cloneGachaCatalogEntry(entry GachaCatalogEntry) GachaCatalogEntry {
	out := entry
	out.GachaMode = append([]byte(nil), entry.GachaMode...)
	return out
}

func cloneConsumableItemPtr(item *ConsumableItemState) *ConsumableItemState {
	if item == nil {
		return nil
	}
	out := *item
	return &out
}

func cloneNotReceivedGifts(gifts []NotReceivedGiftState) []NotReceivedGiftState {
	out := make([]NotReceivedGiftState, len(gifts))
	for i, gift := range gifts {
		out[i] = NotReceivedGiftState{
			GiftCommon: GiftCommonState{
				PossessionType:        gift.GiftCommon.PossessionType,
				PossessionId:          gift.GiftCommon.PossessionId,
				Count:                 gift.GiftCommon.Count,
				GrantDatetime:         gift.GiftCommon.GrantDatetime,
				DescriptionGiftTextId: gift.GiftCommon.DescriptionGiftTextId,
				EquipmentData:         append([]byte(nil), gift.GiftCommon.EquipmentData...),
			},
			ExpirationDatetime: gift.ExpirationDatetime,
			UserGiftUuid:       gift.UserGiftUuid,
		}
	}
	return out
}

func cloneReceivedGifts(gifts []ReceivedGiftState) []ReceivedGiftState {
	out := make([]ReceivedGiftState, len(gifts))
	for i, gift := range gifts {
		out[i] = ReceivedGiftState{
			GiftCommon: GiftCommonState{
				PossessionType:        gift.GiftCommon.PossessionType,
				PossessionId:          gift.GiftCommon.PossessionId,
				Count:                 gift.GiftCommon.Count,
				GrantDatetime:         gift.GiftCommon.GrantDatetime,
				DescriptionGiftTextId: gift.GiftCommon.DescriptionGiftTextId,
				EquipmentData:         append([]byte(nil), gift.GiftCommon.EquipmentData...),
			},
			ReceivedDatetime: gift.ReceivedDatetime,
		}
	}
	return out
}

func ApplyDeckReplacement(user *UserState, deckType, userDeckNumber int32, slots []DeckCharacterInput, nowMillis int64) {
	deckKey := DeckKey{DeckType: deckType, UserDeckNumber: userDeckNumber}
	deck := user.Decks[deckKey]
	deck.DeckType = deckType
	deck.UserDeckNumber = userDeckNumber
	if deck.Name == "" {
		deck.Name = fmt.Sprintf("Deck %d", userDeckNumber)
	}
	if deck.Power == 0 {
		deck.Power = 100
	}

	uuids := []*string{&deck.UserDeckCharacterUuid01, &deck.UserDeckCharacterUuid02, &deck.UserDeckCharacterUuid03}
	for i, uuid := range uuids {
		if i >= len(slots) || slots[i].UserCostumeUuid == "" {
			*uuid = ""
			continue
		}
		slot := slots[i]
		dcUuid := fmt.Sprintf("deck-%d-%d-%d", deckType, userDeckNumber, i+1)
		dc := user.DeckCharacters[dcUuid]
		dc.UserDeckCharacterUuid = dcUuid
		dc.UserCostumeUuid = slot.UserCostumeUuid
		dc.MainUserWeaponUuid = slot.MainUserWeaponUuid
		dc.UserCompanionUuid = slot.UserCompanionUuid
		dc.UserThoughtUuid = slot.UserThoughtUuid
		dc.LatestVersion = nowMillis
		user.DeckCharacters[dcUuid] = dc
		user.DeckSubWeapons[dcUuid] = slot.SubWeaponUuids
		*uuid = dcUuid
	}

	deck.LatestVersion = nowMillis
	user.Decks[deckKey] = deck
}
