package memory

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"lunar-tear/server/internal/store"
)

func snapshotPath(dir string, sceneId int32) string {
	return filepath.Join(dir, fmt.Sprintf("scene_%d.json", sceneId))
}

func saveSnapshot(user *store.UserState, dir string) {
	sceneId := user.MainQuest.CurrentQuestSceneId
	if sceneId == 0 {
		return
	}
	data, err := json.MarshalIndent(user, "", "  ")
	if err != nil {
		log.Printf("[snapshot] marshal error for scene=%d: %v", sceneId, err)
		return
	}
	path := snapshotPath(dir, sceneId)
	if err := os.WriteFile(path, data, 0644); err != nil {
		log.Printf("[snapshot] write error for scene=%d: %v", sceneId, err)
		return
	}
	log.Printf("[snapshot] saved scene=%d (%d bytes)", sceneId, len(data))
}

func loadSnapshot(dir string, sceneId int32) (*store.UserState, error) {
	path := snapshotPath(dir, sceneId)
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read snapshot scene=%d: %w", sceneId, err)
	}
	var user store.UserState
	if err := json.Unmarshal(data, &user); err != nil {
		return nil, fmt.Errorf("unmarshal snapshot scene=%d: %w", sceneId, err)
	}
	user.EnsureMaps()
	return &user, nil
}
