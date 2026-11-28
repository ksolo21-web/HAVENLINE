extends RefCounted
const Finish = preload("res://field_finishes.gd")
## The authored bank stays the strike surface until the finishing contact.
## Its four cut sections retain the bank's actual exterior materials and UVs.
const SEAM := preload("res://assets/mining_fracture/working_face.gdshader")
const PIECES := {
	"stone":preload("res://assets/mining_fracture/stone.glb"),
	"slate":preload("res://assets/mining_fracture/slate.glb"),
	"coal":preload("res://assets/mining_fracture/coal.glb"),
	"metal":preload("res://assets/mining_fracture/metal.glb")
}
const FRESH_FACE := {"stone":Color("#817363"),"slate":Color("#526379"),"coal":Color("#2e323c"),"metal":Color("#53545b")}
const DURATION := .43
static var seams := {}
var exposed_seam: MeshInstance3D
var debris: Node3D
var shards := []
var age := 0.

func show_contacts(part: MeshInstance3D, count: int) -> void:
	if count < 1 or count > 2:
		if exposed_seam: exposed_seam.hide()
		return
	if not seams.has(part.mesh): seams[part.mesh] = {}
	var stages: Dictionary = seams[part.mesh]
	if not stages.has(count):
		var seam := ShaderMaterial.new()
		seam.shader = SEAM
		var bounds := part.mesh.get_aabb()
		seam.set_shader_parameter("bank_center",bounds.get_center())
		seam.set_shader_parameter("bank_size",bounds.size[bounds.size.max_axis_index()])
		seam.set_shader_parameter("contacts",float(count))
		stages[count] = seam
	if not exposed_seam:
		exposed_seam = MeshInstance3D.new()
		exposed_seam.name = "ExposedFissure"
		exposed_seam.mesh = part.mesh
		exposed_seam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		exposed_seam.material_override = stages[count]
		part.add_child(exposed_seam)
	else:
		exposed_seam.material_override = stages[count]
		exposed_seam.show()

func separate(part: MeshInstance3D, kind: String) -> void:
	clear()
	debris = PIECES[kind].instantiate()
	part.get_parent().add_child(debris)
	debris.transform = part.transform
	var interior := Finish.paint(FRESH_FACE[kind],.96)
	var bank_center := part.mesh.get_aabb().get_center()
	for shard: MeshInstance3D in debris.find_children("*","MeshInstance3D",true,false):
		for surface in shard.mesh.get_surface_count():
			var slot := shard.mesh.surface_get_material(surface).resource_name
			var material: Material = interior
			if slot.begins_with("bank_surface_"):
				material = part.mesh.surface_get_material(int(slot.trim_prefix("bank_surface_")))
			shard.set_surface_override_material(surface,material)
		var pivot := shard.mesh.get_aabb().get_center()
		var radial := pivot-bank_center
		radial.y = 0.
		shards.append({"piece":shard,"pivot":pivot,"out":radial.normalized()})
	age = 0.
	advance(0.)

func advance(dt: float) -> void:
	if not debris: return
	age = minf(DURATION,age+dt)
	if age >= DURATION:
		clear()
		return
	var t := age / DURATION
	for row: Dictionary in shards:
		var out: Vector3 = row.out
		var pivot: Vector3 = row.pivot
		var axis := Vector3.UP.cross(out)
		var rotation := Basis(axis, .025+.55*t) if axis.length_squared()>.9 else Basis.IDENTITY
		var frame := rotation.scaled(Vector3.ONE*lerpf(1.,.045,smoothstep(.43,1.,t)))
		# Scale and tumble around each piece's centroid rather than the shared model origin.
		var lift := .16*sin(PI*t)-.24*t*t
		row.piece.transform = Transform3D(frame,pivot-frame*pivot+out*(.06+.32*t)+Vector3.UP*lift)

func clear() -> void:
	if debris:
		debris.hide()
		debris.queue_free()
		debris = null
	shards.clear()
