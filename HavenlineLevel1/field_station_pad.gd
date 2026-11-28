extends RefCounted
## Shallow deck below the original interactive face. Its thickness is visual only.
const FACE_Y := .039
const COLORS := {
	"build": Color("#af633b"),
	"upgrade": Color("#bd8e4c"),
	"input": Color("#407798"),
	"output": Color("#498b7a"),
	"stock": Color("#718293"),
	"payment": Color("#a77346"),
}
const SILHOUETTES := {
	"build": Vector2(.15,.15),
	"upgrade": Vector2(.27,.19),
	"input": Vector2(.30,.10),
	"output": Vector2(.10,.30),
	"stock": Vector2(.085,.085),
	"payment": Vector2(.22,.22),
}
const FACES := {
	"build": Color("#9eabb6"),
	"upgrade": Color("#855c3e"),
	"input": Color("#596c7a"),
	"output": Color("#566b60"),
	"stock": Color("#554732"),
	"payment": Color("#71523c"),
}
const FRAME := {
	"build":Vector2(1.487,1.236), "upgrade":Vector2(1.515,1.253),
	"input":Vector2(1.555,1.238), "output":Vector2(1.484,1.299),
	"stock":Vector2(1.510,1.257), "payment":Vector2(1.538,1.259),
}
# Separated strokes retain the same meanings at the short gameplay camera span.
const STROKES := {
	"build":[[Vector2(-.31,.24),Vector2(-.31,-.15),Vector2(0,-.34),Vector2(.31,-.15),Vector2(.31,.24),Vector2(-.31,.24)],
		[Vector2(-.10,.24),Vector2(-.10,-.01),Vector2(.10,-.01),Vector2(.10,.24)]],
	"upgrade":[[Vector2(-.29,.23),Vector2(.13,-.17)], [Vector2(-.11,-.24),Vector2(.16,-.32),Vector2(.35,-.09),Vector2(.16,.02),Vector2(-.11,-.24)],
		[Vector2(.01,.22),Vector2(.25,.22)],[Vector2(.13,.10),Vector2(.13,.34)]],
	"input":[[Vector2(-.32,-.28),Vector2(-.32,.13),Vector2(.32,.13),Vector2(.32,-.28)],
		[Vector2(0,-.32),Vector2(0,.02)],[Vector2(-.14,-.11),Vector2(0,.02),Vector2(.14,-.11)]],
	"output":[[Vector2(-.32,.30),Vector2(-.32,.04),Vector2(.32,.04),Vector2(.32,.30),Vector2(-.32,.30)],
		[Vector2(0,.02),Vector2(0,-.34)],[Vector2(-.14,-.20),Vector2(0,-.34),Vector2(.14,-.20)]],
	"stock":[[Vector2(-.31,-.15),Vector2(0,-.30),Vector2(.31,-.15),Vector2(.31,.15),Vector2(0,.30),Vector2(-.31,.15),Vector2(-.31,-.15),Vector2(0,0),Vector2(.31,-.15)],
		[Vector2(0,0),Vector2(0,.30)],[Vector2(-.16,-.23),Vector2(.17,-.08)]],
	"payment":[[Vector2(-.32,-.19),Vector2(.32,-.19),Vector2(.32,.19),Vector2(-.32,.19),Vector2(-.32,-.19)],
		[Vector2(-.28,.30),Vector2(.36,.30),Vector2(.36,-.09)],
		[Vector2(-.09,0),Vector2(0,-.075),Vector2(.09,0),Vector2(0,.075),Vector2(-.09,0)]],
}
const SLOT_WIDTH := .22
static var decks := {}
static var paint: StandardMaterial3D
static var stamp_paint: StandardMaterial3D
static var stamps := {}

static func bracket_color(focused: bool) -> Color:
	return Color("#5be72e") if focused else Color("#f8fbff")

