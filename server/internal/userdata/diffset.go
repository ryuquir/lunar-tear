package userdata

import (
	"encoding/json"
	"fmt"
	"strings"

	pb "lunar-tear/server/gen/proto"
)

type DiffSet struct {
	updates map[string]string
	deletes map[string]string
}

func NewDiffSet(tables map[string]string) *DiffSet {
	return &DiffSet{
		updates: tables,
		deletes: make(map[string]string),
	}
}

func (ds *DiffSet) WithDeletes(table, deleteKeysJSON string) *DiffSet {
	if deleteKeysJSON != "" && deleteKeysJSON != "[]" {
		ds.deletes[table] = deleteKeysJSON
	}
	return ds
}

func (ds *DiffSet) Build() map[string]*pb.DiffData {
	diff := make(map[string]*pb.DiffData, len(ds.updates))
	for table, payload := range ds.updates {
		diff[table] = ds.entry(table, payload)
	}
	return diff
}

func (ds *DiffSet) BuildOrdered(order []string) map[string]*pb.DiffData {
	diff := make(map[string]*pb.DiffData, len(order))
	for _, table := range order {
		payload := ds.updates[table]
		diff[table] = ds.entry(table, payload)
	}
	return diff
}

func (ds *DiffSet) entry(table, payload string) *pb.DiffData {
	if payload == "" {
		payload = "[]"
	}
	deleteKeys := "[]"
	if dk, ok := ds.deletes[table]; ok {
		deleteKeys = dk
	}
	return &pb.DiffData{
		UpdateRecordsJson: payload,
		DeleteKeysJson:    deleteKeys,
	}
}

func ComputeDeleteKeys(oldRecords, newRecords []map[string]any, keyFields []string) string {
	if len(oldRecords) == 0 {
		return "[]"
	}

	newSet := make(map[string]struct{}, len(newRecords))
	for _, r := range newRecords {
		newSet[compositeKey(r, keyFields)] = struct{}{}
	}

	var deleted []map[string]any
	for _, r := range oldRecords {
		if _, exists := newSet[compositeKey(r, keyFields)]; !exists {
			deleted = append(deleted, r)
		}
	}

	if len(deleted) == 0 {
		return "[]"
	}
	b, err := json.Marshal(deleted)
	if err != nil {
		return "[]"
	}
	return string(b)
}

func compositeKey(record map[string]any, fields []string) string {
	var sb strings.Builder
	for i, f := range fields {
		if i > 0 {
			sb.WriteByte('|')
		}
		sb.WriteString(fmt.Sprint(record[f]))
	}
	return sb.String()
}
