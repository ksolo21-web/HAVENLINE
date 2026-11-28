extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")
var world
var failures: Array[String] = []
var rows: Array[Dictionary] = []

func _initialize() -> void:
	var guard := preload("res://opening_save.gd").new()
	if guard.configure(OS.get_cmdline_user_args()): call_deferred("run")
	elif not Session.isolated(self,"res://tests/qa_forest_perimeter_safety.gd"): call_deferred("run")

func expect(ok:bool, message:String) -> void:
	if not ok: failures.append(message)

func row_clear(pos:Vector3, radius:float, rect:Vector4) -> bool:
	var p := Vector2(pos.x,pos.z)
	return p.distance_to(p.clamp(Vector2(rect.x,rect.y),Vector2(rect.z,rect.w))) > radius+.15

func purchase(id:String)->void:
	for k:String in world.inventory.remaining(id):
		var qty:int=world.inventory.remaining(id)[k]
		for i in qty: world.inventory.collect("forest-boundary-"+id+k+str(i),k)
		world.inventory.payment(id,k,false,qty)
	world._finish_purchase(id)

func test_stage(stage:int) -> void:
	var r:Vector4 = world.field_env.COURTS[stage-1]
	var visible_count:=0
	var visible_live:=0
	var min_clear:=INF
	for row:Dictionary in world.forest.records:
		if row.get("occupied",false):
			expect(not row.proxy_visible and not is_instance_valid(row.live),"purchased forest row resurfaced "+row.id)
			continue
		var size:Vector2 = world.field_env.pine_shapes[row.variant]
		var tr:Transform3D = row.transform
		var p:=Vector2(tr.origin.x,tr.origin.z)
		var crown:=tr.basis.get_scale().x*size.x
		expect(row_clear(tr.origin,crown,r),"visible crown crosses paid fence "+row.id)
		var clear:=p.distance_to(p.clamp(Vector2(r.x,r.y),Vector2(r.z,r.w)))-crown-.15
		min_clear=minf(min_clear,clear)
		visible_count+=1
		if is_instance_valid(row.live): visible_live+=1
	var measured:=0
	for stem:Node3D in world.trees:
		if stem.is_queued_for_deletion(): continue
		var crown:float = stem.crown_size.x*stem.TREE_SCALE*stem.scale.x
		expect(crown>.40 and row_clear(stem.position,crown,r),"active harvest crown clips camp "+str(stem.position))
		measured+=1
	var g=world.gates[1]
	var far:=Vector3(46,0,43)
	var e:Array[Vector4]=[]
	for i in 120:g.advance_automatic(1./60.,far,.31,Vector3.INF,e)
	var west:=Vector3(r.x,0,(r.y+r.w)*.5)
	var outside:=west-Vector3.RIGHT*.40
	var inside:=west+Vector3.RIGHT*.40
	expect(not world.field_env.travel_clear(outside,inside,.06),"west across-wall interaction")
	expect(not world.field_env.travel_clear(Vector3(r.x-15.,0.,r.y+2.),Vector3(r.z+15.,0.,r.y+2.),.21),"long timestep tunnel")
	expect(not world.field_env.travel_clear(g.to_global(Vector3(0,0,1.6)),g.to_global(Vector3(0,0,-1.6)),.31),"closed east gate tunnel")
	var k:="boundary-same-"+str(stage)
	world._place_drop(k,"wood",outside,inside,0.,0.)
	var landed:Vector3=world.drops[k].at
	expect(landed.x<=r.x-.27,"scatter escaped into camp")
	world.actor.position=inside
	for i in 28: world._step_drops(1./60.)
	expect(world.drops.has(k) and not world.inventory.collected.has(k),"opposite-side collection through fence")
	world.actor.position=west-Vector3.RIGHT*.86
	world.actor.rotation.y=PI*.5
	world._step_drops(.02)
	expect(not world.drops.has(k),"unobstructed same-side collection lost")
	for i in 100:g.advance_automatic(1./60.,g.to_global(Vector3(0,0,2.)),.31,Vector3.INF,e)
	expect(world.field_env.travel_clear(g.to_global(Vector3(0,0,1.6)),g.to_global(Vector3(0,0,-1.6)),.31),"fully open east gate wrongly blocked")
	expect(not world.field_env.travel_clear(g.to_global(Vector3(-1.19,0,-.5)),g.to_global(Vector3(1.19,0,-.5)),.13),"open leaf body ignored")
	rows.append({"stage":stage,"visible_batch_or_harvest":visible_count,"of_which_live":visible_live,"independent_stems":measured,"smallest_crown_clearance_m":min_clear,"drop_outside_wall_m":r.x-landed.x})

