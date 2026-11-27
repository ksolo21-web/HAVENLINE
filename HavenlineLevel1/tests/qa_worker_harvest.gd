extends "res://tests/qa_worker_jobs.gd"
## The real worker works unassisted in the published opening snowfield.
const HERE := "res://tests/qa_worker_harvest.gd"
const WorkSwing := preload("res://forester_work_swing.gd")
const ApprovedTools := preload("res://weapon_orbit.gd")
const SAMPLE_PHASES := [.03,.16,.26,.35,.46,.55,.62,.70,.79,.89,.98]
var view_path := OS.get_environment("HAVENLINE_HARVEST_VIEW")
var motion: Dictionary = {}
var camera_pairs: Array[String] = []

func run() -> void:
	if not Save.Profile.new().configure(OS.get_cmdline_user_args()):
		var path := Session.make_directory()
		var status := Session.child(HERE,path,"--worker-harvest")
		Session.remove_owned(path)
		quit(status)
		return
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	for i in 4: await process_frame
	game.set_physics_process(false)
	game.set_process(false)
	worker=game.survivor
	setup_camp()
	var tools := {"axe":worker.actor.tool.scene_file_path,"pickaxe":worker.actor.mining_tool.scene_file_path}
	check(tools.axe==ApprovedTools.AXE.resource_path and tools.pickaxe==ApprovedTools.PICK.resource_path,"hired survivor holds the same approved Meshy meshes as the player")
	game.actor.position=Vector3(-3.1,0,-3.9)
	var player: Vector3 = game.actor.global_position
	var known_wood := {}
	var known_stone := {}
	var wood_deposited := 0
	var stone_deposited := 0
	var actual_chops := 0
	var actual_mines := 0
	var first_chop := -1
	var first_mine := -1
	var finished_at := -1
	var receipt_trace: Array[Dictionary] = []
	var cursor: int = game.events.size()
	var wood_last := ""
	var bank_last := ""
	var previous_phase := ""
	for frame in 60*300:
		tick(1./60.)
		if not view_path.is_empty() and frame%2==0: await process_frame
		if worker.phase!=previous_phase:
			if worker.phase in ["to_tree","mining_approach","bulk_return","bin_delivery"]:
				var site: Node3D=worker.tree if worker.phase=="to_tree" else (worker.assigned_bank if worker.phase=="mining_approach" else null)
				var name_: String = site.get_meta("field_source_id","") if is_instance_valid(site) else ""
				receipt_trace.append({"tick":frame,"phase":worker.phase,"site":name_,"worker":str(worker.actor.global_position),"load":game.inventory.settlement.worker_load.duplicate()})
			previous_phase=worker.phase
		if worker.phase in ["chopping","mining"]:
			var mining: bool=worker.phase=="mining"
			var site: Node3D=worker.assigned_bank if mining else worker.tree
			if is_instance_valid(site):
				var name_: String=site.get_meta("field_source_id","")
				if mining: bank_last=name_
				else: wood_last=name_
				await _inspect_motion("Mine" if mining else "Chop",site,float(worker.bank_swing if mining else worker.swing_time)/worker.Human.CHOP_SECONDS,mining)
		for i in range(cursor,game.events.size()):
			var event: Dictionary=game.events[i]
			match event.event:
				"survivor_chop_contact":
					known_wood[wood_last]=int(known_wood.get(wood_last,0))+1
					actual_chops+=1
					if first_chop<0:
						first_chop=frame
						await _views("Chop-contact",worker.actor.global_position.lerp(worker.tree.global_position,.43))
				"survivor_mine_contact":
					known_stone[bank_last]=int(known_stone.get(bank_last,0))+1
					actual_mines+=1
					if first_mine<0:
						first_mine=frame
						await _views("Mine-contact",worker.actor.global_position.lerp(worker.assigned_bank.global_position,.47))
				"deposit_wood": wood_deposited+=1
				"deposit_stone": stone_deposited+=1
		cursor=game.events.size()
		if worker.phase=="bin_delivery" and not worker.delivery_stream.is_empty() and game.inventory.settlement.worker_load.stone>0:
			await _views("Stone-stock",worker.actor.global_position)
		if known_wood.size()>=2 and actual_chops>=6 and actual_mines>=6 and wood_deposited>=4 and stone_deposited>=4:
			finished_at=frame
			break
		if game.persist_blocked: break
	check(known_wood.size()>=2 and actual_chops>=6,"real axe edge contacts on at least two different trees")
	check(actual_mines>=6,"real pick head contacts repeat across at least two stone-bank cycles")
	check(wood_deposited>=4 and stone_deposited>=4,"autonomous worker delivered recurring timber and stone to the warehouse")
	check(game.actor.global_position.is_equal_approx(player) and game.inventory.carried.stone==0 and game.inventory.carried.wood==0,"parked player supplied neither tool contact nor wallet receipts")
	check(worker.can_defend() and not game.persist_blocked,"worker stays live and transfers are valid")
	var restored=game.Inventory.new()
	check(restored.configure(game.inventory.configured_costs) and restored.restore(game.inventory.snapshot()),"a cold ledger conserves the repeated work")
	print("WORKER_HARVEST ",JSON.stringify({"checks":checks,"failures":errors,"tools":tools,"first_chop":first_chop,"first_mine":first_mine,"last_frame":finished_at,"wood_contacts":known_wood,"stone_contacts":known_stone,"wood_deposits":wood_deposited,"stone_deposits":stone_deposited,"work_motion":motion,"viewport":str(root.size),"cameras":camera_pairs,"trace":receipt_trace}))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 4: await process_frame
	quit(int(not errors.is_empty()))

