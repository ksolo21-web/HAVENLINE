extends RefCounted
const Wolf = preload("res://field_enemy.gd")
const LIVE_CAP := 4
const WAVE_SECONDS := 24.0
const BOSS_CHANCE := .18
const MIN_PLAYER_GAP := 5.2
const RETIRE_RANGE := 32.0
var world: Node3D
var rng := RandomNumberGenerator.new()
var encounter_seconds := WAVE_SECONDS
var boss_chance := BOSS_CHANCE
var remaining := 0.0
var wave := 0
var serial := 0
var boss_rolls := 0
var last_roll := false
var repath := 0.0

func setup(host: Node3D) -> void:
	world = host
	rng.randomize()

func _point_inside(p: Vector3) -> bool:
	if world.field_env.has_method("is_inside_camp"):
		return world.field_env.is_inside_camp(p)
	var rect: Array = world.layout.camp_rect_xz
	return world.camp_active and p.x >= rect[0] and p.x <= rect[2] and p.z >= rect[1] and p.z <= rect[3]

func outside(p: Vector3, radius: float) -> bool:
	var limit := float(world.layout.snow_extent_half)-radius
	if absf(p.x)>limit or absf(p.z)>limit: return false
	for dx: float in [-radius,0.0,radius]:
		for dz: float in [-radius,0.0,radius]:
			if _point_inside(p+Vector3(dx,0,dz)): return false
	return true

func sweep(from: Vector3,to: Vector3,radius: float) -> bool:
	var count := maxi(1,ceili(from.distance_to(to)/.4))
	for i in range(1,count+1):
		if not outside(from.lerp(to,float(i)/count),radius): return false
	return true

func can_walk(from: Vector3,to: Vector3,wolf: Wolf) -> bool:
	if not sweep(from,to,wolf.sanctuary_margin()): return false
	for other in world.enemies:
		if other==wolf or other.hp<=0: continue
		var clearance: float=wolf.sanctuary_margin()+other.sanctuary_margin()
		var d: float=to.distance_squared_to(other.position)
		if d<clearance*clearance and d<from.distance_squared_to(other.position):
			return false
	return true

func _plan(anchor: Vector3, player: Vector3, occupied: Array, capacity: int) -> Array:
	var result: Array = []
	if capacity <= 0: return result
	var count := mini(capacity,rng.randi_range(2,4))
	# Consider the largest footprint before rolling. A blocked spawn never consumes a boss roll.
	for _attempt in range(56):
		var angle := rng.randf_range(0,TAU)
		var r := rng.randf_range(2.0,5.2)
		var pos := anchor + Vector3(cos(angle)*r,0,sin(angle)*r)
		if pos.distance_to(player)<MIN_PLAYER_GAP or not outside(pos,2.0): continue
		var gap := true
		for other in occupied + result:
			if pos.distance_squared_to(other)<15.21:
				gap=false
				break
		if not gap: continue
		result.append(pos)
		if result.size()==count: break
	if not result.is_empty():
		last_roll = rng.randf()<boss_chance
		boss_rolls += 1
	return result

func anchor_for(pos: Vector3) -> Vector3:
	var east := maxf(8.0,float(world.layout.camp_rect_xz[2]))
	if pos.distance_squared_to(Vector3.ZERO)<19.0*19.0:
		return Vector3(east+4.2,0,1.8)
	var limit := float(world.layout.snow_extent_half)-7.3
	var offset := Vector3(-8.8 if pos.x+8.8>limit else 8.8,0,-1.8 if pos.z>0 else 1.8)
	return Vector3(clampf(pos.x+offset.x,-limit,limit),0,clampf(pos.z+offset.z,-limit,limit))

func _add(p: Vector3, boss: bool, id: int, home: Vector3) -> Wolf:
	var wolf := Wolf.new()
	wolf.name = ("AlphaWolf" if boss else "RidgeWolf")+str(id)
	wolf.is_boss=boss
	wolf.spawn_id=id
	wolf.position=p
	world.add_child(wolf)
	wolf.configure(world.actor)
	wolf.home=home
	wolf.player_hit.connect(world._player_hit)
	wolf.defeated.connect(world._wolf_defeated.bind(wolf))
	world.enemies.append(wolf)
	if wolf.contact_mesh(): world.register_hostile(wolf,wolf.contact_mesh())
	if "tracks" in world and world.tracks and world.tracks.has_method("register_actor"):
		world.tracks.register_actor(wolf,"wolf",wolf.size_factor())
	return wolf

