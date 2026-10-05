extends Node3D

const Character1Motion = preload("res://scripts/character1_motion.gd")
const Harvest = preload("res://scripts/harvest_presentation.gd")
const CHARACTER_SCENE = preload("res://assets/characters/Character1.glb")
const MOTION_REVIEW_HEIGHT_METERS := 1.75
const TARGET_ASSETS := {
	"wood":"res://assets/environment_v2/pine_1.glb",
	"stone":"res://assets/environment_v2/stone.glb",
	"metal":"res://assets/environment_v2/metal.glb",
	"fuel":"res://assets/environment_v2/fuel.glb",
}

var visual: Node3D
var presenter: HavenlineHarvestPresentation
var targets: Dictionary = {}
var current_resource := ""

func _transparent_review_material() -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = Color(0.0,0.0,0.0,0.0)
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.disable_receive_shadows = true
	return material

func _bark_contact_cutaway_material() -> ShaderMaterial:
	var shader := Shader.new()
	shader.code = """
shader_type spatial;
render_mode depth_draw_opaque, cull_back;
varying vec3 local_vertex_position;
void vertex() {
	local_vertex_position = VERTEX;
}
void fragment() {
	float radius = length(local_vertex_position.xz);
	float allowed_radius = mix(0.34, 0.17, smoothstep(0.0, 0.42, local_vertex_position.y));
	if (radius > allowed_radius) {
		discard;
	}
	ALBEDO = mix(vec3(0.24, 0.115, 0.055), vec3(0.46, 0.25, 0.13), clamp(COLOR.r, 0.0, 1.0));
	ROUGHNESS = 0.92;
}
"""
	var material := ShaderMaterial.new()
	material.shader = shader
	material.resource_name = "T09_C5_authored_trunk_cutaway"
	return material

func configure_contact_cutaway(resource: String,target: Node3D) -> void:
	# C5 is an inspection capture, not a beauty render. The shipping pine uses
	# separate bark, needles and snow surfaces, so hide only the crown surfaces
	# here. This keeps the authored trunk/contact geometry while exposing the
	# character, hands and tool from every required review angle. Gameplay
	# evidence still renders the complete shipping pine.
	if resource != "wood":
		return
	var hidden := _transparent_review_material()
	var meshes: Array[MeshInstance3D] = []
	gather_meshes(target,meshes)
	var kept_bark := false
	var hidden_surfaces := 0
	for mesh_instance in meshes:
		if mesh_instance.mesh == null:
			continue
		for surface_index in range(mesh_instance.mesh.get_surface_count()):
			var surface_material := mesh_instance.mesh.surface_get_material(surface_index)
			var surface_name := String(surface_material.resource_name).to_lower() if surface_material != null else ""
			if surface_name.contains("bark"):
				mesh_instance.set_surface_override_material(surface_index,_bark_contact_cutaway_material())
				kept_bark = true
			else:
				mesh_instance.set_surface_override_material(surface_index,hidden)
				hidden_surfaces += 1
	assert(kept_bark and hidden_surfaces > 0,"T09 C5 wood cutaway requires authored bark and crown surfaces")

