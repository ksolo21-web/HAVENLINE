extends Node3D
## Only a paid tower fires. Flight resolves against the same living enemy it targeted.
const EAST_SITE := Vector3(8.1,0,-2.4)
const FOOTPRINT := Rect2(-.98,-.98,1.96,2.04)
const REACH := 13.0
const RELOAD := 1.65
const BOLT_SPEED := 13.0
var world: Node3D
var guard := StaticBody3D.new()
var art: Node3D
var active := false
var presented := false
var raising := 1.0
var reload := .45
var flights: Array[Dictionary] = []

func setup(host: Node3D) -> void:
	world=host
	position=EAST_SITE
	var shape := CollisionShape3D.new()
	var base := BoxShape3D.new()
	base.size = Vector3(FOOTPRINT.size.x,1.75,FOOTPRINT.size.y)
	shape.shape = base
	shape.position = Vector3(FOOTPRINT.get_center().x,.875,FOOTPRINT.get_center().y)
	guard.add_child(shape)
	guard.name = "TowerFootings"
	guard.collision_layer = 0
	guard.collision_mask = 0
	add_child(guard)
	if ResourceLoader.exists("res://field_tower_art.gd"):
		art=load("res://field_tower_art.gd").new()
		add_child(art)
		art.follow_hero(world.hero_model)
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
		guard.collision_layer = 1 if paid else 0
		# The offer lies at the tower's future feet. Give the purchaser a
		# solid stance on the camp-facing side as the foundation rises.
		if paid:
			var p:Vector3 = to_local(world.actor.global_position)
			var span := FOOTPRINT.grow(float(world.layout.actor_radius)+.05)
			if span.has_point(Vector2(p.x,p.z)):
				p.x=span.position.x-.01
				world.actor.global_position=to_global(p)
		if art:
			art.visible=paid
			if not paid: art.set_hero_outline(false)
			raising=0.0 if paid and presented else 1.0
			art.set_build_progress(raising)
	presented=true
	if not active or not art: return
	art.animate(dt)
	art.update_sightline(world.actor.global_position,world.camera)
	if raising<1.0:
		raising=minf(1.0,raising+dt*1.6)
		art.set_build_progress(raising)
		return
	reload=maxf(0.0,reload-dt)
	var target := nearest()
	if is_instance_valid(target):
		var aim: Vector3=target.position+Vector3.UP*.72*target.size_factor()
		var aligned: bool = art.aim_at_world(aim,dt)
		if aligned and reload<=0.0:
			var model: Node3D = art.projectile()
			if model:
				world.add_child(model)
				model.global_transform=art.bolt.global_transform
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
		if arrived and alive and world.encounters.outside(target_node.position,target_node.sanctuary_margin()) and target_node.receive_hit(1,global_position):
			var spark: Sprite3D = art.impact()
			world.add_child(spark)
			spark.global_position = _visible_contact(target_node,f.at)
			art.play_impact(spark)
			world._event("tower_hit",f.at)

# The damage point is inside the torso. Keep its screen position, but draw
# the contact on the camera-facing fur so the wolf cannot hide the burst.
func _visible_contact(target: Node3D, at: Vector3) -> Vector3:
	var fur: MeshInstance3D = target.surface
	var toward_camera: Vector3 = world.camera.global_basis.z.normalized()
	var front: Vector3 = at + toward_camera * 3.0 * target.size_factor()
	if fur:
		var contact = fur.get_aabb().intersects_segment(fur.to_local(front),fur.to_local(at))
		if contact != null:
			return fur.to_global(contact) + toward_camera * .08
	return at + toward_camera * .84 * target.size_factor()
