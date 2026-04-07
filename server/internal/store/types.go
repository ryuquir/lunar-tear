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
	ExtraQuest    ExtraQuestState
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
	PartsGroupNotes       map[int32]PartsGroupNoteState
	PartsPresets          map[int32]PartsPresetState
	ImportantItems        map[int32]int32
	CostumeActiveSkills   map[string]CostumeActiveSkillState
	WeaponSkills          map[string][]WeaponSkillState   // key: userWeaponUuid
	WeaponAbilities       map[string][]WeaponAbilityState // key: userWeaponUuid
	DeckTypeNotes         map[model.DeckType]DeckTypeNoteState
	WeaponNotes           map[int32]WeaponNoteState
	DeckSubWeapons        map[string][]string
	DeckParts             map[string][]string
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

	CharacterBoards         map[int32]CharacterBoardState
	CharacterBoardAbilities map[CharacterBoardAbilityKey]CharacterBoardAbilityState
	CharacterBoardStatusUps map[CharacterBoardStatusUpKey]CharacterBoardStatusUpState

	CostumeAwakenStatusUps map[CostumeAwakenStatusKey]CostumeAwakenStatusUpState
	AutoSaleSettings       map[int32]AutoSaleSettingState
	CharacterRebirths      map[int32]CharacterRebirthState
}

func (u *UserState) EnsureMaps() {
	if u.Tutorials == nil {
		u.Tutorials = make(map[int32]TutorialProgressState)
	}
	if u.Characters == nil {
		u.Characters = make(map[int32]CharacterState)
	}
	if u.Costumes == nil {
		u.Costumes = make(map[string]CostumeState)
	}
	if u.Weapons == nil {
		u.Weapons = make(map[string]WeaponState)
	}
	if u.Companions == nil {
		u.Companions = make(map[string]CompanionState)
	}
	if u.Thoughts == nil {
		u.Thoughts = make(map[string]ThoughtState)
	}
	if u.DeckCharacters == nil {
		u.DeckCharacters = make(map[string]DeckCharacterState)
	}
	if u.Decks == nil {
		u.Decks = make(map[DeckKey]DeckState)
	}
	if u.DeckSubWeapons == nil {
		u.DeckSubWeapons = make(map[string][]string)
	}
	if u.DeckParts == nil {
		u.DeckParts = make(map[string][]string)
	}
	if u.Quests == nil {
		u.Quests = make(map[int32]UserQuestState)
	}
	if u.QuestMissions == nil {
		u.QuestMissions = make(map[QuestMissionKey]UserQuestMissionState)
	}
	if u.Missions == nil {
		u.Missions = make(map[int32]UserMissionState)
	}
	if u.WeaponStories == nil {
		u.WeaponStories = make(map[int32]WeaponStoryState)
	}
	if u.CageOrnamentRewards == nil {
		u.CageOrnamentRewards = make(map[int32]CageOrnamentRewardState)
	}
	if u.ConsumableItems == nil {
		u.ConsumableItems = make(map[int32]int32)
	}
	if u.Materials == nil {
		u.Materials = make(map[int32]int32)
	}
	if u.Parts == nil {
		u.Parts = make(map[string]PartsState)
	}
	if u.PartsGroupNotes == nil {
		u.PartsGroupNotes = make(map[int32]PartsGroupNoteState)
	}
	if u.PartsPresets == nil {
		u.PartsPresets = make(map[int32]PartsPresetState)
	}
	if u.ImportantItems == nil {
		u.ImportantItems = make(map[int32]int32)
	}
	if u.CostumeActiveSkills == nil {
		u.CostumeActiveSkills = make(map[string]CostumeActiveSkillState)
	}
	if u.WeaponSkills == nil {
		u.WeaponSkills = make(map[string][]WeaponSkillState)
	}
	if u.WeaponAbilities == nil {
		u.WeaponAbilities = make(map[string][]WeaponAbilityState)
	}
	if u.DeckTypeNotes == nil {
		u.DeckTypeNotes = make(map[model.DeckType]DeckTypeNoteState)
	}
	if u.WeaponNotes == nil {
		u.WeaponNotes = make(map[int32]WeaponNoteState)
	}
	if u.NaviCutInPlayed == nil {
		u.NaviCutInPlayed = make(map[int32]bool)
	}
	if u.ViewedMovies == nil {
		u.ViewedMovies = make(map[int32]int64)
	}
	if u.DrawnOmikuji == nil {
		u.DrawnOmikuji = make(map[int32]int64)
	}
	if u.PremiumItems == nil {
		u.PremiumItems = make(map[int32]int64)
	}
	if u.DokanConfirmed == nil {
		u.DokanConfirmed = make(map[int32]bool)
	}
	if u.ShopItems == nil {
		u.ShopItems = make(map[int32]UserShopItemState)
	}
	if u.ShopReplaceableLineup == nil {
		u.ShopReplaceableLineup = make(map[int32]UserShopReplaceableLineupState)
	}
	if u.ExploreScores == nil {
		u.ExploreScores = make(map[int32]ExploreScoreState)
	}
	if u.CharacterBoards == nil {
		u.CharacterBoards = make(map[int32]CharacterBoardState)
	}
	if u.CharacterBoardAbilities == nil {
		u.CharacterBoardAbilities = make(map[CharacterBoardAbilityKey]CharacterBoardAbilityState)
	}
	if u.CharacterBoardStatusUps == nil {
		u.CharacterBoardStatusUps = make(map[CharacterBoardStatusUpKey]CharacterBoardStatusUpState)
	}
	if u.CostumeAwakenStatusUps == nil {
		u.CostumeAwakenStatusUps = make(map[CostumeAwakenStatusKey]CostumeAwakenStatusUpState)
	}
	if u.AutoSaleSettings == nil {
		u.AutoSaleSettings = make(map[int32]AutoSaleSettingState)
	}
	if u.CharacterRebirths == nil {
		u.CharacterRebirths = make(map[int32]CharacterRebirthState)
	}
	if u.Gimmick.Progress == nil {
		u.Gimmick.Progress = make(map[GimmickKey]GimmickProgressState)
	}
	if u.Gimmick.OrnamentProgress == nil {
		u.Gimmick.OrnamentProgress = make(map[GimmickOrnamentKey]GimmickOrnamentProgressState)
	}
	if u.Gimmick.Sequences == nil {
		u.Gimmick.Sequences = make(map[GimmickSequenceKey]GimmickSequenceState)
	}
	if u.Gimmick.Unlocks == nil {
		u.Gimmick.Unlocks = make(map[GimmickKey]GimmickUnlockState)
	}
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
	PartsUuids         []string
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

type ExtraQuestState struct {
	CurrentQuestId      int32
	CurrentQuestSceneId int32
	HeadQuestSceneId    int32
	LatestVersion       int64
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
	CageOrnamentId      int32
	AcquisitionDatetime int64
	LatestVersion       int64
}

type PartsState struct {
	UserPartsUuid       string
	PartsId             int32
	Level               int32
	PartsStatusMainId   int32
	IsProtected         bool
	AcquisitionDatetime int64
	LatestVersion       int64
}

type PartsGroupNoteState struct {
	PartsGroupId             int32
	FirstAcquisitionDatetime int64
	LatestVersion            int64
}

type PartsPresetState struct {
	UserPartsPresetNumber    int32
	UserPartsUuid01          string
	UserPartsUuid02          string
	UserPartsUuid03          string
	Name                     string
	UserPartsPresetTagNumber int32
	LatestVersion            int64
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

type CharacterBoardState struct {
	CharacterBoardId int32
	PanelReleaseBit1 int32
	PanelReleaseBit2 int32
	PanelReleaseBit3 int32
	PanelReleaseBit4 int32
	LatestVersion    int64
}

type CharacterBoardAbilityKey struct {
	CharacterId int32
	AbilityId   int32
}

func (k CharacterBoardAbilityKey) MarshalText() ([]byte, error) {
	return fmt.Appendf(nil, "%d:%d", k.CharacterId, k.AbilityId), nil
}

func (k *CharacterBoardAbilityKey) UnmarshalText(text []byte) error {
	parts := strings.Split(string(text), ":")
	if len(parts) != 2 {
		return fmt.Errorf("invalid CharacterBoardAbilityKey: %s", text)
	}
	a, err := strconv.ParseInt(parts[0], 10, 32)
	if err != nil {
		return err
	}
	b, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		return err
	}
	k.CharacterId = int32(a)
	k.AbilityId = int32(b)
	return nil
}

type CharacterBoardAbilityState struct {
	CharacterId   int32
	AbilityId     int32
	Level         int32
	LatestVersion int64
}

type CharacterBoardStatusUpKey struct {
	CharacterId           int32
	StatusCalculationType int32
}

func (k CharacterBoardStatusUpKey) MarshalText() ([]byte, error) {
	return fmt.Appendf(nil, "%d:%d", k.CharacterId, k.StatusCalculationType), nil
}

func (k *CharacterBoardStatusUpKey) UnmarshalText(text []byte) error {
	parts := strings.Split(string(text), ":")
	if len(parts) != 2 {
		return fmt.Errorf("invalid CharacterBoardStatusUpKey: %s", text)
	}
	a, err := strconv.ParseInt(parts[0], 10, 32)
	if err != nil {
		return err
	}
	b, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		return err
	}
	k.CharacterId = int32(a)
	k.StatusCalculationType = int32(b)
	return nil
}

