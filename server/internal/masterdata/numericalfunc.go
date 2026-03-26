package masterdata

import (
	"fmt"
	"sort"

	"lunar-tear/server/internal/model"
	"lunar-tear/server/internal/utils"
)

type numericalFunctionRow struct {
	NumericalFunctionId               int32 `json:"NumericalFunctionId"`
	NumericalFunctionType             int32 `json:"NumericalFunctionType"`
	NumericalFunctionParameterGroupId int32 `json:"NumericalFunctionParameterGroupId"`
}

type numericalFunctionParameterRow struct {
	NumericalFunctionParameterGroupId int32 `json:"NumericalFunctionParameterGroupId"`
	ParameterIndex                    int32 `json:"ParameterIndex"`
	ParameterValue                    int32 `json:"ParameterValue"`
}

type NumericalFunc struct {
	Type   model.NumericalFunctionType
	Params []int32
}

func (f NumericalFunc) Evaluate(value int32) int32 {
	p := f.Params
	switch f.Type {
	case model.NumericalFunctionTypeLinear:
		return p[1] + p[0]*value
	case model.NumericalFunctionTypeMonomial:
		v := value - 1
		result := v
		counter := p[1]
		if counter > 1 {
			counter--
			for counter > 0 {
				counter--
				result *= v
			}
		}
		return result * p[0]
	case model.NumericalFunctionTypeLinearPermil:
		return p[0]*value/1000 + p[1]
	case model.NumericalFunctionTypePolynomialThird:
		return p[3] + (p[2]+(p[1]+p[0]*value)*value)*value
	case model.NumericalFunctionTypePolynomialThirdPermil:
		return p[0]*value*value*value/1000 +
			p[1]*value*value/1000 +
			p[2]*value/1000 +
			p[3]
	default:
		return 0
	}
}

type FunctionResolver struct {
	functions map[int32]NumericalFunc
}

func LoadFunctionResolver() (*FunctionResolver, error) {
	funcRows, err := utils.ReadJSON[numericalFunctionRow]("EntityMNumericalFunctionTable.json")
	if err != nil {
		return nil, fmt.Errorf("load numerical function table: %w", err)
	}

	paramRows, err := utils.ReadJSON[numericalFunctionParameterRow]("EntityMNumericalFunctionParameterGroupTable.json")
	if err != nil {
		return nil, fmt.Errorf("load numerical function parameter group table: %w", err)
	}

	paramsByGroup := make(map[int32][]numericalFunctionParameterRow, len(paramRows))
	for _, r := range paramRows {
		paramsByGroup[r.NumericalFunctionParameterGroupId] = append(
			paramsByGroup[r.NumericalFunctionParameterGroupId], r)
	}
	for _, group := range paramsByGroup {
		sort.Slice(group, func(i, j int) bool {
			return group[i].ParameterIndex < group[j].ParameterIndex
		})
	}

	functions := make(map[int32]NumericalFunc, len(funcRows))
	for _, fr := range funcRows {
		group := paramsByGroup[fr.NumericalFunctionParameterGroupId]
		params := make([]int32, len(group))
		for _, pr := range group {
			if int(pr.ParameterIndex) < len(params) {
				params[pr.ParameterIndex] = pr.ParameterValue
			}
		}
		functions[fr.NumericalFunctionId] = NumericalFunc{
			Type:   model.NumericalFunctionType(fr.NumericalFunctionType),
			Params: params,
		}
	}

	return &FunctionResolver{functions: functions}, nil
}

func (r *FunctionResolver) Resolve(functionId int32) (NumericalFunc, bool) {
	f, ok := r.functions[functionId]
	return f, ok
}
