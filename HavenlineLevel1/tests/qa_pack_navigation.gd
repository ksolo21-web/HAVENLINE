extends SceneTree
## The player and pack are positioned once per scenario; all subsequent travel,
## acquisition, bites and retreat use the live enemy and encounter state machines.
const Session = preload("res://tests/lifecycle_test_profile.gd")
var world
var checks := {}
var measurements := {}

func _initialize() -> void:
	if not Session.isolated(self,"res://tests/qa_pack_navigation.gd"): call_deferred("run")

func prepare(at: Vector3, player: Vector3):
	for wolf in world.enemies.duplicate(): world.encounters._remove(wolf)
	world.encounters.remaining = 90.
	world.actor.position = player
	world.player_hp = world.MAX_HP
	world.player_invulnerability = 0.
	world.encounters.serial += 1
	return world.encounters._add(at,false,world.encounters.serial,at)

func cross(key: String, at: Vector3, player: Vector3, use_lake: bool) -> void:
	var wolf=prepare(at,player)
	var dry := true
	var earliest_bite := -1
	var touched_states := {}
	var route := []
	var longest_streak := 0
	var still := 0
	for i in 900:
		var prev: Vector3 = wolf.position
		world.encounters.advance(1./60.)
		touched_states[wolf.state]=true
		var here := Vector2(wolf.position.x,wolf.position.z)
		if use_lake:
			var near: Vector2=world.lakeshore._closest_bank(here)
			if Geometry2D.is_point_in_polygon(here,world.lakeshore.shore) or here.distance_to(near)<wolf.sanctuary_margin()-.02: dry=false
		else:
			var margin: float=wolf.sanctuary_margin()-.005
			for delta in [Vector3(margin,0,margin),Vector3(-margin,0,margin),Vector3(margin,0,-margin),Vector3(-margin,0,-margin)]:
				if world.field_env.is_inside_camp(wolf.position+delta): dry=false
		if i%20==0: route.append([snappedf(wolf.position.x,.01),snappedf(wolf.position.z,.01)])
		still = still+1 if wolf.state=="stalk" and prev.distance_squared_to(wolf.position)<.000001 else 0
		longest_streak=maxi(longest_streak,still)
		if world.player_hp<world.MAX_HP:
			earliest_bite=i
			break
	checks[key+"_detours_to_a_real_bite"] = earliest_bite>=0 and touched_states.has_all(["stalk","windup","lunge"])
	checks[key+"_footprint_stays_dry_and_outside"] = dry
	checks[key+"_no_stuck_chase"] = longest_streak<15
	measurements[key]={"bite_seconds":earliest_bite/60.0,"source":str(at),"target":str(player),"route_xz":route,"longest_stuck_ticks":longest_streak}
	if not use_lake:
		world.actor.position=Vector3.ZERO
		var hp: int=world.player_hp
		var returned := false
		for i in 1600:
			world.encounters.advance(1./60)
			if wolf.state=="guard" and wolf.position.distance_to(at)<.06:
				returned=true;break
		checks["animal_finds_its_way_home_around_other_side_of_fence"] = returned and world.player_hp==hp
		var patrol_reached := 0.
		var patrolled := false
		for i in 420:
			world.encounters.advance(1./60)
			patrolled = patrolled or wolf.state=="patrol"
			patrol_reached=maxf(patrol_reached,wolf.position.distance_to(at))
		checks["unengaged_wolf_patrols_its_territory_while_owner_is_safe"] = patrolled and patrol_reached>.8 and world.player_hp==hp
		measurements[key]["patrol_excursion_m"]=patrol_reached

func run() -> void:
	world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await physics_frame
	world.set_physics_process(false)
	world.world_landscape.set_physics_process(false)
	# Choose a real short cross-section near the northern tip of the mapped inlet.
	var bank=world.lakeshore
	var crossing_z: float=bank.bounds.end.y-2.2
	var xs: Array[float]=[]
	for i in bank.shore.size():
		var a: Vector2=bank.shore[i]
		var b: Vector2=bank.shore[(i+1)%bank.shore.size()]
		if (a.y>crossing_z)==(b.y>crossing_z): continue
		xs.append(lerpf(a.x,b.x,(crossing_z-a.y)/(b.y-a.y)))
	xs.sort()
	cross("unbuilt_camp_inlet",Vector3(xs[0]-2.6,0,crossing_z),Vector3(xs[-1]+2.6,0,crossing_z),true)
	for j in world.inventory.costs.center_hearth.wood:
		world.inventory.collect("pack-"+str(j),"wood")
		world.inventory.payment("center_hearth","wood",false)
	world._finish_purchase("center_hearth")
	world._apply_hearth(true,false)
	cross("paid_camp_perimeter",Vector3(-6.8,0,0),Vector3(6.8,0,.18),false)
	print("PACK_NAV ",JSON.stringify({"passed":not checks.values().has(false),"checks":checks,"observations":measurements}))
	await Session.drain_field_audio(self,world)
	world.queue_free()
	for i in 3:await process_frame
	quit(int(checks.values().has(false)))
