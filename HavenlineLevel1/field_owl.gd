extends Node3D
## The expedition owl follows the survivor purchase and only damages a wolf under its talons.
const OwlArt := preload("res://assets/settlement_people/expedition_owl_strike.glb")
const SENSE := 7.4
const RELOAD := 2.7
const WINDUP := .24
const RAKE := .18
const CHEST := Vector3(0,.34,-.03)
var world: Node3D
var art: Node3D
var plumage: MeshInstance3D
var shoulders: Array[Node3D] = []
var elbows: Array[Node3D] = []
var wrists: Array[Node3D] = []
var claw_binds := PackedVector3Array()
var claw_tucks := PackedVector3Array()
var claw_reaches := PackedVector3Array()
var claw_grips := PackedVector3Array()
var talon_weights := Vector3.ZERO
var dive_length := 1.0
var approach_axis := Vector3.FORWARD
var bank_side := 1.0
var planted_claw := 0
var planted_at := Vector3.ZERO
var planted_local := Vector3.ZERO
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
	for foot in ["Left","Right"]:
		for toe in range(3):
			var sensor: Node3D = plumage.find_child("Claw%s%d" % [foot,toe],false,false)
			claw_binds.append(sensor.position)
			claw_tucks.append(sensor.get_child(0).position)
			claw_reaches.append(sensor.get_child(1).position)
			claw_grips.append(sensor.get_child(2).position)
	hide()

func claw_tip(index: int) -> Vector3:
	var p := claw_binds[index] + claw_tucks[index] * talon_weights.x
	p += claw_reaches[index] * talon_weights.y + claw_grips[index] * talon_weights.z
	return plumage.to_global(p)

func _tips() -> PackedVector3Array:
	var tips := PackedVector3Array()
	for i in claw_binds.size(): tips.append(claw_tip(i))
	return tips

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
	recovery = global_position+Vector3(forward.x*1.60,1.72,forward.z*1.60)
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
						approach_axis = (target.global_position-global_position).slide(Vector3.UP).normalized()
						if approach_axis.length_squared()<.1: approach_axis=Vector3.FORWARD
						bank_side = 1.0 if global_basis.x.dot(approach_axis)>=0 else -1.0
						var flank := approach_axis.cross(Vector3.UP) * bank_side
						approach = -approach_axis*1.68 + flank*.62 + Vector3.UP*(2.35*target.size_factor())
						_switch("bank")
			"bank","windup","dive":
				if not _eligible(target) or target.global_position.distance_to(world.actor.global_position)>SENSE+1.8:
					_recover()
				elif state == "bank":
					var staging: Vector3 = target.global_position+approach
					_fly(staging,7.6,dt)
					if global_position.distance_to(staging)<.12 and age>.20: _switch("windup")
				elif state == "windup":
					var crest: Vector3 = target.global_position+approach+Vector3.UP*.24*sin(.5*PI*age/WINDUP)
					global_position = global_position.move_toward(crest,4.0*dt)
					_turn(target.global_position-global_position,dt*1.7)
					if age>=WINDUP:
						dive_length = maxf(.65,claw_tip(1).distance_to(_back(target)))
						_switch("dive")
						if world.has_method("_event"): world._event("owl_dive",global_position)
				else:
					_dive(dt)
					return
			"strike":
				_pose(dt)
				if is_instance_valid(target) and not target.is_queued_for_deletion():
					planted_at = target.to_global(planted_local)
				global_position += planted_at-claw_tip(planted_claw)
				if age >= RAKE: _recover()
				return
			"recover":
				_fly(recovery,4.7,dt)
				if age>=.56: _switch("follow")
	_pose(dt)

func _dive(dt: float) -> void:
	var back := _back(target)
	if not back.is_finite() or age>.82:
		_recover()
		_pose(dt)
		return
	var before := _tips()
	var remaining := claw_tip(1).distance_to(back)
	var travel := clampf(1.0-remaining/dive_length,0,1)
	_pose(dt,travel)
	# Aim the center claw just through the back, so contact requires the actual
	# curved vertex trajectory to intersect the target, including its lateral movement.
	var goal := global_position + back - claw_tip(1) - Vector3.UP*.10
	_fly(goal,lerpf(5.8,8.8,smoothstep(0,.55,travel)),dt)
	var first := 2.0
	var hit_at := Vector3.INF
	for i in before.size():
		var now := claw_tip(i)
		var at := _intersection(target,before[i],now)
		if not at.is_finite(): continue
		var fraction := before[i].distance_to(at)/maxf(.0001,before[i].distance_to(now))
		if fraction < first:
			first = fraction
			hit_at = at
			planted_claw = i
	if not hit_at.is_finite(): return
	# Stop at first contact. Keep that animated claw planted while the body
	# brakes and the toes close, even if the struck animal is still moving.
	global_position += hit_at-claw_tip(planted_claw)
	planted_at = hit_at
	planted_local = target.to_local(hit_at)
	contact_target = target
	contact_point = hit_at
	var landed: bool = world.owl_contact(target,hit_at)
	contact_target = null
	contact_point = Vector3.INF
	if landed:
		if is_instance_valid(target) and not target.is_queued_for_deletion():
			planted_at = target.to_global(planted_local)
			global_position += planted_at-claw_tip(planted_claw)
		_switch("strike")
	else: _recover()

