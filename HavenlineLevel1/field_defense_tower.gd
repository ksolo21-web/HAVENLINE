extends Node3D
## Only a paid tower fires. Flight resolves against the same living enemy it targeted.
const EAST_SITE := Vector3(8.1,0,-2.4)
const REACH := 13.0
const RELOAD := 1.65
const BOLT_SPEED := 13.0
var world: Node3D
var art: Node3D
var active := false
var presented := false
var raising := 1.0
var reload := .45
var flights: Array[Dictionary] = []

func setup(host: Node3D) -> void:
	world=host
	position=EAST_SITE
	if ResourceLoader.exists("res://field_tower_art.gd"):
		art=load("res://field_tower_art.gd").new()
		add_child(art)
		art.hide()

func nearest() -> Node3D:
	var best: Node3D
	var distance := REACH*REACH
	for wolf in world.enemies:
		if wolf.hp<=0 or not wolf.active or not wolf.visible or wolf.position.x<position.x-.25: continue
		if not world.encounters.outside(wolf.position,wolf.sanctuary_margin()): continue
		var d := position.distance_squared_to(wolf.position)
		if d<distance: best=wolf; distance=d
	return best

func advance(dt: float, paid: bool) -> void:
	if active!=paid:
		active=paid
		if art:
			art.visible=paid
			raising=0.0 if paid and presented else 1.0
			art.set_build_progress(raising)
	presented=true
	if not active or not art: return
	art.update_sightline(world.actor.global_position,world.camera)
	if raising<1.0:
		raising=minf(1.0,raising+dt*1.6)
		art.set_build_progress(raising)
		return
	reload=maxf(0.0,reload-dt)
	var target := nearest()
	if is_instance_valid(target):
		var aim: Vector3=target.position+Vector3.UP*.72*target.size_factor()
		art.aim_at_world(aim)
		if reload<=0.0:
			var model: Node3D = art.projectile()
			if model:
				world.add_child(model)
				model.global_position=art.muzzle_global_position()
				art.fire(aim)
				flights.append({"mesh":model,"target":weakref(target),"at":aim,"life":2.0})
				world._event("tower_fire",model.global_position)
				reload=RELOAD
	for i in range(flights.size()-1,-1,-1):
		var f: Dictionary=flights[i]
		var target_node = f.target.get_ref()
		var alive: bool=is_instance_valid(target_node) and target_node.active and target_node.hp>0
		if alive: f.at=target_node.position+Vector3.UP*.72*target_node.size_factor()
		var model: Node3D=f.mesh
		if model.global_position.distance_squared_to(f.at)>.001:
			model.look_at(f.at,Vector3.UP,true)
		model.global_position=model.global_position.move_toward(f.at,BOLT_SPEED*dt)
		f.life-=dt
		var arrived := model.global_position.distance_squared_to(f.at)<.003
		if not arrived and f.life>0: continue
		model.queue_free()
		flights.remove_at(i)
		if arrived and alive and world.encounters.outside(target_node.position,target_node.sanctuary_margin()) and target_node.receive_hit(1):
			world._event("tower_hit",f.at)
