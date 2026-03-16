package utils

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

func ReadJSON[T any](filename string) ([]T, error) {
	path := filepath.Join("assets", "master_data", filename)
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", path, err)
	}
	var out []T
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, fmt.Errorf("unmarshal %s: %w", path, err)
	}
	return out, nil
}
