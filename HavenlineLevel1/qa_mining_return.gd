extends SceneTree
## Isolated real-scene regression. Only the actor's approach is positioned by the
## fixture; the ordinary orbit, pick collision, inventory and clock run unmodified.
const Profile = preload("res://opening_save.gd")
const Isolated = preload("res://tests/lifecycle_test_profile.gd")
const MineKinds := preload("res://mining_resources.gd").KINDS
const FAR := Vector3(79,0,68)
const SIDE := Vector3(.707107,0,-.707107)

var world
var checks := {}
var evidence := {}

func _initialize() -> void:
	if Profile.new().configure(OS.get_cmdline_user_args()):
		run.call_deferred()
	elif not Isolated.isolated(self,"res://qa_mining_return.gd"):
		run.call_deferred()

func open_scene() -> void:
	world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)

func reload_scene() -> void:
	world._persist_world()
	reopen_from_disk()

func reopen_from_disk() -> void:
	world.sound.stop_playback()
	world.free()
	open_scene()

func move_to(at:Vector3) -> void:
	world.actor.position=at
	world.actor.velocity=Vector3.ZERO
	world.camera.position=at+Vector3(7,11,11)

func observe_events(kind:String, at:Vector3) -> int:
	var total:=0
	for e in world.events:
		if e.event==kind and Vector2(e.x,e.z).distance_to(Vector2(at.x,at.z))<.04: total+=1
	return total

func nearby_drops(kind:String, at:Vector3) -> Array:
	var found:=[]
	for id in world.drops:
		var d:Dictionary=world.drops[id]
		if d.kind==kind and at.distance_to(d.at)<1.75: found.append(id)
	found.sort()
	return found

func working_face(id:String) -> Variant:
	return world.lifecycle.loaded.get(id)

func approach(face:Vector3) -> void:
	move_to(face+SIDE*2.50)
	world.actor.rotation.y=atan2(-SIDE.x,-SIDE.z)+PI*.67

func strike_until(id:String, kind:String, at:Vector3, hits:int) -> int:
	var before:=observe_events("impact_"+kind,at)
	for tick in 500:
		await physics_frame
		var face=working_face(id)
		if face and face.strikes==hits and observe_events("impact_"+kind,at)>before:
			return observe_events("impact_"+kind,at)-before
	return -1

func examine(row:Dictionary, streamed:bool) -> void:
	var id:String=row.id
	var kind:String=row.kind
	var at:Vector3=row.position
	var prefix:=id+" "
	approach(at)
	var old_drops:=nearby_drops(kind,at)
	var hit_one:int=await strike_until(id,kind,at,1)
	checks[prefix+"first pick contact"]=hit_one==1
	if hit_one!=1: return
	checks[prefix+"first contact leaves the yield in the bank"]=nearby_drops(kind,at)==old_drops and working_face(id)._mesh.is_visible_in_tree()
	var stock:Dictionary=world.inventory.stored.duplicate()
	move_to(at+FAR if streamed else at+SIDE*4.25)
	for i in 18: await physics_frame
	if streamed: checks[prefix+"unloads partially worked face"]=not world.lifecycle.loaded.has(id)
	reload_scene()
	checks[prefix+"partial ledger restored"]=world.lifecycle.partial.get(id)==1 and not world.persist_blocked
	move_to(at+SIDE*4.25)
	for i in 15: await physics_frame
	var face=working_face(id)
	checks[prefix+"one strike restored on real face"]=face!=null and face.strikes==1
	approach(at)
	var next:int=await strike_until(id,kind,at,2)
	checks[prefix+"second contact leaves the yield in the bank"]=next==1 and nearby_drops(kind,at)==old_drops and working_face(id)._mesh.is_visible_in_tree()
	var remaining:int=next+await strike_until(id,kind,at,3)
	checks[prefix+"two remaining pick contacts"]=remaining==2
	if remaining!=2: return
	var drops:=nearby_drops(kind,at)
	checks[prefix+"final contact releases four sections and clears intact source"]=working_face(id).fracture.shards.size()==4 and not working_face(id)._mesh.visible
	var once:=observe_events("deplete_"+kind,at)==1
	var duration:=float(world.lifecycle.cooling.get(id,-1.))
	checks[prefix+"one typed three-unit yield"]=drops.size()==3 and once
	var unavailable:=true
	var obstructed:=false
	var regrowing:=false
	var early:=false
	var missing:=false
	var loaded_back:=false
	var save_matched:=false
	var tick_back:=-1
	var prior_tick:=-1.
	move_to(at+SIDE*4.25)
	for age in range(1,303):
		await physics_frame
		face=working_face(id)
		var available:bool=world.is_source_available(id)
		if available:
			tick_back=age
			early=age<300
			break
		if face:
			unavailable=unavailable and not face.can_address(at+SIDE*2.5,-SIDE)
			obstructed=obstructed or face.bank_body.collision_layer!=0
			if age>273 and face._mesh.is_visible_in_tree() and face._mesh.scale.y>.01 and face._mesh.scale.y<.999: regrowing=true
		if streamed and age==24: move_to(at+FAR)
		if streamed and age==48: missing=not world.lifecycle.loaded.has(id)
		if age==92:
			prior_tick=float(world.lifecycle.cooling[id])
			reload_scene()
			save_matched=is_equal_approx(float(world.lifecycle.cooling.get(id,-1.)),prior_tick)
		if age==110: move_to(at+SIDE*4.25)
		if age==150: loaded_back=working_face(id)!=null
	checks[prefix+"five playable seconds incl reload"]=absf(duration-5.)<.02 and tick_back==300 and not early and save_matched
	checks[prefix+"unhittable with collision off until availability"]=unavailable and not obstructed
	checks[prefix+"visible growing bank before reopening"]=regrowing
	checks[prefix+"one return with original drops"]=observe_events("regrow_"+kind,at)==1 and nearby_drops(kind,at)==drops
	if streamed: checks[prefix+"cooldown continues across real streaming"]=missing and loaded_back
	var restored=working_face(id)
	checks[prefix+"restored full collider"]=restored!=null and restored.phase=="seated" and restored.strikes==0 and restored.bank_body.collision_layer!=0
	if tick_back==300:
		approach(at)
		var second:int=await strike_until(id,kind,at,3)
		var extra:=nearby_drops(kind,at)
		checks[prefix+"second fresh three-hit three-unit harvest"]=second==3 and extra.size()==6 and drops.all(func(s): return extra.has(s)) and observe_events("deplete_"+kind,at)==1
		var start_amount:int=world.inventory.carried[kind]
		move_to(at)
		for i in 140: await physics_frame
		checks[prefix+"both yields enter typed inventory only once"]=world.inventory.carried[kind]==start_amount+6 and extra.all(func(key):return world.inventory.collected.get(key)==kind) and nearby_drops(kind,at).is_empty()
	checks[prefix+"stored balance unchanged"]=world.inventory.stored==stock
	evidence[id]={"kind":kind,"at":str(at),"natural_contacts":[hit_one,remaining],"first_yield_ids":drops,"initial_seconds":duration,"saved_remaining":prior_tick,"available_at_tick":tick_back,"return_mesh_visible":regrowing,"streamed_away":missing,"restored_before_available":loaded_back}

