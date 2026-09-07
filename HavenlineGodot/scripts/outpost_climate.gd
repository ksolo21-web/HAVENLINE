extends RefCounted
# Simulation-time clock. Pausing/suspending cannot advance weather or accrue debt.
const DAY_SECONDS := 1200.0
const WEATHER_SECONDS := 900.0
const START_HOUR := 10.0
const MAX_SECONDS := 315360000.0
const STAGES := [
	{"name":"Clear", "start":0.0, "snow":0.03, "wind":0.14},
	{"name":"Flurries", "start":180.0, "snow":0.27, "wind":0.30},
	{"name":"Snowfall", "start":360.0, "snow":0.60, "wind":0.48},
	{"name":"Blizzard", "start":540.0, "snow":1.0, "wind":0.90},
	{"name":"Clearing", "start":720.0, "snow":0.18, "wind":0.23}
]
var seconds := 0.0

func step(dt: float):
	if not is_finite(dt) or dt <= 0.0: return
	seconds = minf(MAX_SECONDS, seconds + minf(dt, 0.1))

func hour() -> float:
	return fposmod(START_HOUR + seconds / DAY_SECONDS * 24.0, 24.0)

func day_number() -> int:
	return 1 + int(floor((START_HOUR / 24.0) + seconds / DAY_SECONDS))

func daylight() -> float:
	return smoothstep(-0.12, 0.38, sin((hour() - 6.0) * PI / 12.0))

func weather() -> Dictionary:
	var phase := fposmod(seconds, WEATHER_SECONDS)
	var index := mini(int(phase / 180.0), STAGES.size() - 1)
	var stage: Dictionary = STAGES[index]
	var previous: Dictionary = STAGES[(index + STAGES.size() - 1) % STAGES.size()]
	# Start a new game clear; subsequent transitions blend continuously for 24s.
	if seconds < 180.0: previous = STAGES[0]
	var blend := smoothstep(0.0, 24.0, phase - float(stage.start))
	return {"name":stage.name, "snow":lerpf(previous.snow, stage.snow, blend),
		"wind":lerpf(previous.wind, stage.wind, blend), "transition":blend}

func cold_multiplier() -> float:
	return 1.0 + maxf(0.0, float(weather().snow) - 0.03) * 0.9 + (1.0 - daylight()) * 0.25

func snapshot() -> Dictionary:
	return {"revision":1, "seconds":seconds}

func restore(value) -> bool:
	if not value is Dictionary or value.size() != 2: return false
	var revision = value.get("revision")
	if not numeric(revision) or float(revision) != 1.0: return false
	var clock = value.get("seconds")
	if not numeric(clock) or clock < 0.0 or clock > MAX_SECONDS: return false
	seconds = float(clock)
	return true

static func numeric(value) -> bool:
	return (value is float or value is int) and is_finite(float(value))
