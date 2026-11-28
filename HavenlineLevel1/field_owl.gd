extends Node3D
## The expedition owl watches the gate and protects its owner beyond camp.
const Crew = preload("res://field_crew.gd")
const OwlArt := preload("res://assets/settlement_people/expedition_owl_authored.glb")
const PlumageShader := preload("res://assets/settlement_people/expedition_plumage.gdshader")
# Match the wolf notice range. The owl can intercept before the player's axe
# consumes a three-health wolf, even when the player is running toward the pack.
const SENSE := 14.0
const GATE_GUARD := 1.85
const POST_SWITCH_MARGIN := 1.25
const MODEL_SCALE := 1.30
const FLIGHT_CLEARANCE := .12
const BANK_LIMIT := 1.70
const RELOAD := 2.30
const WINDUP := .30
const RAKE := .22
const CHEST := Vector3(0,.34,-.03)
var world: Node3D
var art: Node3D
var plumage: MeshInstance3D
var folded: MeshInstance3D
var skeleton: Skeleton3D
var shoulders := PackedInt32Array()
var elbows := PackedInt32Array()
var wrists := PackedInt32Array()
var flight_fade: ShaderMaterial
var perimeter_route := preload("res://field_pack_route.gd").new()
var gate_request: Node3D
var perch_fade: ShaderMaterial
var previous_flight := -1.0
var lookout_yaw := 0.0
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
var last_owner_hp := -1
var approach := Vector3.ZERO
var recovery := Vector3.ZERO
var post_index := 0
var contact_point := Vector3.INF
var contact_target: Node3D
var fallen_left := 0.0

func setup(host: Node3D) -> void:
	if art: return
	world = host
	name = "ExpeditionOwlCompanion"
	art = OwlArt.instantiate()
	art.scale = Vector3.ONE*MODEL_SCALE
	add_child(art)
	plumage = art.find_child("SkyboundSentinel",true,false)
	folded = art.find_child("FrostwingPathfinder",true,false)
	skeleton = plumage.get_node(plumage.skeleton)
	flight_fade = _plumage_material(plumage,false)
	perch_fade = _plumage_material(folded,true)
	for suffix in ["L","R"]:
		shoulders.append(skeleton.find_bone("Shoulder"+suffix))
		elbows.append(skeleton.find_bone("Elbow"+suffix))
		wrists.append(skeleton.find_bone("Wrist"+suffix))
	for foot in ["Left","Right"]:
		for toe in range(3):
			var sensor: Node3D = art.find_child("Claw%s%d" % [foot,toe],true,false)
			claw_binds.append(sensor.position)
			claw_tucks.append(sensor.get_child(0).position)
			claw_reaches.append(sensor.get_child(1).position)
			claw_grips.append(sensor.get_child(2).position)
	hide()

func _plumage_material(mesh: MeshInstance3D, is_folded: bool) -> ShaderMaterial:
	var imported: BaseMaterial3D = mesh.get_active_material(0)
	var mat := ShaderMaterial.new()
	mat.shader = PlumageShader
	mat.set_shader_parameter("feather_color",imported.albedo_texture)
	mat.set_shader_parameter("packed_surface",imported.roughness_texture)
	mat.set_shader_parameter("feather_normals",imported.normal_texture)
	mat.set_shader_parameter("folded",is_folded)
	mesh.set_surface_override_material(0,mat)
	return mat

func _blend_art(flight: float) -> void:
	if is_equal_approx(flight,previous_flight): return
	previous_flight=flight
	plumage.visible = flight > 0.0
	folded.visible = flight < 1.0
	flight_fade.set_shader_parameter("coverage",flight)
	perch_fade.set_shader_parameter("coverage",1.-flight)

func claw_tip(index: int) -> Vector3:
	var p := claw_binds[index] + claw_tucks[index] * talon_weights.x
	p += claw_reaches[index] * talon_weights.y + claw_grips[index] * talon_weights.z
	return plumage.to_global(p)

