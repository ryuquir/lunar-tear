package model

type RarityType int32

const (
	RarityTypeUnknown RarityType = 0
	RarityTypeNormal  RarityType = 10
	RarityTypeRare    RarityType = 20
	RarityTypeSRare   RarityType = 30
	RarityTypeSSRare  RarityType = 40
	RarityTypeLegend  RarityType = 50
)
