extends "res://tests/qa_worker_jobs.gd"
## Exercise the real settlement jobs and the selected tundra stag through its
## visible hunt, loose drops, bounded worker carry, warehouse and cold restore.

const HERE := "res://tests/qa_survivor_hunt.gd"
const EXPECTED_STAG_YIELD := 4
var view_record := OS.get_environment("HAVENLINE_HUNT_VIEW")
var hunt_views := {}

func run() -> void:
	if not Save.Profile.new().configure(OS.get_cmdline_user_args()):
		var path := Session.make_directory()
		var status := Session.child(HERE,path,"--survivor-hunt")
		Session.remove_owned(path)
		quit(status)
		return
	game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	for i in 4: await process_frame
	game.set_physics_process(false)
	game.set_process(false)
	game.tracks.set_physics_process(false)
	worker = game.survivor
	setup_camp()
	var journal: Dictionary = game.inventory.settlement
	var stag: Node3D = worker.wildlife
	var prey_hp := int(stag.hp)
	await _game_views("Stag-rest",stag.global_position)
	var prior_deposits: int = game.events.filter(func(event): return event.event=="deposit_meat").size()
	var first_proactive := -1
	var first_hit := -1
	var kill_tick := -1
	var transport_tick := -1
	var landing_tick := -1
	var cargo_peak := 0
	var warehouse_count := 0
	var hoof_peak := 0
	var stag_feet: Array = game.tracks.living[stag].feet
	var hoof_min := INF
	var hoof_max := -INF
	var drops_at_death := 0
	var windup_shown := false
	var prior := ""
	var beats: Array[Dictionary] = []
	for i in 60*360:
		tick(1.0/60.0)
		game.tracks._physics_process(1.0/60.0)
		if first_proactive>=0 and kill_tick<0:
			var prints := 0
			for chunk: Dictionary in game.tracks.chunks.values():
				for mark: Dictionary in chunk.marks:
					if mark.hoof: prints+=1
			hoof_peak=maxi(prints,hoof_peak)
			if stag.flight_left>0.0:
				for foot: Dictionary in stag_feet:
					var hoof_position: Vector3 = stag.rig.get_bone_global_pose(foot.bone).origin
					var lift := hoof_position.y-float(foot.height)
					hoof_min=minf(hoof_min,lift)
					hoof_max=maxf(hoof_max,lift)
		if not view_record.is_empty() and i%2==0: await process_frame
		if worker.phase != prior and beats.size()<100:
			beats.append({"tick":i,"worker":str(worker.actor.position),"stag":str(stag.position),"phase":worker.phase,"hp":stag.hp,"aboard":journal.worker_load.meat,"stored":game.inventory.stored.meat})
			prior=worker.phase
		if first_proactive<0 and worker.phase=="hunt_approach" and stag.hp==prey_hp:
			first_proactive=i
		if not windup_shown and worker.phase=="hunt_strike" and worker.hunt_elapsed>=.33:
			windup_shown=true
			await _game_views("Hunt-windup", worker.actor.global_position.lerp(stag.global_position,.5))
		if first_hit<0 and stag.hp<prey_hp:
			first_hit=i
			await _game_views("Hunt-contact", worker.actor.global_position.lerp(stag.global_position,.5))
		if kill_tick<0 and stag.hp==0:
			kill_tick=i
			for drop: Dictionary in game.drops.values():
				if drop.kind=="meat": drops_at_death+=1
		if kill_tick>=0:
			cargo_peak=maxi(cargo_peak,int(journal.worker_load.meat))
			if transport_tick<0 and worker.phase=="bulk_return" and journal.worker_load.meat>0:
				transport_tick=i
				await _game_views("Hunt-return")
			if transport_tick>=0 and worker.phase=="bin_delivery" and not worker.delivery_stream.is_empty():
				await _game_views("Hunt-stock")
			if transport_tick>=0:
				warehouse_count=game.events.filter(func(event): return event.event=="deposit_meat").size()-prior_deposits
			if warehouse_count==EXPECTED_STAG_YIELD:
				landing_tick=i
				break
		if game.persist_blocked:break
	check(first_proactive>=0,"paid survivor proactively routes to prey")
	check(first_hit>first_proactive,"native carried axe sweep hits after proactive pursuit")
	check(kill_tick>first_hit and drops_at_death==EXPECTED_STAG_YIELD,"defeated stag produces one four-bundle meat reward")
	check(transport_tick>kill_tick and cargo_peak==EXPECTED_STAG_YIELD,"real pickup packs the entire yield on its meat shelf")
	check(landing_tick>transport_tick and warehouse_count==EXPECTED_STAG_YIELD,"same native worker returns and stocks exactly four meat bundles")
	check(game.inventory.carried.meat==0,"worker hunt credited no material to the distant player")
	check(game.tracks.living[stag].feet.size()==4 and hoof_peak>0,"actual moving stag sampled four rig hooves and left cloven prints")
	var saved = game.Inventory.new()
	check(saved.configure(game.inventory.configured_costs) and saved.restore(game.inventory.snapshot()),"actual post-hunt save migration and conservation accept")
	if saved.settlement.has("stag_health"):
		check(saved.settlement.stag_health==0 and saved.world_state.cooling.has(stag.SOURCE_ID),"cold state records the prey cooldown")
	game.lifecycle.advance(stag.RETURN_DELAY)
	stag.advance(1.0/60.0)
	check(stag.is_huntable() and stag.hp==prey_hp and not game.lifecycle.cooling.has(stag.SOURCE_ID),"native wildlife cooldown returned the same single prey alive")
	print("CREW_HUNT ",JSON.stringify({"checks":checks,"errors":errors,"beats":beats,"proactive":first_proactive,"first_hit":first_hit,"kill":kill_tick,"transport":transport_tick,"landing":landing_tick,"meat_peak":cargo_peak,"warehouse_count":warehouse_count,"hoof_peak":hoof_peak,"hoof_count":stag_feet.size(),"hoof_min":hoof_min,"hoof_max":hoof_max,"camera":hunt_views}))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 4: await process_frame
	quit(int(not errors.is_empty()))

func _game_views(label: String, anchor := Vector3.INF) -> void:
	if view_record.is_empty() or hunt_views.has(label): return
	var camera: Camera3D = game.camera
	var previous := camera.global_position
	if not anchor.is_finite(): anchor = worker.actor.global_position
	camera.global_position = anchor+game.camera_follow_offset
	hunt_views[label]={"position":str(anchor),"health":worker.wildlife.hp,"renderer":RenderingServer.get_video_adapter_name()}
	for scale_ in [1.0,2.0]:
		game.set_zoom_ratio(scale_)
		await process_frame
		RenderingServer.force_draw(false)
		root.get_texture().get_image().save_jpg(view_record.path_join("%s-%dx.jpg" % [label,int(scale_)]),.92)
	game.set_zoom_ratio(1.0)
	camera.global_position = previous
