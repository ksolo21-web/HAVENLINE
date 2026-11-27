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
	if world.lakeshore.at_cooker(here): return "meat"
	return world.processors.at_station(here)

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
	return world.settlement_loop.Rules.HOPPER_CAPACITY - int(journal.hoppers[kind])

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
