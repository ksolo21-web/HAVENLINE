extends Node3D
## Character 1's visible rig for the existing survivor. The survivor owns its
## route, tools and receipts even while its original body is hidden.
const Character = preload("res://assets/characters/Character1Fresh.glb")
const Motion = preload("res://field_character_motion.gd")
const WorkSwing = preload("res://forester_work_swing.gd")
const AXE_GRIPS := [Vector3(.392,-.19,0.), Vector3(.447,-.73,0.)]
const PICK_GRIPS := [WorkSwing.PICK_GRIPS[1], WorkSwing.PICK_GRIPS[0]]
var actor: Node3D
var model: Node3D
var gait = preload("res://gait_motor.gd").new()
var locomotion = preload("res://orbit_locomotion.gd").new()
var motion := Motion.new()
var previous_feet := Vector3.INF
var speed := 0.
var cue := &""
var last_contact := &""
var character_kit: Dictionary
var pivot_boots: Array[Transform3D] = []
var pivot_toes: Array[Transform3D] = []

func bind(world: Node3D, worker: Node3D) -> bool:
	actor = worker
	model = world.model(Character, self, float(world.layout.actor_height))
	if not locomotion.bind(model): return false
	locomotion.use_field_run()
	character_kit = {"locomotion": locomotion}
	gait.use_field_run()
	gait._bind_soles(self, model)
	if not motion.bind(actor, model, gait): return false
	for surface: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		surface.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return true

func start_frame() -> void:
	motion.clear_pose()
	if actor.forester_gait.pivot_elapsed < 0.:
		pivot_boots = [gait._boot_world(0), gait._boot_world(1)]
		pivot_toes = [gait._toe_relative(0), gait._toe_relative(1)]

func contact(action: StringName, at: Vector3) -> void:
	last_contact = action
	motion.contact(action, at)

func clear_tool_path(tool: Node3D, mining: bool, progress: float) -> void:
	# Keep the visible edge at the contact point used by the field worker.
	var phase := clampf(progress, 0., 1.)
	var impact := smoothstep(.35, .56, phase) * (1. - smoothstep(.72, .91, phase))
	var direction := .16 * impact
	var tip: Vector3 = WorkSwing.PICK_TIP if mining else WorkSwing.AXE_EDGE
	var grips: Array = PICK_GRIPS if mining else AXE_GRIPS
	var grip_center: Vector3 = (grips[0] + grips[1]) * .5
	var point := tool.transform * tip
	var basis := Basis(Vector3.UP, direction) * Basis(Vector3.RIGHT, -.10 * impact) * tool.basis
	var wind := smoothstep(.07, .31, phase) * (1. - smoothstep(.38, .60, phase)) if mining else 0.
	if mining:
		# The cut runs beside the leading shoulder. Keep the shaft more
		# upright so the lower grip never requires threading it past the belt.
		var tooth_axis := Vector3(-.94, .47, -.24).normalized()
		var press := smoothstep(.40, .60, phase) * (1. - smoothstep(.70, .85, phase))
		var handle_axis := Vector3(-.06, 1., .035 - .12 * press).slide(tooth_axis).normalized()
		# Raise the pick outside the shoulder and square its tooth before contact.
		var swing := Basis(Vector3.RIGHT, -.21 * wind) * Basis(Vector3.FORWARD, -.35 * wind)
		basis = (swing * Basis(tooth_axis, handle_axis, tooth_axis.cross(handle_axis))).scaled(tool.basis.get_scale() * .58)
	else:
		basis = basis.scaled(Vector3.ONE * .76)
		basis *= Basis((grip_center - tip).normalized(), deg_to_rad(40.))
		var cutting := smoothstep(.31, .39, phase) * (1. - smoothstep(.64, .73, phase))
		basis = Basis(Vector3.UP, .22 - .14 * cutting) * Basis(Vector3.RIGHT, -.18 * cutting) * basis
	if mining:
		var parked := 1. - smoothstep(.44, .56, phase) + smoothstep(.69, .78, phase)
		var lift := smoothstep(.06, .29, phase) * (1. - smoothstep(.36, .49, phase))
		var settle := smoothstep(.37, .404, phase) * (1. - smoothstep(.43, .48, phase))
		var ready := Vector3(.10 + .024 * settle, .62 + .13 * lift, .52 + .020 * settle) + basis * (tip - grip_center)
		# The hands carry the arc from the guard into the cutting plane.
		ready += Vector3(.10, .185, .015) * wind
		point = point.lerp(ready, parked)
		point.y += .15 * wind * (1. - parked)
	tool.transform = Transform3D(basis, point - basis * tip)

func advance(dt: float, job: String, landed: bool) -> void:
	var at := actor.global_position
	var measured := 0.
	if previous_feet.is_finite() and previous_feet.distance_squared_to(at) < .75:
		measured = previous_feet.distance_to(at) / maxf(dt, .0001)
	if speed < .08 and measured > .10:
		gait._begin_launch()
	if measured < .01 and speed > .4:
		# Planted action poses are seated immediately. Ordinary stops blend
		# back to idle over the last part of the route's braking interval.
		gait.launch_remaining = 0.
	var working: bool = actor.mode in ["chop", "mine"]
	speed = measured if working or measured > .04 else move_toward(speed, 0., 16. * dt)
	gait.floor_pending = speed > .035
	locomotion.observe(speed, true, dt)
	previous_feet = at
	var steer = actor.forester_gait
	if steer.pivot_frame and not pivot_boots.is_empty():
		var step_length: float = steer.PIVOT_STEP
		var elapsed: float = steer.pivot_elapsed if steer.pivot_elapsed >= 0. else 2. * step_length
		gait.follow_pivot(pivot_boots, pivot_toes, steer.pivot_heading + steer.pivot_angle, steer.pivot_first, elapsed / step_length)
		cue = &""
		return
	if working:
		var mining: bool = actor.mode == "mine"
		cue = &"mine" if mining else (&"attack_contact" if job in ["hunt_strike", "defend"] else &"chop")
		var data: Array = Motion.CLIPS[cue]
		var phase: float = clampf(actor.pose_progress, 0., 1.)
		var before := phase * float(data[2]) / .61
		var after := lerpf(float(data[2]), 1., clampf((phase - .61) / .39, 0., 1.))
		var progress := minf(before, float(data[2])) if phase < .61 else after
		if landed and last_contact != cue:
			progress = float(data[2])
			last_contact = cue
		elif not landed:
			last_contact = &""
		motion.pose(Motion.select(0., actor.rotation.y, actor.rotation.y, cue, progress, Motion.COMPANION), .55, actor.work_strike_point)
		motion.grip_tool(actor.mining_tool if mining else actor.tool, PICK_GRIPS if mining else AXE_GRIPS, .32 if mining else .21, mining, phase)
	else:
		cue = motion.action
		motion.advance(dt, speed, false, Motion.COMPANION)
