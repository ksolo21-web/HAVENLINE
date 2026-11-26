extends RefCounted
## Timers use played simulation seconds. Cooling sources keep their IDs when streamed out.
const WOOD_REGROW_SECONDS := 22.0
const STONE_REGROW_SECONDS := 32.0
const DROP_LIFETIME_SECONDS := 100.0
const DROP_CAP := 72
var wood_seconds := WOOD_REGROW_SECONDS
var stone_seconds := STONE_REGROW_SECONDS
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
		_set_available(node, false)
	elif partial.has(id):
		_restore_strikes(node,partial[id])

func _restore_strikes(node: Node3D, count: int) -> void:
	node.strikes = count
	if node.get_meta("resource_kind")=="stone":
		node._mesh.scale=Vector3.ONE*(1.0-.18*count)
		node._mesh.position.y=-node._mesh.mesh.get_aabb().position.y*node._mesh.scale.y

func record_strike(node: Node3D) -> void:
	var id: String = node.get_meta("field_source_id")
	if node.strikes>0 and node.strikes<3: partial[id]=node.strikes

func deplete(node: Node3D) -> void:
	var id: String = node.get_meta("field_source_id")
	var kind: String = node.get_meta("resource_kind")
	partial.erase(id)
	availability_revision += 1
	cooling[id] = wood_seconds if kind == "wood" else stone_seconds
	_set_available(node,false)

func _set_available(node: Node3D, available: bool) -> void:
	if node.get_meta("resource_kind") == "wood":
		if available:
			node._regrow()
		else:
			node.phase = "credited"
			node._pivot.hide()
	else:
		node.phase = "seated" if available else "mined"
		node.strikes = 0 if available else 3
		node._mesh.visible = available
		if available:
			node._mesh.scale = Vector3.ONE
			node._mesh.position.y = -node._mesh.mesh.get_aabb().position.y

func advance(dt: float) -> void:
	for id: String in cooling.keys():
		cooling[id] -= maxf(dt,0.0)
		if cooling[id] > 0.0: continue
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
	return {"version":1,"player":{"x":world.actor.position.x,"z":world.actor.position.z,"yaw":world.actor.rotation.y,"hp":world.player_hp},"cooling":cooling.duplicate(),"partial":partial.duplicate(),"drops":ground,"serial":world.drop_id,"pack":world.encounters.snapshot()}

static func _number(v: Variant) -> bool:
	return (v is float or v is int) and is_finite(float(v))

func _near_closed_boundary(p: Vector3) -> bool:
	if not world.camp_active: return false
	var r:Array=world.layout.camp_rect_xz
	var pad:=float(world.layout.actor_radius)+.22
	var along_x:bool=p.x>=r[0]-pad and p.x<=r[2]+pad
	var along_z:bool=p.z>=r[1]-pad and p.z<=r[3]+pad
	return (along_x and minf(absf(p.z-r[1]),absf(p.z-r[3]))<pad) or (along_z and minf(absf(p.x-r[0]),absf(p.x-r[2]))<pad)

func safe_start() -> Vector3:
	var p:Vector3=world.point(world.layout.start_xz)
	if _near_closed_boundary(p):
		p.z=float(world.layout.camp_rect_xz[3])+float(world.layout.actor_radius)+.8
	return p

func _restore_actor(state: Variant) -> void:
	if not state is Dictionary: return
	var pos:=safe_start()
	var limit:=float(world.layout.snow_extent_half)-float(world.layout.private_travel_inset)-float(world.layout.actor_radius)
	if _number(state.get("x")) and _number(state.get("z")):
		var candidate:=Vector3(state.x,0,state.z)
		if absf(candidate.x)<=limit and absf(candidate.z)<=limit and not _near_closed_boundary(candidate):
			pos=candidate
	world.actor.position=pos
	world.actor.velocity=Vector3.ZERO
	if _number(state.get("yaw")): world.actor.rotation.y=wrapf(float(state.yaw),-PI,PI)
	world.player_hp=world.MAX_HP
	if _number(state.get("hp")) and state.hp==int(state.hp) and state.hp>=0 and state.hp<=world.MAX_HP:
		world.player_hp=int(state.hp)
	world.reset_time=1.05 if world.player_hp==0 else 0.0
	world.camera.position=pos+Vector3(7,11,11)
	if world.tracks: world.tracks.reset_actor(world.actor)

func restore(data: Dictionary) -> bool:
	if data.is_empty(): return true
	if data.get("version") != 1 or not data.get("cooling") is Dictionary or not data.get("drops") is Array or not data.get("pack") is Dictionary: return false
	if not _number(data.get("serial")) or data.serial < 0 or data.serial != int(data.serial) or data.serial > 9007199254740991: return false
	if data.cooling.size() > 8192 or data.drops.size() > DROP_CAP: return false
	for key in data.cooling:
		if not key is String or key.is_empty() or not _number(data.cooling[key]) or data.cooling[key]<0 or data.cooling[key]>86400: return false
	var unique := {}
	for d in data.drops:
		if not d is Array or d.size()!=5 or not d[0] is String or d[0].is_empty() or unique.has(d[0]) or d[1] not in ["wood","stone","meat"]: return false
		if not _number(d[2]) or not _number(d[3]) or not _number(d[4]) or d[4]<0 or d[4]>DROP_LIFETIME_SECONDS: return false
		unique[d[0]]=true
	var hits: Variant = data.get("partial",{})
	if not hits is Dictionary or hits.size()>8192: return false
	for id in hits:
		if not id is String or id.is_empty() or id in data.cooling or not _number(hits[id]) or hits[id]!=int(hits[id]) or int(hits[id]) not in [1,2]: return false
	if not world.encounters.restore(data.pack): return false
	for id in cooling:
		if is_instance_valid(loaded.get(id)): _set_available(loaded[id],true)
	for id in partial:
		if is_instance_valid(loaded.get(id)): _restore_strikes(loaded[id],0)
	partial = hits.duplicate()
	for id in partial:
		if is_instance_valid(loaded.get(id)): _restore_strikes(loaded[id],int(partial[id]))
	cooling = data.cooling.duplicate()
	availability_revision += 1
	for id in cooling:
		if is_instance_valid(loaded.get(id)): _set_available(loaded[id],false)
	for id in world.drops.keys(): world._remove_drop(id)
	_restore_actor(data.get("player"))
	world.drop_id = int(data.serial)
	for d in data.drops:
		if world.inventory.collected.has(d[0]) or d[4]<=0: continue
		var p := Vector3(d[2],0,d[3])
		world._place_drop(d[0],d[1],p,p,0.0,maxf(.30,DROP_LIFETIME_SECONDS-float(d[4])))
	return true
