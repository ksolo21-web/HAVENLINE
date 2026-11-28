extends RefCounted
## Timers use played simulation seconds. Cooling sources keep their IDs when streamed out.
const WOOD_REGROW_SECONDS := preload("res://resource_tree.gd").REGROW_SECONDS
const MiningResources = preload("res://mining_resources.gd")
const Inventory = preload("res://field_inventory.gd")
const DROP_LIFETIME_SECONDS := 100.0
const VERSION := 2
const V1_PLAYER_MAX_HP := 4
var wood_seconds := WOOD_REGROW_SECONDS
var mining_seconds := MiningResources.REGROW_SECONDS
var world: Node3D
var loaded := {}
var cooling := {}
var partial := {}
var availability_revision := 0

func register(id: String, kind: String, node: Node3D) -> void:
	node.set_meta("field_source_id",id)
	node.set_meta("resource_kind",kind)
	loaded[id] = node
	if cooling.has(id):
		cooling[id] = minf(cooling[id], wood_seconds if kind == "wood" else mining_seconds)
		_set_available(node, false)
		node.show_return(float(cooling[id]))
	elif partial.has(id):
		_restore_strikes(node,partial[id])

func _restore_strikes(node: Node3D, count: int) -> void:
	if node.get_meta("resource_kind")=="wood":
		node.restore_notches(count)
	else:
		node.restore_strikes(count)

func record_strike(node: Node3D) -> void:
	var id: String = node.get_meta("field_source_id")
	if node.strikes>0 and node.strikes<3: partial[id]=node.strikes

func deplete(node: Node3D) -> void:
	var id: String = node.get_meta("field_source_id")
	var kind: String = node.get_meta("resource_kind")
	if cooling.has(id): return
	partial.erase(id)
	availability_revision += 1
	cooling[id] = wood_seconds if kind == "wood" else mining_seconds
	_set_available(node,false)

func _set_available(node: Node3D, available: bool) -> void:
	if node.get_meta("resource_kind") == "wood":
		if available:
			node._regrow()
		else:
			node.phase = "credited"
			node._pivot.hide()
	else:
		node.set_available(available)

func advance(dt: float) -> void:
	for id: String in cooling.keys():
		cooling[id] -= maxf(dt,0.0)
		if cooling[id] > .000001:
			var active = loaded.get(id)
			if is_instance_valid(active) and cooling[id] <= active.RETURN_SECONDS:
				active.show_return(cooling[id])
			continue
		cooling.erase(id)
		availability_revision += 1
		var node = loaded.get(id)
		if is_instance_valid(node):
			_set_available(node,true)
			world._event("regrow_"+String(node.get_meta("resource_kind")),node.position)

func snapshot() -> Dictionary:
	var ground: Array = []
	for id: String in world.drops:
		if world.inventory.collected.has(id): continue
		var d: Dictionary = world.drops[id]
		var at: Vector3 = d.at
		ground.append([id,d.kind,at.x,at.z,maxf(0.0,DROP_LIFETIME_SECONDS-float(d.age))])
	var player := {"x":world.actor.position.x,"z":world.actor.position.z,"yaw":world.actor.rotation.y,
		"hp":world.player_hp,"camp_heal_elapsed":world.camp_heal_elapsed,"protection_left":world.player_invulnerability,"fall_left":world.reset_time}
	return {"version":VERSION,"river_layout":world.river.LAYOUT_VERSION,"river_time":world.river.flow_time,
		"previous_kitchen_site":world.camp_layout != null and world.camp_layout.previous_kitchen_site,
		"layout":world.camp_layout.snapshot() if world.camp_layout else {}, "player":player,"cooling":cooling.duplicate(),"partial":partial.duplicate(),"drops":ground,"serial":world.drop_id,"pack":world.encounters.snapshot()}

static func _number(v: Variant) -> bool:
	return (v is float or v is int) and is_finite(float(v))

func _closed_boundary_clearance() -> float:
	return float(world.layout.actor_radius) + float(world.field_env.FENCE_DEPTH)*.5 + .025

func _near_closed_boundary(p: Vector3) -> bool:
	if not world.camp_active: return false
	var r:Array=world.layout.camp_rect_xz
	var pad:=_closed_boundary_clearance()
	var along_x:bool=p.x>=r[0]-pad and p.x<=r[2]+pad
	var along_z:bool=p.z>=r[1]-pad and p.z<=r[3]+pad
	return (along_x and minf(absf(p.z-r[1]),absf(p.z-r[3]))<pad) or (along_z and minf(absf(p.x-r[0]),absf(p.x-r[2]))<pad)

func safe_start() -> Vector3:
	if world.inventory.complete(world.HEARTH_OFFER):
		# Clear of the central furnace, both gate arcs, and the northwest apron.
		return Vector3(1.72,0,1.8)
	return world.point(world.layout.pad_xz)