func remote_faces() -> Dictionary:
	var found:={}
	# Prefer the three deposits on the independent filming route. The census
	# below still finds each kind if world generation changes later.
	for cell in [Vector2i(4,-1),Vector2i(6,0),Vector2i(7,-1)]:
		for r in world.world_landscape.describe_chunk(cell):
			if r.kind not in MineKinds or r.kind=="stone": continue
			if r.id.ends_with("/0"): found[r.kind]=r
	for z in range(-7,8):
		for x in range(-7,8):
			var rows:Array=world.world_landscape.describe_chunk(Vector2i(x,z))
			for r in rows:
				if r.kind not in MineKinds or found.has(r.kind):continue
				var where:Vector3=r.position+SIDE*2.50
				if rows.any(func(o):return o.id!=r.id and where.distance_to(o.position)<3.4):continue
				found[r.kind]=r
			if found.size()==MineKinds.size():return found
	return found

func legacy_save(remote_id: String) -> void:
	var state:Dictionary=world.lifecycle.snapshot()
	state.cooling={"starter-stone":29.,remote_id:31.0}
	state.partial={}
	world.inventory.world_state=state
	checks["writes legacy mine timers to disposable save"]=world.field_save.commit(world.inventory)==OK
	reopen_from_disk()
	checks["legacy starter and unloaded quarry restored at five seconds"]=world.lifecycle.cooling.get("starter-stone")==5.0 and world.lifecycle.cooling.get(remote_id)==5.0 and not world.is_source_available("starter-stone")
	state.cooling={"starter-stone":.375,remote_id:2.7}
	world.inventory.world_state=state
	checks["writes short timers to disposable save"]=world.field_save.commit(world.inventory)==OK
	reopen_from_disk()
	checks["short saved timers retained"]=is_equal_approx(float(world.lifecycle.cooling.get("starter-stone",-1.)),.375) and is_equal_approx(float(world.lifecycle.cooling.get(remote_id,-1.)),2.7)

func run() -> void:
	open_scene()
	for i in 8: await physics_frame
	checks["stone and all three distant minerals catalogued"]=["stone","metal","coal","slate"].all(func(kind): return kind in MineKinds)
	var remote:=remote_faces()
	for kind in MineKinds: checks[kind+" registered in real streamed districts"]=remote.has(kind)
	await examine({"id":"starter-stone","kind":"stone","position":world.resource_rock.position},false)
	for kind in MineKinds:
		if remote.has(kind): await examine(remote[kind],true)
	if remote.has("stone"): legacy_save(remote.stone.id)
	print(JSON.stringify({"physics_hz":Engine.physics_ticks_per_second,"checks":checks,"evidence":evidence}))
	world.set_physics_process(false)
	await Isolated.drain_field_audio(self,world)
	world.queue_free()
	await process_frame
	quit(1 if false in checks.values() else 0)