func _tips() -> PackedVector3Array:
	var tips := PackedVector3Array()
	for i in claw_binds.size(): tips.append(claw_tip(i))
	return tips

func _perch() -> Vector3:
	var gate: Node3D = world.gates[post_index]
	return gate.to_global(Vector3(-float(gate.HALF_SPAN)-.15,1.718,0))

func _switch(next: String) -> void:
	state = next
	age = 0.

func _eligible(wolf: Node3D) -> bool:
	return is_instance_valid(wolf) and not wolf.is_queued_for_deletion() and wolf.can_receive_swirl() and world.encounters.outside(wolf.global_position,wolf.sanctuary_margin())

func _pick_post(player: Vector3) -> float:
	var nearest_distance := player.distance_to(world.gates[post_index].global_position)
	for i in world.gates.size():
		var distance := player.distance_to(world.gates[i].global_position)
		if distance + POST_SWITCH_MARGIN < nearest_distance:
			post_index = i
			nearest_distance = distance
	return nearest_distance

func _nearest(reach: float = SENSE) -> Node3D:
	var chosen: Node3D
	var best := INF
	for wolf in world.enemies:
		if not _eligible(wolf): continue
		var player_range: float = world.actor.global_position.distance_to(wolf.global_position)
		if player_range > reach: continue
		# Weight the threat to the owner first, then actual flight distance.
		var closing := 2.1 if wolf.state in ["windup","lunge"] else 0.
		var score := player_range + .30 * global_position.distance_to(wolf.global_position) - closing
		if score < best:
			best = score
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

func _watch_perch(dt: float) -> void:
	var gate: Node3D = world.gates[post_index]
	var outward := _outward(gate)
	_turn(outward,dt*.29)
	# Survey the outside shoulder of the occupied post. Only the head
	# scans this arc, so the folded wings, pack and claws hold their seat.
	var glance := outward-gate.global_basis.x*(.76+.46*sin(elapsed*1.12))
	var aim := angle_difference(rotation.y,atan2(glance.x,glance.z))
	lookout_yaw = move_toward(lookout_yaw,clampf(aim,-1.,1.),dt*1.9)
	perch_fade.set_shader_parameter("lookout_yaw",lookout_yaw)

func _outward(gate: Node3D) -> Vector3:
	return gate.global_basis.z.slide(Vector3.UP).normalized()

func _post_entry(gate: Node3D) -> Vector3:
	return gate.to_global(Vector3(-float(gate.HALF_SPAN)-.15,2.40,0)) + _outward(gate)*(float(gate.LEAF_LENGTH)+.52)

