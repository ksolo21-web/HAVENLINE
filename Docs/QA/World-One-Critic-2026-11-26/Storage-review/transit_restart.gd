extends SceneTree
## Three separately launched Godot processes share only a marked disposable profile.
const Scene = preload("res://field_opening.tscn")
const Rules = preload("res://field_progression.gd")
const Profiles = preload("res://tests/lifecycle_test_profile.gd")
var checks := {}
func _initialize() -> void: call_deferred("run")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var guard := Profiles.Profile.new()
	if not guard.configure(args): quit(2);return
	var game=Scene.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	var ledger = game.inventory
	var carry=game.carry
	checks["disposable profile loaded"] = not game.persist_blocked
	if "--seed-flight" in args:
		for id in [Rules.HEARTH,Rules.FIRST]+Rules.STORAGE:
			for kind in ledger.costs[id]:
				for n in int(ledger.costs[id][kind]):
					assert(ledger.collect("%s-%s-%d"%[id,kind,n],kind))
					assert(ledger.payment(id,kind,false))
		assert(ledger.collect("measured-single-ore","metal"))
		assert(ledger.collect("measured-single-timber","wood"))
		carry.sync()
		checks["launch deposit"] = carry.deposit_storage("metal")
		carry.advance(.14)
		checks["unsettled ore still owned"] = ledger.carried.metal==1 and ledger.stored.metal==0 and carry.flights.size()==1
	elif "--resume-payment" in args:
		checks["interrupted deposit returned to its original lane"] = ledger.carried.metal==1 and ledger.stored.metal==0 and carry.flights.is_empty() and carry.pieces["carry/metal"][0].is_visible_in_tree()
		checks["ore cannot be collected twice"] = not ledger.collect("measured-single-ore","metal")
		checks["deposit retries once"] = carry.deposit_storage("metal")
		carry.advance(.32)
		checks["one ore lands"] = ledger.carried.metal==0 and ledger.stored.metal==1
		checks["launch payment"] = carry.contribute(Rules.SECOND)
		carry.advance(.14)
		checks["unsettled payment still owned"] = ledger.carried.wood==1 and ledger.paid[Rules.SECOND].wood==0 and carry.flights.size()==1
	else:
		checks["interrupted payment restored once"] = ledger.carried.wood==1 and ledger.paid[Rules.SECOND].wood==0 and carry.flights.is_empty()
		checks["finished ore deposit remains stored"] = ledger.carried.metal==0 and ledger.stored.metal==1
		checks["payment retries"] = carry.contribute(Rules.SECOND)
		carry.advance(.32)
		checks["one timber landed, receipt retained"] = ledger.carried.wood==0 and ledger.paid[Rules.SECOND].wood==1 and not ledger.collect("measured-single-timber","wood")
		checks["cannot pay again"] = not carry.contribute(Rules.SECOND)
	game._persist_world()
	print(JSON.stringify(checks))
	await Profiles.drain_field_audio(self,game)
	game.queue_free()
	for tick in 3:await process_frame
	quit(int(false in checks.values()))
