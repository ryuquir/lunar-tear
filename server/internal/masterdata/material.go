package masterdata

import (
	"fmt"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type MaterialRow struct {
	MaterialId   int32              `json:"MaterialId"`
	MaterialType model.MaterialType `json:"MaterialType"`
	WeaponType   int32              `json:"WeaponType"`
	EffectValue  int32              `json:"EffectValue"`
	SellPrice    int32              `json:"SellPrice"`
}

type numericalParameterMapRow struct {
	NumericalParameterMapId int32 `json:"NumericalParameterMapId"`
	ParameterKey            int32 `json:"ParameterKey"`
	ParameterValue          int32 `json:"ParameterValue"`
}

func LoadParameterMap() ([]numericalParameterMapRow, error) {
	rows, err := utils.ReadJSON[numericalParameterMapRow]("EntityMNumericalParameterMapTable.json")
	if err != nil {
		return nil, fmt.Errorf("load numerical parameter map table: %w", err)
	}
	return rows, nil
}

func BuildExpThresholds(paramMapRows []numericalParameterMapRow, mapId int32) []int32 {
	maxKey := int32(0)
	for _, r := range paramMapRows {
		if r.NumericalParameterMapId == mapId && r.ParameterKey > maxKey {
			maxKey = r.ParameterKey
		}
	}
	thresholds := make([]int32, maxKey+1)
	for _, r := range paramMapRows {
		if r.NumericalParameterMapId == mapId {
			thresholds[r.ParameterKey] = r.ParameterValue
		}
	}
	return thresholds
}

type MaterialCatalog struct {
	All    map[int32]MaterialRow
	ByType map[model.MaterialType]map[int32]MaterialRow
}

func LoadMaterialCatalog() (*MaterialCatalog, error) {
	rows, err := utils.ReadJSON[MaterialRow]("EntityMMaterialTable.json")
	if err != nil {
		return nil, fmt.Errorf("load material table: %w", err)
	}

	catalog := &MaterialCatalog{
		All:    make(map[int32]MaterialRow, len(rows)),
		ByType: make(map[model.MaterialType]map[int32]MaterialRow),
	}
	for _, row := range rows {
		catalog.All[row.MaterialId] = row
		if catalog.ByType[row.MaterialType] == nil {
			catalog.ByType[row.MaterialType] = make(map[int32]MaterialRow)
		}
		catalog.ByType[row.MaterialType][row.MaterialId] = row
	}
	return catalog, nil
}