type CharacterBoardStatusUpState struct {
	CharacterId           int32
	StatusCalculationType int32
	Hp                    int32
	Attack                int32
	Vitality              int32
	Agility               int32
	CriticalRatio         int32
	CriticalAttack        int32
	LatestVersion         int64
}

type CostumeAwakenStatusKey struct {
	UserCostumeUuid       string
	StatusCalculationType model.StatusCalculationType
}

func (k CostumeAwakenStatusKey) MarshalText() ([]byte, error) {
	return fmt.Appendf(nil, "%s:%d", k.UserCostumeUuid, k.StatusCalculationType), nil
}

func (k *CostumeAwakenStatusKey) UnmarshalText(text []byte) error {
	s := string(text)
	idx := strings.LastIndex(s, ":")
	if idx < 0 {
		return fmt.Errorf("invalid CostumeAwakenStatusKey: %s", text)
	}
	k.UserCostumeUuid = s[:idx]
	v, err := strconv.ParseInt(s[idx+1:], 10, 32)
	if err != nil {
		return err
	}
	k.StatusCalculationType = model.StatusCalculationType(v)
	return nil
}

type CostumeAwakenStatusUpState struct {
	UserCostumeUuid       string
	StatusCalculationType model.StatusCalculationType
	Hp                    int32
	Attack                int32
	Vitality              int32
	Agility               int32
	CriticalRatio         int32
	CriticalAttack        int32
	LatestVersion         int64
}

type AutoSaleSettingState struct {
	PossessionAutoSaleItemType  int32
	PossessionAutoSaleItemValue string
}

type CharacterRebirthState struct {
	CharacterId   int32
	RebirthCount  int32
	LatestVersion int64
}
