extends Node
## Render policy scoped to the orbit trial. The window keeps its native size.
var ultra := true
var quality_button := Button.new()
var lights: Array[Node] = []
var snow_surface: MeshInstance3D
var material_copies := {}
var originals := {}
var scene: Node3D
var original_canvas := Vector2i.ZERO
var original_aspect := Window.CONTENT_SCALE_ASPECT_KEEP
var original_orientation := DisplayServer.SCREEN_LANDSCAPE

func install(world: Node3D, hud: Control) -> void:
	scene = world
	snow_surface = scene.get_node("SnowGround_NoPaintedPaths").find_children("*", "MeshInstance3D", false, false)[0]
	original_canvas = get_window().content_scale_size
	original_aspect = get_window().content_scale_aspect
	if OS.has_feature("mobile"):
		original_orientation = DisplayServer.screen_get_orientation()
		DisplayServer.screen_set_orientation(DisplayServer.SCREEN_SENSOR)
	lights = scene.find_children("*", "DirectionalLight3D", true, false)
	for geometry: MeshInstance3D in scene.find_children("*", "MeshInstance3D", true, false):
		configure_mesh(geometry)
	get_tree().node_added.connect(on_node_added)
	# The other touchscreen action controls receive presses through Opening._input.
	quality_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	quality_button.focus_mode = Control.FOCUS_NONE
	quality_button.name = "TrialGraphicsQuality"
	quality_button.add_theme_font_size_override("font_size", 18)
	hud.add_child(quality_button)
	get_viewport().size_changed.connect(refresh_window)
	set_ultra(true)

func on_node_added(node: Node) -> void:
	if node is MeshInstance3D and scene.is_ancestor_of(node):
		_configure_added_mesh.call_deferred(node.get_instance_id())

func _configure_added_mesh(id: int) -> void:
	if not is_instance_id_valid(id): return
	var mesh := instance_from_id(id) as MeshInstance3D
	if mesh and mesh.is_inside_tree() and scene.is_ancestor_of(mesh):
		configure_mesh(mesh)

func filtered(source: Material) -> Material:
	if not source is BaseMaterial3D or (source.albedo_texture == null and source.normal_texture == null):
		return source
	if originals.has(source):
		return source
	if material_copies.has(source):
		return material_copies[source]
	var copy: BaseMaterial3D = source.duplicate()
	material_copies[source] = copy
	originals[copy] = source.texture_filter
	copy.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC if ultra else source.texture_filter
	return copy

func configure_mesh(geometry: MeshInstance3D) -> void:
	if not is_instance_valid(geometry) or geometry.mesh == null:
		return
	if geometry.material_override:
		geometry.material_override = filtered(geometry.material_override)
		return
	for i in geometry.mesh.get_surface_count():
		var source := geometry.get_active_material(i)
		var material := filtered(source)
		if material != source:
			geometry.set_surface_override_material(i, material)

func set_ultra(enabled: bool) -> void:
	ultra = enabled
	get_viewport().msaa_3d = Viewport.MSAA_4X if enabled else Viewport.MSAA_DISABLED
	get_viewport().mesh_lod_threshold = .5 if enabled else 1.0
	for light: DirectionalLight3D in lights:
		light.directional_shadow_max_distance = 36.0 if enabled else 64.0
		# Snow receives scattered light even under the boots and weapon.
		light.shadow_opacity = 0.74 if enabled else 1.0
	for material: BaseMaterial3D in originals:
		material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC if enabled else originals[material]
	quality_button.text = "Graphics · Ultra" if enabled else "Graphics · Standard"
	refresh_window()

func refresh_window() -> void:
	var viewport := get_viewport()
	var window := get_window()
	var window_px := Vector2(window.size)
	var portrait := window_px.y > window_px.x
	var canvas_base := Vector2i(720, 1280) if portrait else Vector2i(1280, 720)
	if window.content_scale_size != canvas_base:
		window.content_scale_size = canvas_base
	if window.content_scale_aspect != Window.CONTENT_SCALE_ASPECT_EXPAND:
		window.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	scene.camera.keep_aspect = Camera3D.KEEP_WIDTH if portrait else Camera3D.KEEP_HEIGHT
	# The taller view sees beyond the movement boundary. Extend only the
	# ground's artwork; the original snow collider and travel bounds stay local.
	snow_surface.scale = Vector3(2.5, 1, 2.5) if portrait else Vector3.ONE
	# Bound the 3D draw area to a 4K envelope, including rotated displays.
	var limit := Vector2(3840, 2160) if window_px.x >= window_px.y else Vector2(2160, 3840)
	var ratio := minf(1.0, minf(limit.x / maxf(1, window_px.x), limit.y / maxf(1, window_px.y)))
	viewport.scaling_3d_scale = ratio
	var canvas := viewport.get_visible_rect()
	quality_button.size = Vector2(180, 48)
	quality_button.position = canvas.end - quality_button.size - Vector2(16,16)


func _exit_tree() -> void:
	if original_canvas != Vector2i.ZERO:
		get_viewport().size_changed.disconnect(refresh_window)
		get_window().content_scale_aspect = original_aspect
		get_window().content_scale_size = original_canvas
		if OS.has_feature("mobile"):
			DisplayServer.screen_set_orientation(original_orientation)
