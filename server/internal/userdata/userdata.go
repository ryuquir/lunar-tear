package userdata

import (
	"encoding/base64"
	"encoding/json"
	"fmt"

	"lunar-tear/server/internal/gametime"

	"github.com/vmihailenco/msgpack/v5"
)

// EntityIUser mirrors the game's EntityIUser [MessagePackObject] with [Key(0..7)].
// Serialized as a MessagePack array of 8 elements.
type EntityIUser struct {
	_msgpack            struct{} `msgpack:",asArray"`
	UserId              int64    // Key(0)
	PlayerId            int64    // Key(1)
	OsType              int32    // Key(2) — 2 = Android
	PlatformType        int32    // Key(3) — 2 = GooglePlay
	UserRestrictionType int32    // Key(4) — 0 = None
	RegisterDatetime    int64    // Key(5) — unix millis
	GameStartDatetime   int64    // Key(6) — unix millis
	LatestVersion       int64    // Key(7)
}

// EntityIUserSetting mirrors EntityIUserSetting [Key(0..2)].
type EntityIUserSetting struct {
	_msgpack              struct{} `msgpack:",asArray"`
	UserId                int64    `json:"userId"`                // Key(0)
	IsNotifyPurchaseAlert bool     `json:"isNotifyPurchaseAlert"` // Key(1)
	LatestVersion         int64    `json:"latestVersion"`         // Key(2)
}

// EntityIUserTutorialProgress mirrors EntityIUserTutorialProgress [Key(0..4)].
type EntityIUserTutorialProgress struct {
	_msgpack      struct{} `msgpack:",asArray"`
	UserId        int64    // Key(0)
	TutorialType  int32    // Key(1)
	ProgressPhase int32    // Key(2)
	ChoiceId      int32    // Key(3)
	LatestVersion int64    // Key(4)
}

// EntityIUserQuest mirrors EntityIUserQuest [Key(0..9)].
type EntityIUserQuest struct {
	_msgpack            struct{} `msgpack:",asArray"`
	UserId              int64    // Key(0)
	QuestId             int32    // Key(1)
	QuestStateType      int32    // Key(2) — 2 = Cleared
	IsBattleOnly        bool     // Key(3)
	LatestStartDatetime int64    // Key(4) — unix millis
	ClearCount          int32    // Key(5)
	DailyClearCount     int32    // Key(6)
	LastClearDatetime   int64    // Key(7) — unix millis
	ShortestClearFrames int32    // Key(8)
	LatestVersion       int64    // Key(9)
}

// EntityIUserMainQuestFlowStatus mirrors EntityIUserMainQuestFlowStatus [Key(0..2)].
type EntityIUserMainQuestFlowStatus struct {
	_msgpack             struct{} `msgpack:",asArray"`
	UserId               int64    // Key(0)
	CurrentQuestFlowType int32    // Key(1) // QuestFlowType: 0=UNKNOWN, 1=MAIN_FLOW, 2=SUB_FLOW, 3=REPLAY_FLOW, 4=ANOTHER_ROUTE_REPLAY_FLOW
	LatestVersion        int64    // Key(2)
}

// EntityIUserMainQuestMainFlowStatus mirrors EntityIUserMainQuestMainFlowStatus [Key(0..5)].
type EntityIUserMainQuestMainFlowStatus struct {
	_msgpack                struct{} `msgpack:",asArray"`
	UserId                  int64    // Key(0)
	CurrentMainQuestRouteId int32    // Key(1)
	CurrentQuestSceneId     int32    // Key(2)
	HeadQuestSceneId        int32    // Key(3)
	IsReachedLastQuestScene bool     // Key(4)
	LatestVersion           int64    // Key(5)
}

// EntityIUserMainQuestProgressStatus mirrors EntityIUserMainQuestProgressStatus [Key(0..4)].
// This table is used by ActivePlayerToEntityPlayingMainQuestStatus (0x2AB4A48).
type EntityIUserMainQuestProgressStatus struct {
	_msgpack             struct{} `msgpack:",asArray"`
	UserId               int64    // Key(0)
	CurrentQuestSceneId  int32    // Key(1)
	HeadQuestSceneId     int32    // Key(2)
	CurrentQuestFlowType int32    // Key(3) // QuestFlowType: 0=UNKNOWN, 1=MAIN_FLOW, 2=SUB_FLOW, 3=REPLAY_FLOW, 4=ANOTHER_ROUTE_REPLAY_FLOW
	LatestVersion        int64    // Key(4)
}