func test_unreserved_cooling_pine() -> void:
	# This authored bank crosses the queue footprint when the north counter
	# moves left. Moving the counter back must not resume the tree early.
	var id := "grove@-3000,-18550"
	var target: Dictionary
	for row: Dictionary in world.forest.records:
		if row.id == id:
			target = row
			break
	expect(not target.is_empty() and not target.get("occupied",false),"north queue fixture starts with a free pine")
	if target.is_empty(): return
	if not is_instance_valid(target.live): world.forest._open_pine(target)
	world.lifecycle.deplete(target.live)
	var original: Vector2 = world.camp_layout.center("north_counter")
	var alternate := Vector2(-4.5,original.y)
	expect(world.camp_layout.relocate("north_counter",alternate) and target.occupied,"legal counter move reserves the depleted pine")
	expect(world.camp_layout.relocate("north_counter",original) and not target.occupied,"legal return frees the depleted pine site")
	expect(not target.proxy_visible and not world.is_source_available(id),"freed site must not display a standing tree during cooldown")
	world.lifecycle.advance(4.99)
	world.forest.advance(.20)
	expect(not target.proxy_visible and not world.is_source_available(id),"freed site still respects the five-second timer")
	world.lifecycle.advance(.02)
	world.forest.advance(.20)
	expect(target.proxy_visible and world.is_source_available(id),"same distant pine reappears after five seconds")

func run()->void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	for i in 6:await physics_frame
	if not world.field_ready or world.persist_blocked or world.forest.records.is_empty():quit(2);return
	for size:Vector2 in world.field_env.pine_shapes: expect(size.x>1. and size.y>2.,"mesh bounds missing")
	world.actor.position=Vector3(-2.2,0,4.85)
	for stage in [1,2,3]:
		if stage==1: purchase("center_hearth");world._apply_hearth(true,false)
		if stage==2: purchase("expansion_1")
		if stage==3:
			for offer in ["storage_wood","storage_stone","storage_meat","expansion_2"]:purchase(offer)
		for i in 8:await physics_frame
		test_stage(stage)
	var tree:Node3D=world.resource_tree
	var p:=tree.global_position
	var wallward:=Vector3.FORWARD
	for i in 3:
		tree.cooldown=0.
		expect(tree.strike(tree.TREE_ID,tree.last_sequence+1,p-wallward,wallward,wallward,Vector3.INF,true),"real trunk did not accept contact")
	var crown:float=tree.crown_size.x*tree.TREE_SCALE
	var height:float=tree.crown_size.y*tree.TREE_SCALE
	var r:Vector4=world.field_env.COURTS[2]
	for i in 19:
		var u:=i/18.
		expect(row_clear(p+tree.fall_direction*height*u,crown,r),"fallen crown passes through fence")
	expect(world.field_env.travel_clear(p,p+tree.fall_direction*height,crown),"standing pine falls through fence")
	var tree_id:String=tree.get_meta("field_source_id")
	world.lifecycle.deplete(tree)
	world.lifecycle.advance(4.99)
	expect(tree.phase=="credited" and not world.is_source_available(tree_id),"wood regrew early")
	world.lifecycle.advance(.02)
	expect(tree.phase=="rooted" and world.is_source_available(tree_id) and row_clear(tree.position,crown,r),"regrowth crossed perimeter")
	test_unreserved_cooling_pine()
	var receipt={"scene":"res://field_opening.tscn","stages":rows,"failures":failures}
	print("FOREST_PERIMETER ",JSON.stringify(receipt))
	world.set_physics_process(false)
	await Session.drain_field_audio(self,world)
	world.queue_free()
	for i in 4:await process_frame
	quit(0 if failures.is_empty() else 1)
