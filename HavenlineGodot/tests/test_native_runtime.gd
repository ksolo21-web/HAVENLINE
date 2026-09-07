extends SceneTree
const Sim = preload("res://scripts/native_simulation.gd")
const Policy = preload("res://scripts/native_render_policy.gd")
const Collision = preload("res://scripts/native_collision.gd")
const Recorder = preload("res://scripts/native_frame_recorder.gd")
var checks: Array = []
var failures: Array = []
func check(label: String, passed: bool):
	checks.append({"name":label,"passed":passed})
	if not passed: failures.append(label)
func simulate(sim, seconds: float):
	for frame in range(int(ceil(seconds*60))): sim.step(1.0/60,Vector2.ZERO)
func total_resource(sim, kind: String) -> int:
	var total: int = sim.stored[kind] + sim.inventory[kind]
	for r in sim.resources:
		if r.kind == kind: total += r.units
	for c in sim.companions:
		if c.get("cargo_kind","wood") == kind: total += c.get("cargo",0)
	return total
func _initialize():
	check("16:9 actual 3840x2160",Policy.dimensions(Vector2(1920,1080)) == Vector2i(3840,2160))
	check("ultrawide preserves at least 2160 vertical pixels",Policy.dimensions(Vector2(2520,1080)) == Vector2i(5040,2160))
	check("foldable 4:3 preserves 3840 horizontal pixels",Policy.dimensions(Vector2(1200,900)) == Vector2i(3840,2880))
	check("review resolution is explicitly separate",Policy.dimensions(Vector2(1920,1080),true) == Vector2i(1280,720))
	check("120-Hz target is not capped at 60",Policy.frame_target(120) == 120)
	check("unknown refresh never requests below 60",Policy.frame_target(-1) == 60)
	var safe := Policy.logical_safe_rect(Vector2(1920,1080),Vector2i(2400,1350),Rect2i(60,0,2340,1300))
	check("safe-area coordinates convert to logical canvas",safe.position.is_equal_approx(Vector2(48,0)) and safe.size.is_equal_approx(Vector2(1872,1040)))
	var obstacle: Array = [{"center":Vector2.ZERO,"half":Vector2(1.5,.18)}]
	var stopped := Collision.solve(Vector2(0,2),Vector2(0,-4),obstacle,Vector2(14,16))
	check("swept collision prevents barricade tunneling",stopped.y > .45)
	var sliding := Collision.solve(Vector2(0,1),Vector2(2,-2),obstacle,Vector2(14,16))
	check("collision allows sliding rather than freezing",sliding.x > 1.0)
	var circle: Array = [{"center":Vector2.ZERO,"radius":.94}]
	check("zero-distance penetration is recovered finitely",Collision.project(Vector2.ZERO,circle,Vector2(14,16)).length() >= 1.21)
	var s = Sim.new()
	s.position = Vector2(0,3)
	for i in range(100): s.step(1.0/60,Vector2.UP,true)
	check("player cannot run through the furnace",s.position.y > 1.4)
	check("valid worker job accepted",s.assign_job(2,"stone"))
	check("unknown worker and job rejected",not s.assign_job(1,"stone") and not s.assign_job(2,"alchemy"))
	s = Sim.new()
	var start_total := total_resource(s,"stone")
	s.assign_job(2,"stone")
	simulate(s,35)
	check("assigned worker gathers and deposits stone",s.stored.stone > 0)
	check("worker does not mint or lose stone",total_resource(s,"stone") == start_total)
	var worker: Dictionary = s.companions[0]
	worker.cargo = 3
	worker.cargo_kind = "wood"
	var wood_before: int = s.stored.wood
	var metal_before: int = s.stored.metal
	s.assign_job(2,"metal")
	worker.position = Sim.point(s.contract.world.furnace)+Vector2(0,1.55)
	s.step(1.0/60,Vector2.ZERO)
	check("job changes do not transmute existing cargo",s.stored.wood == wood_before+3 and s.stored.metal == metal_before)
	var copied = Sim.new()
	var state: Dictionary = s.snapshot()
	check("native worker jobs survive JSON round-trip",copied.restore(JSON.parse_string(JSON.stringify(state))) and copied.companions[0].job == "metal")
	var invalid: Dictionary = state.duplicate(true)
	invalid.native_runtime.workers["2"].cargo_kind = "invented"
	var before: Dictionary = copied.snapshot()
	check("invalid native extension rejected atomically",not copied.restore(invalid) and copied.snapshot() == before)
	var legacy: Dictionary = state.duplicate(true)
	legacy.erase("native_runtime")
	check("old schema-1 saves still load",Sim.new().restore(legacy))
	s.threat_presentation_ready = false
	s.enemies.append({"id":"hidden","position":s.position,"health":50.0,"cooldown":0.0})
	var prior_health: float = s.health
	s.step(1.0/60,Vector2.ZERO)
	check("missing enemy art cannot cause invisible damage",s.health >= prior_health)
	var recorder = Recorder.new()
	recorder.warmup = 0
	for i in range(130): recorder.sample(1000000+i*16667,Vector2i(3840,2160))
	var report: Dictionary = recorder.report({"render_scale":1.0})
	check("frame recorder reports measured callback intervals",report.sample_count == 129 and absf(report.p99_callback_ms-16.667)<.001)
	check("source callback measurements cannot certify physical performance",report.performance_certified == false and report.physical_device_verified == false)
	recorder.reset_segment()
	check("pause/fold resets cannot be hidden inside a sustained sample",recorder.count == 0 and recorder.discontinuities == 1)
	for id in [2,3,4]:
		var library: AnimationLibrary = load("res://assets/animations/Character%d.res" % id)
		check("C%d has derived idle/walk/run libraries" % id,library != null and library.has_animation("idle") and library.has_animation("walk") and library.has_animation("run"))
		if library == null: continue
		for clip in library.get_animation_list():
			var animation := library.get_animation(clip)
			var valid := animation.length > 0 and animation.get_track_count() == 23
			for track in range(animation.get_track_count()):
				if animation.track_get_type(track) != Animation.TYPE_ROTATION_3D: continue
				for key in range(animation.track_get_key_count(track)):
					var q: Quaternion = animation.track_get_key_value(track,key)
					valid = valid and is_finite(q.length()) and absf(q.length()-1.0)<.0001
			check("C%d %s contains finite unit-quaternion samples" % [id,clip],valid)
	print(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