func _inspect_motion(name_: String, site: Node3D, phase: float, mining: bool) -> void:
	if not motion.has(name_): motion[name_]=[]
	var recording_phase: Array=motion[name_]
	if recording_phase.size()>=SAMPLE_PHASES.size() or phase<SAMPLE_PHASES[recording_phase.size()]: return
	var tool: Node3D=worker.actor.mining_tool if mining else worker.actor.tool
	var grips: Array=WorkSwing.PICK_GRIPS if mining else WorkSwing.AXE_GRIPS
	var rig: Skeleton3D=worker.actor.skeleton
	var grip_distance := 0.0
	for side_index in 2:
		var name_bone := "Palm.L" if side_index==0 else "Palm.R"
		var hand := rig.to_global(rig.get_bone_global_pose(rig.find_bone(name_bone)).origin)
		grip_distance=maxf(grip_distance,hand.distance_to(tool.to_global(grips[side_index])))
	var boots: PackedVector3Array=worker.actor.forester_gait.tread.points()
	var low := INF
	for boot: Vector3 in boots: low=minf(low,boot.y)
	var tip: Vector3=tool.to_global(WorkSwing.PICK_TIP if mining else WorkSwing.AXE_EDGE)
	recording_phase.append({"phase":phase,"grip_error_m":grip_distance,"lowest_sole_m":low,"tool_position":str(tool.global_position),"tip":str(worker.actor.to_local(tip)),"aim":str(worker.actor.to_local(worker.actor.work_strike_point)),"tip_error_m":tip.distance_to(worker.actor.work_strike_point)})
	if not view_path.is_empty():
		await _views("%s-phase-%02d" % [name_,recording_phase.size()],worker.actor.global_position.lerp(site.global_position,.43),[2.0])

func _views(label: String, anchor: Vector3, zoom_ratios := [1.0,2.0]) -> void:
	if view_path.is_empty() or label in camera_pairs:return
	camera_pairs.append(label)
	var camera: Camera3D = game.camera
	var original := camera.global_position
	camera.global_position=anchor+game.camera_follow_offset
	for ratio: float in zoom_ratios:
		game.set_zoom_ratio(ratio)
		await process_frame
		RenderingServer.force_draw(false)
		root.get_texture().get_image().save_jpg(view_path.path_join("%s-%dx.jpg" % [label,int(ratio)]),.93)
	game.set_zoom_ratio(1.0)
	camera.global_position=original