static func create(role: String) -> MeshInstance3D:
	if not decks.has(role):
		decks[role] = _deck(role)
	var deck := MeshInstance3D.new()
	deck.name = "Platform"
	deck.mesh = decks[role]
	deck.material_override = paint
	# The original plate was unshadowed. The extremely thin frame should not
	# consume another shadow submission or darken the inlaid text.
	deck.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return deck

static func _rim(x: float, z: float, corner: Vector2, y: float) -> PackedVector3Array:
	return PackedVector3Array([
		Vector3(x-corner.x,y,-z), Vector3(x,y,-z+corner.y),
		Vector3(x,y,z-corner.y), Vector3(x-corner.x,y,z),
		Vector3(-x+corner.x,y,z), Vector3(-x,y,z-corner.y),
		Vector3(-x,y,-z+corner.y), Vector3(-x+corner.x,y,-z),
	])

static func _strip(tool: SurfaceTool, outer: PackedVector3Array, inner: PackedVector3Array, tint: Color) -> void:
	tool.set_color(tint)
	for i in outer.size():
		var j := (i+1)%outer.size()
		for vertex in [outer[i],outer[j],inner[j],outer[i],inner[j],inner[i]]:
			tool.add_vertex(vertex)

static func _deck(role: String) -> ArrayMesh:
	if paint == null:
		paint = StandardMaterial3D.new()
		paint.vertex_color_use_as_albedo = true
		paint.vertex_color_is_srgb = true
		paint.roughness = .86
		paint.cull_mode = BaseMaterial3D.CULL_DISABLED
	var trim: Color = COLORS[role]
	var corner: Vector2 = SILHOUETTES[role]
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Corners are chamfered outside the exact T04 interaction border.
	var span: Vector2 = FRAME[role]
	var foot := _rim(span.x,span.y,corner,.001)
	var fascia := _rim(span.x,span.y,corner,.018)
	var curb := _rim(span.x-.027,span.y-.027,corner,.034)
	var metal := _rim(span.x-.059,span.y-.059,corner,.035)
	var fill := _rim(1.370,1.129,corner,.034)
	var inset := _rim(1.18,.94,Vector2(.03,.03),.034)
	_strip(tool,foot,fascia,Color("#464b55"))
	_strip(tool,fascia,curb,trim.darkened(.27))
	_strip(tool,curb,metal,trim)
	_strip(tool,metal,fill,trim.lightened(.23))
	_strip(tool,fill,inset,Color("#65717c"))
	# Close beneath the inherited shader face so the tapered corners read as
	# one solid piece in overhead and side captures.
	_strip(tool,inset,_rim(.005,.005,Vector2(.002,.002),.034),Color("#65717c"))
	tool.generate_normals()
	return tool.commit()

static func ground_color(ink: ShaderMaterial, role: String) -> void:
	ink.set_shader_parameter("grounded",FACES[role])

static func glyph_socket(parent: Node3D, role: String, with_emblem := true) -> Marker3D:
	var socket := Marker3D.new()
	socket.name = "IconSocket"
	socket.position = Vector3(0.,FACE_Y+.012,-SLOT_WIDTH)
	parent.add_child(socket)
	if with_emblem:
		var emblem := MeshInstance3D.new()
		emblem.name = "InlaidPurpose"
		if not stamps.has(role): stamps[role] = _stamp(role)
		emblem.mesh = stamps[role]
		emblem.material_override = stamp_paint
		emblem.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		socket.add_child(emblem)
	return socket

static func _stamp(role: String) -> ArrayMesh:
	if stamp_paint == null:
		stamp_paint = StandardMaterial3D.new()
		stamp_paint.albedo_color = Color("#fff1d8")
		stamp_paint.cull_mode = BaseMaterial3D.CULL_DISABLED
		stamp_paint.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	for stroke in STROKES[role]:
		for i in range(1,stroke.size()):
			var a: Vector2 = stroke[i-1]*1.28
			var b: Vector2 = stroke[i]*1.28
			var across := (b-a).orthogonal().normalized()*.032
			for v in [a-across,a+across,b+across,a-across,b+across,b-across]:
				tool.add_vertex(Vector3(v.x,0,v.y))
	return tool.commit()
