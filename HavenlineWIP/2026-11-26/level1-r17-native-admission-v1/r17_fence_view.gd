extends "res://previews/integrated_opening.gd"
## Detached wall shell. The original camp builds first and owns every authority.
const R17_PANEL: Mesh = preload("res://previews/r17_fence/assets/fence_panel.obj")
const R17_POST: Mesh = preload("res://previews/r17_fence/assets/gate_post.obj")
const R17_SHADER: Shader = preload("res://previews/r17_fence/assets/t03_boundary_v2.gdshader")
const WALL_COUNTS := [2, 2, 1, 1, 3, 3]
const PANEL_SOURCE_LENGTH := 2.9409
const WALL_DEPTH_SCALE := 1.95
const PANEL_DEPTH_RECENTER := .005 * WALL_DEPTH_SCALE
const POST_SCALE := Vector3(1.12, 1.14, 1.12)
const POST_CENTER_BACKSET := .19616 # .168 * 1.12 + .008 beyond exact half span.
const JOIN := .012
var _r17_materials: Dictionary = {}

func setup_camp() -> void:
	super.setup_camp()
	# Keep the original entirely intact if layout drift or donor import disagrees.
	if layout.walls_xz.size() != 6 or gates.size() != 2 or camp_colliders.size() != 7:
		return
	if R17_PANEL.get_surface_count() != 2 or R17_POST.get_surface_count() != 3:
		return
	var old_visuals: Array[MeshInstance3D] = []
	var panel_transforms: Array[Transform3D] = []
	var post_transforms: Array[Transform3D] = []
	for i in range(6):
		var row: Array = layout.walls_xz[i]
		var width := float(row[2])
		var depth := float(row[3])
		var long_x := width > depth
		var run := width if long_x else depth
		var count: int = WALL_COUNTS[i]
		var axis := Vector3.RIGHT if long_x else Vector3.BACK
		var cross := axis.cross(Vector3.UP)
		var wall := camp_colliders[i]
		var stock := wall.get_child(0) as MeshInstance3D
		if not stock or not stock.mesh is BoxMesh or not is_equal_approx(minf(width, depth), .30):
			return
		old_visuals.append(stock)
		var center := Vector3(wall.position.x, 0, wall.position.z)
		for j in range(count):
			var start_along := -run * .5 + run * float(j) / count
			var end_along := -run * .5 + run * float(j + 1) / count
			if j > 0:
				start_along -= JOIN * .5
			if j + 1 < count:
				end_along += JOIN * .5
			var a := center + axis * start_along
			var b := center + axis * end_along
			var base_y := _r17_seat(a, b, cross, .14742)
			var at := (a + b) * .5 + cross * PANEL_DEPTH_RECENTER
			at.y = base_y
			var orientation := Basis(axis * ((end_along - start_along) / PANEL_SOURCE_LENGTH), Vector3.UP, cross * WALL_DEPTH_SCALE)
			panel_transforms.append(Transform3D(orientation, at))
	for gate in gates:
		var axis := gate.basis.x.normalized()
		var cross := axis.cross(Vector3.UP)
		for side in [-1, 1]:
			var hinge_xz := gate.position + axis * (Gate.HALF_SPAN * float(side))
			var at := hinge_xz + axis * (POST_CENTER_BACKSET * float(side))
			# Marker names may get deduplicated under the same parent, so don't
			# assume a matching NodePath for both sides (see exact-position scan).
			var stock := _r17_marker(gate, side)
			if not stock:
				return
			old_visuals.append(stock)
			at.y = _r17_seat(at - axis * .18816, at + axis * .18816, cross, .19309)
			var orientation := Basis(axis * POST_SCALE.x, Vector3.UP * POST_SCALE.y, cross * POST_SCALE.z)
			post_transforms.append(Transform3D(orientation, at))
	var panels := _r17_mesh(R17_PANEL)
	var posts := _r17_mesh(R17_POST)
	if not panels or not posts:
		return
	var shell := Node3D.new()
	shell.name = "R17FenceViewOnly"
	camp_built.add_child(shell)
	_r17_batch(shell, "R17WallPanels", panels, panel_transforms)
	_r17_batch(shell, "R17ThresholdPosts", posts, post_transforms)
	for mesh in old_visuals:
		mesh.hide()

func _r17_marker(gate: Node3D, side: int) -> MeshInstance3D:
	var keys := Vector2(gate.position.x, gate.position.z)
	var axis := gate.basis.x.normalized()
	keys += Vector2(axis.x, axis.z) * (2.40 * .52 * float(side))
	for child in camp_built.get_children():
		if child is Node3D and not child is CollisionObject3D and child.get_child_count() == 1:
			var marker := child.get_child(0) as MeshInstance3D
			if marker and marker.mesh is BoxMesh and marker.mesh.size.is_equal_approx(Vector3(.20, 1.44, .20)):
				if Vector2(child.position.x, child.position.z).distance_to(keys) <= .001:
					return marker
	return null

func _r17_seat(a: Vector3, b: Vector3, cross: Vector3, extent: float) -> float:
	var low := INF
	for sample in range(17):
		var line := a.lerp(b, float(sample) / 16.0)
		for f in [-1.0, 0.0, 1.0]:
			var p := line + cross * (float(f) * extent)
			low = minf(low, float(Terrain.sample(Vector2(p.x, p.z)).height))
	return low - .04

func _r17_mesh(source: Mesh) -> Mesh:
	var copy := source.duplicate() as Mesh
	for i in range(source.get_surface_count()):
		var existing := source.surface_get_material(i)
		if not existing:
			return null
		var key := existing.resource_name.to_lower()
		if key not in ["timber", "snow", "orange"]:
			return null
		if not _r17_materials.has(key):
			var mat := ShaderMaterial.new()
			mat.shader = R17_SHADER
			match key:
				"timber":
					mat.set_shader_parameter("base_color", Color(.76, .53, .40, 1.0))
					mat.set_shader_parameter("roughness_value", .86)
					mat.set_shader_parameter("detail_strength", .024)
					mat.set_shader_parameter("detail_scale", 3.2)
				"snow":
					mat.set_shader_parameter("base_color", Color(.95, .985, 1.0, 1.0))
					mat.set_shader_parameter("roughness_value", .78)
					mat.set_shader_parameter("detail_strength", .025)
					mat.set_shader_parameter("detail_scale", 4.0)
				"orange":
					mat.set_shader_parameter("base_color", Color(.98, .66, .22, 1.0))
					mat.set_shader_parameter("roughness_value", .38)
					mat.set_shader_parameter("metallic_value", .10)
					mat.set_shader_parameter("emission_color", Vector3(.20, .045, .006))
					mat.set_shader_parameter("detail_strength", .015)
			_r17_materials[key] = mat
		copy.surface_set_material(i, _r17_materials[key])
	return copy

func _r17_batch(parent: Node3D, label: String, mesh: Mesh, transforms: Array[Transform3D]) -> void:
	var batch := MultiMesh.new()
	batch.transform_format = MultiMesh.TRANSFORM_3D
	batch.mesh = mesh
	batch.instance_count = transforms.size()
	for i in range(transforms.size()):
		batch.set_instance_transform(i, transforms[i])
	var view := MultiMeshInstance3D.new()
	view.name = label
	view.multimesh = batch
	parent.add_child(view)