func launch(announce := true) -> bool:
	var points: Array = []
	for wolf in world.enemies: points.append(wolf.position)
	var player: Vector3 = world.actor.position
	var plans := _plan(anchor_for(player),player,points,LIVE_CAP-points.size())
	if plans.is_empty(): return false
	wave+=1
	for i in plans.size():
		serial+=1
		var wolf = _add(plans[i],last_roll and i==0,serial,plans[i])
		if announce and wolf.is_boss: world._event("boss_arrival",wolf.position)
	if announce: world._event("wolf_return",plans[0])
	world.enemy=world.enemies.front()
	remaining=encounter_seconds
	return true

func _remove(wolf: Wolf) -> void:
	world.surfaces.erase(wolf)
	world.enemies.erase(wolf)
	wolf.active=false
	wolf.hide()
	wolf.remove_from_group("swirl_hostiles")
	wolf.queue_free()
	world.enemy=world.enemies.front() if not world.enemies.is_empty() else null

func advance(dt: float) -> bool:
	var pos: Vector3 = world.actor.position
	var danger := false
	var hero_safe := _point_inside(pos)
	repath -= dt
	var scan := repath<=0
	if scan: repath=.25
	for wolf in world.enemies.duplicate():
		if wolf.hp<=0:
			wolf.advance(dt)
			if not wolf.visible: _remove(wolf)
			continue
		if not outside(wolf.position,wolf.sanctuary_margin()) or (scan and wolf.position.distance_squared_to(pos)>RETIRE_RANGE*RETIRE_RANGE):
			_remove(wolf)
			continue
		var prev: String=wolf.state
		wolf.advance(dt,can_walk.bind(wolf),not hero_safe)
		if prev != wolf.state:
			if wolf.state=="stalk" and prev in ["guard","return"]: world._event("approach",wolf.position)
			elif wolf.state=="windup": world._event("wolf_brace",wolf.position)
			elif wolf.state=="lunge": world._event("enemy_attack",wolf.position)
		danger = danger or wolf.state in ["stalk","windup","lunge","recover","stagger"]
	remaining=maxf(0.0,remaining-dt)
	if remaining<=0.0 and world.enemies.size()<LIVE_CAP:
		if launch(): world._checkpoint_lifecycle()
		else: remaining=1.0
	return danger

func snapshot() -> Dictionary:
	var list := []
	for wolf in world.enemies:
		if wolf.hp>0: list.append([wolf.spawn_id,wolf.is_boss,wolf.hp,wolf.position.x,wolf.position.z,wolf.home.x,wolf.home.z])
	return {"remaining":remaining,"wave":wave,"serial":serial,"rng":str(rng.state),"live":list}

func restore(p: Dictionary) -> bool:
	if not p.get("live") is Array or p.live.size()>LIVE_CAP or not p.get("rng") is String or not p.rng.is_valid_int(): return false
	for key in ["remaining","wave","serial"]:
		var v: Variant = p.get(key)
		if (not v is int and not v is float) or not is_finite(float(v)) or v<0: return false
	if p.remaining>86400 or p.serial!=int(p.serial) or p.wave!=int(p.wave): return false
	var ids := {}
	for row in p.live:
		if not row is Array or row.size()!=7 or not row[1] is bool: return false
		for i in [0,2,3,4,5,6]:
			if (not row[i] is float and not row[i] is int) or not is_finite(float(row[i])): return false
		if row[0]!=int(row[0]) or row[0]<1 or row[0]>p.serial or ids.has(int(row[0])) or row[2]!=int(row[2]) or row[2]<1 or row[2]>(Wolf.BOSS_HEALTH if row[1] else Wolf.MAX_HEALTH): return false
		ids[int(row[0])]=true
	for wolf in world.enemies.duplicate(): _remove(wolf)
	for row in p.live:
		var point := Vector3(row[3],0,row[4])
		if not outside(point,1.975 if row[1] else 1.25): continue
		var wolf = _add(point,row[1],int(row[0]),Vector3(row[5],0,row[6]))
		wolf.hp=int(row[2])
		wolf._refresh_health()
	if not world.enemies.is_empty(): world.enemy=world.enemies.front()
	remaining=p.remaining
	wave=int(p.wave)
	serial=int(p.serial)
	rng.state=p.rng.to_int()
	return true
