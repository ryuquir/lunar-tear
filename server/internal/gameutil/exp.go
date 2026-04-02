package gameutil

// LevelAndCap returns the level for the given cumulative EXP based on
// the thresholds slice, and clamps EXP so it never exceeds the last
// threshold (max-level cap).
func LevelAndCap(exp int32, thresholds []int32) (level, capped int32) {
	level = 1
	for lvl := 1; lvl < len(thresholds); lvl++ {
		if exp >= thresholds[lvl] {
			level = int32(lvl)
		} else {
			break
		}
	}
	if len(thresholds) > 0 && exp > thresholds[len(thresholds)-1] {
		exp = thresholds[len(thresholds)-1]
	}
	return level, exp
}
