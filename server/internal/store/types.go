package store

import (
	"fmt"
	"strconv"
	"strings"
	"time"

	"lunar-tear/server/internal/model"
)

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
	Tutorials     map[int32]TutorialProgressState
	MainQuest     MainQuestState
	EventQuest    EventQuestState
	Battle        BattleState
	Gifts         GiftState
	Gacha         GachaState
	Notifications NotificationState

	Characters            map[int32]CharacterState
	Costumes              map[string]CostumeState
	Weapons               map[string]WeaponState
	Companions            map[string]CompanionState
	Thoughts              map[string]ThoughtState
	DeckCharacters        map[string]DeckCharacterState
	Decks                 map[DeckKey]DeckState
	Quests                map[int32]UserQuestState
	QuestMissions         map[QuestMissionKey]UserQuestMissionState
	Missions              map[int32]UserMissionState
	WeaponStories         map[int32]WeaponStoryState
	Gimmick               GimmickState
	CageOrnamentRewards   map[int32]CageOrnamentRewardState
	ConsumableItems       map[int32]int32
	Materials             map[int32]int32
	Parts                 map[string]PartsState
	ImportantItems        map[int32]int32
	CostumeActiveSkills   map[string]CostumeActiveSkillState
	WeaponSkills          map[string][]WeaponSkillState   // key: userWeaponUuid
	WeaponAbilities       map[string][]WeaponAbilityState // key: userWeaponUuid
	DeckTypeNotes         map[model.DeckType]DeckTypeNoteState
	WeaponNotes           map[int32]WeaponNoteState
	DeckSubWeapons        map[string][]string
	NaviCutInPlayed       map[int32]bool
	ViewedMovies          map[int32]int64
	DrawnOmikuji          map[int32]int64
	PremiumItems          map[int32]int64
	DokanConfirmed        map[int32]bool
	PortalCageStatus      PortalCageStatusState
	GuerrillaFreeOpen     GuerrillaFreeOpenState
	ShopItems             map[int32]UserShopItemState
	ShopReplaceable       UserShopReplaceableState
	ShopReplaceableLineup map[int32]UserShopReplaceableLineupState

	Explore       ExploreState
	ExploreScores map[int32]ExploreScoreState
}

type ExploreState struct {
	IsUseExploreTicket bool
	PlayingExploreId   int32
	LatestPlayDatetime int64
	LatestVersion      int64
}

type ExploreScoreState struct {
	ExploreId              int32
	MaxScore               int32
	MaxScoreUpdateDatetime int64
	LatestVersion          int64
}

type GuerrillaFreeOpenState struct {
	StartDatetime    int64
	OpenMinutes      int32
	DailyOpenedCount int32
	LatestVersion    int64
}

type PortalCageStatusState struct {
	IsCurrentProgress     bool
	DropItemStartDatetime int64
	CurrentDropItemCount  int32
	LatestVersion         int64
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
	DeckType       model.DeckType
	UserDeckNumber int32
}

func (k DeckKey) MarshalText() ([]byte, error) {
	return fmt.Appendf(nil, "%d:%d", k.DeckType, k.UserDeckNumber), nil
}

func (k *DeckKey) UnmarshalText(text []byte) error {
	parts := strings.Split(string(text), ":")
	if len(parts) != 2 {
		return fmt.Errorf("invalid DeckKey: %s", text)
	}
	a, err := strconv.ParseInt(parts[0], 10, 32)
	if err != nil {
		return err
	}
	b, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		return err
	}
	k.DeckType = model.DeckType(a)
	k.UserDeckNumber = int32(b)
	return nil
}

