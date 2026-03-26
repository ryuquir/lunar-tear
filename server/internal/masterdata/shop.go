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

type ShopCatalog struct {
	Items    map[int32]ShopItemRow
	Contents map[int32][]ShopContentRow
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

	catalog := &ShopCatalog{
		Items:    make(map[int32]ShopItemRow, len(items)),
		Contents: make(map[int32][]ShopContentRow, len(contents)),
	}
	for _, row := range items {
		catalog.Items[row.ShopItemId] = row
	}
	for _, row := range contents {
		catalog.Contents[row.ShopItemId] = append(catalog.Contents[row.ShopItemId], row)
	}
	return catalog, nil
}
