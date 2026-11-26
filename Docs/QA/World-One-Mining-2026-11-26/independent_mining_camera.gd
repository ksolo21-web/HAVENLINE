extends SceneTree
## The fixture stages the starting viewpoint. All contacts, yields, regrowth and world proxies use the live scene clock.
const SIDE := Vector3(.7071068,0,-.7071068)
const HEAD = preload("res://orbit_head_contacts.gd")
var scene
var out := OS.get_environment("MINE_CRITIC_OUTPUT")
var kind := OS.get_environment("MINE_CRITIC_KIND")
var samples := {}
var checks := {}
var at := Vector3.ZERO
var ident := ""
var projected := {}
var sweeps := []
var elapsed := 0

func _initialize() -> void:
	call_deferred("run")

func wait_tick() -> void:
	await physics_frame
	elapsed += 1

func stand(p:Vector3) -> void:
	scene.actor.position = p
	scene.actor.velocity = Vector3.ZERO
	scene.camera.position = p + Vector3(7,11,11)
	scene.actor.rotation.y = atan2(-SIDE.x,-SIDE.z)+PI*.67

func snap(label:String, face, age:int) -> void:
	var pos:Vector2 = scene.camera.unproject_position(at+Vector3.UP*.57)
	RenderingServer.force_draw()
	var im := root.get_texture().get_image()
	var px := Vector2(im.get_size()) / root.get_visible_rect().size
	var center := Vector2i(pos * px)
	var entry := {"physics":elapsed,"since_depleted_ticks":age,"screen_bank_center":[center.x,center.y],"size":[im.get_width(),im.get_height()],"camera":str(scene.camera.get_path()),"scale_3d":root.scaling_3d_scale,"bank_available":scene.is_source_available(ident),"tool":scene.character_kit.equipped}
	if is_instance_valid(face):
		entry.merge({"strikes":face.strikes,"visible":face._mesh.is_visible_in_tree(),"mesh_scale":face._mesh.scale.y,"collision":face.bank_body.collision_layer})
	samples[label]=entry
	im.save_jpg(out.path_join(kind+"-"+label+".jpg"),.95)

func event_count(name:String) -> int:
	var n:=0
	for e: Dictionary in scene.events:
		if e.event==name and Vector2(e.x,e.z).distance_to(Vector2(at.x,at.z))<.04: n+=1
	return n

func typed_loot() -> Array:
	var arr:=[]
	for key in scene.drops:
		var d:Dictionary=scene.drops[key]
		if Vector3(d.at).distance_to(at)<1.76: arr.append([key,d.kind])
	return arr

func mineral_tokens() -> Array:
	var tokens:=[]
	for token in scene.drops:
		if scene.drops[token].kind==kind:tokens.append(token)
	for token in scene.inventory.collected:
		if scene.inventory.collected[token]==kind:tokens.append(token)
	tokens.sort()
	return tokens

func mesh_intersection(face, prior:Transform3D) -> Dictionary:
	var geom:TriangleMesh=scene.surfaces[face][1]
	var kit=scene.character_kit
	for slot in kit.slots.slice(0,kit.count):
		var prev:Transform3D=prior.affine_inverse()*slot.before
		var next:Transform3D=prior.affine_inverse()*slot.after
		for v:Vector3 in HEAD.PICKAXE:
			var hit:Dictionary=geom.intersect_segment(prev*v,next*v)
			if not hit.is_empty():
				var pos:Vector3=prior*hit.position
				return {"tool":kit.equipped,"turn":kit.turn_id,"physics_tick":elapsed,"hit_world":[pos.x,pos.y,pos.z]}
	return {}

func far_row() -> Dictionary:
	var land=scene.world_landscape
	var key:Vector2i=land.chunk_for(at)
	var chunk:Dictionary=land.chunks.get(key,{})
	for row:Dictionary in chunk.get("sources",[]):
		if row.id==ident:return row
	return {}

func proxy_transform(row:Dictionary) -> Transform3D:
	var land=scene.world_landscape
	var chunk:Dictionary=land.chunks[land.chunk_for(at)]
	var batch:Dictionary=chunk.batches[row.variant][0]
	var mesh:MultiMesh=batch.mesh
	return chunk.node.global_transform*mesh.get_instance_transform(row.index)

