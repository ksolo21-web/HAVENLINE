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
	checks["hearth shows no free stockrooms"] = camp.stock_anchors.values().all(func(a):return not a.is_visible_in_tree())
	pay("expansion_1")
	for kind: String in ["wood","stone","meat"]:
		pay("storage_"+kind)
	world._refresh_field()
	for kind: String in ["wood","stone","meat"]:
		var anchor: Node3D = camp.stock_anchors[kind]
		var center: Vector2 = camp.receiver_position(kind)
		var surface: Vector3 = camp.landing_position(kind,0)
		checks[kind+" receiver is flush with authored plate"] = absf(anchor.position.y-.005)<.001 and absf(surface.y-anchor.position.y)<.001
		checks[kind+" floor source is the authored inlaid shell"] = anchor.get_child(0).scene_file_path == "res://assets/field_camp/wood_storage_empty.glb"
		checks[kind+" receiver fits inside wall and clears furnace"] = camp.is_inside_camp(Vector3(center.x-1.4432,0,center.y-1.1352)) and camp.is_inside_camp(Vector3(center.x+1.4432,0,center.y+1.1352)) and center.length()>2.7 and anchor.is_visible_in_tree()
		var final_slot: int = {"wood":0, "stone":1, "meat":6}[kind]
		var final_position: Vector3 = camp.landing_position(kind, final_slot)
		checks[kind+" overflowing stock lands on final visible pile"] = camp.landing_position(kind,999999).is_equal_approx(final_position) and final_position.y < 0.6
	camp.sync_stock({"wood":12,"stone":4,"meat":8})
	checks["counts identify only deposited typed stock"] = camp.count_labels.wood.text=="12" and camp.count_labels.stone.text=="4" and camp.count_labels.meat.text=="8"
	for kind: String in ["wood","stone","meat"]:
		checks[kind+" stocked plot shows only physical units"] = camp.stock_surfaces[kind][0][0].get_active_material(camp.stock_surfaces[kind][0][1]).albedo_texture == camp.STOCKED_PAINT
	camp.sync_stock({"wood":1000000,"stone":100001,"meat":101})
	checks["quantity labels preserve overflow balances"] = camp.count_labels.wood.text=="1000000" and camp.count_labels.stone.text=="100001" and camp.count_labels.meat.text=="101"
	camp.sync_stock({"wood":0,"stone":0,"meat":0})
	for kind: String in ["wood","stone","meat"]:
		checks[kind+" emptied plot recovers its painted type"] = camp.stock_surfaces[kind][0][0].get_active_material(camp.stock_surfaces[kind][0][1]).albedo_texture == camp.empty_stock_paint[kind]
	camp.set_upgrade_payment({"stone":0,"meat":0})
	checks["paid upgrade retires its ground inlay"] = not camp.upgrade_anchor.is_visible_in_tree()
	for gate in world.gates:
		var outside: Vector3 = gate.global_basis.z.normalized()
		var at: Vector3 = gate.global_position
		world.actor.position = at + outside*1.45
		await physics_frame
		gate.request_toggle(world.actor.global_position)
		for i in 66:
			gate.advance(1./60.,world.actor.global_position,float(world.layout.actor_radius))
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
