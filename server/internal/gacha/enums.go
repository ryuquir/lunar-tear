package gacha

const (
	GachaLabelUnknown    int32 = 0
	GachaLabelPremium    int32 = 1
	GachaLabelEvent      int32 = 2
	GachaLabelChapter    int32 = 3
	GachaLabelPortalCage int32 = 4
	GachaLabelRecycle    int32 = 5
)

const (
	GachaModeUnknown int32 = 0
	GachaModeBasic   int32 = 1
	GachaModeStepup  int32 = 2
	GachaModeBox     int32 = 3
)

const (
	GachaUnlockUnknown                  int32 = 0
	GachaUnlockNone                     int32 = 1
	GachaUnlockUserRankGreaterOrEqual   int32 = 2
	GachaUnlockWithinHoursFromGameStart int32 = 3
	GachaUnlockMainQuestClear           int32 = 4
	GachaUnlockMainFunctionReleased     int32 = 5
)
