extends RefCounted

const HEARTH := "center_hearth"
const FIRST := "expansion_1"
const SECOND := "expansion_2"
const TOWER := "watchtower"
const AXES := "orbit_upgrade"
const MACHINES := {"wood":"saw_bench", "stone":"quarry_drill", "meat":"camp_cooker"}
const FOOD_LINE := "meal_conveyor"
const SUPPLY_LINE := "supply_conveyors"
const LINES := [FOOD_LINE,SUPPLY_LINE]
const STORAGE := ["storage_wood", "storage_stone", "storage_meat"]
const PREREQUISITES := {
	"center_hearth": [], "expansion_1": ["center_hearth"],
	"storage_wood": ["expansion_1"], "storage_stone": ["expansion_1"], "storage_meat": ["expansion_1"],
	"expansion_2": STORAGE, "watchtower": ["expansion_2"], "orbit_upgrade": ["expansion_2"],
	"camp_cooker": ["expansion_2"], "saw_bench": ["camp_cooker"], "quarry_drill": ["saw_bench"],
	"meal_conveyor": ["camp_cooker"], "supply_conveyors": ["camp_cooker","storage_meat"]
}
const TITLES := {
	"center_hearth":"Build hearth", "expansion_1":"Expand camp", "expansion_2":"Expand east",
	"storage_wood":"Build storehouse", "storage_stone":"Reinforce storehouse", "storage_meat":"Advance storehouse",
	"watchtower":"Build watchtower", "orbit_upgrade":"Equip extra axes",
	"camp_cooker":"Build cooker", "saw_bench":"Build saw bench", "quarry_drill":"Build quarry drill",
	"meal_conveyor":"Automate meal service", "supply_conveyors":"Connect storehouse supply"
}
const POSITIONS := {"expansion_1":Vector2(2.6,-1.5), "expansion_2":Vector2(2.6,-1.5),
	"watchtower":Vector2(8.1,-2.4), "orbit_upgrade":Vector2(7.6,2.9),
	"camp_cooker":Vector2(.55,-5.22), "saw_bench":Vector2(-8.55,-5.05), "quarry_drill":Vector2(-7.15,.70),
	"meal_conveyor":Vector2(3.65,-5.30), "supply_conveyors":Vector2(.25,-3.85)}

# Receipts, carry meshes and machine inputs are physical bundles. Each bundle
# contains ten raw units; a tree/bank awards three bundles, a wolf two.
const UNITS_PER_BUNDLE := 10
const SURVIVOR := "survivor_plot"
const SURVIVOR_BUNDLES := 8
const OLD_SURVIVOR_BUNDLES := 2
const OFFERS := {
	"center_hearth":{"wood":20}, "expansion_1":{"wood":12,"stone":6},
	"storage_wood":{"wood":10}, "storage_stone":{"wood":8,"stone":6}, "storage_meat":{"wood":7,"meat":5},
	"expansion_2":{"wood":15,"stone":10},
	"camp_cooker":{"wood":12,"stone":8}, "saw_bench":{"wood":14,"stone":6}, "quarry_drill":{"wood":10,"stone":12},
	"watchtower":{"wood":12,"stone":10}, "orbit_upgrade":{"stone":6,"meat":4},
	"meal_conveyor":{"wood":10,"stone":6}, "supply_conveyors":{"wood":16,"stone":12}
}

static func units(bundles: int) -> int:
	return bundles * UNITS_PER_BUNDLE

static func offers(_opening_cost: Dictionary = {}) -> Dictionary:
	return OFFERS.duplicate(true)

# Recipes printed in v1–v5. A previously offered price becomes a contract on
# its first committed payment. Unfunded offers use the current recipes.
static func old_offers() -> Dictionary:
	return {HEARTH:{"wood":3}, FIRST:{"wood":3,"stone":1},
		"storage_wood":{"wood":2}, "storage_stone":{"wood":2,"stone":1}, "storage_meat":{"wood":2,"meat":1},
		SECOND:{"wood":3,"stone":2}, TOWER:{"wood":3,"stone":2}, AXES:{"stone":2,"meat":1}}

static func stage(ledger) -> int:
	if ledger.complete(SECOND): return 3
	if ledger.complete(FIRST): return 2
	return 1 if ledger.complete(HEARTH) else 0

static func price_text(remaining: Dictionary) -> String:
	var words := PackedStringArray()
	for kind in ["wood","stone","meat"]:
		if int(remaining.get(kind,0)) > 0: words.append("%d %s" % [units(remaining[kind]), kind])
	return " · ".join(words)


static func house_tier(ledger) -> int:
	for i in range(STORAGE.size()-1,-1,-1):
		if ledger.complete(STORAGE[i]): return i+1
	return 0

static func next_storage(ledger) -> String:
	if not ledger.complete(FIRST): return ""
	for id: String in STORAGE:
		if not ledger.complete(id): return id
	return ""


static func next_build(ledger) -> String:
	var first := ""
	for id: String in OFFERS:
		if id in LINES or not ledger.offer_open(id): continue
		if first.is_empty(): first = id
		for paid in ledger.paid[id].values():
			if paid > 0: return id
	return first
