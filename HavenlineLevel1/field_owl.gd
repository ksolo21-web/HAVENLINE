extends Node3D
## The expedition owl follows the survivor purchase and only damages a wolf under its talons.
const OwlArt := preload("res://assets/settlement_people/expedition_owl.glb")
const SENSE := 7.4
const RELOAD := 2.7
const CUP := Vector3(.043,.013,.040)
var world: Node3D
var art: Node3D
var plumage: MeshInstance3D
var shoulders: Array[Node3D] = []
var elbows: Array[Node3D] = []
var wrists: Array[Node3D] = []
var state := "locked"
var target: Node3D
var elapsed := 0.0
var phase := 0.0
var spread := 0.0
var age := 0.0
var cooldown := 0.0
var approach := Vector3.ZERO
var recovery := Vector3.ZERO
var contact_point := Vector3.INF
var contact_target: Node3D

func setup(host: Node3D) -> void:
	if art: return
	world = host
	name = "ExpeditionOwlCompanion"
	art = OwlArt.instantiate()
	add_child(art)
	plumage = art.find_child("EightViewOwl",true,false)
	for suffix in ["L","R"]:
		shoulders.append(art.find_child("Shoulder"+suffix,true,false))
		elbows.append(art.find_child("Elbow"+suffix,true,false))
		wrists.append(art.find_child("Wrist"+suffix,true,false))
	hide()

func _perch() -> Vector3:
	var gate: Node3D = world.gates[0]
	return gate.to_global(Vector3(-float(gate.HALF_SPAN)-.15,1.718,0))

func _switch(next: String) -> void:
	state = next
	age = 0.

func _eligible(wolf: Node3D) -> bool:
	return is_instance_valid(wolf) and not wolf.is_queued_for_deletion() and wolf.can_receive_swirl() and world.encounters.outside(wolf.global_position,wolf.sanctuary_margin())

func _nearest() -> Node3D:
	var chosen: Node3D
	var distance := SENSE*SENSE
	for wolf in world.enemies:
		if not _eligible(wolf): continue
		var d := world.actor.global_position.distance_squared_to(wolf.global_position) as float
		if d < distance:
			distance = d
			chosen = wolf
	return chosen

func _intersection(wolf: Node3D, a: Vector3, b: Vector3) -> Vector3:
	var skin: MeshInstance3D = wolf.contact_mesh()
	var hit: Dictionary = wolf.hit_surface.intersect_segment(skin.to_local(a),skin.to_local(b))
	return Vector3.INF if hit.is_empty() else skin.to_global(hit.position)

func _back(wolf: Node3D) -> Vector3:
	var skin: MeshInstance3D = wolf.contact_mesh()
	var bounds: AABB = skin.global_transform * skin.get_aabb()
	var p := bounds.get_center()
	return _intersection(wolf,p+Vector3.UP*(bounds.size.y+.10),p-Vector3.UP*(bounds.size.y+.10))

func permits_contact(wolf: Node3D, at: Vector3) -> bool:
	return state == "dive" and is_instance_valid(contact_target) and contact_target == wolf and contact_point == at

func _turn(direction: Vector3, dt: float) -> void:
	if direction.x*direction.x+direction.z*direction.z > .003:
		rotation.y = rotate_toward(rotation.y,atan2(direction.x,direction.z),dt*6.9)

func _fly(goal: Vector3, speed: float, dt: float) -> void:
	_turn(goal-global_position,dt)
	global_position = global_position.move_toward(goal,speed*dt)

func _lane() -> Vector3:
	var player: Vector3 = world.actor.global_position
	var theta := elapsed*.64
	return player + Vector3(-1.42+.48*sin(theta),1.95+.16*sin(2.*theta),-.66+.55*cos(theta))

func _recover() -> void:
	var forward := global_basis.z
	recovery = global_position+Vector3(forward.x*1.35,1.72,forward.z*1.35)
	cooldown = RELOAD
	target = null
	_switch("recover")

