extends SceneTree
const Kit = preload("res://character_kit.gd")
const Hero = preload("res://assets/characters/Character1.glb")
const STRIKE_SAMPLE_SECONDS := 0.375
const EPS := 0.00015
var failures: Array[String] = []
var checks := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label)
func _initialize() -> void:
	call_deferred("run")
func vec(v: Vector3) -> Array:
	return [v.x,v.y,v.z]
func frame(t: Transform3D) -> Dictionary:
	return {"origin":vec(t.origin),"x":vec(t.basis.x),"y":vec(t.basis.y),"z":vec(t.basis.z)}
func snapshot(host: Node3D, kit, rig: Skeleton3D, player: AnimationPlayer, degrees_y: float) -> Dictionary:
	host.rotation.y = deg_to_rad(degrees_y)
	await process_frame
	await process_frame
	# Exact authored placement after the same natively evaluated, paused clip pose.
	kit.equipped = "axe"
	kit._place(false)
	var inverse := host.global_transform.affine_inverse()
	var tool: Node3D = kit._axe
	var left: Node3D = kit._palm_l.get_node("LocalOffset")
	var right: Node3D = kit._palm_r.get_node("LocalOffset")
	var bones: Array[Transform3D] = []
	for b in range(rig.get_bone_count()):
		bones.append(rig.get_bone_global_pose(b))
	return {"degrees_y":degrees_y,"pose_s":player.current_animation_position,"pose_clip":String(player.current_animation),
		"left_world":left.global_transform,"right_world":right.global_transform,
		"left_actor_local":inverse*left.global_transform,"right_actor_local":inverse*right.global_transform,
		"tool_actor_local":inverse*tool.global_transform,"tool_world":tool.global_transform,
		"pivot_world":host.global_position,"bones":bones}
func run() -> void:
	var host := Node3D.new()
	root.add_child(host)
	host.position = Vector3(1.7,-0.2,2.4)
	var hero := Hero.instantiate() as Node3D
	host.add_child(hero)
	var bounds := AABB()
	var started := false
	for node in hero.find_children("*","MeshInstance3D",true,false):
		var mesh := node as MeshInstance3D
		var box := (host.global_transform.affine_inverse()*mesh.global_transform)*mesh.get_aabb()
		bounds = bounds.merge(box) if started else box
		started = true
	var layout: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://layout.json"))
	var scale_factor := float(layout.actor_height)/maxf(.01,bounds.size.y)
	hero.scale *= scale_factor
	hero.position = Vector3(-bounds.get_center().x,-bounds.position.y,-bounds.get_center().z)*scale_factor
	var kit = Kit.new()
	if not started or not kit.install(host,hero,null):
		push_error("Exact PR asset/kit did not install")
		quit(2); return
	var rig: Skeleton3D = kit._skeleton
	var player: AnimationPlayer = kit._player
	kit.begin_action("chop")
	var deadline := Time.get_ticks_msec()+2500
	while player.current_animation_position < STRIKE_SAMPLE_SECONDS and Time.get_ticks_msec() < deadline:
		await process_frame
	var reached := player.current_animation_position
	if reached < STRIKE_SAMPLE_SECONDS or reached > .402:
		push_error("Natural chop sampling window skipped")
		quit(3); return
	# Freeze exactly once, before rotating the actor; no advance/seek/bone forcing.
	player.pause()
	var a: Dictionary = await snapshot(host,kit,rig,player,0.)
	var b: Dictionary = await snapshot(host,kit,rig,player,180.)
	check(a.pose_s==b.pose_s and a.pose_clip==b.pose_clip,"same natural time and action")
	check(a.pivot_world==b.pivot_world,"fixed actor pivot")
	check(a.bones==b.bones,"every imported evaluated bone pose fixed")
	check(a.left_actor_local.is_equal_approx(b.left_actor_local) and a.right_actor_local.is_equal_approx(b.right_actor_local),"both anatomical marker transforms actor-local invariant")
	check(a.left_world.origin.y>a.right_world.origin.y and b.left_world.origin.y>b.right_world.origin.y,"assignment R-lower / L-upper invariant")
	var local_a: Transform3D = a.tool_actor_local
	var local_b: Transform3D = b.tool_actor_local
	var ax := local_a.basis.x.normalized()
	var by := local_a.basis.y.normalized()
	var az := local_a.basis.z.normalized()
	var delta := local_b.origin-local_a.origin
	check((delta+.16*ax).length()<=EPS,"expected old lateral origin flip in actor-local space")
	check(ax.dot(local_b.basis.x.normalized())<-.9999 and az.dot(local_b.basis.z.normalized())<-.9999 and by.dot(local_b.basis.y.normalized())>.9999,"expected old half-turn about local shaft Y")
	var bands: Array = kit._sockets.axe_grip_y
	var band_deltas: Array = []
	for y in bands:
		var local_band := Vector3(0,float(y),0)
		var d := (local_b*local_band)-(local_a*local_band)
		check(d.distance_to(delta)<=EPS,"expected exact held band shift")
		band_deltas.append(vec(d))
	print(JSON.stringify({"checks":checks,"failed":failures,"fixed_engine_pose_seconds":a.pose_s,"nominal_trigger_seconds":STRIKE_SAMPLE_SECONDS,
		"native_clip":a.pose_clip,"bone_count":a.bones.size(),"anatomy":"R lower, L upper both headings","actor_pivot_world":vec(a.pivot_world),
		"actor_local_heading0":frame(local_a),"actor_local_heading180":frame(local_b),"delta_local_m":vec(delta),"delta_norm_m":delta.length(),
		"band_deltas_actor_local_m":band_deltas,"scope":"animated headless actor pivot only; diagnostic mathematical defect reproduction, not grip or approved fix"}, "  "))
	quit(0 if failures.is_empty() else 1)
