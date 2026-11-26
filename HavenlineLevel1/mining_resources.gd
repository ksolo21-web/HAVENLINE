extends RefCounted
## Natural deposits in the playable World One field. Steel is a processed ingot.
const KINDS := ["stone", "metal", "coal", "slate"]
const REGROW_SECONDS := 5.0

static func bank_scale(kind: String) -> float:
	# The snow quarry has its original authored units. Other bank meshes are
	# grounded at their base and normalized to one metre across before placement.
	return preload("res://resource_rock.gd").BANK_SCALE if kind == "stone" else 2.20
