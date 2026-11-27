extends Node3D
## A short handoff moves one carried unit onto the plot or into a machine hopper.
## Only the handoff requires the carrier's presence. Machines own the unit once it lands.
const FloorOffer = preload("res://field_offer_floor.gd")
const PLOT_AT := Vector3(-5.5,0,10.9)
var world
var plot
var active := ""
var nearer_plot := false
var last_paid := -1

func setup(host) -> void:
	world = host
	world.carry.worksite_demand = demand
	world.carry.worksite_land = receive
	world.carry.worksite_goal = _goal
	plot = FloorOffer.new()
	add_child(plot)
	plot.install_custom(world.field_env,"survivor_plot",PLOT_AT,"Rescue survivor",["wood"])
	refresh()

func refresh() -> void:
	var journal: Dictionary = world.inventory.settlement
	plot.visible = world.camp_active and not journal.survivor_paid
	if last_paid != int(journal.survivor_wood):
		last_paid = int(journal.survivor_wood)
		world.field_env.show_costs(plot.price,{"wood":world.inventory.survivor_cost-last_paid})
		plot.set_fill(float(last_paid) / world.inventory.survivor_cost)

func _site() -> String:
	var here: Vector3 = world.actor.global_position
	if world.camp_active and not world.inventory.settlement.survivor_paid and world.Reach.plot_distance(plot,here) <= world.Reach.NEAR:
		return "survivor_plot"
	if not world.inventory.complete(world.Progress.SECOND) or not world.field_env.is_inside_camp(here): return ""
	# Adjacent worktables may both be in reach. Finish an in-flight handoff
	# first, then prefer a compatible open inlet before comparing wall distance.
	var best := ""
	var best_rank := 4
	var best_distance := INF
	var floor_point := Vector2(here.x,here.z)
	for kind: String in world.settlement_loop.Rules.KINDS:
		if not world.inventory.is_machine_owned(kind): continue
		var wall: Rect2 = world.lakeshore._footprint(0.) if kind == "meat" else world.processors._rect(kind,0.)
		var distance: float = world.Reach.distance_to_rect(floor_point,wall)
		if wall.has_point(floor_point) or distance > world.Reach.NEAR: continue
		var rank := 3
		if world.carry.incoming(kind,kind) > 0:
			rank = 0
		elif world.carry.available_to_station(kind) > 0 and world.settlement_loop.available_to_feeder(kind):
			rank = 1
		elif kind == "meat" and world.inventory.settlement.held_meal == 0 and world.settlement_loop.Rules.waiting_meals(world.inventory.settlement) > 0:
			rank = 2
		var tied_active := kind == active and is_equal_approx(distance,best_distance)
		if rank < best_rank or (rank == best_rank and (distance < best_distance or tied_active)):
			best = kind
			best_rank = rank
			best_distance = distance
	return best

func handoff_distance(at: Vector3) -> float:
	var site := _site()
	if site.is_empty(): return INF
	var kind := _raw(site)
	if demand(site,kind) <= 0 or (world.carry.available_to_station(kind) == 0 and world.carry.incoming(site,kind) == 0): return INF
	if site == "survivor_plot": return world.Reach.plot_distance(plot,at)
	var rect: Rect2 = world.lakeshore._footprint(0.) if site == "meat" else world.processors._rect(site,0.)
	return world.Reach.distance_to_rect(Vector2(at.x,at.z),rect)

func _raw(site: String) -> String:
	return "wood" if site == "survivor_plot" else site

func _goal(site: String) -> Vector3:
	if site == "survivor_plot": return plot.global_position + Vector3.UP*.12
	if site == "meat": return world.lakeshore.cooker_input.global_position
	return world.processors.input_position(site)

func cancel() -> void:
	if not active.is_empty(): world.carry.cancel_worksite(active)
	active = ""

func demand(site: String, kind: String) -> int:
	if kind != _raw(site) or not world.settlement_loop.can_transact() or site != _site(): return 0
	var journal: Dictionary = world.inventory.settlement
	if site == "survivor_plot": return world.inventory.survivor_cost - int(journal.survivor_wood)
	return world.settlement_loop.Rules.HOPPER_CAPACITY - int(journal.hoppers[kind]) - int(journal.line_load[kind])

func advance(_dt: float) -> void:
	refresh()
	if nearer_plot:
		cancel()
		return
	var site := _site()
	if active != site: cancel()
	if site.is_empty() or not world.settlement_loop.can_transact(): return
	var kind := _raw(site)
	if demand(site,kind) <= 0 or (world.carry.available_to_station(kind) == 0 and world.carry.incoming(site,kind) == 0):
		cancel()
		return
	active = site
	world.carry.visit("work:"+site)

func receive(site: String, kind: String, amount: int) -> bool:
	if active != site or amount <= 0 or amount > demand(site,kind) or world.inventory.carried[kind] < amount: return false
	if not world.carry.take_worksite_receipt(site,kind,amount): return false
	var journal: Dictionary = world.inventory.settlement
	world.inventory.carried[kind] -= amount
	var cue := "spend_"+kind
	if site == "survivor_plot":
		journal.survivor_wood += amount
		journal.survivor_paid = journal.survivor_wood == world.inventory.survivor_cost
		cue = "purchase" if journal.survivor_paid else cue
	else:
		journal.hoppers[kind] += amount
	var target := _goal(site)
	var saved: bool = world.settlement_loop.commit_receipt(cue,target)
	if saved and site == "survivor_plot" and journal.survivor_paid:
		world._event("owl_equip",target)
	refresh()
	return saved
