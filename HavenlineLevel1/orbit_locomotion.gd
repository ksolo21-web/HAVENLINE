extends RefCounted
## Synchronize both sets of footfalls while blending from a walk into a run.
const LOOP_LIBRARY := &"orbit_gait"
const WALK_SPEED := 1.12
const RUN_SPEED := 2.65
const BLEND_START := 1.12
const BLEND_END := 2.35
var player: AnimationPlayer
var tree: AnimationTree
var current := ""
var walk_length := 0.0
var run_length := 0.0
var gait_weight := 0.0
var moving_weight := 0.0
var stride_hz := 0.0

func bind(visual: Node3D) -> bool:
	var found := visual.find_children("*", "AnimationPlayer", true, false)
	if found.size() != 1:
		return false
	player = found[0]
	var library := AnimationLibrary.new()
	for original: StringName in player.get_animation_list():
		var state := String(original).get_file().to_lower()
		if state in ["idle","walk","run"]:
			if library.has_animation(state): return false
			var clip := player.get_animation(original).duplicate() as Animation
			clip.loop_mode = Animation.LOOP_LINEAR
			library.add_animation(state, clip)
	if library.get_animation_list().size() != 3: return false
	player.add_animation_library(LOOP_LIBRARY, library)
	walk_length = library.get_animation("walk").length
	run_length = library.get_animation("run").length
	player.stop()
	tree = AnimationTree.new()
	visual.add_child(tree)
	tree.anim_player = tree.get_path_to(player)
	tree.root_node = tree.get_path_to(player.get_node(player.root_node))
	var graph := AnimationNodeBlendTree.new()
	for state in ["idle","walk","run"]:
		var sample := AnimationNodeAnimation.new()
		sample.animation = String(LOOP_LIBRARY) + "/" + state
		graph.add_node(state, sample)
		if state != "idle":
			graph.add_node(state + "_rate", AnimationNodeTimeScale.new())
			graph.connect_node(state + "_rate", 0, state)
	var mix := AnimationNodeBlend2.new()
	mix.sync = true
	graph.add_node("gait", mix)
	graph.connect_node("gait", 0, "walk_rate")
	graph.connect_node("gait", 1, "run_rate")
	var launch := AnimationNodeBlend2.new()
	launch.sync = true
	graph.add_node("movement", launch)
	graph.connect_node("movement", 0, "idle")
	graph.connect_node("movement", 1, "gait")
	graph.connect_node("output", 0, "movement")
	tree.tree_root = graph
	tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	tree.active = true
	current = "idle"
	observe(0.0, true, 0.0)
	return tree.is_active()

func observe(planar_speed: float, grounded: bool, dt: float = -1.0) -> void:
	if not is_instance_valid(tree): return
	if dt < 0.0: dt = 1.0 / Engine.physics_ticks_per_second
	var speed := maxf(0.0, planar_speed) if grounded and is_finite(planar_speed) else 0.0
	var walk_stride := walk_length * WALK_SPEED
	var run_stride := run_length * RUN_SPEED
	var transition := clampf(inverse_lerp(BLEND_START, BLEND_END, speed), 0.0, 1.0)
	# Grow cadence and stride together. Blending strides by stick magnitude alone
	# can briefly slow the feet as the player accelerates through the gait change.
	var blend_hz := lerpf(BLEND_START / walk_stride, BLEND_END / run_stride, transition)
	gait_weight = clampf(inverse_lerp(walk_stride, run_stride, speed / blend_hz), 0.0, 1.0)
	moving_weight = smoothstep(0.025, 0.45, speed)
	stride_hz = speed / lerpf(walk_stride, run_stride, gait_weight)
	tree.set("parameters/walk_rate/scale", stride_hz * walk_length)
	tree.set("parameters/run_rate/scale", stride_hz * run_length)
	tree.set("parameters/gait/blend_amount", gait_weight)
	tree.set("parameters/movement/blend_amount", moving_weight)
	tree.advance(dt)
	current = "idle" if speed < 0.08 else ("run" if gait_weight >= 0.5 else "walk")
