package gametime

import "time"

var (
	realBaseTime = time.Now()
	fakeBaseTime = time.Date(2024, 4, 4, 12, 0, 0, 0, time.UTC)
)

// Now returns the current game time as a time.Time.
// Maps real elapsed time onto an April 2024 base so the client sees
// timestamps consistent with the master data release window.
func Now() time.Time {
	return fakeBaseTime.Add(time.Since(realBaseTime))
}

// NowMillis returns Now() as Unix milliseconds.
func NowMillis() int64 {
	return Now().UnixMilli()
}