// EntityIUserMainQuestSeasonRoute mirrors EntityIUserMainQuestSeasonRoute [Key(0..3)].
type EntityIUserMainQuestSeasonRoute struct {
	_msgpack          struct{} `msgpack:",asArray"`
	UserId            int64    // Key(0)
	MainQuestSeasonId int32    // Key(1)
	MainQuestRouteId  int32    // Key(2)
	LatestVersion     int64    // Key(3)
}

// EntityIUserStatus mirrors EntityIUserStatus [Key(0..5)].
type EntityIUserStatus struct {
	_msgpack              struct{} `msgpack:",asArray"`
	UserId                int64    // Key(0)
	Level                 int32    // Key(1)
	Exp                   int32    // Key(2)
	StaminaMilliValue     int32    // Key(3)
	StaminaUpdateDatetime int64    // Key(4)
	LatestVersion         int64    // Key(5)
}

// EntityIUserGem mirrors EntityIUserGem [Key(0..2)].
type EntityIUserGem struct {
	_msgpack struct{} `msgpack:",asArray"`
	UserId   int64    `json:"userId"`  // Key(0)
	PaidGem  int32    `json:"paidGem"` // Key(1)
	FreeGem  int32    `json:"freeGem"` // Key(2)
}

// EntityIUserProfile mirrors EntityIUserProfile [Key(0..7)].
type EntityIUserProfile struct {
	_msgpack                        struct{} `msgpack:",asArray"`
	UserId                          int64    // Key(0)
	Name                            string   // Key(1)
	NameUpdateDatetime              int64    // Key(2)
	Message                         string   // Key(3)
	MessageUpdateDatetime           int64    // Key(4)
	FavoriteCostumeId               int32    // Key(5)
	FavoriteCostumeIdUpdateDatetime int64    // Key(6)
	LatestVersion                   int64    // Key(7)
}

// EntityIUserCharacter mirrors EntityIUserCharacter [Key(0..4)].
type EntityIUserCharacter struct {
	_msgpack      struct{} `msgpack:",asArray"`
	UserId        int64    // Key(0)
	CharacterId   int32    // Key(1)
	Level         int32    // Key(2)
	Exp           int32    // Key(3)
	LatestVersion int64    // Key(4)
}

// EntityIUserCostume mirrors EntityIUserCostume [Key(0..9)].
type EntityIUserCostume struct {
	_msgpack            struct{} `msgpack:",asArray"`
	UserId              int64    // Key(0)
	UserCostumeUuid     string   // Key(1)
	CostumeId           int32    // Key(2)
	LimitBreakCount     int32    // Key(3)
	Level               int32    // Key(4)
	Exp                 int32    // Key(5)
	HeadupDisplayViewId int32    // Key(6)
	AcquisitionDatetime int64    // Key(7)
	AwakenCount         int32    // Key(8)
	LatestVersion       int64    // Key(9)
}

// EntityIUserWeapon mirrors EntityIUserWeapon [Key(0..8)].
type EntityIUserWeapon struct {
	_msgpack            struct{} `msgpack:",asArray"`
	UserId              int64    // Key(0)
	UserWeaponUuid      string   // Key(1)
	WeaponId            int32    // Key(2)
	Level               int32    // Key(3)
	Exp                 int32    // Key(4)
	LimitBreakCount     int32    // Key(5)
	IsProtected         bool     // Key(6)
	AcquisitionDatetime int64    // Key(7)
	LatestVersion       int64    // Key(8)
}

// EntityIUserCompanion mirrors EntityIUserCompanion [Key(0..6)].
type EntityIUserCompanion struct {
	_msgpack            struct{} `msgpack:",asArray"`
	UserId              int64    // Key(0)
	UserCompanionUuid   string   // Key(1)
	CompanionId         int32    // Key(2)
	HeadupDisplayViewId int32    // Key(3)
	Level               int32    // Key(4)
	AcquisitionDatetime int64    // Key(5)
	LatestVersion       int64    // Key(6)
}

// EntityIUserDeckCharacter mirrors EntityIUserDeckCharacter [Key(0..7)].
type EntityIUserDeckCharacter struct {
	_msgpack              struct{} `msgpack:",asArray"`
	UserId                int64    // Key(0)
	UserDeckCharacterUuid string   // Key(1)
	UserCostumeUuid       string   // Key(2)
	MainUserWeaponUuid    string   // Key(3)
	UserCompanionUuid     string   // Key(4)
	Power                 int32    // Key(5)
	UserThoughtUuid       string   // Key(6)
	LatestVersion         int64    // Key(7)
}

