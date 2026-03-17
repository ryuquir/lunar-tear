package mock

import (
	pb "lunar-tear/server/gen/proto"
)

// EmptyDiff returns an empty DiffUserData map (no table updates).
// Use when the RPC has nothing to sync.
func EmptyDiff() map[string]*pb.DiffData {
	return map[string]*pb.DiffData{}
}