func _outside_waypoint(goal: Vector3) -> Vector3:
	var env = world.field_env
	# The post top is a landing surface. Take off along its outside face, and
	# approach that same face before folding the wings for a landing.
	for gate: Node3D in world.gates:
		var post := gate.to_global(Vector3(-float(gate.HALF_SPAN)-.15,1.718,0))
		var entry := _post_entry(gate)
		var out := _outward(gate)
		var here := (global_position-post).slide(Vector3.UP)
		var there := (goal-post).slide(Vector3.UP)
		var landing := there.length_squared() < .03
		if absf(here.dot(out.cross(Vector3.UP))) < .19 and absf(here.dot(out)) < float(gate.LEAF_LENGTH)+.65 and global_position.y > 1.6:
			if landing: return goal
			if here.dot(out)<float(gate.LEAF_LENGTH)+.43: return entry
		if landing: goal = entry
	if env.travel_clear(global_position,goal,FLIGHT_CLEARANCE): return goal
	# A growing camp may enclose a bird already in flight. It can request the
	# same auto gate while approaching its centre line; closed leaves still block it.
	if env.is_inside_camp(global_position):
		if env.is_inside_camp(goal): return env.clip_travel(global_position,goal,FLIGHT_CLEARANCE)
		var closest: Node3D = world.gates[0]
		for gate: Node3D in world.gates:
			if gate.global_position.distance_to(global_position)+gate.global_position.distance_to(goal) < closest.global_position.distance_to(global_position)+closest.global_position.distance_to(goal):
				closest = gate
		gate_request = closest
		var line := closest.global_position
		line.y = maxf(global_position.y,1.85)
		var entry := line-_outward(closest)*.82
		var exit := line+_outward(closest)*.86
		if (global_position-line).slide(Vector3.UP).length()<.88 and env.travel_clear(global_position,exit,FLIGHT_CLEARANCE): return exit
		return entry if env.travel_clear(global_position,entry,FLIGHT_CLEARANCE) else env.clip_travel(global_position,entry,FLIGHT_CLEARANCE)
	# Exterior flight rounds the nearest real fence corner instead of cutting
	# through the camp to the next post or through a wall during a hunting bank.
	var route_margin := float(env.FENCE_DEPTH)*.5+FLIGHT_CLEARANCE+.02
	perimeter_route.configure(world,route_margin)
	var navigation := perimeter_route.route(Vector2(global_position.x,global_position.z),Vector2(goal.x,goal.z))
	if not navigation.is_empty():
		var next := Vector3(navigation[0].x,goal.y,navigation[0].y)
		goal = next
	var stop: Vector3 = env.clip_travel(global_position,goal,FLIGHT_CLEARANCE)
	if (stop-global_position).slide(Vector3.UP).length_squared() >= .000025: return stop
	# Near a fence corner the old heading can be blocked even when the owl
	# is just clear. Step away from the actual wall before requesting a route.
	var clear_at: Vector3 = env.safe_drop_origin(global_position,FLIGHT_CLEARANCE+.04)
	if env.travel_clear(global_position,clear_at,FLIGHT_CLEARANCE): return Vector3(clear_at.x,goal.y,clear_at.z)
	return stop

func _fly(goal: Vector3, speed: float, dt: float) -> void:
	if world.field_env.has_method("travel_clear") and world.field_env.perimeter_stage>0:
		goal = _outside_waypoint(goal)
	_turn(goal-global_position,dt)
	global_position = global_position.move_toward(goal,speed*dt)

func _lane() -> Vector3:
	var player: Vector3 = world.actor.global_position
	var theta := elapsed*.64
	return player + Vector3(-1.70+.50*sin(theta),1.99+.16*sin(2.*theta),-.80+.55*cos(theta))

func _recover() -> void:
	var forward := global_basis.z
	recovery = global_position+Vector3(forward.x*1.72,1.86,forward.z*1.72)
	cooldown = RELOAD
	target = null
	_switch("recover")

func _start_intercept(wolf: Node3D) -> void:
	target = wolf
	approach_axis = (target.global_position-global_position).slide(Vector3.UP).normalized()
	if approach_axis.length_squared()<.1: approach_axis=Vector3.FORWARD
	bank_side = 1.0 if global_basis.x.dot(approach_axis)>=0 else -1.0
	var flank := approach_axis.cross(Vector3.UP)*bank_side
	# Stage from the actual shoulder line. Large enemies still stay in the
	# same readable attack lane instead of pulling the whole pass above frame.
	var shoulder := _back(wolf)
	var high := clampf(shoulder.y-wolf.global_position.y+1.50,2.20,3.22) if shoulder.is_finite() else 2.35
	approach = -approach_axis*1.90 + flank*.71 + Vector3.UP*high
	_switch("bank")

func can_be_targeted() -> bool:
	return world != null and visible and Crew.owns_owl(world.inventory.settlement) and global_position.y <= 1.60