func _restore_actor(state: Variant, version: int = VERSION) -> void:
	if not state is Dictionary: return
	var pos:=safe_start()
	var limit:=float(world.layout.snow_extent_half)-float(world.layout.private_travel_inset)-float(world.layout.actor_radius)
	if _number(state.get("x")) and _number(state.get("z")):
		var candidate:=Vector3(state.x,0,state.z)
		if absf(candidate.x)<=limit and absf(candidate.z)<=limit:
			if not _near_closed_boundary(candidate):
				pos=candidate
			elif not world.field_env.is_inside_camp(candidate):
				# Gates load closed. Push an exterior save back onto snow instead
				# of moving an injured traveller across the fence into sanctuary.
				var bounds: Array = world.layout.camp_rect_xz
				var clear := _closed_boundary_clearance()
				pos = candidate
				if pos.x < bounds[0]: pos.x = minf(pos.x,bounds[0]-clear)
				if pos.x > bounds[2]: pos.x = maxf(pos.x,bounds[2]+clear)
				if pos.z > bounds[3]: pos.z = maxf(pos.z,bounds[3]+clear)
				if pos.z < bounds[1]:
					# The final service counter projects farther than the fence.
					if world.field_env.perimeter_stage == 3 and absf(pos.x-world.field_env.counter_center_x) < world.field_env.CounterLayout.HALF_BAY+clear:
						clear += .9
					pos.z = minf(pos.z,bounds[1]-clear)
	if world.camp_active:
		pos = world.field_env.clear_hearth_footprint(pos)
	if world.counter and world.counter.active:
		pos = world.counter.constrain_actor(pos,pos,float(world.layout.actor_radius))
	if world.river: pos = world.river.safe_feet(pos,float(world.layout.actor_radius))
	world.actor.position=pos
	world.actor.velocity=Vector3.ZERO
	if _number(state.get("yaw")): world.actor.rotation.y=wrapf(float(state.yaw),-PI,PI)
	world.player_hp=world.MAX_HP
	var recorded_max: int = V1_PLAYER_MAX_HP if version == 1 else world.MAX_HP
	if _number(state.get("hp")) and state.hp==int(state.hp) and state.hp>=0 and state.hp<=recorded_max:
		world.player_hp = roundi(float(state.hp) * world.MAX_HP / recorded_max)
	world.player_invulnerability = 0.0
	if _number(state.get("protection_left")):
		world.player_invulnerability = clampf(float(state.protection_left),0.0,2.0)
	world.reset_time = 0.0
	if world.player_hp == 0:
		world.reset_time = 1.05
		if _number(state.get("fall_left")) and state.fall_left > 0:
			world.reset_time = minf(float(state.fall_left),1.05)
	world.camp_heal_elapsed = 0.0
	if world.is_camp_healing() and _number(state.get("camp_heal_elapsed")) and state.camp_heal_elapsed >= 0 and state.camp_heal_elapsed < world.CAMP_HEAL_INTERVAL:
		world.camp_heal_elapsed = float(state.camp_heal_elapsed)
	world.camera.position=pos+world.camera_follow_offset
	if world.tracks: world.tracks.reset_actor(world.actor)

func _saved_source_kind(id: String, node) -> String:
	if is_instance_valid(node): return node.get_meta("resource_kind")
	if id == "starter-stone": return "stone"
	if id == "starter-wood" or id.begins_with("pine@") or id.begins_with("grove@"): return "wood"
	if id.begins_with("world1/"): return id.get_slice("/", 3)
	return ""

func restore(data: Dictionary) -> bool:
	if data.is_empty(): return true
	if (data.get("version") != 1 and data.get("version") != VERSION) or not data.get("cooling") is Dictionary or not data.get("drops") is Array or not data.get("pack") is Dictionary: return false
	var river_time: Variant = data.get("river_time",0.)
	if data.get("river_layout",world.river.LAYOUT_VERSION) != world.river.LAYOUT_VERSION or not _number(river_time) or river_time < 0.0 or river_time >= 400.0: return false
	if not _number(data.get("serial")) or data.serial < 0 or data.serial != int(data.serial) or data.serial > 9007199254740991: return false
	if data.cooling.size() > 8192: return false
	for key in data.cooling:
		if not key is String or key.is_empty() or not _number(data.cooling[key]) or data.cooling[key]<0 or data.cooling[key]>86400: return false
	var unique := {}
	for d in data.drops:
		if not d is Array or d.size()!=5 or not d[0] is String or d[0].is_empty() or unique.has(d[0]) or d[1] not in Inventory.KINDS: return false
		if not _number(d[2]) or not _number(d[3]) or not _number(d[4]) or d[4]<0 or d[4]>DROP_LIFETIME_SECONDS: return false
		unique[d[0]]=true
	var hits: Variant = data.get("partial",{})
	if not hits is Dictionary or hits.size()>8192: return false
	for id in hits:
		if not id is String or id.is_empty() or id in data.cooling or not _number(hits[id]) or hits[id]!=int(hits[id]) or int(hits[id]) not in [1,2]: return false
	if not world.encounters.restore(data.pack): return false
	world.river.flow_time = float(river_time)
	world.river.tick(0.0)
	for id in cooling:
		if is_instance_valid(loaded.get(id)): _set_available(loaded[id],true)
	for id in partial:
		if is_instance_valid(loaded.get(id)): _restore_strikes(loaded[id],0)
	partial = hits.duplicate()
	for id in partial:
		if is_instance_valid(loaded.get(id)): _restore_strikes(loaded[id],int(partial[id]))
	cooling = data.cooling.duplicate()
	availability_revision += 1
	for id: String in cooling:
		var entry = loaded.get(id)
		# Clamp known deposits from old versions even when their cell isn't loaded.
		# Unrecognised IDs retain their timer until a source registers its kind.
		var kind := _saved_source_kind(id, entry)
		if kind == "wood":
			cooling[id] = minf(cooling[id], wood_seconds)
		elif kind in MiningResources.KINDS:
			cooling[id] = minf(cooling[id], mining_seconds)
		if is_instance_valid(entry):
			_set_available(entry,false)
			entry.show_return(float(cooling[id]))
	for id in world.drops.keys(): world._remove_drop(id)
	_restore_actor(data.get("player"),int(data.version))
	world.drop_id = int(data.serial)
	for d in data.drops:
		if world.inventory.collected.has(d[0]) or d[4]<=0: continue
		var p := Vector3(d[2],0,d[3])
		world._place_drop(d[0],d[1],p,p,0.0,maxf(.30,DROP_LIFETIME_SECONDS-float(d[4])))
	return true