func gather_meshes(node: Node, meshes: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		meshes.append(node as MeshInstance3D)
	for child in node.get_children():
		gather_meshes(child, meshes)

func _ready() -> void:
	# QA-only PackedScene consumed by the production C5 motion harness. It uses
	# the immutable shipping Character 1 GLB, shipping T06 clips, actual T09 tools,
	# actual source meshes, and the same T09 contact solver used by gameplay.
	visual = CHARACTER_SCENE.instantiate() as Node3D
	visual.name = "Character1Visual"
	add_child(visual)
	var meshes: Array[MeshInstance3D] = []
	gather_meshes(visual, meshes)
	var bounds := AABB()
	var first := true
	for mesh in meshes:
		var box := global_transform.affine_inverse()*mesh.global_transform*mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	assert(not first and bounds.size.y > 0.01, "T09 C5 fixture requires Character 1 render geometry")
	# Match shipping Character 1's 1.75 m presentation scale. The dedicated T09
	# camera is close enough for hands, knees, feet and contact inspection, so the
	# fixture no longer distorts tool-to-body proportions merely to fill the frame.
	var scale_factor := MOTION_REVIEW_HEIGHT_METERS/bounds.size.y
	visual.scale *= scale_factor
	visual.position = Vector3(-bounds.get_center().x,-bounds.position.y,-bounds.get_center().z)*scale_factor
	var installed := Character1Motion.install(self,"player_lead")
	assert(bool(installed.get("passed",false)), "T09 C5 fixture failed to install shipping Character 1 motion")
	presenter = Harvest.new()
	presenter.name = "ShippingT09HarvestPresentation"
	presenter.set_process(false)
	add_child(presenter)
	assert(presenter.bind_actor(self),"T09 C5 fixture requires shipping hand contacts")
	for resource in TARGET_ASSETS:
		var packed: Variant = load(String(TARGET_ASSETS[resource]))
		assert(packed is PackedScene,"T09 C5 fixture target asset missing: "+resource)
		var target := (packed as PackedScene).instantiate() as Node3D
		target.name = "Target_"+resource
		# Match each profile's shipping interaction/contact reach. A pine's narrow
		# trunk contact radius is much smaller than the broad stone/fuel surfaces;
		# placing every asset at the same origin leaves the chop target outside the
		# validated two-hand reach even though its rendered trunk looks nearby.
		target.position = Vector3(0.0,0.0,1.05 if resource == "wood" else 1.42)
		target.visible = false
		add_child(target)
		configure_contact_cutaway(resource,target)
		targets[resource] = target
	set_meta("t09_qa_only",true)
	set_meta("t09_motion_review_height_m",MOTION_REVIEW_HEIGHT_METERS)
	set_meta("t09_motion_profiles",["human_player_chop","human_player_mine","human_player_dismantle"])
	set_meta("t09_motion_fixture_content","shipping_character_tools_targets_and_contact_solver")
	set_meta("t09_contact_review_cutaway","wood_crown_surfaces_hidden_trunk_preserved")

func resource_for_animation(animation: String) -> String:
	if animation.ends_with("chop"):
		return "wood"
	if animation.ends_with("mine"):
		return "stone"
	return "fuel"

func configure_harvest_sample(animation: String, time: float, length: float) -> Dictionary:
	var resource := resource_for_animation(animation)
	for key in targets:
		(targets[key] as Node3D).visible = String(key) == resource
	var target := targets[resource] as Node3D
	var profile := Harvest.profile_for_resource(resource)
	var presented_progress := clampf(time/maxf(length,0.001),0.0,1.0)
	var impact := float(profile.impact_progress)
	var raw_progress := presented_progress/maxf(impact,0.001)
	var post_contact := presented_progress > impact
	if post_contact:
		raw_progress = (presented_progress-impact)/maxf(1.0-impact,0.001)*Harvest.RECOVERY_PORTION
	var action := {
		"kind":"gather", "id":"c5_"+resource, "resource":resource,
		"source_id":"c5_"+resource, "action_token":["wood","stone","fuel"].find(resource)+1,
		"progress":clampf(raw_progress,0.0,1.0), "role":"player_lead", "actionable":true,
	}
	# Every independently labelled t=0 review starts from the same presentation
	# state. This resets only T09's fixture-owned tool/contact history; the frozen
	# AnimationPlayer sample and converged Character 1 skeleton remain untouched.
	if current_resource != resource or time <= 0.000001:
		presenter.reset()
		current_resource = resource
	presenter.prepare_actor_contact(self)
	if not presenter.begin_action(action,1):
		return {"passed":false,"resource":resource}
	var attachment := Harvest.attachment_transform(self,profile)
	var target_position := Harvest.source_contact_target(target,attachment,profile,global_position)
	var contact_window := absf(presented_progress-impact) <= Harvest.CONTACT_TOLERANCE
	var descriptor: Dictionary
	if contact_window:
		# Shipping commits call the same forced-contact synchronizer immediately
		# before the authoritative simulation mutation. Sample that exact pose for
		# C5 rather than asking the pre-commit interpolator to infer it.
		descriptor = presenter.synchronize_committed_contact(action,attachment,target_position,1)
	elif post_contact:
		presenter.active["has_committed"] = true
		presenter.begin_action(action,1)
		descriptor = presenter.update_action(action,attachment,target_position,true)
	else:
		descriptor = presenter.update_action(action,attachment,target_position,true)
	descriptor["passed"] = true
	descriptor["fixture_resource"] = resource
	descriptor["fixture_presented_progress"] = presented_progress
	descriptor["fixture_has_tool_and_target"] = true
	return descriptor
