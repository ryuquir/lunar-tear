package main

import (
	"flag"
	"log"
	"os"
	"strconv"

	"lunar-tear/server/internal/gacha"
	"lunar-tear/server/internal/gametime"
	"lunar-tear/server/internal/masterdata"
	"lunar-tear/server/internal/questflow"
	"lunar-tear/server/internal/store/memory"
)

func main() {
	httpPort := flag.Int("http-port", 8080, "HTTP server port (Octo API)")
	host := flag.String("host", "127.0.0.1", "hostname the client will connect to")
	resourcesBaseURL := flag.String("resources-base-url", "", "Resources base URL for list.bin rewrite (must be exactly 43 chars); empty = derive from host (so client uses our server for assets)")
	scene := flag.Int("scene", 0, "Bootstrap to scene N (0 = fresh start)")
	starterItems := flag.Bool("starter-items", false, "Grant starter items to new users")
	flag.Parse()

	octoURL := "http://" + *host + ":" + strconv.Itoa(*httpPort)
	if *resourcesBaseURL == "" {
		candidate := "http://" + *host + ":" + strconv.Itoa(*httpPort) + "/resource-bundle-server"
		if len(candidate) == 43 {
			*resourcesBaseURL = candidate
		}
	}
	if *resourcesBaseURL != "" && len(*resourcesBaseURL) != 43 {
		log.Printf("[config] resources-base-url length is %d (need 43); list.bin will be served unchanged", len(*resourcesBaseURL))
		*resourcesBaseURL = ""
	}

	go startHTTP(*httpPort, *resourcesBaseURL)

	snapshotDir := "snapshots"
	if err := os.MkdirAll(snapshotDir, 0755); err != nil {
		log.Fatalf("create snapshot dir: %v", err)
	}

	gameConfig, err := masterdata.LoadGameConfig()
	if err != nil {
		log.Fatalf("load game config: %v", err)
	}
	log.Printf("game config loaded (goldId=%d, skipTicketId=%d, rebirthGold=%d)",
		gameConfig.ConsumableItemIdForGold, gameConfig.ConsumableItemIdForQuestSkipTicket, gameConfig.CharacterRebirthConsumeGold)

	partsCatalog, err := masterdata.LoadPartsCatalog()
	if err != nil {
		log.Fatalf("load parts catalog: %v", err)
	}
	log.Printf("parts catalog loaded: %d parts, %d rarities", len(partsCatalog.PartsById), len(partsCatalog.RarityByRarityType))

	questCatalog, err := masterdata.LoadQuestCatalog(partsCatalog)
	if err != nil {
		log.Fatalf("load quest catalog: %v", err)
	}
	questHandler := questflow.NewQuestHandler(questCatalog, gameConfig)
	userStore := memory.New(gametime.Now,
		memory.WithSnapshotDir(snapshotDir),
		memory.WithSceneId(int32(*scene)),
		memory.WithStarterItems(*starterItems),
	)
	if *scene != 0 {
		log.Printf("bootstrap scene: %d (from snapshot)", *scene)
	}

	gachaEntries, medalInfo, err := masterdata.LoadGachaCatalog()
	if err != nil {
		log.Fatalf("load gacha catalog: %v", err)
	}
	log.Printf("gacha catalog loaded: %d entries", len(gachaEntries))

	gachaPool, err := masterdata.LoadGachaPool()
	if err != nil {
		log.Fatalf("load gacha pool: %v", err)
	}
	log.Printf("gacha pool loaded: costumes=%d rarities, weapons=%d rarities, materials=%d",
		len(gachaPool.CostumesByRarity), len(gachaPool.WeaponsByRarity), len(gachaPool.Materials))

	gachaPool.BuildFeaturedMapping(gachaEntries)
	gachaPool.BuildBannerPools(gachaEntries)
	masterdata.EnrichCatalogPromotions(gachaEntries, gachaPool)
	userStore.ReplaceCatalog(gachaEntries)

	dupExchange, err := masterdata.LoadDupExchange()
	if err != nil {
		log.Fatalf("load dup exchange: %v", err)
	}
	dupAdded, err := masterdata.EnrichDupExchange(dupExchange, gachaPool)
	if err != nil {
		log.Fatalf("enrich dup exchange: %v", err)
	}
	log.Printf("dup exchange loaded: %d entries (%d derived from limit-break materials)", len(dupExchange), dupAdded)

	gachaHandler := gacha.NewGachaHandler(gachaPool, gameConfig, questHandler.Granter, medalInfo, dupExchange)

	conditionResolver, err := masterdata.LoadConditionResolver()
	if err != nil {
		log.Fatalf("load condition resolver: %v", err)
	}

	cageOrnamentCatalog := masterdata.LoadCageOrnamentCatalog()
	loginBonusCatalog := masterdata.LoadLoginBonusCatalog()
	characterViewerCatalog := masterdata.LoadCharacterViewerCatalog(conditionResolver)
	omikujiCatalog := masterdata.LoadOmikujiCatalog()

	shopCatalog, err := masterdata.LoadShopCatalog()
	if err != nil {
		log.Fatalf("load shop catalog: %v", err)
	}
	log.Printf("shop catalog loaded: %d items, %d content groups", len(shopCatalog.Items), len(shopCatalog.Contents))

	materialCatalog, err := masterdata.LoadMaterialCatalog()
	if err != nil {
		log.Fatalf("load material catalog: %v", err)
	}
	log.Printf("material catalog loaded: %d materials", len(materialCatalog.All))

	costumeCatalog, err := masterdata.LoadCostumeCatalog(materialCatalog)
	if err != nil {
		log.Fatalf("load costume catalog: %v", err)
	}
	log.Printf("costume catalog loaded: %d costumes, %d materials, %d rarity curves", len(costumeCatalog.Costumes), len(costumeCatalog.Materials), len(costumeCatalog.ExpByRarity))

	weaponCatalog, err := masterdata.LoadWeaponCatalog(materialCatalog)
	if err != nil {
		log.Fatalf("load weapon catalog: %v", err)
	}
	log.Printf("weapon catalog loaded: %d weapons, %d materials, %d enhance configs", len(weaponCatalog.Weapons), len(weaponCatalog.Materials), len(weaponCatalog.ExpByEnhanceId))

	exploreCatalog, err := masterdata.LoadExploreCatalog()
	if err != nil {
		log.Fatalf("load explore catalog: %v", err)
	}
	log.Printf("explore catalog loaded: %d explores, %d grade assets", len(exploreCatalog.Explores), len(exploreCatalog.GradeAssets))

	gimmickCatalog, err := masterdata.LoadGimmickCatalog(conditionResolver)
	if err != nil {
		log.Fatalf("load gimmick catalog: %v", err)
	}

	characterBoardCatalog, err := masterdata.LoadCharacterBoardCatalog()
	if err != nil {
		log.Fatalf("load character board catalog: %v", err)
	}
	log.Printf("character board catalog loaded: %d panels, %d boards", len(characterBoardCatalog.PanelById), len(characterBoardCatalog.BoardById))

	characterRebirthCatalog, err := masterdata.LoadCharacterRebirthCatalog()
	if err != nil {
		log.Fatalf("load character rebirth catalog: %v", err)
	}
	log.Printf("character rebirth catalog loaded: %d characters", len(characterRebirthCatalog.StepGroupByCharacterId))

	companionCatalog, err := masterdata.LoadCompanionCatalog()
	if err != nil {
		log.Fatalf("load companion catalog: %v", err)
	}
	log.Printf("companion catalog loaded: %d companions, %d categories", len(companionCatalog.CompanionById), len(companionCatalog.GoldCostByCategory))

	startGRPC(
		*host,
		octoURL,
		userStore,
		questHandler,
		gachaHandler,
		cageOrnamentCatalog,
		loginBonusCatalog,
		characterViewerCatalog,
		shopCatalog,
		costumeCatalog,
		omikujiCatalog,
		weaponCatalog,
		exploreCatalog,
		gimmickCatalog,
		characterBoardCatalog,
		partsCatalog,
		characterRebirthCatalog,
		companionCatalog,
		materialCatalog,
		gameConfig,
	)
}
