package masterdata

import (
	"fmt"
	"log"
	"sort"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/store"
	"lunar-tear/server/internal/utils"
)

type GachaPoolItem struct {
	PossessionType int32
	PossessionId   int32
	RarityType     model.RarityType
	CharacterId    int32
}

type FeaturedSet struct {
	Costumes []GachaPoolItem
	Weapons  []GachaPoolItem
}

type BannerPool struct {
	CostumesByRarity map[int32][]GachaPoolItem
	WeaponsByRarity  map[int32][]GachaPoolItem
	Featured         []GachaPoolItem
}

type GachaCatalog struct {
	CostumesByRarity   map[int32][]GachaPoolItem
	WeaponsByRarity    map[int32][]GachaPoolItem
	Materials          []GachaPoolItem
	CostumeById        map[int32]GachaPoolItem
	WeaponById         map[int32]GachaPoolItem
	CostumeWeaponMap   map[int32]int32 // costumeId -> paired weaponId
	FeaturedByGacha    map[int32]FeaturedSet
	BannerPools        map[int32]*BannerPool
	costumesByTermDate map[int64][]int32
	weaponsByTermDate  map[int64][]int32
	sortedTermDates    []int64
}

type costumePoolRow struct {
	CostumeId          int32 `json:"CostumeId"`
	CharacterId        int32 `json:"CharacterId"`
	SkillfulWeaponType int32 `json:"SkillfulWeaponType"`
	RarityType         int32 `json:"RarityType"`
}

type weaponPoolRow struct {
	WeaponId   int32 `json:"WeaponId"`
	WeaponType int32 `json:"WeaponType"`
	RarityType int32 `json:"RarityType"`
}

type catalogCostumeRow struct {
	CostumeId     int32 `json:"CostumeId"`
	CatalogTermId int32 `json:"CatalogTermId"`
}

type catalogWeaponRow struct {
	WeaponId      int32 `json:"WeaponId"`
	CatalogTermId int32 `json:"CatalogTermId"`
}

type catalogTermRow struct {
	CatalogTermId int32 `json:"CatalogTermId"`
	StartDatetime int64 `json:"StartDatetime"`
}

type materialPoolRow struct {
	MaterialId   int32 `json:"MaterialId"`
	MaterialType int32 `json:"MaterialType"`
	RarityType   int32 `json:"RarityType"`
}

const featuredWindowMs = 3 * 24 * 3600 * 1000 // 3-day tolerance for matching
const farFutureDatetime int64 = 4_000_000_000_000

func trackTermDate(dateMap map[int64][]int32, id int32, termIdMap map[int32]int32, termDateById map[int32]int64) {
	tid, ok := termIdMap[id]
	if !ok {
		return
	}
	dt, ok := termDateById[tid]
	if !ok || dt >= farFutureDatetime {
		return
	}
	dateMap[dt] = append(dateMap[dt], id)
}