func _pose(dt: float, travel: float = 0.) -> void:
	var extended := 0.0 if state=="perched" else 1.0
	if state == "land": extended = clampf(global_position.distance_to(_perch())*1.65,.12,1.)
	var frequency := 3.05 if state in ["recover","takeoff","land"] else 1.85
	phase = fposmod(phase+dt*TAU*frequency,TAU)
	var beat := .78*sin(phase)
	var fold := 0.02
	var elbow := .24*sin(phase-.64)
	var wrist := .29*sin(phase-1.0)
	var pitch := (.53+.075*cos(phase))*spread
	var roll := .06*sin(phase*.5)*spread
	var asymmetric := 0.0
	var feet := Vector3(extended,0,0)
	match state:
		"bank":
			roll = .37*bank_side
			asymmetric = .16*bank_side
		"windup":
			var t := smoothstep(0.,WINDUP,age)
			pitch = lerpf(.47,.16,t)
			roll = bank_side*(1.-t)*.36
			beat = lerpf(.36,1.04,t)
			elbow = .18
			wrist = -.31*t
			fold = -.11
		"dive":
			var fan := smoothstep(.45,.90,travel)
			extended = lerpf(.62,1.,fan)
			pitch = lerpf(1.05,.30,fan)
			roll = bank_side*.21*(1.-fan)
			fold = lerpf(.87,-.15,fan)
			beat = lerpf(-.35,.86,fan)
			elbow = lerpf(-.47,.32,fan)
			wrist = lerpf(-.62,-.19,fan)
			var reach := smoothstep(.04,.68,travel)
			feet = Vector3(1.-reach,reach,0.)
		"strike":
			var t := smoothstep(0.,RAKE,age)
			pitch = lerpf(.30,-.43,t)
			roll = bank_side*lerpf(.05,-.20,t)
			beat = lerpf(.87,-.88,t)
			elbow = lerpf(.35,-.51,t)
			wrist = lerpf(-.18,.36,t)
			fold = -.13
			feet = Vector3(0,1.-t,t)
		"recover":
			var kick := smoothstep(0.,.27,age)
			pitch = lerpf(-.34,.49,kick)
			roll = -bank_side*.31*(1.-smoothstep(0.,.56,age))
			beat = lerpf(-.88,beat,kick)
			feet = Vector3(kick,0,1.-kick)
	spread = move_toward(spread,extended,dt*4.5)
	talon_weights = feet
	for i in 3: plumage.set_blend_shape_value(i,feet[i])
	var blend := 1.-exp((-24. if state=="strike" else -15.)*dt)
	art.rotation.x = lerp_angle(art.rotation.x,pitch,blend)
	art.rotation.z = lerp_angle(art.rotation.z,roll,blend)
	art.position = CHEST-art.basis*CHEST
	for i in 2:
		var side := -1. if i==0 else 1.
		shoulders[i].scale = Vector3.ONE*lerpf(.025,1.,smoothstep(.02,.55,spread))
		_wing_joint(shoulders[i],side*lerpf(1.27,fold,spread),side*lerpf(-.54,beat+side*asymmetric,spread),dt)
		_wing_joint(elbows[i],side*lerpf(.80,.32*fold,spread),side*lerpf(-.42,elbow,spread),dt)
		_wing_joint(wrists[i],side*lerpf(.23,.22*fold-.09,spread),side*lerpf(.12,wrist,spread),dt)

func _wing_joint(joint: Node3D, sweep: float, flap: float, dt: float) -> void:
	var goal := Quaternion.from_euler(Vector3(0,sweep,flap))
	var angle := joint.quaternion.angle_to(goal)
	if angle <= .001:
		joint.quaternion = goal
	else:
		joint.quaternion = joint.quaternion.slerp(goal,minf(1.,13.5*dt/angle)).normalized()
