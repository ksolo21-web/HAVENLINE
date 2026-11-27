extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")
var game
var kit
var env
var failures:Array[String]=[]
var rows:Array[Dictionary]=[]
var geometry_samples:=0
var media:=OS.get_environment("HL_ORBIT_MEDIA")

func _initialize()->void:
	var guard := preload("res://opening_save.gd").new()
	if guard.configure(OS.get_cmdline_user_args()): call_deferred("run")
	elif not Session.isolated(self,"res://tests/qa_fence_orbit.gd"):call_deferred("run")

func ensure(value:bool,label:String)->void:
	if not value and not failures.has(label): failures.append(label)

func target(at:Vector3,height:float)->MeshInstance3D:
	# Test the shipped mining-surface triangles at a measured location.
	var donor:MeshInstance3D=game.surfaces[game.resource_rock][0]
	var part:=MeshInstance3D.new()
	part.mesh=donor.mesh
	game.add_child(part)
	part.scale=Vector3.ONE*.16
	part.global_position=at+Vector3.UP*height-part.global_basis*part.get_aabb().get_center()
	part.hide()
	return part

func run_turn(label:String,feet:Vector3,blocked:Vector3,clear:Vector3,should_block:bool,tool:String)->void:
	var at:=feet
	game.actor.global_position=feet
	game.previous_dry_position=feet
	game.camera.position=feet+game.camera_follow_offset
	kit.begin(tool)
	kit.height=kit.desired_height()
	kit.pose(at)
	for s in kit.slots:s.before=s.after
	var target_a:=target(blocked,kit.height)
	var target_b:=target(clear,kit.height)
	var mesh:TriangleMesh=target_a.mesh.generate_triangle_mesh()
	var hidden_hits:=0
	var exposed_hits:=0
	var samples:=0
	var maximum:=0.
	var close_path:=0
	var period_begin:int=kit.turn_id
	for frame in 54:
		kit.advance(1./60.,at)
		var pose_at:Transform3D=kit.slots[0].after
		var bounds:AABB=kit.model_boxes[tool]
		# Every vertex is enclosed by the authored, transformed AABB. A convex
		# swept fence test from the actor to its eight corners certifies the box.
		for i in 8:
			var p:Vector3=pose_at*bounds.get_endpoint(i)
			if not env.travel_clear(feet,p,0.):close_path+=1
			maximum=maxf(maximum,Vector2(feet.x-p.x,feet.z-p.z).length())
			samples+=1
		if kit.crosses_surface(target_a,mesh):hidden_hits+=1
		if kit.crosses_surface(target_b,mesh):exposed_hits+=1
		kit.finish_turn()
		if not media.is_empty() and frame%4==0:
			await process_frame
			RenderingServer.force_draw(false)
			root.get_texture().get_image().save_jpg(media.path_join("%s-%s-%02d.jpg"%[label,tool,frame]),.87)
	ensure(close_path==0,label+" "+tool+" visible model entered the wood")
	ensure(hidden_hits==0 if should_block else hidden_hits>0,label+" "+tool+" damage on far target")
	ensure(exposed_hits>0,label+" "+tool+" lost reachable target")
	ensure(kit.turn_id==period_begin+1,label+" "+tool+" rotation timing changed")
	geometry_samples+=samples
	rows.append({"site":label,"tool":tool,"physical_mesh_box_corner_sweeps":samples,"blocked_mesh_corner_sweeps":close_path,"far_target_contact_frames":hidden_hits,"near_target_contact_frames":exposed_hits,"maximum_box_corner_radius":maximum})
	target_a.queue_free()
	target_b.queue_free()

func run()->void:
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	for i in 5:await physics_frame
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	for i in game.inventory.costs.center_hearth.wood:
		game.inventory.collect("orbit-fence-"+str(i),"wood")
		game.inventory.payment("center_hearth","wood",false)
	game._finish_purchase("center_hearth")
	game._apply_hearth(true,false)
	kit=game.character_kit
	env=game.field_env
	var gate=game.gates[1]
	var p:Vector3=gate.global_position
	var approach:=p+Vector3.RIGHT*.62
	var empty:Array[Vector4]=[]
	var far:=Vector3(38,0,41)
	for i in 120:gate.advance_automatic(1./60.,far,.31,Vector3.INF,empty)
	for tool in ["axe","pickaxe"]:
		await run_turn("wall",p+Vector3(.57,0.,2.48),p+Vector3(-.60,0.,2.48),p+Vector3(1.82,0.,2.63),true,tool)
		await run_turn("closed-east",approach,p-Vector3.RIGHT*.59,p+Vector3(1.68,0,.16),true,tool)
	for i in 100:gate.advance_automatic(1./60.,p+Vector3.RIGHT*2.,.31,Vector3.INF,empty)
	for tool in ["axe","pickaxe"]:
		await run_turn("open-east",approach,p-Vector3.RIGHT*.59,p+Vector3(1.68,0,.16),false,tool)
	var snow:=Vector3(27,0,26)
	for tool in ["axe","pickaxe"]:
		await run_turn("snow",snow,snow+Vector3.LEFT*.82,snow+Vector3.BACK*1.9,false,tool)
	print("FENCE_ORBIT ",JSON.stringify({"failures":failures,"cases":rows,"mesh_sweeps":geometry_samples}))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 4:await process_frame
	quit(0 if failures.is_empty() else 1)