func LoadGachaPool() (*GachaCatalog, error) {
	costumes, err := utils.ReadJSON[costumePoolRow]("EntityMCostumeTable.json")
	if err != nil {
		return nil, fmt.Errorf("load costume table: %w", err)
	}
	weapons, err := utils.ReadJSON[weaponPoolRow]("EntityMWeaponTable.json")
	if err != nil {
		return nil, fmt.Errorf("load weapon table: %w", err)
	}
	catalogCostumes, err := utils.ReadJSON[catalogCostumeRow]("EntityMCatalogCostumeTable.json")
	if err != nil {
		return nil, fmt.Errorf("load catalog costume table: %w", err)
	}
	catalogWeapons, err := utils.ReadJSON[catalogWeaponRow]("EntityMCatalogWeaponTable.json")
	if err != nil {
		return nil, fmt.Errorf("load catalog weapon table: %w", err)
	}
	materials, err := utils.ReadJSON[materialPoolRow]("EntityMMaterialTable.json")
	if err != nil {
		return nil, fmt.Errorf("load material table: %w", err)
	}
	catalogTerms, err := utils.ReadJSON[catalogTermRow]("EntityMCatalogTermTable.json")
	if err != nil {
		return nil, fmt.Errorf("load catalog term table: %w", err)
	}

	termDateById := make(map[int32]int64, len(catalogTerms))
	for _, t := range catalogTerms {
		termDateById[t.CatalogTermId] = t.StartDatetime
	}

	catalogCostumeSet := make(map[int32]bool, len(catalogCostumes))
	costumeTermId := make(map[int32]int32, len(catalogCostumes))
	for _, c := range catalogCostumes {
		catalogCostumeSet[c.CostumeId] = true
		costumeTermId[c.CostumeId] = c.CatalogTermId
	}
	catalogWeaponSet := make(map[int32]bool, len(catalogWeapons))
	weaponTermId := make(map[int32]int32, len(catalogWeapons))
	for _, w := range catalogWeapons {
		catalogWeaponSet[w.WeaponId] = true
		weaponTermId[w.WeaponId] = w.CatalogTermId
	}

	costumeWeaponType := make(map[int32]int32, len(costumes))
	for _, c := range costumes {
		costumeWeaponType[c.CostumeId] = c.SkillfulWeaponType
	}

	weaponTypeById := make(map[int32]int32, len(weapons))
	weaponRarityById := make(map[int32]int32, len(weapons))
	for _, w := range weapons {
		weaponTypeById[w.WeaponId] = w.WeaponType
		weaponRarityById[w.WeaponId] = w.RarityType
	}

	pool := &GachaCatalog{
		CostumesByRarity:   make(map[int32][]GachaPoolItem),
		WeaponsByRarity:    make(map[int32][]GachaPoolItem),
		CostumeById:        make(map[int32]GachaPoolItem),
		WeaponById:         make(map[int32]GachaPoolItem),
		CostumeWeaponMap:   make(map[int32]int32),
		FeaturedByGacha:    make(map[int32]FeaturedSet),
		costumesByTermDate: make(map[int64][]int32),
		weaponsByTermDate:  make(map[int64][]int32),
	}

	for _, c := range costumes {
		if !catalogCostumeSet[c.CostumeId] {
			continue
		}
		if c.RarityType < model.RaritySRare {
			continue
		}
		item := GachaPoolItem{
			PossessionType: int32(model.PossessionTypeCostume),
			PossessionId:   c.CostumeId,
			RarityType:     c.RarityType,
			CharacterId:    c.CharacterId,
		}
		pool.CostumesByRarity[c.RarityType] = append(pool.CostumesByRarity[c.RarityType], item)
		pool.CostumeById[c.CostumeId] = item
		trackTermDate(pool.costumesByTermDate, c.CostumeId, costumeTermId, termDateById)
	}

	for _, w := range weapons {
		if !catalogWeaponSet[w.WeaponId] {
			continue
		}
		if w.RarityType < model.RarityRare {
			continue
		}
		item := GachaPoolItem{
			PossessionType: int32(model.PossessionTypeWeapon),
			PossessionId:   w.WeaponId,
			RarityType:     w.RarityType,
		}
		pool.WeaponsByRarity[w.RarityType] = append(pool.WeaponsByRarity[w.RarityType], item)
		pool.WeaponById[w.WeaponId] = item
		trackTermDate(pool.weaponsByTermDate, w.WeaponId, weaponTermId, termDateById)
	}

	dateSet := make(map[int64]bool)
	for dt := range pool.costumesByTermDate {
		dateSet[dt] = true
	}
	for dt := range pool.weaponsByTermDate {
		dateSet[dt] = true
	}
	for dt := range dateSet {
		pool.sortedTermDates = append(pool.sortedTermDates, dt)
	}
	sort.Slice(pool.sortedTermDates, func(i, j int) bool {
		return pool.sortedTermDates[i] < pool.sortedTermDates[j]
	})

	type weaponKey struct {
		TermId     int32
		WeaponType int32
		Rarity     int32
	}
	weaponsByKey := make(map[weaponKey][]int32)
	for _, cw := range catalogWeapons {
		wt := weaponTypeById[cw.WeaponId]
		r := weaponRarityById[cw.WeaponId]
		if wt == 0 || r < model.RaritySRare {
			continue
		}
		k := weaponKey{TermId: cw.CatalogTermId, WeaponType: wt, Rarity: r}
		weaponsByKey[k] = append(weaponsByKey[k], cw.WeaponId)
	}
	for k, ids := range weaponsByKey {
		sort.Slice(ids, func(i, j int) bool { return ids[i] < ids[j] })
		weaponsByKey[k] = ids
	}

	exact, pattern, bestGuess := 0, 0, 0
	for costumeId, item := range pool.CostumeById {
		if item.RarityType < model.RaritySRare {
			continue
		}
		tid := costumeTermId[costumeId]
		wt := costumeWeaponType[costumeId]
		k := weaponKey{TermId: tid, WeaponType: wt, Rarity: item.RarityType}
		candidates := weaponsByKey[k]
		if len(candidates) == 0 {
			continue
		}
		if len(candidates) == 1 {
			pool.CostumeWeaponMap[costumeId] = candidates[0]
			exact++
			continue
		}
		idPattern := costumeId*10 + 1
		found := false
		for _, wid := range candidates {
			if wid == idPattern {
				pool.CostumeWeaponMap[costumeId] = wid
				pattern++
				found = true
				break
			}
		}
		if !found {
			pool.CostumeWeaponMap[costumeId] = candidates[0]
			bestGuess++
		}
	}
	log.Printf("[GachaPool] costume-weapon pairing: %d exact, %d id-pattern, %d best-guess, %d total",
		exact, pattern, bestGuess, len(pool.CostumeWeaponMap))

	for _, m := range materials {
		pool.Materials = append(pool.Materials, GachaPoolItem{
			PossessionType: int32(model.PossessionTypeMaterial),
			PossessionId:   m.MaterialId,
			RarityType:     m.RarityType,
		})
	}

	return pool, nil
}