type DeckState struct {
	DeckType                model.DeckType
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

type WeaponSkillState struct {
	UserWeaponUuid string
	SlotNumber     int32
	Level          int32
}

type WeaponAbilityState struct {
	UserWeaponUuid string
	SlotNumber     int32
	Level          int32
}

type DeckTypeNoteState struct {
	DeckType      model.DeckType
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

type EventQuestState struct {
	CurrentEventQuestChapterId int32
	CurrentQuestId             int32
	CurrentQuestSceneId        int32
	HeadQuestSceneId           int32
	LatestVersion              int64
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

type UserQuestState struct {
	QuestId             int32
	QuestStateType      model.UserQuestStateType
	IsBattleOnly        bool
	UserDeckNumber      int32
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

func (k QuestMissionKey) MarshalText() ([]byte, error) {
	return fmt.Appendf(nil, "%d:%d", k.QuestId, k.QuestMissionId), nil
}

func (k *QuestMissionKey) UnmarshalText(text []byte) error {
	parts := strings.Split(string(text), ":")
	if len(parts) != 2 {
		return fmt.Errorf("invalid QuestMissionKey: %s", text)
	}
	a, err := strconv.ParseInt(parts[0], 10, 32)
	if err != nil {
		return err
	}
	b, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		return err
	}
	k.QuestId = int32(a)
	k.QuestMissionId = int32(b)
	return nil
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

type GimmickSequenceKey struct {
	GimmickSequenceScheduleId int32
	GimmickSequenceId         int32
}

func (k GimmickSequenceKey) MarshalText() ([]byte, error) {
	return fmt.Appendf(nil, "%d:%d", k.GimmickSequenceScheduleId, k.GimmickSequenceId), nil
}

func (k *GimmickSequenceKey) UnmarshalText(text []byte) error {
	parts := strings.Split(string(text), ":")
	if len(parts) != 2 {
		return fmt.Errorf("invalid GimmickSequenceKey: %s", text)
	}
	a, err := strconv.ParseInt(parts[0], 10, 32)
	if err != nil {
		return err
	}
	b, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		return err
	}
	k.GimmickSequenceScheduleId = int32(a)
	k.GimmickSequenceId = int32(b)
	return nil
}

type GimmickKey struct {
	GimmickSequenceScheduleId int32
	GimmickSequenceId         int32
	GimmickId                 int32
}

func (k GimmickKey) MarshalText() ([]byte, error) {
	return fmt.Appendf(nil, "%d:%d:%d", k.GimmickSequenceScheduleId, k.GimmickSequenceId, k.GimmickId), nil
}

func (k *GimmickKey) UnmarshalText(text []byte) error {
	parts := strings.Split(string(text), ":")
	if len(parts) != 3 {
		return fmt.Errorf("invalid GimmickKey: %s", text)
	}
	a, err := strconv.ParseInt(parts[0], 10, 32)
	if err != nil {
		return err
	}
	b, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		return err
	}
	c, err := strconv.ParseInt(parts[2], 10, 32)
	if err != nil {
		return err
	}
	k.GimmickSequenceScheduleId = int32(a)
	k.GimmickSequenceId = int32(b)
	k.GimmickId = int32(c)
	return nil
}

type GimmickOrnamentKey struct {
	GimmickSequenceScheduleId int32
	GimmickSequenceId         int32
	GimmickId                 int32
	GimmickOrnamentIndex      int32
}

func (k GimmickOrnamentKey) MarshalText() ([]byte, error) {
	return fmt.Appendf(nil, "%d:%d:%d:%d", k.GimmickSequenceScheduleId, k.GimmickSequenceId, k.GimmickId, k.GimmickOrnamentIndex), nil
}

func (k *GimmickOrnamentKey) UnmarshalText(text []byte) error {
	parts := strings.Split(string(text), ":")
	if len(parts) != 4 {
		return fmt.Errorf("invalid GimmickOrnamentKey: %s", text)
	}
	a, err := strconv.ParseInt(parts[0], 10, 32)
	if err != nil {
		return err
	}
	b, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		return err
	}
	c, err := strconv.ParseInt(parts[2], 10, 32)
	if err != nil {
		return err
	}
	d, err := strconv.ParseInt(parts[3], 10, 32)
	if err != nil {
		return err
	}
	k.GimmickSequenceScheduleId = int32(a)
	k.GimmickSequenceId = int32(b)
	k.GimmickId = int32(c)
	k.GimmickOrnamentIndex = int32(d)
	return nil
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

type UserShopItemState struct {
	ShopItemId                       int32
	BoughtCount                      int32
	LatestBoughtCountChangedDatetime int64
	LatestVersion                    int64
}

type UserShopReplaceableState struct {
	LineupUpdateCount          int32
	LatestLineupUpdateDatetime int64
	LatestVersion              int64
}

type UserShopReplaceableLineupState struct {
	SlotNumber    int32
	ShopItemId    int32
	LatestVersion int64
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