// EntityIUserDeck mirrors EntityIUserDeck [Key(0..8)].
type EntityIUserDeck struct {
	_msgpack                struct{} `msgpack:",asArray"`
	UserId                  int64    // Key(0)
	DeckType                int32    // Key(1)
	UserDeckNumber          int32    // Key(2)
	UserDeckCharacterUuid01 string   // Key(3)
	UserDeckCharacterUuid02 string   // Key(4)
	UserDeckCharacterUuid03 string   // Key(5)
	Name                    string   // Key(6)
	Power                   int32    // Key(7)
	LatestVersion           int64    // Key(8)
}

// EntityIUserLogin mirrors EntityIUserLogin [Key(0..6)].
type EntityIUserLogin struct {
	_msgpack                  struct{} `msgpack:",asArray"`
	UserId                    int64    `json:"userId"`                    // Key(0)
	TotalLoginCount           int32    `json:"totalLoginCount"`           // Key(1)
	ContinualLoginCount       int32    `json:"continualLoginCount"`       // Key(2)
	MaxContinualLoginCount    int32    `json:"maxContinualLoginCount"`    // Key(3)
	LastLoginDatetime         int64    `json:"lastLoginDatetime"`         // Key(4)
	LastComebackLoginDatetime int64    `json:"lastComebackLoginDatetime"` // Key(5)
	LatestVersion             int64    `json:"latestVersion"`             // Key(6)
}

// EntityIUserLoginBonus mirrors EntityIUserLoginBonus [Key(0..5)].
type EntityIUserLoginBonus struct {
	_msgpack                    struct{} `msgpack:",asArray"`
	UserId                      int64    `json:"userId"`                      // Key(0)
	LoginBonusId                int32    `json:"loginBonusId"`                // Key(1)
	CurrentPageNumber           int32    `json:"currentPageNumber"`           // Key(2)
	CurrentStampNumber          int32    `json:"currentStampNumber"`          // Key(3)
	LatestRewardReceiveDatetime int64    `json:"latestRewardReceiveDatetime"` // Key(4)
	LatestVersion               int64    `json:"latestVersion"`               // Key(5)
}

// EntityIUserMission mirrors EntityIUserMission [Key(0..6)].
type EntityIUserMission struct {
	_msgpack                  struct{} `msgpack:",asArray"`
	UserId                    int64    // Key(0)
	MissionId                 int32    // Key(1)
	StartDatetime             int64    // Key(2)
	ProgressValue             int32    // Key(3)
	MissionProgressStatusType int32    // Key(4)
	ClearDatetime             int64    // Key(5)
	LatestVersion             int64    // Key(6)
}

// EncodeRecords serializes a slice of entities to the client-expected format:
// a JSON array of base64-encoded MessagePack byte strings.
func EncodeRecords(entities ...any) (string, error) {
	b64List := make([]string, 0, len(entities))
	for _, e := range entities {
		data, err := msgpack.Marshal(e)
		if err != nil {
			return "", fmt.Errorf("msgpack marshal: %w", err)
		}
		b64List = append(b64List, base64.StdEncoding.EncodeToString(data))
	}
	jsonBytes, err := json.Marshal(b64List)
	if err != nil {
		return "", fmt.Errorf("json marshal: %w", err)
	}
	return string(jsonBytes), nil
}

func encodeJSONRecords(entities ...any) (string, error) {
	jsonBytes, err := json.Marshal(entities)
	if err != nil {
		return "", fmt.Errorf("json marshal records: %w", err)
	}
	return string(jsonBytes), nil
}

func encodeJSONMaps(records ...map[string]any) (string, error) {
	jsonBytes, err := json.Marshal(records)
	if err != nil {
		return "", fmt.Errorf("json marshal maps: %w", err)
	}
	return string(jsonBytes), nil
}

// DefaultUserData returns pre-built user data tables for a fresh user.
// We provide BOTH msgpack-encoded (base64) and plain JSON variants.
// The server tries msgpack first; if the client doesn't accept it, switch to JSON.
func DefaultUserData(userId int64) map[string]string {
	now := gametime.Now().Unix()

	userRecord, _ := EncodeRecords(&EntityIUser{
		UserId:           userId,
		PlayerId:         userId,
		OsType:           2,
		PlatformType:     2,
		RegisterDatetime: now,
	})

	settingRecord, _ := EncodeRecords(&EntityIUserSetting{
		UserId: userId,
	})

	data := map[string]string{
		"user":         userRecord,
		"user_setting": settingRecord,
	}
	return data
}
