package store

import (
	"errors"
	"time"
)

var ErrNotFound = errors.New("store: not found")

type Clock func() time.Time

type UserRepository interface {
	EnsureUser(uuid string) (UserState, error)
	SnapshotUser(userId int64) (UserState, error)
	UpdateUser(userId int64, mutate func(*UserState)) (UserState, error)
	DefaultUserId() (int64, error)
}

type SessionRepository interface {
	CreateSession(uuid string, ttl time.Duration) (UserState, SessionState, error)
	ResolveUserId(sessionKey string) (int64, error)
}

type GachaRepository interface {
	SnapshotCatalog() ([]GachaCatalogEntry, error)
	ReplaceCatalog(entries []GachaCatalogEntry) error
}
