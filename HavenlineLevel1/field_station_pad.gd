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
const SLOT_WIDTH := .22
static var decks := {}
static var paint: StandardMaterial3D

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
	var foot := _rim(1.487,1.236,corner,.001)
	var fascia := _rim(1.487,1.236,corner,.018)
	var curb := _rim(1.457,1.206,corner,.034)
	var metal := _rim(1.427,1.176,corner,.035)
	var fill := _rim(1.411,1.160,corner,.034)
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

static func glyph_socket(parent: Node3D, y := FACE_Y) -> Marker3D:
	var socket := Marker3D.new()
	socket.name = "IconSocket"
	socket.position = Vector3(0.,y+.012,-SLOT_WIDTH)
	parent.add_child(socket)
	return socket
