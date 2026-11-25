extends RefCounted
## Target kind selects the harvesting tool. Trees take the axe, stone takes the pickaxe.

static func for_target(kind: String) -> String:
	if kind == "tree":
		return "axe"
	if kind == "rock":
		return "pickaxe"
	return ""
