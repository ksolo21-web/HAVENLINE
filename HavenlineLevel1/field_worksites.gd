extends Node3D
## A short handoff moves one carried unit onto the plot or into a machine hopper.
## Only the handoff requires the carrier's presence. Machines own the unit once it lands.
const FloorOffer = preload("res://field_offer_floor.gd")
const PLOT_AT := Vector3(-5.5,0,10.9)
const PLOT_SECONDS := .42
const LOAD_SECONDS := .32
var world
var plot
var flight: Node3D
var active := ""
var elapsed := 0.0
var origin := Vector3.ZERO
var last_paid := -1

func setup(host) -> void:
	world = host
	plot = FloorOffer.new()
	add_child(plot)
	plot.install_custom(world.field_env,"survivor_plot",PLOT_AT,"Rescue survivor",["wood"])
	refresh()

func refresh() -> void:
	var journal: Dictionary = world.inventory.settlement
	plot.visible = world.camp_active and not journal.survivor_paid
	if last_paid != int(journal.survivor_wood):
		last_paid = int(journal.survivor_wood)
		world.field_env.show_costs(plot.price,{"wood":2-last_paid})
		plot.ink.set_shader_parameter("paid",last_paid / 2.0)

func _site() -> String:
	var here: Vector3 = world.actor.global_position
	if world.camp_active and not world.inventory.settlement.survivor_paid and here.distance_squared_to(PLOT_AT) <= .94*.94:
		return "survivor_plot"
	if not world.inventory.complete(world.Progress.SECOND): return ""
	if world.lakeshore.at_cooker(here): return "meat"
	return world.processors.at_station(here)

func _raw(site: String) -> String:
	return "wood" if site == "survivor_plot" else site

func _goal() -> Vector3:
	if active == "survivor_plot": return plot.global_position + Vector3.UP*.12
	if active == "meat": return world.lakeshore.cooker_input.global_position
	return world.processors.input_position(active)

func _duration() -> float:
	return PLOT_SECONDS if active == "survivor_plot" else LOAD_SECONDS

func cancel() -> void:
	if active.is_empty(): return
	world.carry.show_station_transfer("")
	if is_instance_valid(flight):
		flight.visible = false
		flight.queue_free()
	flight = null
	active = ""
	elapsed = 0.0

func _can_load(site: String) -> bool:
	if site.is_empty() or not world.settlement_loop.can_transact(): return false
	if site != "survivor_plot" and not world.settlement_loop.available_to_feeder(site): return false
	return world.carry.available_to_station(_raw(site)) > 0

func advance(dt: float) -> void:
	refresh()
	var site := _site()
	if active != site: cancel()
	if not _can_load(site):
		cancel()
		return
	var kind := _raw(site)
	if active.is_empty():
		active = site
		origin = world.carry.show_station_transfer(kind)
		flight = world.FieldArt.make(kind)
		add_child(flight)
	elapsed += dt
	var fraction := clampf(elapsed / _duration(),0,1)
	flight.global_position = origin.lerp(_goal(),fraction) + Vector3.UP*.40*sin(fraction*PI)
	if elapsed >= _duration(): finish(site)

func finish(site: String) -> bool:
	if active.is_empty() or active != site or site != _site() or elapsed < _duration() or not _can_load(site):
		return false
	var raw := _raw(site)
	var target := _goal()
	cancel()
	var journal: Dictionary = world.inventory.settlement
	world.inventory.carried[raw] -= 1
	var cue := "spend_"+raw
	if site == "survivor_plot":
		journal.survivor_wood += 1
		journal.survivor_paid = journal.survivor_wood == 2
		cue = "purchase" if journal.survivor_paid else cue
	else:
		journal.hoppers[raw] += 1
	var saved: bool = world.settlement_loop.commit_receipt(cue,target)
	refresh()
	return saved