func advance(delta: float) -> void:
	if not world or not world.field_ready: return
	var dt := clampf(delta,0.,.1)
	if not world.inventory.settlement.get("survivor_paid",false):
		if visible: hide()
		state = "locked"
		target = null
		return
	var inside: bool = world.field_env.is_inside_camp(world.actor.global_position) or world.player_hp <= 0
	if state == "locked":
		show()
		_switch("perched" if inside else "follow")
		global_position = _perch() if inside else _lane()
		rotation.y = .35
	age += dt
	elapsed += dt
	cooldown = maxf(0,cooldown-dt)
	if inside:
		target = null
		var perch := _perch()
		if state != "perched" and state != "land": _switch("land")
		if state == "land":
			var over_post := perch+Vector3.UP*.72
			var near_post := Vector2(global_position.x-perch.x,global_position.z-perch.z).length() < .30
			_fly(perch if near_post else over_post,4.1 if near_post else 6.8,dt)
			if global_position.distance_to(perch) < .025: _switch("perched")
		if state == "perched":
			global_position=perch
			_turn(world.actor.global_position-perch,dt*.22)
	else:
		if state in ["perched","land"]: _switch("takeoff")
		match state:
			"takeoff":
				_fly(_perch()+Vector3(-.22,1.03,.34),4.4,dt)
				if age>=.30: _switch("follow")
			"follow":
				_fly(_lane(),6.5,dt)
				if cooldown <= 0:
					target = _nearest()
					if target:
						var axis: Vector3 = (target.global_position-global_position).slide(Vector3.UP).normalized()
						if axis.length_squared()<.1: axis=Vector3.FORWARD
						approach = -axis*1.25 + Vector3.UP*(2.2*target.size_factor())
						_switch("bank")
			"bank","dive":
				if not _eligible(target) or target.global_position.distance_to(world.actor.global_position)>SENSE+1.8:
					_recover()
				elif state == "bank":
					var staging: Vector3 = target.global_position+approach
					_fly(staging,7.6,dt)
					if global_position.distance_to(staging)<.12 and age>.20: _switch("dive")
				else:
					var back := _back(target)
					if back == Vector3.INF or age>.58:
						_recover()
					else:
						var foot := art.to_global(CUP)
						var other := art.to_global(Vector3(-CUP.x,CUP.y,CUP.z))
						_fly(back+(global_position-foot)-Vector3.UP*.20,8.6,dt)
						var hit := _intersection(target,foot,art.to_global(CUP))
						if hit == Vector3.INF:
							hit = _intersection(target,other,art.to_global(Vector3(-CUP.x,CUP.y,CUP.z)))
						if hit != Vector3.INF:
							contact_target = target
							contact_point = hit
							world.owl_contact(target, hit)
							contact_target = null
							contact_point = Vector3.INF
							_recover()
			"recover":
				_fly(recovery,5.8,dt)
				if age>=.45: _switch("follow")
	_pose(dt)

func _pose(dt: float) -> void:
	var fly := state != "perched"
	var extended := .72 if state=="dive" else (1. if fly else 0.)
	if state == "land":
		extended = clampf(global_position.distance_to(_perch())*1.65,.12,1.)
	spread = move_toward(spread,extended,dt*4.0)
	var frequency := 3.15 if state in ["recover","takeoff","land"] else 2.2
	phase = fposmod(phase+dt*TAU*frequency,TAU)
	var beat := sin(phase) * (.18 if state == "dive" else .76)
	if plumage.get_blend_shape_count() == 1:
		plumage.set_blend_shape_value(0,spread*(0. if state=="dive" else 1.))
	var tilt := .86 if state=="dive" else (.58*spread)
	art.rotation.x = lerp_angle(art.rotation.x,tilt,1.-exp(-9.*dt))
	for i in range(2):
		var s := -1. if i==0 else 1.
		shoulders[i].scale = Vector3.ONE*lerpf(.025,1.,smoothstep(.02,.75,spread))
		shoulders[i].rotation = Vector3(0,s*lerpf(1.27,.02,spread),s*lerpf(-.54,beat,spread))
		elbows[i].rotation = Vector3(0,s*lerpf(.80,.04,spread),s*lerpf(-.42,.23*sin(phase-.62),spread))
		wrists[i].rotation = Vector3(0,s*lerpf(.23,-.09,spread),s*lerpf(.12,.31*sin(phase-.93),spread))
