extends "res://tests/test_integrated_disposable_opening.gd"
const SFX_FIXTURE = preload("res://tests/sfx_observer.gd")
const PICKUPS = ["wood_pickup:wood-b", "wood_pickup:wood-c", "wood_pickup:wood-a"]
const BUILD = "hearth_build:center-hearth:1"

func report() -> void:
	print("sfx-route checks=", checks, " failures=", failures)
	quit(0 if failures == 0 else 1)

func run() -> void:
	var phases := ["write", "cold", "savefail", "mute"]
	var phase := ""
	for s: String in phases:
		if "--sfx-phase=" + s in OS.get_cmdline_user_args():
			check(phase.is_empty(), "single phase flag")
			phase = s
	if phase.is_empty() or failures:
		quit(2)
		return
	game = SFX_FIXTURE.new()
	game.position = Vector3(2, 1.1, -3)
	game.sfx_muted = phase == "mute"
	root.add_child(game)
	check(game.bound and game.persist_requested and not game.persist_blocked, "exact combined fixture admitted")
	check(game.accepted_cues.is_empty() and game.mixer_intents.is_empty(), "hydrate/publish emits no live cue")
	if failures:
		report()
		return
	var primary: String = game.profile.path_join(STORE.PRIMARY)
	await tick(5)
	if phase == "cold":
		check(game.ledger.collected.size() == 3 and not game.ledger.receipt.is_empty() and game.camp_built.visible, "independent process restored paid baseline")
		var before := FileAccess.get_file_as_bytes(primary)
		check(not before.is_empty(), "verified existing durable receipt")
		check(await travel(game.wood_anchors["wood-b"]), "walk over old pickup after reload")
		check(await travel(game.point([0.0, 6.0])), "walk to south hinge")
		press(KEY_E)
		await tick(70)
		check(game.gates[0].target_open, "ordinary input opens south gate")
		check(await travel(game.pad_anchor), "cross previously paid pad after reload")
		check(not game.fund_opening_receiver("center-hearth", "wood"), "exact paid receiver denies retrigger")
		check(not game._collect_wood_source("wood-b"), "duplicate source denial at ledger boundary")
		check(game.accepted_cues.is_empty() and game.mixer_intents.is_empty(), "cold replay not a live pickup/receipt")
		check(before == FileAccess.get_file_as_bytes(primary), "no duplicate durable mutation")
	else:
		check(game.ledger.collected.is_empty() and not FileAccess.file_exists(primary), "empty exact receipt/ledger start")
		check(not game.fund_opening_receiver("center-hearth", "wood"), "real unfunded distant request denied")
		check(await travel(game.pad_anchor), "actual full approach while unfunded")
		check(game.accepted_cues.is_empty() and not game.camp_built.visible, "unfunded at exact pad is silent")
		check(await travel(game.point([0.0, 6.0])), "return to wood route before funding")
		await earn_wood_through_input()
		check(game.accepted_cues == PICKUPS, "three distinct pickup events match normal accepted wood receipts")
		check(not game._collect_wood_source("wood-b"), "duplicate actual source refused")
		check(not game.fund_opening_receiver("fake", "wood"), "unknown receiver refused")
		check(not game.fund_opening_receiver("center-hearth", "ore"), "wrong actual material refused")
		check(game.accepted_cues == PICKUPS, "failed paths never enqueue cues")
		var prepay := FileAccess.get_file_as_bytes(primary)
		if phase == "savefail":
			check(DirAccess.open(game.profile).make_dir(STORE.STAGING) == OK, "inject real disposable stage write failure")
		check(await travel(game.pad_anchor), "actual full approach while funded")
		await tick(8)
		if phase == "savefail":
			check(game.persist_blocked and not game.camp_built.visible and game.ledger.receipt.is_empty(), "real save denial blocks build publication")
			check(game.ledger.stock.wood == 3 and prepay == FileAccess.get_file_as_bytes(primary), "authority unchanged despite destination reach")
			check(game.accepted_cues == PICKUPS and game.mixer_intents == PICKUPS, "failed durable build stays silent")
		else:
			var both: Array = PICKUPS + [BUILD]
			check(game.camp_built.visible and not game.ledger.receipt.is_empty() and game.ledger.stock.wood == 0, "real paid publication")
			check(game.accepted_cues == both and prepay != FileAccess.get_file_as_bytes(primary), "exact one build event after durable promotion")
			check(not game.fund_opening_receiver("center-hearth", "wood"), "duplicate purchase refused")
			check(game.accepted_cues == both, "held pad and duplicate request don't replay")
			if phase == "mute":
				check(game.mixer_intents.is_empty(), "muted successful pickups and build emit zero mixer intents")
				game.sfx_muted = false
				await tick(8)
				check(game.mixer_intents.is_empty(), "unmute does not replay previously accepted cues")
			else:
				check(game.mixer_intents == both, "unmuted presenter receives distinct pickup and receipt intent once each")
	check(game.adapter_failures == 0, "no unclassified or repeated commit edges")
	print("sfx-route phase=", phase, " accepted=", game.accepted_cues, " mixer_intents=", game.mixer_intents)
	report()
