package model

type StatusKindType int32

const (
	StatusKindTypeUnknown        StatusKindType = 0
	StatusKindTypeAgility        StatusKindType = 1
	StatusKindTypeAttack         StatusKindType = 2
	StatusKindTypeCriticalAttack StatusKindType = 3
	StatusKindTypeCriticalRatio  StatusKindType = 4
	StatusKindTypeEvasionRatio   StatusKindType = 5
	StatusKindTypeHp             StatusKindType = 6
	StatusKindTypeVitality       StatusKindType = 7
)

type CostumeAwakenEffectType int32

const (
	CostumeAwakenEffectTypeUnknown     CostumeAwakenEffectType = 0
	CostumeAwakenEffectTypeStatusUp    CostumeAwakenEffectType = 1
	CostumeAwakenEffectTypeAbility     CostumeAwakenEffectType = 2
	CostumeAwakenEffectTypeItemAcquire CostumeAwakenEffectType = 3
)
