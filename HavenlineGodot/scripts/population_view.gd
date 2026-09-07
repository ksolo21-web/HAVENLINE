extends Node3D

# Actual imported models only. Missing models never become invisible working
# NPCs, colored capsules, clones of a custom character, or claimed final art.
const Surface = preload("res://scripts/outpost_surface.gd")
const CarryStack = preload("res://scripts/carry_stack.gd")
var sim
var nodes: Dictionary = {}
var scenes: Dictionary = {}
var stacks: Dictionary = {}
var resource_loader: Callable

func configure(simulation, loader: Callable):
	sim = simulation
	resource_loader = loader
	sim.population.presentation_required = true
	for key in sim.population.catalog.templates:
		var spec: Dictionary = sim.population.catalog.templates[key]
		var path: String = spec.model
		if spec.asset_status not in ["candidate", "approved"]: continue
		if not path.begins_with("res://assets/npcs/") or not path.ends_with(".glb"): continue
		if ResourceLoader.exists(path):
			var packed = load(path)
			if packed is PackedScene: scenes[key] = packed
	# Validate candidates before enabling their spawn slots; a model missing its
	# locomotion must not occupy an invisible queue slot forever.
	for key in scenes.keys():
		var probe := create_actor({"id": -1, "template": key, "position": Vector2.ZERO,
			"role": sim.population.catalog.templates[key].role})
		if probe: probe.free()
		else: scenes.erase(key)
		stacks.erase(-1)
	sim.population.enabled_templates = scenes.keys()
	sync(0.0)

func find_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer: return node
	for child in node.get_children():
		var result := find_animation(child)
		if result: return result
	return null

func meshes(node: Node, into: Array):
	if node is MeshInstance3D: into.append(node)
	for child in node.get_children(): meshes(child, into)

func create_actor(person: Dictionary) -> Node3D:
	if not scenes.has(person.template): return null
	var root := Node3D.new()
	root.name = "NPC_" + str(person.id)
	add_child(root)
	var visual = scenes[person.template].instantiate()
	if not visual is Node3D:
		visual.free()
		root.queue_free()
		return null
	root.add_child(visual)
	var surfaces: Array = []
	meshes(visual, surfaces)
	if surfaces.is_empty():
		root.queue_free()
		return null
	var bounds := AABB()
	var first := true
	for surface in surfaces:
		var box: AABB = root.global_transform.affine_inverse() * surface.global_transform * surface.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	var animation := find_animation(visual)
	if not animation:
		root.queue_free()
		return null
	# A static rest pose is not a playable person or animal.
	for required in ["idle", "walk", "run"]:
		var found := false
		for clip in animation.get_animation_list():
			if clip.to_lower().ends_with(required): found = true
		if not found:
			root.queue_free()
			return null
	var factor: float = sim.population.catalog.templates[person.template].height / maxf(0.01, bounds.size.y)
	visual.scale *= factor
	visual.position = Vector3(-bounds.get_center().x, -bounds.position.y, -bounds.get_center().z) * factor
	root.set_meta("animation", animation)
	root.set_meta("appearance_descriptor", person.get("appearance", {}))
	root.set_meta("visual_variants_applied", false)
	root.position = Vector3(person.position.x, Surface.height_at(person.position), person.position.y)
	if person.role == "survivor":
		var stack := CarryStack.new()
		stack.loader = resource_loader
		stack.position = Vector3(0, 0.65, -0.42)
		root.add_child(stack)
		stacks[person.id] = stack
	return root

func sync(dt: float):
	if sim == null: return
	var records: Array = sim.population.actor_records()
	var opening := {"id": 5, "template": sim.population.catalog.opening_survivor_template,
		"position": sim.point(sim.contract.world.survivor), "role": "survivor"}
	if sim.rescued:
		for c in sim.companions:
			if c.id == 5: opening.merge(c, true)
	records.append(opening)
	var keep: Array = []
	var present: Array = []
	for person in records:
		keep.append(person.id)
		if not nodes.has(person.id):
			var actor := create_actor(person)
			if actor: nodes[person.id] = actor
		if not nodes.has(person.id): continue
		present.append(person.id)
		var root: Node3D = nodes[person.id]
		var target := Vector3(person.position.x, Surface.height_at(person.position), person.position.y)
		var motion := target - root.position
		root.position = target
		if motion.length() > 0.001:
			root.rotation.y = lerp_angle(root.rotation.y, atan2(motion.x, motion.z), 1.0 - exp(-12.0 * dt))
		var speed := motion.length() / maxf(0.001, dt)
		var wanted := "run" if speed > 3.5 else ("walk" if speed > 0.1 else "idle")
		var animation: AnimationPlayer = root.get_meta("animation")
		for clip in animation.get_animation_list():
			if clip.to_lower().ends_with(wanted):
				animation.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
				if animation.current_animation != clip: animation.play(clip, 0.16)
				break
		if stacks.has(person.id):
			var cargo := {"wood": 0, "stone": 0, "metal": 0, "fuel": 0}
			cargo[person.get("cargo_kind", "wood")] = person.get("cargo", 0)
			stacks[person.id].update_inventory(cargo)
	for id in nodes.keys():
		if id not in keep:
			nodes[id].queue_free()
			nodes.erase(id)
			stacks.erase(id)
	sim.population.presented_ids = present
	sim.rescue_enabled = 5 in present
	sim.presented_actor_ids = [1, 2, 3, 4]
	if 5 in present: sim.presented_actor_ids.append(5)

func pause_animations(value: bool):
	for root in nodes.values(): root.get_meta("animation").speed_scale = 0.0 if value else 1.0

func evidence() -> Dictionary:
	return {"available_model_templates": scenes.keys(), "visible_npcs": nodes.keys(),
		"required_templates": sim.population.catalog.templates.keys(),
		"missing_templates": sim.population.catalog.templates.keys().filter(func(k): return k not in scenes),
		"visual_variants_applied": false, "final_art_approved": false}
