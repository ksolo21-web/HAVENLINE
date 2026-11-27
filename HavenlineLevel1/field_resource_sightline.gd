extends RefCounted
## Live harvest meshes retain their original material overrides whenever they
## leave the character's sightline. Distant grove MultiMeshes stay batched.
const CUTAWAY := preload("res://assets/field_world/resource_sightline.gdshader")
var materials := {}
var opened := {}
var last_feet := Vector3.INF
var last_eye := Vector3.INF
var last_ultra := true
var worker_feet := Vector3.INF

func _cutaway(source: StandardMaterial3D) -> ShaderMaterial:
	if not materials.has(source):
		var paint := ShaderMaterial.new()
		paint.shader = CUTAWAY
		paint.set_shader_parameter("paint", source.albedo_texture)
		paint.set_shader_parameter("paint_ultra", source.albedo_texture)
		paint.set_shader_parameter("tint", source.albedo_color)
		paint.set_shader_parameter("ultra_filter", source.texture_filter == BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC)
		paint.set_shader_parameter("vertex_paint", source.vertex_color_use_as_albedo)
		paint.set_shader_parameter("roughness", source.roughness)
		paint.set_shader_parameter("metalness", source.metallic)
		paint.set_shader_parameter("specular", source.metallic_specular)
		paint.set_shader_parameter("has_relief", source.normal_enabled)
		paint.set_shader_parameter("relief", source.normal_texture)
		paint.set_shader_parameter("relief_ultra", source.normal_texture)
		paint.set_shader_parameter("relief_depth", source.normal_scale)
		paint.set_shader_parameter("emission", source.emission)
		paint.set_shader_parameter("emission_energy", source.emission_energy_multiplier if source.emission_enabled else 0.0)
		paint.set_shader_parameter("worker_window",source.resource_name.to_lower() in ["crown","lip"])
		_apply_worker(paint)
		materials[source] = paint
	return materials[source]

func _apply_worker(paint: ShaderMaterial) -> void:
	paint.set_shader_parameter("worker_in_view",worker_feet.is_finite())
	if worker_feet.is_finite(): paint.set_shader_parameter("worker_origin",worker_feet)

func _near_sightline(part: MeshInstance3D, feet: Vector3, eye: Vector3) -> bool:
	if not part.is_visible_in_tree() or part.global_position.distance_squared_to(feet) > 42.25:
		return false
	var bounds := (part.global_transform * part.get_aabb()).grow(.62)
	for height: float in [0.16, 0.90, 1.64]:
		var from := feet + Vector3.UP * height
		if bounds.intersects_segment(from, from + eye * 8.0) != null:
			return true
	return false

func _restore(part: MeshInstance3D, overrides: Array) -> void:
	for i in overrides.size():
		part.set_surface_override_material(i, overrides[i])

func update(world: Node3D) -> void:
	var feet: Vector3 = world.actor.global_position
	var eye: Vector3 = world.camera.global_basis.z.normalized()
	if feet != last_feet:
		RenderingServer.global_shader_parameter_set("field_player_feet", feet)
		last_feet = feet
	if eye != last_eye:
		RenderingServer.global_shader_parameter_set("field_player_eye", eye)
		last_eye = eye
	var working := Vector3.INF
	var worker: Node3D = world.survivor
	if is_instance_valid(worker) and worker.phase in ["chopping","mining"] and worker.can_defend():
		working=worker.actor.global_position
	if working!=worker_feet:
		worker_feet=working
		for paint: ShaderMaterial in materials.values(): _apply_worker(paint)

	if world.graphics.ultra != last_ultra:
		last_ultra = world.graphics.ultra
		for source: StandardMaterial3D in materials:
			materials[source].set_shader_parameter("ultra_filter", source.texture_filter == BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC)
	for source in world.surfaces:
		if not source.has_meta("field_source_id"):
			continue
		var part: MeshInstance3D = world.surfaces[source][0]
		var clear_worker: bool=source.get_meta("resource_kind","")=="wood" and worker_feet.is_finite() and _near_sightline(part,worker_feet,eye)
		if not clear_worker and not _near_sightline(part, feet, eye):
			if opened.has(part):
				_restore(part, opened[part])
				opened.erase(part)
			continue
		if not opened.has(part):
			world.graphics.configure_mesh(part)
			var originals := []
			for i in part.mesh.get_surface_count():
				originals.append(part.get_surface_override_material(i))
				var material := part.get_active_material(i) as StandardMaterial3D
				if material:
					part.set_surface_override_material(i, _cutaway(material))
			opened[part] = originals
	# Streamed-out sources can disappear between two render frames.
	for part in opened.keys():
		if not is_instance_valid(part):
			opened.erase(part)
