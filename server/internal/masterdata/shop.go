package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/utils"
)

type ShopItemRow struct {
	ShopItemId             int32 `json:"ShopItemId"`
	PriceType              int32 `json:"PriceType"`
	PriceId                int32 `json:"PriceId"`
	Price                  int32 `json:"Price"`
	ShopItemLimitedStockId int32 `json:"ShopItemLimitedStockId"`
}

type ShopContentRow struct {
	ShopItemId     int32 `json:"ShopItemId"`
	PossessionType int32 `json:"PossessionType"`
	PossessionId   int32 `json:"PossessionId"`
	Count          int32 `json:"Count"`
}

type ShopContentEffectRow struct {
	ShopItemId       int32 `json:"ShopItemId"`
	EffectTargetType int32 `json:"EffectTargetType"`
	EffectValueType  int32 `json:"EffectValueType"`
	EffectValue      int32 `json:"EffectValue"`
}

type ShopCatalog struct {
	Items            map[int32]ShopItemRow
	Contents         map[int32][]ShopContentRow
	Effects          map[int32][]ShopContentEffectRow
	MaxStaminaMillis map[int32]int32 // level -> max stamina in millis
}

type userLevelEntry struct {
	UserLevel  int32 `json:"UserLevel"`
	MaxStamina int32 `json:"MaxStamina"`
}

func LoadShopCatalog() (*ShopCatalog, error) {
	items, err := utils.ReadJSON[ShopItemRow]("EntityMShopItemTable.json")
	if err != nil {
		return nil, fmt.Errorf("load shop item table: %w", err)
	}
	contents, err := utils.ReadJSON[ShopContentRow]("EntityMShopItemContentPossessionTable.json")
	if err != nil {
		return nil, fmt.Errorf("load shop content possession table: %w", err)
	}
	effects, err := utils.ReadJSON[ShopContentEffectRow]("EntityMShopItemContentEffectTable.json")
	if err != nil {
		return nil, fmt.Errorf("load shop content effect table: %w", err)
	}
	userLevels, err := utils.ReadJSON[userLevelEntry]("EntityMUserLevelTable.json")
	if err != nil {
		return nil, fmt.Errorf("load user level table: %w", err)
	}

	catalog := &ShopCatalog{
		Items:            make(map[int32]ShopItemRow, len(items)),
		Contents:         make(map[int32][]ShopContentRow, len(contents)),
		Effects:          make(map[int32][]ShopContentEffectRow, len(effects)),
		MaxStaminaMillis: make(map[int32]int32, len(userLevels)),
	}
	for _, row := range items {
		catalog.Items[row.ShopItemId] = row
	}
	for _, row := range contents {
		catalog.Contents[row.ShopItemId] = append(catalog.Contents[row.ShopItemId], row)
	}
	for _, row := range effects {
		catalog.Effects[row.ShopItemId] = append(catalog.Effects[row.ShopItemId], row)
	}
	for _, ul := range userLevels {
		catalog.MaxStaminaMillis[ul.UserLevel] = ul.MaxStamina * 1000
	}
	return catalog, nil
}
