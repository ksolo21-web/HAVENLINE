extends RefCounted
## Representative stock on each paid plate. The world count label displays the
## full balance. Positions leave room at the front for that painted quantity.

# Each wood mesh already contains the three tied logs. The rock pair uses
# unequal sizes, and alternating meat slices form two low stacks with a loose cut in front.
const WIDTHS := {
	"wood": [1.52],
	"stone": [1.06, .73],
	"meat": [.72, .72, .72, .72, .72, .72, .62],
}
const CENTERS := {
	"wood": [Vector3(0, 0, -.14)],
	"stone": [Vector3(-.32, 0, -.23), Vector3(.43, 0, .03)],
	"meat": [
		Vector3(-.43, 0, -.15), Vector3(.43, 0, -.15),
		Vector3(-.43, .26, -.15), Vector3(.43, .26, -.15),
		Vector3(-.43, .52, -.15), Vector3(.43, .52, -.15),
		Vector3(-.30, 0, .54),
	],
}

static func slot(kind: String, index: int) -> int:
	return clampi(index, 0, CENTERS[kind].size() - 1)

static func position(kind: String, index: int) -> Vector3:
	return CENTERS[kind][slot(kind, index)]

static func width(kind: String, index: int) -> float:
	return WIDTHS[kind][slot(kind, index)]
