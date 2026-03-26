package memory

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"lunar-tear/server/internal/store"
)

type Option func(*MemoryStore)

func WithSnapshotDir(dir string) Option {
	return func(s *MemoryStore) {
		s.snapshotDir = dir
	}
}

func WithSceneId(sceneId int32) Option {
	return func(s *MemoryStore) {
		s.bootstrapSceneId = sceneId
	}
}

func WithStarterItems(v bool) Option {
	return func(s *MemoryStore) {
		s.starterItems = v
	}
}

type MemoryStore struct {
	mu                  sync.RWMutex
	clock               store.Clock
	bootstrapSceneId    int32
	snapshotDir         string
	starterItems        bool
	lastSnapshotSceneId int32
	nextUserId          int64
	users               map[int64]*store.UserState
	userIdsByUuid       map[string]int64
	sessionToUserId     map[string]int64
	sessions            map[string]store.SessionState
	gachaCatalog        map[int32]store.GachaCatalogEntry
}

var (
	_ store.UserRepository    = (*MemoryStore)(nil)
	_ store.SessionRepository = (*MemoryStore)(nil)
	_ store.GachaRepository   = (*MemoryStore)(nil)
)

func New(clock store.Clock, options ...Option) *MemoryStore {
	if clock == nil {
		clock = time.Now
	}
	s := &MemoryStore{
		clock:           clock,
		nextUserId:      defaultUserId,
		users:           make(map[int64]*store.UserState),
		userIdsByUuid:   make(map[string]int64),
		sessionToUserId: make(map[string]int64),
		sessions:        make(map[string]store.SessionState),
		gachaCatalog:    make(map[int32]store.GachaCatalogEntry),
	}
	for _, opt := range options {
		opt(s)
	}
	return s
}

func (s *MemoryStore) EnsureUser(uuid string) (store.UserState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return cloneUserState(*s.getOrCreateLocked(normalizeUUID(uuid))), nil
}

func (s *MemoryStore) CreateSession(uuid string, ttl time.Duration) (store.UserState, store.SessionState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	user := s.getOrCreateLocked(normalizeUUID(uuid))
	now := s.clock()
	session := store.SessionState{
		SessionKey: fmt.Sprintf("session_%d_%d", user.UserId, now.UnixNano()),
		UserId:     user.UserId,
		Uuid:       user.Uuid,
		ExpireAt:   now.Add(ttl),
	}

	s.sessionToUserId[session.SessionKey] = user.UserId
	s.sessions[session.SessionKey] = session

	return cloneUserState(*user), session, nil
}

func (s *MemoryStore) ResolveUserId(sessionKey string) (int64, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	userId, ok := s.sessionToUserId[sessionKey]
	if !ok {
		return 0, store.ErrNotFound
	}
	return userId, nil
}

func (s *MemoryStore) SnapshotUser(userId int64) (store.UserState, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	user, ok := s.users[userId]
	if !ok {
		return store.UserState{}, store.ErrNotFound
	}
	return cloneUserState(*user), nil
}

func (s *MemoryStore) UpdateUser(userId int64, mutate func(*store.UserState)) (store.UserState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	user, ok := s.users[userId]
	if !ok {
		return store.UserState{}, store.ErrNotFound
	}
	mutate(user)
	sceneId := user.MainQuest.CurrentQuestSceneId
	if s.snapshotDir != "" && sceneId != 0 && sceneId != s.lastSnapshotSceneId {
		saveSnapshot(user, s.snapshotDir)
		s.lastSnapshotSceneId = sceneId
	}
	return cloneUserState(*user), nil
}

func (s *MemoryStore) DefaultUserId() (int64, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if _, ok := s.users[defaultUserId]; ok {
		return defaultUserId, nil
	}
	if len(s.users) == 0 {
		return defaultUserId, nil
	}

	var minUserId int64
	for userId := range s.users {
		if minUserId == 0 || userId < minUserId {
			minUserId = userId
		}
	}
	return minUserId, nil
}

func (s *MemoryStore) SnapshotCatalog() ([]store.GachaCatalogEntry, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	out := make([]store.GachaCatalogEntry, 0, len(s.gachaCatalog))
	for _, entry := range s.gachaCatalog {
		out = append(out, cloneGachaCatalogEntry(entry))
	}
	return out, nil
}

func (s *MemoryStore) ReplaceCatalog(entries []store.GachaCatalogEntry) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.gachaCatalog = make(map[int32]store.GachaCatalogEntry, len(entries))
	for _, entry := range entries {
		s.gachaCatalog[entry.GachaId] = cloneGachaCatalogEntry(entry)
	}
	return nil
}

func (s *MemoryStore) getOrCreateLocked(uuid string) *store.UserState {
	if userId, ok := s.userIdsByUuid[uuid]; ok {
		return s.users[userId]
	}

	userId := s.nextUserId
	s.nextUserId++

	user := seedUserState(userId, uuid, s.clock().UnixMilli(), s.bootstrapSceneId, s.snapshotDir, s.starterItems)
	s.users[userId] = user
	s.userIdsByUuid[uuid] = userId
	return user
}

func normalizeUUID(uuid string) string {
	uuid = strings.TrimSpace(uuid)
	if uuid == "" {
		return defaultUUID
	}
	return uuid
}
