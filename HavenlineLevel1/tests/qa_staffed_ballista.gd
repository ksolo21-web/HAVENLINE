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
		var rest:Vector3 = art.bow.to_global(Vector3(-.18,.14,-.39) if side=="R" else Vector3(-.095,.16,-.29))
		observations["glove_to_grip_"+side+"_m"] = palm.distance_to(rest)
		checks["Glove "+side+" stays within a gloved palm of the operating grip"] = palm.distance_to(rest)<.12
	print("STAFFED_BALLISTA ",JSON.stringify({"checks":checks,"observed":observations}))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,game)
	game.queue_free()
	for i in 5:await process_frame
	quit(0 if not checks.values().has(false) else 1)
