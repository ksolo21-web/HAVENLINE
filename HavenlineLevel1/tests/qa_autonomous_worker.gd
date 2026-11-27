extends "res://tests/qa_worker_jobs.gd"
## A bought and rescued forester starts with empty pockets in a hearth-only camp.
## Gathered materials, plot transactions, travel and subsequent stock delivery
## use the field scene's real worker, drops, save, fence and placement systems.
const HERE := "res://tests/qa_autonomous_worker.gd"
var peak_speed := 0.
var laden_peak := 0.
var empty_peak := 0.
var progress := []
var receipts := []
var last_pose := ""
var motion := []

func seed_rescue() -> void:
	var book=game.inventory
	var hearth: String = game.Progress.HEARTH
	for i in book.remaining(hearth).wood:
		book.collect("hearth-grant-%d"%i,"wood")
		book.payment(hearth,"wood",false)
	game._apply_hearth(true,false)
	for i in book.survivor_cost:
		book.collect("rescue-fee-%d"%i,"wood")
	book.carried.wood-=book.survivor_cost
	book.settlement.survivor_wood=book.survivor_cost
	book.settlement.survivor_paid=true
	game.actor.position=worker.RESCUE
	worker.advance(1./60.)
	check(book.settlement.rescued,"normal proximity activates the paid survivor")
	# No goods are supplied to the worker or its stockroom. The held meat is a
	# sentinel proving the player's own pocket is never spent by the employee.
	book.collect("hero-meat-sentinel","meat")
	game.actor.position=Vector3(1.95,0,1.30)
	game.camera.position=game.actor.position+game.camera_follow_offset
	game._inventory_changed()

func watch_step(dt: float, frame: int) -> void:
	var before: Vector3 = worker.actor.position
	var was_loaded: bool = worker._has_cargo()
	tick(dt)
	if worker.phase!=last_pose:
		progress.append({"frame":frame,"phase":worker.phase,"x":worker.actor.position.x,"z":worker.actor.position.z})
		last_pose=worker.phase
	var speed:=before.distance_to(worker.actor.position)/dt
	peak_speed=maxf(speed,peak_speed)
	if was_loaded: laden_peak=maxf(laden_peak,speed)
	else: empty_peak=maxf(empty_peak,speed)
	if speed>=2. and motion.size()<320:
		var rig:Skeleton3D=worker.actor.skeleton
		var knee_angles:=[0.,0.]
		var ankle_pitch:=[0.,0.]
		for i in 2:
			var side:String=["L","R"][i]
			var hip:=rig.get_bone_global_pose(rig.find_bone("Thigh."+side)).origin
			var knee:=rig.get_bone_global_pose(rig.find_bone("Shin."+side)).origin
			var ankle:=rig.get_bone_global_pose(rig.find_bone("Foot."+side))
			knee_angles[i]=snappedf(rad_to_deg((knee-hip).angle_to(ankle.origin-knee)),.01)
			ankle_pitch[i]=snappedf(rad_to_deg(ankle.basis.get_euler().x),.01)
		motion.append([frame,worker.phase,snappedf(speed,.001),snappedf(worker.step_cycle,.001),knee_angles,ankle_pitch])
	for id:String in game.inventory.build_order:
		if id not in receipts: receipts.append(id)

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.is_empty() or not Save.Profile.new().configure(args):
		var private_dir:=Session.make_directory()
		var code:=Session.child(HERE,private_dir,"early")
		Session.remove_owned(private_dir)
		quit(code)
		return
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.set_process(false)
	for i in 3: await process_frame
	worker=game.survivor
	seed_rescue()
	var book=game.inventory
	var start:Dictionary=book.paid.duplicate(true)
	for i in 60*450:
		watch_step(1./60.,i)
		if book.settlement.worker_deliveries > 0 or game.persist_blocked: break
	check(not game.persist_blocked,"every transaction was valid on disk")
	check(book.complete(game.Progress.FIRST) and start[game.Progress.FIRST].wood==0 and start[game.Progress.FIRST].stone==0,"worker gathered and initiated first perimeter expansion from zero owner payment")
	check(book.complete(game.Progress.STORAGE[0]) and start[game.Progress.STORAGE[0]].wood==0,"worker gathered and bought first house with no prior storage or down payment")
	check(book.settlement.worker_deliveries>0,"worker continued working after the house purchase")
	check(book.carried.meat==1 and book.carried.wood==0 and book.carried.stone==0,"worker never spent the player's pocket inventory")
	check(absf(empty_peak-worker.EMPTY_SPEED)<.05 and absf(laden_peak-worker.LADEN_SPEED)<.05 and peak_speed<game.gait_motor.MAX_SPEED,"empty and loaded trips reach their own capped speeds below Character 1")
	var copy=game.Inventory.new()
	check(copy.configure(book.configured_costs) and copy.restore(book.snapshot()),"the earned field, construction and store balances conserve receipts")
	var result={"checks":checks,"errors":errors,"actual_peak_m_s":peak_speed,"loaded_peak_m_s":laden_peak,"empty_peak_m_s":empty_peak,"phases":progress,"motion_samples":motion,"build_order":receipts,"elapsed":timelapsed,"ledger":book.settlement,"paid":book.paid,"stored":book.stored,"worker_feet":str(worker.actor.position),"remaining_waypoints":str(worker.route),"save_error":game.persist_error}
	print("Early worker ",checks.size()," checks, elapsed ",timelapsed,", failures ",errors," phase ",worker.phase," feet ",worker.actor.position)
	if not output.is_empty():
		var f:=FileAccess.open(output.path_join("Early-autonomous-camp.json"),FileAccess.WRITE)
		f.store_string(JSON.stringify(result,"\t")+"\n")
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 3: await process_frame
	quit(0 if errors.is_empty() else 1)