func (pool *GachaCatalog) BuildFeaturedMapping(entries []store.GachaCatalogEntry) {
	matched := 0
	for _, entry := range entries {
		if entry.StartDatetime <= 0 || entry.StartDatetime >= farFutureDatetime {
			continue
		}

		var ssrCostumes []GachaPoolItem
		var ssrWeapons []GachaPoolItem

		costumeIds := pool.findItemsByDate(pool.costumesByTermDate, entry.StartDatetime)
		for _, cid := range costumeIds {
			if item, ok := pool.CostumeById[cid]; ok && item.RarityType >= model.RaritySSRare {
				ssrCostumes = append(ssrCostumes, item)
			}
		}
		weaponIds := pool.findItemsByDate(pool.weaponsByTermDate, entry.StartDatetime)
		for _, wid := range weaponIds {
			if item, ok := pool.WeaponById[wid]; ok && item.RarityType >= model.RaritySSRare {
				ssrWeapons = append(ssrWeapons, item)
			}
		}

		if len(ssrCostumes) == 0 && len(ssrWeapons) == 0 {
			continue
		}

		pool.FeaturedByGacha[entry.GachaId] = FeaturedSet{
			Costumes: ssrCostumes,
			Weapons:  ssrWeapons,
		}
		matched++
	}
	log.Printf("[GachaPool] featured mapping: %d/%d banners matched via catalog terms", matched, len(entries))
}

func (pool *GachaCatalog) BuildBannerPools(entries []store.GachaCatalogEntry) {
	allFeaturedCostumes := make(map[int32]bool)
	allFeaturedWeapons := make(map[int32]bool)
	for _, fs := range pool.FeaturedByGacha {
		for _, c := range fs.Costumes {
			allFeaturedCostumes[c.PossessionId] = true
		}
		for _, w := range fs.Weapons {
			allFeaturedWeapons[w.PossessionId] = true
		}
	}

	commonCostumes := make(map[int32][]GachaPoolItem)
	for rarity, items := range pool.CostumesByRarity {
		for _, item := range items {
			if !allFeaturedCostumes[item.PossessionId] {
				commonCostumes[rarity] = append(commonCostumes[rarity], item)
			}
		}
	}
	commonWeapons := make(map[int32][]GachaPoolItem)
	for rarity, items := range pool.WeaponsByRarity {
		for _, item := range items {
			if !allFeaturedWeapons[item.PossessionId] {
				commonWeapons[rarity] = append(commonWeapons[rarity], item)
			}
		}
	}

	commonPool := &BannerPool{
		CostumesByRarity: commonCostumes,
		WeaponsByRarity:  commonWeapons,
	}

	pool.BannerPools = make(map[int32]*BannerPool)
	for _, entry := range entries {
		fs, hasFeatured := pool.FeaturedByGacha[entry.GachaId]
		if !hasFeatured {
			pool.BannerPools[entry.GachaId] = commonPool
			continue
		}

		var allFeatured []GachaPoolItem
		bannerCostumes := make(map[int32][]GachaPoolItem)
		for rarity, items := range commonCostumes {
			bannerCostumes[rarity] = append(bannerCostumes[rarity], items...)
		}
		for _, c := range fs.Costumes {
			bannerCostumes[c.RarityType] = append(bannerCostumes[c.RarityType], c)
			allFeatured = append(allFeatured, c)
		}

		bannerWeapons := make(map[int32][]GachaPoolItem)
		for rarity, items := range commonWeapons {
			bannerWeapons[rarity] = append(bannerWeapons[rarity], items...)
		}
		for _, w := range fs.Weapons {
			bannerWeapons[w.RarityType] = append(bannerWeapons[w.RarityType], w)
			allFeatured = append(allFeatured, w)
		}

		pool.BannerPools[entry.GachaId] = &BannerPool{
			CostumesByRarity: bannerCostumes,
			WeaponsByRarity:  bannerWeapons,
			Featured:         allFeatured,
		}
	}

	log.Printf("[GachaPool] banner pools: %d banners, %d featured costumes stripped, %d featured weapons stripped",
		len(pool.BannerPools), len(allFeaturedCostumes), len(allFeaturedWeapons))
}

func (pool *GachaCatalog) findItemsByDate(dateMap map[int64][]int32, targetDate int64) []int32 {
	if items, ok := dateMap[targetDate]; ok {
		return items
	}
	var best int64
	bestDist := int64(featuredWindowMs + 1)
	for _, dt := range pool.sortedTermDates {
		dist := targetDate - dt
		if dist < 0 {
			dist = -dist
		}
		if dist <= featuredWindowMs && dist < bestDist {
			bestDist = dist
			best = dt
		}
	}
	if bestDist <= featuredWindowMs {
		return dateMap[best]
	}
	return nil
}
