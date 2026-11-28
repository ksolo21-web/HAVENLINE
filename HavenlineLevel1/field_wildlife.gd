extends Node3D
## The southern tundra stag is prey. Hostiles and owned companions have
## separate controllers and never enter the worker's automatic hunting list.

const StagArt := preload("res://assets/field/tundra_stag.glb")
const HarvestYields := preload("res://field_harvest_yields.gd")
const SOURCE_ID := "wildlife_tundra_stag"
const HOME := Vector3(4.55, 0, 12.80)
const MAX_HP := 3
const RETURN_DELAY := 36.0
const BODY := AABB(Vector3(-.23,.36,-.62),Vector3(.46,1.05,1.34))

var world
var art: Node3D
var rig: Skeleton3D
var hp := MAX_HP
var idle_time := 0.0
var stride := 0.0
var flight_left := 0.0
var flight_wait := 0.0
var hit_left := 0.0
var down_age := 0.0
var fleeing_to := Vector3.ZERO
var leg_bones := {}
var neck := -1
var bone_rest_rotation: Array[Quaternion] = []
var bone_bend_axis: Array[Vector3] = []

func setup(host: Node3D) -> void:
	world = host
	name = "TundraStag"
	position = HOME
	rotation.y = -.63
	art = StagArt.instantiate()
	add_child(art)
	for node in art.find_children("*","Skeleton3D",true,false):
		rig = node as Skeleton3D
		break
	if rig:
		for bone in rig.get_bone_count():
			bone_rest_rotation.append(rig.get_bone_rest(bone).basis.get_rotation_quaternion())
			bone_bend_axis.append((rig.get_bone_global_rest(bone).basis.inverse()*Vector3.RIGHT).normalized())
		neck = rig.find_bone("Neck")
		for leg: String in ["FrontL","FrontR","RearL","RearR"]:
			leg_bones[leg] = [rig.find_bone(leg+"Upper"),rig.find_bone(leg+"Lower"),rig.find_bone(leg+"Paw")]
	if world.tracks: world.tracks.register_actor(self,"stag",1.0)
	hp = int(world.inventory.settlement.get("stag_health",MAX_HP))
	visible = hp > 0

func is_huntable() -> bool:
	return hp > 0 and is_visible_in_tree() and not world.field_env.is_inside_camp(global_position)

func approach_from(origin: Vector3) -> Vector3:
	var direction := (origin-global_position).slide(Vector3.UP).normalized()
	if direction.length_squared() < .01: direction = -global_basis.z
	return global_position+direction*.73

func intersect_blade(from: Vector3, to: Vector3) -> Vector3:
	if not is_huntable(): return Vector3.INF
	var point: Variant = BODY.intersects_segment(to_local(from),to_local(to))
	return to_global(point) if point is Vector3 else Vector3.INF

func receive_hunting_contact(at: Vector3, origin: Vector3, damage := 1) -> bool:
	if damage <= 0 or not is_huntable() or not at.is_finite() or not BODY.grow(.012).has_point(to_local(at)):
		return false
	if not world.settlement_loop.can_transact() or not world.field_env.travel_clear(origin,at,.09):
		return false
	var loss := mini(hp,damage)
	hp -= loss
	world.inventory.settlement.stag_health = hp
	hit_left = .26
	flight_left = 0.0
	flight_wait = maxf(flight_wait,1.35)
	world._event("stag_hit",at,"hit")
	world._combat_number(at+Vector3.UP*.67,"−%d" % loss,Color("#ffebaf"),self)
	if hp == 0:
		down_age = 0.0
		world.lifecycle.cooling[SOURCE_ID] = RETURN_DELAY
		world._event("stag_harvest",global_position,"defeat")
		world._make_drops("meat",global_position,HarvestYields.TUNDRA_STAG)
	world._checkpoint_lifecycle()
	return not world.persist_blocked

func advance(dt: float, hunter: Vector3 = Vector3.INF) -> void:
	if not world.field_ready or world.persist_blocked: return
	var cooling: bool = world.lifecycle.cooling.has(SOURCE_ID)
	if cooling or hp <= 0:
		if cooling:
			down_age += dt
			art.rotation.z = -1.36*smoothstep(0.0,.47,down_age)
			if down_age > .65: hide()
			return
		_respawn()
		return
	idle_time += dt
	hit_left = maxf(0.0,hit_left-dt)
	flight_wait = maxf(0.0,flight_wait-dt)
	var threat := hunter
	if world.actor.global_position.distance_squared_to(global_position)<1.7:
		threat = world.actor.global_position
	if flight_left == 0.0 and flight_wait == 0.0 and threat.distance_squared_to(global_position)<4.15:
		_begin_flight(threat)
	var meters := 0.0
	if flight_left > 0.0:
		flight_left = maxf(0.0,flight_left-dt)
		var direction := global_position.direction_to(fleeing_to)
		var next := global_position.move_toward(fleeing_to,4.10*dt)
		if _clear(next):
			rotation.y = rotate_toward(rotation.y,atan2(direction.x,direction.z),dt*9.0)
			meters = global_position.distance_to(next)
			global_position = next
		if meters < .001 or global_position.distance_to(fleeing_to)<.03: flight_left = 0.0
	stride = fposmod(stride+meters/1.16,1.0)
	_pose(meters>.001)

func _respawn() -> void:
	position = HOME
	rotation.y = -.63
	hp = MAX_HP
	world.inventory.settlement.stag_health = hp
	art.rotation = Vector3.ZERO
	flight_left = 0.0
	flight_wait = .60
	if world.tracks: world.tracks.reset_actor(self)
	show()

func _clear(point: Vector3) -> bool:
	return not world.field_env.is_inside_camp(point) and world.field_env.travel_clear(global_position,point,.27)

func _begin_flight(threat: Vector3) -> void:
	flight_wait = 3.8
	var retreat := (global_position-threat).slide(Vector3.UP).normalized()
	var proposed := global_position+retreat*2.25
	if proposed.distance_squared_to(HOME)>9.5 or not _clear(proposed):
		proposed = HOME + retreat.cross(Vector3.UP)*1.65
	if not _clear(proposed): return
	fleeing_to = proposed
	flight_left = .62

func _pose(moving: bool) -> void:
	if not rig: return
	if neck>=0:
		_bend(neck,.08*sin(idle_time*1.42) if not moving else -.105)
	var recoil := .075*sin(hit_left/.26*PI)
	art.rotation_degrees.z = rad_to_deg(recoil)
	for leg: String in leg_bones:
		var bones: Array = leg_bones[leg]
		if bones.any(func(id): return id < 0): continue
		var left_front := leg in ["FrontL","RearR"]
		var angle := (stride+(0.0 if left_front else .5))*TAU
		var raised := maxf(0.0,sin(angle))
		var upper := cos(angle)*.37 if moving else 0.0
		var lower := raised*.49 if moving else 0.0
		if leg.begins_with("Rear"): lower *= -.68
		_bend(bones[0],upper)
		_bend(bones[1],lower)
		_bend(bones[2],-.48*lower)

func _bend(bone: int, angle: float) -> void:
	rig.set_bone_pose_rotation(bone,bone_rest_rotation[bone]*Quaternion(bone_bend_axis[bone],angle))
