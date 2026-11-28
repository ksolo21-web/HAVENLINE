extends RefCounted
## Select one on-foot interaction. Existing receivers, combat and the journal
## remain the authorities for actual contacts and transfers.
const Director = preload("res://field_context_director.gd")
const PLAYER := "player_lead"
const NEAR := .72
var director := Director.new()
var descriptor: Dictionary = {}
var depot_target := ""
var dispatching := false
var focused_plot: Node3D
var focused_hearth: Node3D

func reset() -> void:
	director.reset()
	descriptor.clear()
	depot_target = ""
	_set_plot_focus(null,null)

func selected() -> String:
	return String(descriptor.get("id","")) if descriptor.get("actionable",false) else ""

func _flat(point: Vector3) -> Vector2:
	return Vector2(point.x,point.z)

func _edge(at: Vector3, center: Vector3, distance: float) -> Vector3:
	var delta := (_flat(center)-_flat(at)).normalized()*distance
	return Vector3(at.x+delta.x,center.y,at.z+delta.y)

func _add(rows: Array, kind: String, id: String, at: Vector3, radius: float, progress := 0.) -> void:
	if at.is_finite():
		rows.append({"kind":kind,"id":id,"position":_flat(at),"radius":radius,
			"eligible":true,"priority":0,"capability":Director.KIND_CAPABILITY[kind],"progress":progress})

func _bill_available(world, id: String) -> bool:
	if not world.inventory.offer_open(id):return false
	var bill: Dictionary = world.inventory.remaining(id)
	for kind: String in bill:
		if bill[kind] <= 0: continue
		if world.carry.available_to_station(kind)>0 or world.carry.incoming(id,kind)>0: return true
		if world.inventory.storage_open(kind) and world.carry.available_on_shelf(kind)>0: return true
	return false

func _progress(world, id: String) -> float:
	var total := 0
	var left := 0
	var due: Dictionary = world.inventory.remaining(id)
	for kind: String in due:
		total += int(world.inventory.costs[id][kind])
		left += int(due[kind])
	return 1. - float(left) / maxi(1,total)

func _stock_ready(world) -> bool:
	var book: Dictionary = world.inventory.settlement
	var cargo: Dictionary = world.inventory.hand_goods()
	for kind: String in world.inventory.KINDS:
		if world.inventory.storage_open(kind) and (world.carry.available_to_station(kind)>int(book.withdrawn.get(kind,0)) or world.carry.incoming(world.carry.STOCK,kind)>0):
			return true
	for kind: String in cargo:
		if int(cargo[kind])>int(book.withdrawn.get(kind,0)):return true
	return false

func _counter_ready(world) -> bool:
	if world.inventory.till_balance() > world.counter.cash_in_exchange():return true
	var goods: Dictionary = world.inventory.hand_goods()
	for kind: String in ["meal","planks","blocks"]:
		if int(goods.get(kind,0))>0 and world.settlement_loop.counter_accepts(kind):return true
	return false

func tick(world, dt: float) -> void:
	var rows: Array = []
	depot_target = ""
	var player: Node3D = world.actor
	var ready: bool = world.settlement_loop.can_transact() and not world.snow_truck.mounted and not world.camp_layout.active and world.reveal_countdown<0.
	var display: Node3D = world.hero_model if world.player_character()==1 else world.player_wardrobe.visual
	var present := is_instance_valid(player) and player.is_visible_in_tree() and is_instance_valid(display) and display.is_visible_in_tree()
	if not present:
		descriptor = director.advance(dt,Vector2.ZERO,Vector2.ZERO,Vector2.ZERO,Vector2.ZERO,PLAYER,rows,false,false)
		_set_plot_focus(null,null)
		return
	if ready and present:
		_candidates(world,player.global_position,rows)
	var move := Vector2.ONE if world.runner_requested_motion else Vector2.ZERO
	# The warehouse receives immediately at a stable stop so its existing
	# four transfer waves keep their full timing. It is still a single focus.
	descriptor = director.advance(dt,_flat(player.global_position),_flat(player.global_basis.z),move,_flat(player.velocity),PLAYER,rows,present,ready,"deposit:pad:"+world.carry.STOCK)

	_preview_plot(world)

func _preview_plot(world) -> void:
	var plot: Node3D
	var hearth: Node3D
	if descriptor.get("kind") == "build" and descriptor.get("state") in ["acquiring","active"]:
		var id: String = descriptor.id
		if id == "pad:" + world.HEARTH_OFFER:
			hearth = world.field_env
		elif id.begins_with("pad:"):
			plot = world.carry.receivers.get(id.trim_prefix("pad:"))
		elif id == "work:survivor_plot":
			plot = world.settlement_loop.works.plot
		elif id == "work:owl_roost":
			plot = world.settlement_loop.works.owl_plot
	_set_plot_focus(plot,hearth)

func _set_plot_focus(plot: Node3D, hearth: Node3D) -> void:
	if focused_plot != plot:
		if is_instance_valid(focused_plot): focused_plot.set_payment_focus(false)
		focused_plot = plot
		if is_instance_valid(plot): plot.set_payment_focus(true)
	if focused_hearth != hearth:
		if is_instance_valid(focused_hearth): focused_hearth.set_hearth_payment_focus(false)
		focused_hearth = hearth
		if is_instance_valid(hearth): hearth.set_hearth_payment_focus(true)

