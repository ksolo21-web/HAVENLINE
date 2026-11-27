extends Node

const MASK_PAINT := preload("res://assets/field_world/guard_depth_mask.gdshader")

var view: Camera3D
var subject: Node3D
var tower: Node3D
var original_meshes: Array[MeshInstance3D]
var mask_meshes: Array[MeshInstance3D] = []
var pass_meshes: Array[MeshInstance3D] = []
var mask := SubViewport.new()
var mask_camera := Camera3D.new()
var mask_paint := ShaderMaterial.new()
var overlay: ShaderMaterial
var shown := false

func setup(camera: Camera3D, guard: Node3D, art: Node3D, occluders: Array[MeshInstance3D], paint: ShaderMaterial) -> void:
	view = camera
	subject = guard
	tower = art
	overlay = paint
	original_meshes = occluders
	process_priority = 100
	mask.own_world_3d = true
	mask.transparent_bg = true
	mask.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(mask)
	mask.add_child(mask_camera)
	mask_camera.make_current()
	mask_paint.shader = MASK_PAINT
	for source: MeshInstance3D in original_meshes:
		var replica := MeshInstance3D.new()
		replica.mesh = source.mesh
		replica.material_override = mask_paint
		replica.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mask.add_child(replica)
		mask_meshes.append(replica)
	overlay.set_shader_parameter("tower_depth",mask.get_texture())
	for part: MeshInstance3D in guard.find_children("*","MeshInstance3D",true,false):
		pass_meshes.append(part)
		part.material_overlay = overlay
	shown = true

func _process(_dt: float) -> void:
	if not is_instance_valid(subject) or not is_instance_valid(view): return
	var in_view := subject.is_visible_in_tree() and view.is_position_in_frustum(subject.global_position + Vector3.UP * .64)
	var refresh := in_view != shown
	if refresh:
		shown = in_view
		for part in pass_meshes: part.material_overlay = overlay if shown else null
	if not shown:
		mask.render_target_update_mode = SubViewport.UPDATE_DISABLED
		return
	var pixels := Vector2i((view.get_viewport().get_visible_rect().size * .5).round()).max(Vector2i(2,2))
	if mask.size != pixels:
		mask.size = pixels
		refresh = true
	if (mask_camera.global_transform != view.global_transform
			or mask_camera.projection != view.projection
			or mask_camera.keep_aspect != view.keep_aspect
			or mask_camera.size != view.size or mask_camera.fov != view.fov
			or mask_camera.frustum_offset != view.frustum_offset
			or mask_camera.h_offset != view.h_offset or mask_camera.v_offset != view.v_offset
			or mask_camera.near != view.near or mask_camera.far != view.far):
		mask_camera.global_transform = view.global_transform
		mask_camera.projection = view.projection
		mask_camera.keep_aspect = view.keep_aspect
		mask_camera.size = view.size
		mask_camera.fov = view.fov
		mask_camera.frustum_offset = view.frustum_offset
		mask_camera.h_offset = view.h_offset
		mask_camera.v_offset = view.v_offset
		mask_camera.near = view.near
		mask_camera.far = view.far
		refresh = true
	for i in original_meshes.size():
		var source := original_meshes[i]
		var replica := mask_meshes[i]
		var visible := source.is_visible_in_tree()
		if replica.global_transform != source.global_transform or replica.visible != visible:
			replica.global_transform = source.global_transform
			replica.visible = visible
			refresh = true
	if refresh:
		var eye := view.global_basis.z.normalized()
		for paint: ShaderMaterial in [mask_paint,overlay]:
			paint.set_shader_parameter("depth_origin",tower.global_position)
			paint.set_shader_parameter("depth_eye",eye)
		mask.render_target_update_mode = SubViewport.UPDATE_ONCE
