package masterdata

import (
	"fmt"
	"sort"

	"lunar-tear/server/internal/model"
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

type shopItemLimitedStockRow struct {
	ShopItemLimitedStockId int32 `json:"ShopItemLimitedStockId"`
	MaxCount               int32 `json:"MaxCount"`
}

type shopRow struct {
	ShopId              int32 `json:"ShopId"`
	ShopGroupType       int32 `json:"ShopGroupType"`
	ShopItemCellGroupId int32 `json:"ShopItemCellGroupId"`
}

type shopItemCellGroupRow struct {
	ShopItemCellGroupId int32 `json:"ShopItemCellGroupId"`
	ShopItemCellId      int32 `json:"ShopItemCellId"`
	SortOrder           int32 `json:"SortOrder"`
}

type shopItemCellRow struct {
	ShopItemCellId int32 `json:"ShopItemCellId"`
	ShopItemId     int32 `json:"ShopItemId"`
}

type ExchangeShopCell struct {
	SortOrder  int32
	ShopItemId int32
}

type ShopCatalog struct {
	Items             map[int32]ShopItemRow
	Contents          map[int32][]ShopContentRow
	Effects           map[int32][]ShopContentEffectRow
	MaxStaminaMillis  map[int32]int32              // level -> max stamina in millis
	LimitedStock      map[int32]int32              // stock id -> max count
	ItemShopPool      []int32                      // shop item IDs for the replaceable item shop, sorted by cell sort order
	ExchangeShopCells map[int32][]ExchangeShopCell // shopId -> sorted cells for exchange shops
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
	stockRows, err := utils.ReadJSON[shopItemLimitedStockRow]("EntityMShopItemLimitedStockTable.json")
	if err != nil {
		return nil, fmt.Errorf("load shop item limited stock table: %w", err)
	}

	catalog := &ShopCatalog{
		Items:            make(map[int32]ShopItemRow, len(items)),
		Contents:         make(map[int32][]ShopContentRow, len(contents)),
		Effects:          make(map[int32][]ShopContentEffectRow, len(effects)),
		MaxStaminaMillis: make(map[int32]int32, len(userLevels)),
		LimitedStock:     make(map[int32]int32, len(stockRows)),
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
	for _, row := range stockRows {
		catalog.LimitedStock[row.ShopItemLimitedStockId] = row.MaxCount
	}

	shops, err := utils.ReadJSON[shopRow]("EntityMShopTable.json")
	if err != nil {
		return nil, fmt.Errorf("load shop table: %w", err)
	}
	cellGroups, err := utils.ReadJSON[shopItemCellGroupRow]("EntityMShopItemCellGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load shop item cell group table: %w", err)
	}
	cells, err := utils.ReadJSON[shopItemCellRow]("EntityMShopItemCellTable.json")
	if err != nil {
		return nil, fmt.Errorf("load shop item cell table: %w", err)
	}

	cellIdToItemId := make(map[int32]int32, len(cells))
	for _, c := range cells {
		cellIdToItemId[c.ShopItemCellId] = c.ShopItemId
	}

	cellGroupByCGId := make(map[int32][]shopItemCellGroupRow, len(cellGroups))
	for _, cg := range cellGroups {
		cellGroupByCGId[cg.ShopItemCellGroupId] = append(cellGroupByCGId[cg.ShopItemCellGroupId], cg)
	}

	catalog.ExchangeShopCells = make(map[int32][]ExchangeShopCell)
	for _, s := range shops {
		entries := cellGroupByCGId[s.ShopItemCellGroupId]
		if len(entries) == 0 {
			continue
		}

		switch s.ShopGroupType {
		case model.ShopGroupTypeItemShop:
			var poolCells []ExchangeShopCell
			for _, cg := range entries {
				if itemId, ok := cellIdToItemId[cg.ShopItemCellId]; ok {
					poolCells = append(poolCells, ExchangeShopCell{cg.SortOrder, itemId})
				}
			}
			sort.Slice(poolCells, func(i, j int) bool { return poolCells[i].SortOrder < poolCells[j].SortOrder })
			catalog.ItemShopPool = make([]int32, len(poolCells))
			for i, pc := range poolCells {
				catalog.ItemShopPool[i] = pc.ShopItemId
			}

		case model.ShopGroupTypeExchangeShop:
			var sc []ExchangeShopCell
			for _, cg := range entries {
				if itemId, ok := cellIdToItemId[cg.ShopItemCellId]; ok {
					sc = append(sc, ExchangeShopCell{cg.SortOrder, itemId})
				}
			}
			sort.Slice(sc, func(i, j int) bool { return sc[i].SortOrder < sc[j].SortOrder })
			catalog.ExchangeShopCells[s.ShopId] = sc
		}
	}

	return catalog, nil
}
