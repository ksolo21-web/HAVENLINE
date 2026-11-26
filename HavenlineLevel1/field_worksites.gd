extends Node3D
## Transfer one visible raw unit at a time to the rescue plot or the two workshop feeders.
const FloorOffer = preload("res://field_offer_floor.gd")
const PLOT_AT := Vector3(-5.5,0,10.9)
const PLOT_SECONDS := .42
const PROCESS_SECONDS := 1.45
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
	if world.inventory.complete(world.Progress.SECOND): return world.processors.at_station(here)
	return ""

func _raw(site: String) -> String:
	return "wood" if site == "survivor_plot" else site

func _goal() -> Vector3:
	if active == "survivor_plot": return plot.global_position + Vector3.UP*.12
	return world.processors.input_position(active)

func _duration() -> float:
	return PLOT_SECONDS if active == "survivor_plot" else PROCESS_SECONDS

func cancel() -> void:
	if active.is_empty(): return
	world.carry.show_station_transfer("")
	world.processors.set_active_kind("")
	if is_instance_valid(flight):
		flight.visible = false
		flight.queue_free()
	flight = null
	active = ""
	elapsed = 0.0

func advance(dt: float) -> void:
	refresh()
	var site := _site()
	if active != site: cancel()
	if site.is_empty() or not world.settlement_loop.can_transact(): return
	var kind := _raw(site)
	if world.carry.available_to_station(kind) < 1:
		cancel()
		return
	if active.is_empty():
		active = site
		origin = world.carry.show_station_transfer(kind)
		flight = world.FieldArt.make(kind)
		add_child(flight)
		if site != "survivor_plot":
			world.processors.set_active_kind(site)
			world._event("process_"+kind,world.processors.input_position(site))
	elapsed += dt
	var t := clampf(elapsed/minf(.34,_duration()),0,1)
	flight.global_position = origin.lerp(_goal(),t) + Vector3.UP*.40*sin(t*PI)
	if elapsed >= _duration(): finish(site)

func finish(site: String) -> bool:
	if active.is_empty() or active != site or site != _site() or elapsed < _duration() or not world.settlement_loop.can_transact():
		return false
	var raw := _raw(site)
	if world.carry.available_to_station(raw) < 1: return false
	var target := _goal()
	cancel()
	var journal: Dictionary = world.inventory.settlement
	world.inventory.carried[raw] -= 1
	var cue := "process_done"
	if site == "survivor_plot":
		journal.survivor_wood += 1
		journal.survivor_paid = journal.survivor_wood == 2
		cue = "purchase" if journal.survivor_paid else "spend_wood"
	else:
		journal["processed_"+site] += 1
		target = world.processors.output_position(site)
	var saved: bool = world.settlement_loop.commit_receipt(cue,target)
	refresh()
	world.processors.sync_outputs()
	return saved
