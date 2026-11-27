extends SceneTree

const HUD = preload("res://field_hud.gd")
const Inventory = preload("res://field_inventory.gd")
const Rules = preload("res://field_settlement.gd")


class Host:
	extends Node
	var inventory := Inventory.new()
	var touch_id := -1


var checks := {}
var host := Host.new()
var hud := HUD.new()


func _initialize() -> void:
	run.call_deferred()


func check(key: String, passed: bool) -> void:
	checks[key] = passed
	if not passed:
		push_error(key)


func run() -> void:
	root.add_child(host)
	host.inventory.configure(Inventory.Progress.offers({}))
	var canvas := CanvasLayer.new()
	host.add_child(canvas)
	canvas.add_child(hud)
	var quality := Button.new()
	hud.add_child(quality)
	root.content_scale_size = Vector2i(720, 720)
	root.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	var balances: Dictionary = Rules.EMPTY.duplicate(true)
	balances.merge(
		{
			"cooked": 5,
			"served": 2,
			"held_meal": 1,
			"worker_meal": 1,
			"processed_wood": 999,
			"processed_stone": 12
		},
		true
	)
	hud.settlement_status(balances, .5)
	hud.set_health(23, 30)
	hud.set_threat(true)
	var counts := {"wood": 109, "stone": 24, "meat": 3, "slate": 1150, "metal": 700, "coal": 6}
	for entry in {
		"cover": Vector2i(360, 840), "inner": Vector2i(492, 546), "landscape": Vector2i(840, 360)
	}:
		root.size = {
			"cover": Vector2i(360, 840),
			"inner": Vector2i(492, 546),
			"landscape": Vector2i(840, 360)
		}[entry]
		for i in 2:
			await process_frame
		hud.field_status(
			counts, "Reinforce storehouse · 80 wood · 60 stone\nApproach the plot to pay"
		)
		hud.position_quality_button(quality, true)
		hud.reflow()
		for i in 2:
			await process_frame
		var safe: Rect2 = hud._safe_rect()
		var center := safe.get_center()
		var all_fit := true
		for control in [
			hud.plate,
			hud.row,
			hud.mineral_row,
			hud.stock_row,
			hud.objective,
			hud.threat_chip,
			quality,
			hud.operation
		]:
			all_fit = (
				all_fit
				and safe.encloses(control.get_global_rect())
				and not control.get_global_rect().has_point(center)
			)
		check(entry + " bounds clear play and respect visible canvas", all_fit)
		var clear_gutter := true
		for cells in [hud.cells, hud.display_goods]:
			for cell in cells.values():
				clear_gutter = (
					clear_gutter
					and (
						cell.art.get_global_rect().end.x + 2.
						< cell.amount.get_global_rect().position.x
					)
				)
		check(entry + " illustrations keep a gap before each quantity", clear_gutter)
		check(
			entry + " no blank stock when a worker is serving",
			hud.outputs.meals.text == "1" and hud.outputs.cash.text == "2" and hud.stock_row.visible
		)
		check(
			entry + " all earned goods have distinct authored icons",
			(
				hud.display_goods.size() == 4
				and (
					hud.display_goods.cash.art.texture.region
					!= hud.display_goods.meals.art.texture.region
				)
			)
		)
		check(
			entry + " purchase card has correct quantities and illustration",
			(
				hud.ticket.costs.size() == 2
				and hud.ticket.costs[0].amount == "80"
				and hud.ticket.ART.has(hud.ticket.heading)
				and not hud.prompt.visible
			)
		)
		check(
			entry + " alert legible over its own surface",
			(
				hud.threat_chip.visible
				and hud.threat_chip.get_global_rect().encloses(hud.threat_text.get_global_rect())
			)
		)
		check(
			entry + " graphics accessible without competing label",
			(
				quality.text.is_empty()
				and quality.accessibility_name.contains("Ultra")
				and quality.size.x >= 82
			)
		)
		check(
			entry + " goal is clear of the graphics switch",
			not quality.get_global_rect().intersects(hud.objective.get_global_rect())
		)
		var stock_message := "Unload beside the storehouse · Next: Reinforce storehouse on the nearby plot\nStored · 1240 wood · 670 stone · 460 meat · 280 coal · 510 slate · 890 metal ore"
		hud.field_status(counts, stock_message)
		check(
			entry + " six typed shelf balances and next upgrade remain readable",
			(
				hud.ticket.costs.size() == 6
				and hud.ticket.next_upgrade == "Reinforce storehouse"
				and hud.ticket.size.y >= hud.ticket.content_height(hud.ticket.size.x)
				and safe.encloses(hud.objective.get_global_rect())
			)
		)
		var last_cost_y: float = hud.ticket.cost_positions(hud.ticket.size.x)[-1].y
		check(entry+" last material clears next-upgrade caption during entrance",
			last_cost_y+26. < hud.ticket.size.y-27.)
		for subject in ["Build cooker", "Build saw bench", "Build quarry drill"]:
			hud.field_status(counts, subject + " · 100 wood · 80 stone")
			check(
				entry + " shows price and reference art for " + subject,
				hud.ticket.ART.has(hud.ticket.heading) and hud.ticket.costs.size() == 2
			)
		hud.field_status(counts, "Progress could not be saved. Restart and retry.")
		check(
			entry + " keeps recovery message visible",
			(
				hud.prompt.visible
				and hud.prompt.text.contains("retry")
				and hud.objective.get_global_rect().encloses(hud.prompt.get_global_rect())
			)
		)
	hud.settlement_status(Rules.EMPTY.duplicate(true), 0.)
	check("unearned finished goods hidden", not hud.stock_row.visible)
	check(
		"worker and player-held meals stay off the tray count", Rules.waiting_meals(balances) == 1
	)
	print("FIELD_HUD ", JSON.stringify(checks))
	host.queue_free()
	await process_frame
	quit(int(checks.values().has(false)))
