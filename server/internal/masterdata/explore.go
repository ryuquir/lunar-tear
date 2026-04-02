package masterdata

import (
	"fmt"
	"sort"

	"lunar-tear/server/internal/utils"
)

type ExploreRow struct {
	ExploreId          int32 `json:"ExploreId"`
	ConsumeItemCount   int32 `json:"ConsumeItemCount"`
	RewardLotteryCount int32 `json:"RewardLotteryCount"`
}

type ExploreGradeScoreRow struct {
	ExploreId      int32 `json:"ExploreId"`
	NecessaryScore int32 `json:"NecessaryScore"`
	ExploreGradeId int32 `json:"ExploreGradeId"`
}

type ExploreGradeAssetRow struct {
	ExploreGradeId   int32 `json:"ExploreGradeId"`
	AssetGradeIconId int32 `json:"AssetGradeIconId"`
}

type ExploreCatalog struct {
	Explores    map[int32]ExploreRow
	GradeScores map[int32][]ExploreGradeScoreRow // keyed by ExploreId, sorted desc by NecessaryScore
	GradeAssets map[int32]int32                  // gradeId -> assetGradeIconId
}

func LoadExploreCatalog() (*ExploreCatalog, error) {
	explores, err := utils.ReadJSON[ExploreRow]("EntityMExploreTable.json")
	if err != nil {
		return nil, fmt.Errorf("load explore table: %w", err)
	}

	gradeScores, err := utils.ReadJSON[ExploreGradeScoreRow]("EntityMExploreGradeScoreTable.json")
	if err != nil {
		return nil, fmt.Errorf("load explore grade score table: %w", err)
	}

	gradeAssets, err := utils.ReadJSON[ExploreGradeAssetRow]("EntityMExploreGradeAssetTable.json")
	if err != nil {
		return nil, fmt.Errorf("load explore grade asset table: %w", err)
	}

	catalog := &ExploreCatalog{
		Explores:    make(map[int32]ExploreRow, len(explores)),
		GradeScores: make(map[int32][]ExploreGradeScoreRow),
		GradeAssets: make(map[int32]int32, len(gradeAssets)),
	}

	for _, e := range explores {
		catalog.Explores[e.ExploreId] = e
	}

	for _, gs := range gradeScores {
		catalog.GradeScores[gs.ExploreId] = append(catalog.GradeScores[gs.ExploreId], gs)
	}
	for eid := range catalog.GradeScores {
		rows := catalog.GradeScores[eid]
		sort.Slice(rows, func(i, j int) bool {
			return rows[i].NecessaryScore > rows[j].NecessaryScore
		})
		catalog.GradeScores[eid] = rows
	}

	for _, ga := range gradeAssets {
		catalog.GradeAssets[ga.ExploreGradeId] = ga.AssetGradeIconId
	}

	return catalog, nil
}

// GradeForScore returns the AssetGradeIconId for the given explore and score.
// Returns 0 if no matching grade is found.
func (c *ExploreCatalog) GradeForScore(exploreId, score int32) int32 {
	rows, ok := c.GradeScores[exploreId]
	if !ok {
		return 0
	}
	for _, r := range rows {
		if score >= r.NecessaryScore {
			return c.GradeAssets[r.ExploreGradeId]
		}
	}
	return 0
}
