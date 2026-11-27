extends RefCounted
## Active simulation time only. Ordinary encounters keep their own wave clock.

const WARNING_SECONDS := 300.
const FIRST_WARNING_AFTER := 1200.
const REPEAT_MIN_WAIT := 2400.
const REPEAT_MAX_WAIT := 3300.
const FAILED_WAIT := 3300.
const ATTACK_SECONDS := 105.
const AWAY_DISTANCE := 24.
const MAX_HP := {
	"gate-south": 26, "gate-east": 26, "furnace": 36,
	"fence-south-west": 30, "fence-south-east": 30, "fence-east-north": 30,
	"fence-east-south": 30, "fence-north": 30, "fence-west": 30,
	"cooker": 28, "saw": 24, "drill": 30, "tower": 34
}
const PHASES := ["quiet", "warning", "attack"]
const CONSUMED_KINDS := ["wood", "stone", "metal"]
const ENTRANCES := ["gate-south", "gate-east", "fence-east-north", "fence-east-south"]

var phase := "quiet"
var seconds_left := FIRST_WARNING_AFTER
var entrance := ""
var raids_started := 0
var breaches_during_attack := false
var condition := {}
var spend := {}

func advance(delta: float, enabled: bool, unattended: bool, pick_entrance: Callable) -> String:
	if delta <= 0. or not is_finite(delta):
		return ""
	if phase == "quiet":
		if not enabled:
			return ""
		seconds_left = maxf(0., seconds_left - delta)
		if seconds_left > .000001 or not unattended:
			return ""
		var chosen: String = pick_entrance.call()
		if chosen not in ENTRANCES:
			return ""
		entrance = chosen
		phase = "warning"
		seconds_left = WARNING_SECONDS
		return "warning"
	seconds_left = maxf(0., seconds_left - delta)
	if seconds_left > .000001:
		return ""
	return "launch" if phase == "warning" else "expired"

func begin_attack() -> void:
	phase = "attack"
	seconds_left = ATTACK_SECONDS
	raids_started += 1
	breaches_during_attack = false

func end_attack(failed: bool, repeat_delay: float) -> void:
	phase = "quiet"
	seconds_left = FAILED_WAIT if failed else clampf(repeat_delay, REPEAT_MIN_WAIT, REPEAT_MAX_WAIT)
	entrance = ""
	breaches_during_attack = false

func hp(id: String) -> int:
	return int(condition.get(id, MAX_HP.get(id, 0)))

func is_down(id: String) -> bool:
	return MAX_HP.has(id) and hp(id) == 0

func damage(id: String, amount: int) -> bool:
	if phase != "attack" or not MAX_HP.has(id) or amount <= 0 or hp(id) <= 0:
		return false
	condition[id] = maxi(0, hp(id) - amount)
	if condition[id] == 0:
		breaches_during_attack = true
	return true

func repair_bill(id: String) -> Dictionary:
	if not MAX_HP.has(id):
		return {}
	var missing: int = int(MAX_HP[id]) - hp(id)
	if missing == 0:
		return {}
	if id == "furnace":
		if hp(id) == 0:
			return {"wood": 16, "stone": 25, "metal": 8}
		return {"wood": ceili(missing / 9.), "stone": ceili(missing / 5.)}
	if id.begins_with("gate") or id.begins_with("fence"):
		return {"wood": ceili(missing / 4.), "stone": ceili(missing / 12.)}
	if hp(id) == 0:
		return {"wood": 12, "stone": 8, "metal": 5}
	return {"wood": ceili(missing / 7.), "metal": ceili(missing / 10.)}

func finish_repair(id: String) -> void:
	var bill := repair_bill(id)
	for kind: String in bill:
		spend[kind] = int(spend.get(kind, 0)) + int(bill[kind])
	condition.erase(id)

func snapshot() -> Dictionary:
	return {
		"phase": phase, "seconds_left": seconds_left, "entrance": entrance,
		"raids_started": raids_started, "breaches": breaches_during_attack,
		"condition": condition.duplicate(), "repair_spend": spend.duplicate()
	}

static func _number(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value)) and value >= 0.

static func _whole(value: Variant) -> bool:
	return _number(value) and float(value) <= 9007199254740991. and value == int(value)

static func valid_spend(amounts: Variant) -> bool:
	if not amounts is Dictionary or amounts.size() > CONSUMED_KINDS.size():
		return false
	for kind in amounts:
		if kind not in CONSUMED_KINDS or not _whole(amounts[kind]) or int(amounts[kind]) == 0:
			return false
	return true

static func repair_spend(snapshot: Variant) -> Variant:
	if not snapshot is Dictionary:
		return null
	if not snapshot.has("pack"):
		return {}
	if not snapshot.pack is Dictionary:
		return null
	if not snapshot.pack.has("raid"):
		return {}
	if not snapshot.pack.raid is Dictionary:
		return null
	var amounts: Variant = snapshot.pack.raid.get("repair_spend")
	return amounts if valid_spend(amounts) else null

func restore(data: Variant) -> bool:
	if data == null:
		return true
	if not data is Dictionary or data.get("phase") not in PHASES or not _number(data.get("seconds_left")):
		return false
	if not _whole(data.get("raids_started")) or not data.get("breaches") is bool or not valid_spend(data.get("repair_spend")):
		return false
	var states: Variant = data.get("condition")
	if not states is Dictionary or states.size() > MAX_HP.size():
		return false
	for id in states:
		if not MAX_HP.has(id) or not _whole(states[id]) or int(states[id]) >= int(MAX_HP[id]):
			return false
	match data.phase:
		"quiet":
			if data.get("entrance") != "" or data.seconds_left > REPEAT_MAX_WAIT or data.breaches:
				return false
		"warning":
			if data.get("entrance") not in ENTRANCES or data.seconds_left > WARNING_SECONDS or data.breaches:
				return false
		"attack":
			if data.get("entrance") not in ENTRANCES or data.seconds_left > ATTACK_SECONDS or data.raids_started < 1:
				return false
	phase = data.phase
	seconds_left = float(data.seconds_left)
	entrance = data.entrance
	raids_started = int(data.raids_started)
	breaches_during_attack = data.breaches
	condition = states.duplicate()
	spend = data.repair_spend.duplicate()
	return true
