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
	world._apply_hearth(true,true)
	checks["thaw retires seasonal trees from harvest"] = world.trees.size()==base_trees and camp.seasonal_pines.is_empty() and temporary.all(func(tree): return not world.surfaces.has(tree))
	for frame in 24: await physics_frame
	checks["thaw removes retired grove from occupied plots"] = temporary.all(func(tree): return not is_instance_valid(tree))
	checks["hearth centered in newly paid court"] = world.camp_built.get_node("CenteredHearth_StudioTrialOnly/RecoveredStoneFurnace").is_visible_in_tree() and not camp.buy_anchor.is_visible_in_tree() and camp.upgrade_anchor.is_visible_in_tree()
	# Use the same scene targets and visibility as the purchase transition. No
	# inventory or world state from this fixture is persisted.
	for kind: String in ["wood","stone","meat"]:
		var anchor: Node3D = camp.stock_anchors[kind]
		var center: Vector2 = camp.receiver_position(kind)
		var surface: Vector3 = camp.landing_position(kind,0)
		checks[kind+" receiver is flush with authored plate"] = absf(anchor.position.y-.005)<.001 and absf(surface.y-anchor.position.y)<.001
		checks[kind+" floor source is the authored inlaid shell"] = anchor.get_child(0).scene_file_path == "res://assets/field_camp/wood_storage_empty.glb"
		checks[kind+" receiver fits inside wall and clears furnace"] = absf(center.x)+1.4432<5 and absf(center.y)+1.1352<4 and center.length()>2.7
		var columns := 2 if kind == "meat" else 3
		var first_upper: Vector3 = camp.landing_position(kind,columns)
		var last_lower: Vector3 = camp.landing_position(kind,columns-1)
		checks[kind+" units fill the reference stock arrangement"] = is_equal_approx(last_lower.y,surface.y) and first_upper.y>surface.y and Vector2(first_upper.x,first_upper.z).is_equal_approx(Vector2(surface.x,surface.z))
	camp.sync_stock({"wood":12,"stone":4,"meat":8})
	checks["counts identify only deposited typed stock"] = camp.count_labels.wood.text=="12" and camp.count_labels.stone.text=="4" and camp.count_labels.meat.text=="8"
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
	quit(1 if checks.values().has(false) else 0)
