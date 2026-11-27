extends SceneTree
## Exercise the exposed weapon, its crew, and the actual flight/damage path.
const Session = preload("res://tests/lifecycle_test_profile.gd")
const DT := 1.0/60.0
var checks := {}
var observations := {}
func _initialize() -> void:
	if not Session.isolated(self, "res://tests/qa_staffed_ballista.gd"):
		call_deferred("run")

func run() -> void:
	var game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	for i in 5:await physics_frame
	game.set_physics_process(false)
	var tower = game.defense_tower
	var art = tower.art
	for enemy in game.enemies:enemy.active = false
	tower.advance(DT,false)
	var at:Vector3 = tower.global_position+Vector3(6.8,0.,4.1)
	var wolf = game.encounters._add(at,false,998,at)
	for i in 120:tower.advance(DT,false)
	checks["No visible station, operator or fire before payment"] = not art.visible and tower.flights.is_empty() and wolf.hp==wolf.max_hp()
	tower.advance(DT,true)
	checks["Purchased footings rise before the crew takes its station"] = art.visible and not art.swivel.is_visible_in_tree()
	for i in 42:tower.advance(DT,true)
	checks["Purchased camp exposes an occupied open deck"] = tower.active and art.crew.is_visible_in_tree() and art.bow.is_visible_in_tree() and art.bolt.is_visible_in_tree() and art.crew.rig.get_bone_count()>=16
	var guard_meshes: Array[Node] = art.crew.find_children("*","MeshInstance3D",true,false)
	checks["See-through pass is attached to the operator's skinned surfaces"] = not guard_meshes.is_empty() and guard_meshes.all(func(part): return part.material_overlay is ShaderMaterial and part.material_overlay.shader==art.GUARD_SIGHTLINE)
	var platform_meshes: Array[Node] = art.frame.find_children("*","MeshInstance3D",true,false)
	checks["Tower and launcher surfaces have no highlight pass or emission"] = platform_meshes.filter(func(part): return part not in guard_meshes).all(func(part): return part.material_overlay==null and not part.get_active_material(0).emission_enabled)
	var bow_box:AABB = art.bow.get_aabb()
	checks["Bow has a two-limb silhouette wider than the operator"] = bow_box.size.x>1.70 and bow_box.size.z>1.15
	for i in 50:art.aim_at_world(at+Vector3.UP*.72,DT)
	art.animate(DT)
	var hand_at_rest:Vector3 = art.crew.rig.get_bone_global_pose(art.crew.bones["Palm.R"]).origin
	var load_point:Vector3 = art.muzzle_global_position()
	var initial_hp:int = wolf.hp
	tower.reload=0.
	tower.advance(0.,true)
	checks["Asset that leaves the stock is the displayed textured quarrel"] = tower.flights.size()==1 and tower.flights[0].mesh.mesh==art.bolt.mesh and not art.bolt.visible
	if tower.flights.is_empty():
		print("STAFFED_BALLISTA ", JSON.stringify(checks))
		quit(2)
		return
	var origin_error:float = load_point.distance_to(tower.flights[0].mesh.global_position)
	observations["muzzle_error_m"]=origin_error
	checks["Release originates at loaded bolt before the first travel tick"] = origin_error<.002
	var launch:Vector3 = tower.flights[0].mesh.global_position
	tower.advance(DT,true)
	checks["Bolt travels toward the live target before damage"] = wolf.hp==initial_hp and tower.flights[0].mesh.global_position.distance_to(launch)>.15
	for i in 39:tower.advance(DT,true)
	checks["Real hit, contact flash and no duplicate damage"] = wolf.hp==initial_hp-1 and game.find_child("BallistaImpact",false,false) != null and tower.flights.is_empty()
	var hand_working:Vector3 = art.crew.rig.get_bone_global_pose(art.crew.bones["Palm.R"]).origin
	observations["winding_hand_travel_m"]=hand_working.distance_to(hand_at_rest)
	checks["Crew works the stock while the next bolt loads"] = hand_working.distance_to(hand_at_rest)>.035 and not art.bolt.visible
	for i in 26:tower.advance(DT,true)
	checks["A fresh quarrel is seated before the next discharge"] = art.bolt.visible and tower.reload>0.
	for side in ["R","L"]:
		var palm:Vector3 = art.crew.rig.to_global(art.crew.rig.get_bone_global_pose(art.crew.bones["Palm."+side]).origin)
		var rest:Vector3 = art.crew.grip_position(side)
		observations["glove_to_grip_"+side+"_m"] = palm.distance_to(rest)
		checks["Glove "+side+" stays within a gloved palm of the operating grip"] = palm.distance_to(rest)<.025
	var tread: MeshInstance3D = art.swivel.find_child("GunnerTread",true,false)
	var supported := is_instance_valid(tread)
	var verts: PackedVector3Array = tread.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var bounds := AABB(verts[0],Vector3.ZERO)
	for pt in verts: bounds=bounds.expand(pt)
	var clear := true
	var max_error := 0.
	for i in 48:
		var yaw := TAU*i/48.
		var direction := Vector3(sin(yaw)*5.5,.72+sin(2.*yaw)*1.3,cos(yaw)*5.5)
		art.aim_at_world(tower.global_position+direction,1.)
		art.animate(DT)
		var bow_back := INF
		for corner in 8:
			var extent: Vector3 = art.swivel.to_local(art.bow.to_global(bow_box.get_endpoint(corner)))
			bow_back = minf(bow_back,extent.z)
		for joint in ["Pelvis","Thigh.L","Thigh.R","Chest"]:
			var bone: Vector3 = art.crew.rig.get_bone_global_pose(art.crew.bones[joint]).origin
			var at_bone: Vector3 = art.swivel.to_local(art.crew.rig.to_global(bone))
			clear = clear and at_bone.z+.10<bow_back
		for side in ["R","L"]:
			var bone: Vector3 = art.crew.rig.get_bone_global_pose(art.crew.bones["Foot."+side]).origin
			var sole: Vector3 = tread.to_local(art.crew.rig.to_global(bone))
			# The first mesh surface is the solid plank under both boots.
			supported = supported and Rect2(bounds.position.x,bounds.position.z,bounds.size.x,bounds.size.z).has_point(Vector2(sole.x,sole.z))
			var palm: Vector3 = art.crew.rig.get_bone_global_pose(art.crew.bones["Palm."+side]).origin
			max_error=maxf(max_error,art.crew.rig.to_global(palm).distance_to(art.crew.grip_position(side)))
	checks["Crew hips, chest and thighs stay behind the swept bow"] = clear
	checks["Both feet stay on the turning tread for a full revolution"] = supported
	observations["max_glove_to_handle_across_traverse_m"] = max_error
	checks["Both gloves follow the modeled controls while turning"] = max_error<.025
	print("STAFFED_BALLISTA ",JSON.stringify({"checks":checks,"observed":observations}))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,game)
	game.queue_free()
	for i in 5:await process_frame
	quit(0 if not checks.values().has(false) else 1)
