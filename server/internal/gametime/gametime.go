package gametime

import "time"

func Now() time.Time {
	return time.Now().UTC()
}

func NowMillis() int64 {
	return Now().UnixMilli()
}
