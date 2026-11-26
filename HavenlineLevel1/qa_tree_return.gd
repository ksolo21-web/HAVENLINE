extends SceneTree
## Actual orbit contacts, three unit felling credit and five seconds on the field clock.
var game
var checks := {}
var evidence := {}
var target := Vector3.ZERO
var output := OS.get_environment("TREE_EVIDENCE")

func _initialize() -> void:
	var guard = preload("res://opening_save.gd").new()
	if not guard.configure(OS.get_cmdline_user_args()):
		if not preload("res://tests/lifecycle_test_profile.gd").isolated(self,"res://qa_tree_return.gd"): call_deferred("run")
	else:
		call_deferred("run")

func still(label: String) -> void:
	if output.is_empty(): return
	RenderingServer.force_draw()
	var frame := root.get_texture().get_image()
	frame.save_jpg(output.path_join(label+".jpg"),.94)
	var logical: Vector2 = game.camera.unproject_position(target+Vector3.UP*.93)
	var px := Vector2(frame.get_size())/root.get_visible_rect().size
	var center := Vector2i(logical*px)
	var area := Rect2i(center-Vector2i(88,82),Vector2i(176,164)).intersection(Rect2i(Vector2i.ZERO,frame.get_size()))
	if area.has_area(): frame.get_region(area).save_jpg(output.path_join(label+"-crop.jpg"),.98)

func events_at(label: String, at: Vector3) -> Array:
	return game.events.filter(func(e): return e.event == label and Vector2(e.x,e.z).distance_to(Vector2(at.x,at.z))<.03)

func harvest(id: String, at: Vector3, stream: bool) -> void:
	target = at
	var stored: Dictionary = game.inventory.stored.duplicate()
	var hits_before := events_at("impact_wood",at).size()
	var drop_before := events_at("deplete_wood",at).size()
	var back_before := events_at("regrow_wood",at).size()
	game.actor.position = at+Vector3(2.18,0,0)
	game.camera.position = game.actor.position+Vector3(7,11,11)
	var swayed := false
	var chips := false
	var fell := false
	var fall_sample := 0.0
	var growing := false
	var early := false
	var streamed := false
	var crossed := false
	var zero_tick := -1
	var return_tick := -1
	var deplete_us := 0
	var return_us := 0
	for tick in 1100:
		await physics_frame
		var tree = game.lifecycle.loaded.get(id)
		if is_instance_valid(tree):
			if tree.phase=="rooted" and tree.strikes>0 and tree.recoil_elapsed<tree.RECOIL_SECONDS:
				if tree._pivot.basis.y.distance_to(Vector3.UP)>.055 and tree.recoil_elapsed>=.05 and not swayed:
					swayed=true
					still(id.validate_filename()+"-impact")
				chips=chips or tree.chips.any(func(c):return c.visible)
				var motion: Vector3=game.character_kit.hit_travel
				motion.y=0.
				crossed=crossed or (tree.to_global(tree.chip_origins[0]).distance_to(game.character_kit.hit_position)<.015 and tree.recoil_direction.dot(motion.normalized())>.99)
			if tree.phase=="falling" and tree.falling_clock>=tree.FALL_SECONDS and not fell:
				fell=true
				fall_sample=tree.falling_clock
				still(id.validate_filename()+"-fall")
			if zero_tick<0 and tree.phase=="credited":
				zero_tick=tick
				deplete_us=Time.get_ticks_usec()
			if zero_tick>=0 and tree.phase=="credited" and tree._pivot.visible and tree._pivot.basis.y.length()>.25 and tree._pivot.basis.y.length()<.9 and not growing:
				growing=true
				still(id.validate_filename()+"-return")
			if tree.phase=="rooted" and zero_tick>=0:
				return_tick=tick
				return_us=Time.get_ticks_usec()
				still(id.validate_filename()+"-available")
				break
		if zero_tick>=0:
			var age:=tick-zero_tick
			if age<300 and game.is_source_available(id):early=true
			if stream and age==60: game.actor.position=at+Vector3(18,0,0)
			if stream and age==105: streamed=not game.lifecycle.loaded.has(id)
			if stream and age==120: game.actor.position=at+Vector3(3.6,0,0)
			if not stream and age==5: game.actor.position=at+Vector3(3.6,0,0)
	var depleted := events_at("deplete_wood",at)
	var regrown := events_at("regrow_wood",at)
	var measured := -1.
	if depleted.size()>drop_before and regrown.size()>back_before:
		measured=regrown[back_before].t-depleted[drop_before].t
	var hit_count:=events_at("impact_wood",at).size()-hits_before
	var loose_wood:=0
	for d in game.drops.values():
		if d.kind=="wood" and d.at.distance_to(at)<1.75:loose_wood+=1
	checks[id+" natural damaging contacts"]=hit_count==3 and swayed and chips and crossed and fell
	checks[id+" one three-unit yield"]=depleted.size()-drop_before==1 and loose_wood==3
	checks[id+" 5s elapsed"]=return_tick-zero_tick==300 and absf(measured-5.)<.002 and not early
	checks[id+" return appears before available"]=growing and regrown.size()-back_before==1
	checks[id+" stored quantities untouched"]=stored==game.inventory.stored
	if stream: checks[id+" unload did not restart timer"]=streamed
	evidence[id]={"contact_events":hit_count,"matches_blade_position_and_travel":crossed,"sway":swayed,"chips":chips,"fell":fell,"fall_frame_seconds":fall_sample,"return_visible":growing,"loose":loose_wood,"depletion_to_available_ticks":return_tick-zero_tick,"game_seconds":measured,"wall_seconds":float(return_us-deplete_us)/1e6,"stored":stored}