func _candidates(world, feet: Vector3, rows: Array) -> void:
	var loop = world.settlement_loop
	var inside: bool = world.field_env.is_inside_camp(feet)
	var limit: float = world.character_kit.maximum_radius()
	if world.orbit_permitted_at(feet):
		_field_candidates(world,feet,limit,rows)
	if world.survivor.at_rescue(feet) and world.survivor.actor.is_visible_in_tree():
		_add(rows,"rescue","survivor",world.survivor.actor.global_position,1.46)
	if inside and world.counter.at_service(feet) and _counter_ready(world):
		_add(rows,"customer_service","counter",world.counter.service_point.global_position,4.)
	var works = loop.works
	var work: String = works._site()
	var work_distance: float = works.handoff_distance(feet)
	if not work.is_empty() and work_distance <= NEAR:
		var kind := "deposit" if work in loop.Rules.KINDS else "build"
		_add(rows,kind,"work:"+work,_edge(feet,works._goal(work),work_distance),NEAR)
	for station: String in loop.Rules.KINDS:
		if station==work and work_distance<=NEAR:continue
		if not works.automatic_handoff(station) or not works.can_operate(station):continue
		if loop.exchange.Logistics.rack(world.inventory.settlement,station)>0:
			_add(rows,"deposit","work:"+station,_edge(feet,works._goal(station),works.machine_distance(station,feet)),NEAR)
	var bay: String = loop.exchange.bay_at(feet)
	if not bay.is_empty():
		var actual := bay if loop.exchange._shelf_amount(bay)>0 else String(loop.exchange.SAME_FACE.get(bay,""))
		if not actual.is_empty() and loop.exchange._shelf_amount(actual)>0 and not world.inventory.settlement.withdrawn.has(actual):
			_add(rows,"deposit","shelf",loop.exchange.pickup_position(bay),.39)
	if inside:
		depot_target = world.depot.target_at(feet)
	if not depot_target.is_empty():
		var selling: bool = depot_target==world.carry.STOCK
		var upgrade: bool = not selling and world.depot.on_upgrade_side(feet)
		var anchor: Node3D = world.depot.upgrade_mark if upgrade else world.depot.apron
		var distance: float = world.Reach.plot_distance(anchor,feet) if upgrade else world.depot.loading_distance(feet)
		if (_stock_ready(world) if selling else _bill_available(world,depot_target)):
			_add(rows,"deposit" if selling else "build","pad:"+depot_target,_edge(feet,anchor.global_position,distance),NEAR,0. if selling else _progress(world,depot_target))
	for id: String in world.inventory.costs:
		if id in world.Progress.STORAGE or (not world.exit_required.has(id) and not world.inventory.offer_open(id)):continue
		if id in world.Progress.LINES and not world.offer_floors[id].visible:continue
		var anchor: Node3D = world.carry.receivers[id]
		var distance: float = world.Reach.plot_distance(anchor,feet)
		if distance>NEAR:
			world.exit_required.erase(id)
			if distance>NEAR+Director.RELEASE_MARGIN or director.current_identity!="build:pad:"+id: continue
		if world.exit_required.has(id) or (world.camp_active and not inside):continue
		if id in [world.Progress.GARAGE,world.Progress.TRUCK] and not world._can_fund_vehicle_offer(id):continue
		if anchor.is_visible_in_tree() and _bill_available(world,id):
			_add(rows,"build","pad:"+id,_edge(feet,anchor.global_position,distance),NEAR,_progress(world,id))
	if inside:
		var sites = world.encounters.raids.sites
		var repair_id: String = sites.repair_target
		if is_instance_valid(sites.repair_pad) and world.Reach.plot_distance(sites.repair_pad,feet)<=.06 and sites._nearby_repair_valid(repair_id,sites.director.repair_bill(repair_id)):
			_add(rows,"defense_repair","repair:"+repair_id,sites.repair_position(repair_id),1.95)

func _field_candidates(world, feet: Vector3, limit: float, rows: Array) -> void:
	for group: Array in [world.enemies,world.trees,world.rocks]:
		for target: Node3D in group:
			if not is_instance_valid(target) or not target.is_visible_in_tree():continue
			if feet.distance_squared_to(target.global_position)>pow(limit+1.7,2.):continue
			if not world.reachable(target):continue
			var mesh: MeshInstance3D = world.surfaces[target][0]
			var bounds: AABB = mesh.global_transform*mesh.mesh.get_aabb()
			var point := feet.clamp(bounds.position,bounds.end)
			if not world.field_env.travel_clear(feet,point):continue
			var hostile := target.is_in_group("swirl_hostiles")
			var id := String(target.get_meta("field_source_id",target.name))
			_add(rows,"enemy" if hostile else "gather",id,point,limit)

func feedback(world) -> String:
	var id := String(descriptor.get("id",""))
	var state := String(descriptor.get("state",""))
	var kind := String(descriptor.get("kind",""))
	if id.is_empty() or state=="idle":return ""
	var activity := ""
	if id.begins_with("pad:") and id != "pad:"+world.carry.STOCK:
		var plot := id.trim_prefix("pad:")
		if state == "blocked_range": return "Move closer to the plot"
		return world.build_hint(plot) if state != "blocked_movement" else "Stop beside the plot to build"
	if id.begins_with("work:"):
		var work := id.trim_prefix("work:")
		activity = {"wood":"Use the saw","stone":"Use the drill","meat":"Use the cooker","survivor_plot":"Fund the rescue"}.get(work,"Fund the roost")
	elif id=="shelf":activity="Collect from the shelf"
	elif kind=="enemy":return "Defending"
	elif kind=="gather":return "Gathering"
	elif kind=="rescue":activity="Rescue survivor"
	elif kind=="defense_repair":activity="Repair"
	elif kind=="customer_service":activity="Serve the counter"
	else:activity="Unload at the storehouse"
	if state == "blocked_movement":return activity + " · stop moving"
	return activity
