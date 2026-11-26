extends SceneTree
const Stage = preload("res://field_opening.tscn")
var world
var counter
var checks := {}
var out := OS.get_environment("SERVICE_OUT")
var images := OS.get_environment("SERVICE_VIEWS") == "1"
func _initialize(): call_deferred("run")
func check(s:String, ok:bool): checks[s]=ok
func fund(id:String):
	for kind:String in world.inventory.remaining(id):
		for i in int(world.inventory.remaining(id)[kind]):
			assert(world.inventory.collect("counter-proof-"+id+kind+str(i),kind))
			assert(world.inventory.payment(id,kind,false))
	world._finish_purchase(id)
func shot(n:String):
	if not images:return
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(out+"/"+n+".jpg",.94)
func run():
	world=Stage.instantiate()
	root.add_child(world)
	for i in 6: await physics_frame
	if world.persist_blocked or not world.field_ready:
		push_error("Native world test requires the actual marked disposable save.")
		quit(3)
		return
	counter=world.counter
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat"]:
		fund(id)
		for i in 2:await physics_frame
	check("counter absent through first expansion",not counter.active)
	fund("expansion_2")
	for i in 12: await physics_frame
	check("paid final expansion docks real counter",counter.active and counter.get_node("AlfredNorthCounter") != null)
	var ahead:Vector3=counter.global_position
	var stops := []
	for offset in [-1.94,-1.825,0.,1.825,1.94]:
		for side in [-1.,1.]:
			var at:=ahead+Vector3(offset,.12,side*2.35)
			var movement:=Vector3(0,0,-side*4.70)
			var result:=KinematicCollision3D.new()
			var hit:bool=world.actor.test_move(Transform3D(Basis.IDENTITY,at),movement,result)
			var stable:bool=hit and result.get_collider() in [counter.guard,world.camp_colliders[4]]
			stops.append({"x":offset,"from":side,"blocked":stable,"body":str(result.get_collider().get_path()) if hit else ""})
	check("capsule blocked at counter, seams and flanks from both sides",stops.all(func(v):return v.blocked))
	check("only two working gate controls",world.gates.size()==2 and world.gates.all(func(g):return g.active))
	world.actor.global_position=counter.service_point.global_position+Vector3(0,0,.35)
	for i in 280: await physics_frame
	shot("counter-camp-gameplay")
	check("both imported visitor models queued outside",counter.queue.size()==3 and counter.front_ready(1) and counter.queue.all(func(e):return e.right != null and e.left != null and not world.field_env.is_inside_camp(e.body.global_position)))
	check("visitor footprints registered",world.tracks.living.has(counter.queue[0].body))
	var working_hand:bool=counter.player_palm != null
	# Ingredient is earned through the normal custody path before the production cooker.
	world.carry.pickup("counter-proof-raw","meat",world.actor.global_position)
	for i in 23:await physics_frame
	world.actor.global_position = world.lakeshore.APRON
	world.actor.global_position.y=0.
	for i in 180:await physics_frame
	var ready:bool=int(world.inventory.settlement.cooked)>int(world.inventory.settlement.served)
	check("normal cooker yields one physically carried serving",ready and working_hand and is_instance_valid(counter.meal))
	world.actor.global_position=counter.service_point.global_position
	world.camera.global_position=world.actor.global_position+Vector3(7,11,11)
	var sampled:=[]
	for i in 115:
		await physics_frame
		if i in [5,20,29,44,66,95]:
			shot("counter-handoff-%03d"%i)
			if counter.sale_committed and is_instance_valid(counter.cash):sampled.append(i)
	check("physical tender animation observed",not sampled.is_empty())
	check("one complete sale through the ordinary loop",world.inventory.settlement.served==1 and world.inventory.settlement.cooked==1 and counter.sale_order==0 and counter.queue[0].order==2)
	var f:=FileAccess.open(out+"/Native-world.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"scene":"res://field_opening.tscn","checks":checks,"capsule_sweeps":stops,"cash_frames":sampled,"snapshots":"Progression purchases and ingredient supplied by the isolated fixture. Cooker and worker-side trade use the ordinary scene physics."},"  ")); f.close()
	print(JSON.stringify(checks))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,world)
	world.queue_free()
	for i in 4:await process_frame
	quit(1 if false in checks.values() else 0)