func stock_fixture() -> void:
	var ledger = game.inventory
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat"]:
		for kind: String in ledger.costs[id]:
			for i in int(ledger.costs[id][kind]):
				ledger.collect("tree-test-fund-%s-%s-%d" % [id,kind,i],kind)
				ledger.payment(id,kind,false)
		game._finish_purchase(id)
	game._apply_hearth(true,false)
	var stock := {"wood":7,"stone":4,"meat":3}
	for kind: String in stock:
		for i in stock[kind]:
			ledger.collect("tree-test-stored-%s-%d" % [kind,i],kind)
			ledger.deposit(kind)
	game._refresh_field()
	checks["typed quantities established through inventory API"]=stock==ledger.stored

func run() -> void:
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	for i in 6:await physics_frame
	if not output.is_empty(): game.set_zoom_ratio(1.65)
	await harvest("starter-wood",game.resource_tree.position,false)
	stock_fixture()
	var rows: Array = game.world_landscape.describe_chunk(Vector2i(3,-4))
	var chosen: Dictionary
	for r in rows:
		if r.kind!="wood": continue
		if rows.any(func(other):return other.id!=r.id and other.position.distance_to(r.position+Vector3(2.18,0,0))<3.45): continue
		chosen=r
		break
	checks["real remote pine selected"]=not chosen.is_empty()
	if not chosen.is_empty():await harvest(chosen.id,chosen.position,true)
	var prior: Dictionary = game.lifecycle.snapshot()
	prior.cooling={"starter-wood":21.5,"grove@10,20":13.8,"pine@77,55":21.1,"world1/4/-5/wood/1":15.,"world1/4/-5/stone/3":29.}
	checks["load prior save"]=game.lifecycle.restore(prior)
	checks["legacy loaded and unloaded wood capped to five"]=game.lifecycle.cooling["starter-wood"]==5. and game.lifecycle.cooling["grove@10,20"]==5. and game.lifecycle.cooling["pine@77,55"]==5. and game.lifecycle.cooling["world1/4/-5/wood/1"]==5.
	checks["legacy stone duration retained"]=game.lifecycle.cooling["world1/4/-5/stone/3"]==29.
	print(JSON.stringify({"checks":checks,"evidence":evidence,"physics_hz":Engine.physics_ticks_per_second}))
	game.sound.stop_playback()
	game.queue_free()
	for i in 12:
		OS.delay_msec(20)
		await process_frame
	quit(1 if false in checks.values() else 0)
