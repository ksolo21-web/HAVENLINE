extends RefCounted
## Deterministic native fixture. NOT actual world, contact or security evidence.
const Count = preload("res://exact_count.gd")
var revision := "1"
var facts: Dictionary = {}
var initial := {
	"authority_id": "fixture-world",
	"resources": ["wood", "steel", "cooked_fish", "money", "new_mineral"],
	"accounts": {
		"player": {"kind": "actor", "generation": 1, "items": {"wood": "1000", "steel": "1000", "cooked_fish": "9007199254740993", "money": "18446744073709551617", "new_mineral": "99999999999999999999999999999999999999999999999999"}},
		"warehouse": {"kind": "storage", "generation": 1, "items": {"wood": "5", "money": "4"}},
		"other-store": {"kind": "storage", "generation": 1, "items": {}}
	}
}
var garage := {"id": "garage", "generation": 1, "camp_id": "home", "ready": true, "plot_inside_camp": true, "construction_receipt_id": "completed-construction-1", "storage_id": "warehouse"}
var allowed_restore := ""
var validation_calls := 0
var invalidate_after_first_check := false
var forge_authority := false
var reentrant_target: Object
var reentrant_result: Dictionary = {}

func vehicle_authority_id() -> String: return "fixture-world"
func capture_vehicle_bootstrap() -> Dictionary: return initial.duplicate(true)
func validate_vehicle_bootstrap(value: Dictionary) -> bool: return Count.canonical(value) == Count.canonical(initial)
func capture_vehicle_observation(operation: String, parameters: Dictionary) -> Dictionary:
	validation_calls = 0
	if reentrant_target != null:
		reentrant_result = reentrant_target.admit_quote("evil", "nested")
	return {"authority_id": "forged" if forge_authority else vehicle_authority_id(), "revision": revision, "operation": operation, "parameters": parameters.duplicate(true), "facts": facts.duplicate(true)}
func validate_vehicle_observation(value: Dictionary) -> bool:
	validation_calls += 1
	return value.revision == revision and Count.canonical(value.facts) == Count.canonical(facts) and not (invalidate_after_first_check and validation_calls > 1)
func permit_restore(value: Dictionary) -> void: allowed_restore = Count.canonical(value).sha256_text()
func authorize_vehicle_restore(value: Dictionary) -> bool: return Count.canonical(value).sha256_text() == allowed_restore

func quote(quote_id := "q1", generation := 1) -> void:
	facts = {"quote": {"id": quote_id, "vehicle_id": "truck", "next_generation": generation, "garage_id": "garage", "garage_generation": garage.generation, "camp_id": "home", "payer_id": "player", "payer_generation": 1, "bill": {"wood": "100", "steel": "200"}, "max_hp": 100, "catalogue_version": "fixture-only"}, "garage": garage.duplicate(true), "acquisition_proof_id": "fixture-attainable-path"}
func buy() -> void: facts = {"garage": garage.duplicate(true), "acquisition_proof_id": "fixture-current-path"}
func load() -> void: facts = {"contact_id": "fixture-source-contact", "source_reachable": true, "source_available": true}
func dock() -> void:
	facts = {"garage": garage.duplicate(true), "receiver": {"id": "warehouse", "generation": 1, "working": true, "route_connected": true, "accepts_all_resources": true, "unbounded_logical_stock": true}, "hull_points": corners([-1,0,-2], [1,3,2]), "blade_points": corners([-2,0,-3],[2,1,-1]), "parking_min": [-3,-0.1,-4], "parking_max": [3,4,4], "speed": 0, "blade_speed": 0, "geometry_profile_id": "fixture-full-hull-plus-blades"}
func hit(contact := "hit1", outside := true, amount := 100) -> void:
	facts = {"contact_id": contact, "damage": amount, "truck_footprint": [[9,-2],[12,-2],[12,2],[9,2]] if outside else [[-2,-2],[2,-2],[2,2],[-2,2]], "camp_polygon": [[-10,-10],[10,-10],[10,10],[-10,10]], "camp_id": "home", "geometry_profile_id": "fixture-full-truck-footprint"}
func claim() -> void: facts = {"contact_id": "fixture-estate-contact", "cache_reachable": true, "recipient_available": true}
func corners(low: Array, high: Array) -> Array:
	var result := []
	for x in [low[0], high[0]]:
		for y in [low[1], high[1]]:
			for z in [low[2], high[2]]:
				result.append([x,y,z])
	return result
