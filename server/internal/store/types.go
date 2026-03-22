package store

import (
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
	DeckSubWeapons      map[string][]string
	NaviCutInPlayed     map[int32]bool
	DokanConfirmed      map[int32]bool
	PortalCageStatus    PortalCageStatusState
	GuerrillaFreeOpen   GuerrillaFreeOpenState
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