func apply_enemy_contact(attacker: Node3D, damage: int) -> bool:
	if damage<=0 or not can_be_targeted() or not world.settlement_loop.can_transact(): return false
	if not is_instance_valid(attacker) or attacker not in world.enemies: return false
	var floor_point := Vector3(global_position.x,0.0,global_position.z)
	if floor_point.distance_squared_to(attacker.global_position)>3.24 or not world.field_env.travel_clear(attacker.global_position,floor_point,.04):
		return false
	var journal: Dictionary = world.inventory.settlement
	var loss := mini(damage,int(journal.get("owl_hp",Crew.OWL_HP)))
	journal.owl_hp = int(journal.get("owl_hp",Crew.OWL_HP))-loss
	if not world.settlement_loop.commit_receipt("owl_hit_received",global_position,"hit"): return false
	world._combat_number(global_position+Vector3.UP*.63,"−%d" % loss,Color("#ffc196"),self)
	if journal.owl_hp == 0:
		fallen_left = .48
		gate_request = null
		target = null
		state = "fallen"
		world._event("owl_fallen",global_position,"defeat")
	return true

func advance(delta: float) -> void:
	if not world or not world.field_ready: return
	var dt := clampf(delta,0.,.1)
	if not Crew.owns_owl(world.inventory.settlement):
		if fallen_left>0.0:
			fallen_left = maxf(0.0,fallen_left-dt)
			global_position.y = move_toward(global_position.y,.055,dt*3.6)
			art.rotation.z = -1.20*(1.0-fallen_left/.48)
			return
		if visible: hide()
		state = "locked"
		target = null
		return
	gate_request = null
	var player: Vector3 = world.actor.global_position
	var inside: bool = world.field_env.is_inside_camp(player)
	# A newly injured explorer can call the resting bird back into a single
	# protection pass. Repeated hits cannot remove the physical recovery.
	var wounded:bool=last_owner_hp>world.player_hp and world.player_hp>0 and not inside
	if wounded and state in ["follow","recover"]:cooldown=minf(cooldown,.35)
	last_owner_hp=world.player_hp
	var old_post := post_index
	var at_gate := _pick_post(player) <= GATE_GUARD
	var watch_target:Node3D
	if inside and world.player_hp>0:
		if at_gate:watch_target=_nearest(SENSE*.68)
		else:
			var nearest:=4.0
			for wolf in world.enemies:
				if not _eligible(wolf):continue
				for i in world.gates.size():
					var distance:float=wolf.global_position.distance_to(world.gates[i].global_position)
					if distance<nearest:
						nearest=distance
						post_index=i
						watch_target=wolf
	# A paid owl guards the exterior of the gate the player is actually using.
	# Retreating into the interior, or falling, still cancels a committed dive.
	var finishing_strike := state == "strike"
	var resting: bool = world.player_hp <= 0 or (inside and not watch_target and not finishing_strike)
	if inside and old_post != post_index and state == "perched": _switch("land")
	if state == "locked":
		show()
		art.rotation.z = 0.0
		_switch("perched" if inside else "follow")
		global_position = _perch() if inside else _lane()
		rotation.y = .35
	age += dt
	elapsed += dt
	cooldown = maxf(0,cooldown-dt)
	if resting:
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
			_watch_perch(dt)
	else:
		if state in ["perched","land"]: _switch("takeoff")
		match state:
			"takeoff":
				_fly(_post_entry(world.gates[post_index])+Vector3.UP*.15,4.4,dt)
				if age>=.30:
					var seen := watch_target if watch_target else _nearest()
					if seen and cooldown <= 0: _start_intercept(seen)
					else: _switch("follow")
			"follow":
				var lane := _lane()
				if inside and watch_target:
					var gate:Node3D=world.gates[post_index]
					lane=_post_entry(gate)+_outward(gate)*.48+gate.global_basis.x*.40*sin(elapsed*1.6)
				_fly(lane, clampf(6.5 + .90*global_position.distance_to(lane),7.2,15.5),dt)
				if cooldown <= 0:
					var seen := watch_target if watch_target else _nearest()
					if seen: _start_intercept(seen)
			"bank","windup","dive":
				if not is_instance_valid(target) or not _eligible(target) or (target != watch_target and target.global_position.distance_to(world.actor.global_position)>SENSE+1.8):
					_recover()
				elif state == "bank":
					var staging: Vector3 = target.global_position+approach
					_fly(staging,clampf(8.5 + global_position.distance_to(staging)*.8,8.6,16.0),dt)
					if global_position.distance_to(staging)<.16 and age>.18: _switch("windup")
					elif age>=BANK_LIMIT: _recover()
				elif state == "windup":
					var crest: Vector3 = target.global_position+approach+Vector3.UP*.24*sin(.5*PI*age/WINDUP)
					_fly(crest,4.,dt)
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
	_fly(goal,lerpf(6.25,10.15,smoothstep(0,.55,travel)),dt)
	var first := 2.0
	var hit_at := Vector3.INF
	for i in before.size():
		var now := claw_tip(i)
		var at := _intersection(target,before[i],now)
		if not at.is_finite(): continue
		if world.field_env.has_method("travel_clear") and not world.field_env.travel_clear(before[i],at,.025): continue
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
	if state != "perched" and not is_zero_approx(lookout_yaw):
		lookout_yaw = move_toward(lookout_yaw,0.,dt*2.9)
		perch_fade.set_shader_parameter("lookout_yaw",lookout_yaw)
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
			pitch = lerpf(.49,.11,t)
			roll = bank_side*(1.-t)*.36
			beat = lerpf(.32,1.14,t)
			elbow = .18
			wrist = -.31*t
			fold = -.11
		"dive":
			var fan := smoothstep(.32,.82,travel)
			extended = lerpf(.62,1.,fan)
			pitch = lerpf(1.10,.27,fan)
			roll = bank_side*.21*(1.-fan)
			fold = lerpf(.87,-.15,fan)
			beat = lerpf(-.35,.86,fan)
			elbow = lerpf(-.47,.32,fan)
			wrist = lerpf(-.62,-.19,fan)
			var reach := smoothstep(.04,.58,travel)
			feet = Vector3(1.-reach,reach,0.)
		"strike":
			var t := smoothstep(0.,RAKE,age)
			pitch = lerpf(.27,-.48,t)
			roll = bank_side*lerpf(.05,-.20,t)
			beat = lerpf(1.03,-.96,t)
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
	_blend_art(smoothstep(.03,.55,spread))
	talon_weights = feet
	for i in 3: plumage.set_blend_shape_value(i,feet[i])
	var blend := 1.-exp((-24. if state=="strike" else -15.)*dt)
	art.rotation.x = lerp_angle(art.rotation.x,pitch,blend)
	art.rotation.z = lerp_angle(art.rotation.z,roll,blend)
	# Scale about the feet so the larger folded bird still seats on its post,
	# then pitch/roll about the same anatomical center during flight.
	art.position = CHEST*MODEL_SCALE-art.basis*CHEST
	for i in 2:
		var side := -1. if i==0 else 1.
		_wing_joint(shoulders[i],side*lerpf(1.27,fold,spread),side*lerpf(-.54,beat+side*asymmetric,spread),dt)
		_wing_joint(elbows[i],side*lerpf(.80,.32*fold,spread),side*lerpf(-.42,elbow,spread),dt)
		_wing_joint(wrists[i],side*lerpf(.23,.22*fold-.09,spread),side*lerpf(.12,wrist,spread),dt)

func _wing_joint(joint: int, sweep: float, flap: float, dt: float) -> void:
	var goal := Quaternion.from_euler(Vector3(0,sweep,flap))
	var current := skeleton.get_bone_pose_rotation(joint)
	var angle := current.angle_to(goal)
	if angle <= .001:
		skeleton.set_bone_pose_rotation(joint,goal)
	else:
		skeleton.set_bone_pose_rotation(joint,current.slerp(goal,minf(1.,13.5*dt/angle)).normalized())
