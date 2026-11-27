extends Node3D
## A short handoff moves one carried unit onto the plot or into a machine hopper.
## Only the handoff requires the carrier's presence. Machines own the unit once it lands.
const Crew = preload("res://field_crew.gd")
const FloorOffer = preload("res://field_offer_floor.gd")
const PLOT_AT := Vector3(-5.5,0,10.9)
var world
var plot
var owl_plot
var last_owl_paid := -1
var active := ""
var nearer_plot := false
var manual_machine := ""
var manual_handoff := {}
var last_paid := -1

func setup(host) -> void:
	world = host
	world.carry.worksite_demand = demand
	world.carry.worksite_land = receive
	world.carry.worksite_goal = _goal
	plot = FloorOffer.new()
	add_child(plot)
	plot.install_custom(world.field_env,"survivor_plot",PLOT_AT,"Rescue survivor",["wood"])
	owl_plot=FloorOffer.new()
	add_child(owl_plot)
	owl_plot.install_custom(world.field_env,Crew.OWL_PLOT,Crew.ROOST_AT,"Befriend owl",["meat"])
	refresh()

func refresh() -> void:
	var journal: Dictionary = world.inventory.settlement
	var survivor_due := Crew.survivor_due(journal,world.inventory.survivor_cost)
	var owl_due := Crew.owl_due(journal)
	plot.visible = world.camp_active and survivor_due > 0
	owl_plot.visible = world.camp_active and owl_due > 0
	plot.title.text = "Hire survivor again" if journal.rescued else "Rescue survivor"
	owl_plot.title.text = "Befriend another owl" if Crew.ever_owned_owl(journal) and owl_due > 0 else "Befriend owl"
	var owl_paid:=Crew.OWL_MEAT-owl_due
	if last_owl_paid!=owl_paid:
		last_owl_paid=owl_paid
		world.field_env.show_costs(owl_plot.price,{"meat":Crew.OWL_MEAT-owl_paid})
		owl_plot.set_fill(float(owl_paid)/Crew.OWL_MEAT)
	var bill := Crew.survivor_bill(journal,world.inventory.survivor_cost)
	if last_paid != survivor_due:
		last_paid = survivor_due
		world.field_env.show_costs(plot.price,{"wood":survivor_due})
		plot.set_fill(1.0-float(survivor_due)/bill)

func machine_distance(kind: String, here: Vector3) -> float:
	if kind not in world.settlement_loop.Rules.KINDS or not world.inventory.is_machine_owned(kind):return INF
	if world.encounters.is_machine_down(kind) or not world.field_env.is_inside_camp(here):return INF
	var floor_point := Vector2(here.x,here.z)
	var wall:Rect2 = world.lakeshore._footprint(0.) if kind=="meat" else world.processors._rect(kind,0.)
	return INF if wall.has_point(floor_point) else world.Reach.distance_to_rect(floor_point,wall)

func can_operate(kind: String) -> bool:
	return not world.snow_truck.mounted and world.settlement_loop.can_transact() and machine_distance(kind,world.actor.global_position)<=world.Reach.NEAR

func automatic_handoff(kind: String) -> bool:
	return not manual_handoff.has(kind)

func toggle_handoff(kind: String) -> void:
	if not world.inventory.is_machine_owned(kind):return
	if not manual_handoff.erase(kind):
		manual_handoff[kind]=true
		if active==kind:cancel()
	if manual_machine==kind:manual_machine=""

func request_machine(kind: String) -> bool:
	if not can_operate(kind) or world.carry.available_to_station(kind)<=0 or not world.settlement_loop.available_to_feeder(kind):return false
	manual_machine=kind
	return true

func _site() -> String:
	var here: Vector3 = world.actor.global_position
	if plot.visible and world.Reach.plot_distance(plot,here) <= world.Reach.NEAR:
		return "survivor_plot"
	if owl_plot.visible and world.Reach.plot_distance(owl_plot,here)<=world.Reach.NEAR:
		return Crew.OWL_PLOT
	if not world.inventory.complete(world.Progress.SECOND) or not world.field_env.is_inside_camp(here): return ""
	if not manual_machine.is_empty() and machine_distance(manual_machine,here)<=world.Reach.NEAR:
		if world.carry.available_to_station(manual_machine)>0 or world.carry.incoming(manual_machine,manual_machine)>0:return manual_machine
	# Adjacent worktables may both be in reach. Finish an in-flight handoff
	# first, then prefer a compatible open inlet before comparing wall distance.
	var best := ""
	var best_rank := 4
	var best_distance := INF
	for kind: String in world.settlement_loop.Rules.KINDS:
		if not automatic_handoff(kind):continue
		var distance := machine_distance(kind,here)
		if distance > world.Reach.NEAR: continue
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
	if site == Crew.OWL_PLOT: return world.Reach.plot_distance(owl_plot,at)
	var rect: Rect2 = world.lakeshore._footprint(0.) if site == "meat" else world.processors._rect(site,0.)
	return world.Reach.distance_to_rect(Vector2(at.x,at.z),rect)

func _raw(site: String) -> String:
	if site == Crew.OWL_PLOT:return "meat"
	return "wood" if site == "survivor_plot" else site

func _goal(site: String) -> Vector3:
	if site == "survivor_plot": return plot.global_position + Vector3.UP*.12
	if site == Crew.OWL_PLOT: return owl_plot.global_position + Vector3.UP*.12
	if site == "meat": return world.lakeshore.cooker_input.global_position
	return world.processors.input_position(site)

func cancel() -> void:
	if not active.is_empty(): world.carry.cancel_worksite(active)
	active = ""

func demand(site: String, kind: String) -> int:
	if kind != _raw(site) or not world.settlement_loop.can_transact() or site != _site(): return 0
	var journal: Dictionary = world.inventory.settlement
	if site == "survivor_plot": return Crew.survivor_due(journal,world.inventory.survivor_cost)
	if site == Crew.OWL_PLOT:return Crew.owl_due(journal)
	if world.encounters.is_machine_down(kind): return 0
	return world.settlement_loop.Rules.HOPPER_CAPACITY - int(journal.hoppers[kind]) - int(journal.line_load[kind])

func advance(_dt: float) -> void:
	refresh()
	if not manual_machine.is_empty() and not can_operate(manual_machine):manual_machine=""
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
		Crew.fund_survivor(journal,amount,world.inventory.survivor_cost)
		if Crew.survivor_due(journal,world.inventory.survivor_cost)==0: cue="purchase"
	elif site == Crew.OWL_PLOT:
		Crew.fund_owl(journal,amount)
		cue="purchase" if Crew.owns_owl(journal) else cue
	else:
		journal.hoppers[kind] += amount
	var target := _goal(site)
	var saved: bool = world.settlement_loop.commit_receipt(cue,target)
	if saved and site == Crew.OWL_PLOT and Crew.owns_owl(journal):
		world._event("owl_equip",target)
	refresh()
	return saved
