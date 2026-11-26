extends SceneTree

const Scene := preload("res://field_opening.tscn")
var checks := {}
var world

func _initialize() -> void:
	call_deferred("run")

func walk(direction: Vector3, frames: int) -> void:
	for i in frames:
		await physics_frame
		world.actor.velocity = direction * 2.5
		world.actor.move_and_slide()

func pay(id: String) -> void:
	for kind: String in world.inventory.costs[id]:
		for i in int(world.inventory.costs[id][kind]):
			world.inventory.collect("environment-%s-%s-%d" % [id,kind,i],kind)
			world.inventory.payment(id,kind,false)
	world._finish_purchase(id)

func run() -> void:
	world = Scene.instantiate()
	root.add_child(world)
	world.set_physics_process(false)
	await physics_frame
	var camp = world.field_env
	checks["unpaid court and upgrade hidden"] = camp.buy_anchor.is_visible_in_tree() and not camp.upgrade_anchor.is_visible_in_tree() and not world.camp_built.visible
	checks["original raised purchase pad is hidden"] = not world.purchase_pad_view.is_visible_in_tree()
	var temporary: Array = camp.seasonal_pines.duplicate()
	var base_trees: int = world.trees.size()-temporary.size()
	checks["future storage grove uses live harvestable trees"] = not temporary.is_empty() and temporary.all(func(tree): return tree in world.trees and tree in world.surfaces and tree.phase=="rooted")
	checks["storage grove clears build approach"] = temporary.all(func(tree): return Vector2(tree.position.x,tree.position.z).distance_to(camp.BUY)>2.0)
	pay("center_hearth")
	world._apply_hearth(true,true)
	checks["thaw retires seasonal trees from harvest"] = world.trees.size()==base_trees and camp.seasonal_pines.is_empty() and temporary.all(func(tree): return not world.surfaces.has(tree))
	for frame in 24: await physics_frame
	checks["thaw removes retired grove from occupied plots"] = temporary.all(func(tree): return not is_instance_valid(tree))
	checks["hearth centered in newly paid court"] = world.camp_built.get_node("CenteredHearth_StudioTrialOnly/RecoveredStoneFurnace").is_visible_in_tree() and not camp.buy_anchor.is_visible_in_tree() and not camp.upgrade_anchor.is_visible_in_tree()
	# Use the same scene targets and visibility as the purchase transition. No
	# inventory or world state from this fixture is persisted.
	checks["hearth shows no free stockrooms"] = not world.depot.apron.is_visible_in_tree() and not world.depot.house.is_visible_in_tree()
	pay("expansion_1")
	for kind: String in ["wood","stone","meat"]:
		pay("storage_"+kind)
	world._refresh_field()
	for kind: String in ["wood","stone","meat"]:
		var bin: Node3D = world.depot.bins[kind]
		var first: Vector3 = world.depot.landing_position(kind,0)
		checks[kind+" physical shelf is inside house"] = camp.is_inside_camp(first) and bin.global_position.distance_to(world.depot.house.global_position)<2.1 and bin.visible
		checks[kind+" all purchases share one apron"] = world.carry.receivers["storage_"+kind] == world.depot.apron
		checks[kind+" retired corner is absent"] = world.find_child(kind.capitalize()+"StoragePlot",true,false)==null
	var storehouse = world.depot.house
	world.actor.position=Vector3.ZERO
	storehouse._physics_process(.4)
	var events_before := int(world.events.size())
	world.actor.position=world.depot.APRON
	for i in 4: storehouse._physics_process(.15)
	world.actor.position=Vector3.ZERO
	for i in 4: storehouse._physics_process(.15)
	var cues: Array = world.events.slice(events_before)
	checks["one spatial door cue per open and close"] = cues.size()==2 and cues[0].event=="gate" and cues[1].event=="gate_latch" and absf(cues[0].x-world.depot.SITE.x)<.01
	world.inventory.collect("world-storehouse-first","wood")
	world.carry.sync()
	checks["one earned unit launches toward timber shelf"] = world.carry.deposit_storage("wood")
	var deposit: Dictionary = world.carry.flights[0]
	world.carry.advance(.35)
	var displayed: Node3D = world.carry.pieces["storage/wood"][0]
	checks["earned display lands at the same shelf size position and count"] = world.inventory.stored.wood==1 and displayed.get_parent()==world.depot.bins.wood and displayed.global_position.is_equal_approx(deposit.mesh.global_position) and displayed.scale.is_equal_approx(deposit.mesh.scale) and world.depot.labels.wood.text=="1"
	checks["east expansion can spend timber from its actual shelf"] = world.carry.contribute("expansion_2")
	var debit: Dictionary = world.carry.flights[0]
	checks["spend originates at visible shelf mesh"] = debit.from=="storage" and debit.mesh.global_position.is_equal_approx(displayed.global_position) and debit.mesh.scale.is_equal_approx(displayed.scale)
	world.carry.advance(.35)
	checks["shelf empties and east expansion receives exactly one unit"] = world.inventory.stored.wood==0 and world.inventory.paid.expansion_2.wood==1 and world.depot.labels.wood.text=="0" and not displayed.visible
	var counts := {"wood":1000000,"stone":100001,"meat":101,"coal":1123,"slate":8900,"metal":999999}
	world.inventory.stored.merge(counts,true)
	world.depot.refresh(true)
	world.carry.sync()
	checks["a million wood and overflow stone and meat stay inside bounded bins"] = world.carry.pieces["storage/wood"].size()==1 and world.carry.pieces["storage/stone"].size()==2 and world.carry.pieces["storage/meat"].size()==7
	checks["bay labels show exact small balances and conservative compact lots"] = world.depot.labels.wood.text=="1M" and world.depot.labels.stone.text=="100k+" and world.depot.labels.meat.text=="101" and world.depot.labels.coal.text=="1k+" and world.depot.labels.metal.text=="999k+"
	var hint:String=world.depot.hint()
	checks["apron HUD retains exact values for all six resources"] = world.Inventory.KINDS.all(func(k):return hint.contains("%d %s"%[counts[k],world.Inventory.TITLES[k].to_lower()]))
	world.inventory.stored = world.Inventory.EMPTY.duplicate()
	world.depot.refresh(true)
	camp.set_upgrade_payment({"stone":0,"meat":0})
	checks["paid upgrade retires its ground inlay"] = not camp.upgrade_anchor.is_visible_in_tree()
	for gate in world.gates:
		var outside: Vector3 = gate.global_basis.z.normalized()
		var at: Vector3 = gate.global_position
		world.actor.position = at + outside*1.45
		await physics_frame
		for i in 66:
			world.step_technical_gates(1./60.)
			await physics_frame
		var open: bool = gate.angle > 1.56
		await walk(-outside,80)
		checks[gate.gate_id+" inward crossing"] = open and (world.actor.global_position-at).dot(outside)<-.85
		await walk(outside,80)
		checks[gate.gate_id+" outward crossing"] = (world.actor.global_position-at).dot(outside)>.85
	print(JSON.stringify({"suite":"actual_field_court","checks":checks}))
	var code := 1 if checks.values().has(false) else 0
	world.sound.stop_playback()
	world.queue_free()
	for i in 12:
		OS.delay_msec(20)
		await process_frame
	quit(code)
