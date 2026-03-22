package model

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

const (
	GachaAutoResetUnknown int32 = 0
	GachaAutoResetNone    int32 = 1
	GachaAutoResetDaily   int32 = 2
	GachaAutoResetMonthly int32 = 3
)

const (
	GachaDecorationUnknown  int32 = 0
	GachaDecorationNormal   int32 = 1
	GachaDecorationFestival int32 = 2
)

const (
	PriceTypeUnknown         int32 = 0
	PriceTypeConsumableItem  int32 = 1
	PriceTypeGem             int32 = 2
	PriceTypePaidGem         int32 = 3
	PriceTypePlatformPayment int32 = 4
)
