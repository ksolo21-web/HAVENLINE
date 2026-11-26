extends RefCounted
## Storage display follows the approved stocked-plot turnaround sheets.
## Coordinates leave the front of each inset clear for its painted quantity.

const WIDTH := {"wood": .91, "stone": .84, "meat": .72}
const FOOTPRINT := {
	"wood": [Vector2(-.50,-.42), Vector2(.50,-.42), Vector2(0,.25)],
	"stone": [Vector2(-.49,-.25), Vector2(.47,.10), Vector2(.45,-.55)],
	"meat": [Vector2(-.43,-.15), Vector2(.43,-.15)],
}
# Heights are measured on the scaled source meshes. Small overlaps seat the
# irregular surfaces together and follow the bevel along the edge of each steak.
const COURSE_HEIGHT := {"wood": .594, "stone": .525, "meat": .344}

static func position(kind: String, index: int) -> Vector3:
	var slots: Array = FOOTPRINT[kind]
	var n := maxi(0,index)
	var center: Vector2 = slots[n % slots.size()]
	return Vector3(center.x, floori(float(n)/slots.size()) * float(COURSE_HEIGHT[kind]), center.y)