func main() -> void:
	for j in 10: await wait_tick()
	if kind=="stone":
		ident="starter-stone"; at=scene.resource_rock.position
	else:
		var key:Vector2i={"metal":Vector2i(4,-1),"slate":Vector2i(6,0),"coal":Vector2i(7,-1)}[kind]
		for row:Dictionary in scene.world_landscape.describe_chunk(key):
			if row.kind==kind and String(row.id).ends_with("/0"):
				at=row.position; ident=row.id; break
	checks["existing authored bank"]=not ident.is_empty()
	if ident.is_empty():return
	stand(at+SIDE*3.60)
	for i in 27:await wait_tick()
	var face=scene.lifecycle.loaded.get(ident)
	checks["real loaded surface"]=is_instance_valid(face) and scene.surfaces.has(face)
	if not checks["real loaded surface"]:return
	snap("before",face,-1)
	checks["unworked surface captured before approach"]=face.strikes==0
	stand(at+SIDE*2.5)
	var distinct_drops:=[]
	var depleted:=-1
	var returned:=-1
	var previous_hits:=0
	var dim:=false
	var early:=false
	var colliding:=false
	var bad_return:=false
	var hit_during_return:=false
	var terminal_tokens:=[]
	for i in 1100:
		var prior:Transform3D=face._mesh.global_transform
		await wait_tick()
		var n:=event_count("impact_"+kind)
		if n>previous_hits:
			var hit:=mesh_intersection(face,prior)
			sweeps.append(hit)
			if n==1:snap("strike",face,-1)
			if depleted>=0 and returned<0 and not scene.is_source_available(ident):hit_during_return=true
			previous_hits=n
		if depleted<0 and event_count("deplete_"+kind)>0:
			depleted=elapsed
			terminal_tokens=mineral_tokens()
			distinct_drops=typed_loot()
			snap("spent",face,0)
		if depleted>=0:
			var age:=elapsed-depleted
			var available:bool=scene.is_source_available(ident)
			if not available:
				if face.bank_body.collision_layer!=0:colliding=true
				if age<272 and face._mesh.is_visible_in_tree():dim=true
				if age==287:snap("returning",face,age)
			elif returned<0:
				returned=elapsed
				early=age<300
				bad_return=not face._mesh.is_visible_in_tree() or face.bank_body.collision_layer!=1
				snap("restored",face,age)
		if returned>=0 and n>=4:break
	checks["three actual mesh swept pick contacts before depletion"]=sweeps.size()>=3 and sweeps.slice(0,3).all(func(r): return not r.is_empty() and r.tool=="pickaxe")
	checks["three distinct typed drops at terminal contact"]=distinct_drops.size()==3 and distinct_drops.all(func(d):return d[1]==kind)
	checks["unavailable and noncolliding through entire five seconds"]=returned-depleted==300 and not early and not colliding and not hit_during_return
	checks["subsurface until reveal, then full colliding visible bank"]=not dim and not bad_return and samples.has("returning") and samples.returning.visible
	checks["next real pick is accepted after return"]=sweeps.size()>=4 and not sweeps[3].is_empty() and sweeps[3].tool=="pickaxe"
	checks["typed token IDs conserved until fresh mining resumes"]=mineral_tokens()==terminal_tokens
	if kind!="stone" and checks["next real pick is accepted after return"]:
		for i in 260:
			await wait_tick()
			if event_count("deplete_"+kind)>=2:break
		var second_event:=event_count("deplete_"+kind)==2
		stand(at+SIDE*9.5)
		for j in 22:await wait_tick()
		var row:=far_row()
		var suppressed:bool=not row.is_empty() and not row.proxy_visible and not is_instance_valid(row.live)
		var hidden_pose:=Transform3D.IDENTITY
		if suppressed:
			hidden_pose=proxy_transform(row)
			snap("far-empty",null,-1)
		for j in 330:
			await wait_tick()
			if not far_row().is_empty() and far_row().proxy_visible:break
		row=far_row()
		var proxy_shown:bool=not row.is_empty() and row.proxy_visible and not is_instance_valid(row.live)
		if proxy_shown:
			var visible_pose:=proxy_transform(row)
			checks["actual MultiMesh is buried during cooldown and rises to its bank position"]=hidden_pose.origin.y<at.y-8 and absf(visible_pose.origin.y-at.y)<2 and hidden_pose.basis.get_scale().length()<visible_pose.basis.get_scale().length()*.01
			snap("far-proxy",null,-1)
		checks["depleted remote deposit disappears and comes back as far proxy"]=second_event and suppressed and proxy_shown
	projected={"source_id":ident,"source_center":[at.x,at.y,at.z],"drop_ids_and_kinds":distinct_drops,"elapsed_between_deplete_and_return_ticks":returned-depleted}

func run() -> void:
	if out.is_empty() or not preload("res://opening_save.gd").new().configure(OS.get_cmdline_user_args()):quit(2);return
	scene=load("res://field_opening.tscn").instantiate()
	root.add_child(scene)
	await main()
	var summary={"kind":kind,"tests":checks,"source":projected,"observed_pick_intersections":sweeps,"stills":samples,"ticks_per_second":Engine.physics_ticks_per_second,"stage_warp":"Fixture placed actor at genuine seeded coordinates; actual input systems and normal camera remained active."}
	var f:=FileAccess.open(out.path_join(kind+".json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(summary,"  ")+"\n");f.close()
	print(kind," ",JSON.stringify(checks))
	scene.set_physics_process(false)
	scene.sound.stop_playback()
	var release_at:=Time.get_ticks_msec()+280
	while Time.get_ticks_msec()<release_at:await process_frame
	scene.queue_free()
	for j in 6:await process_frame
	quit(1 if false in checks.values() else 0)
