extends "res://tests/test_integrated_opening.gd"
const Ledger2 = preload("res://opening_ledger.gd")
const Observer = preload("res://tests/indep_paid_pine_observer.gd")

func approach_pine() -> void:
	check(await travel(game.point([-.35,6.])), "walk east of exact pine")
	check(await travel(game.point([-.85,6.])), "walk into original facing/range")
	check(game.resource_tree.can_address(game.actor.global_position,game.tree_facing()), "actual tree gate")

func cut(w0:int,w1:int) -> void:
	for i in 3:
		press(KEY_F)
		await tick(21)
		check(game.ledger.stock.wood == w0 and game.resource_tree.strikes==i+1, "accepted strike, not settlement %d" % (i+1))
	check(await travel(game.point([0.,6.])), "walk outside pine fall sweep")
	for i in 90:
		if game.resource_tree.phase=="credited" or game.persist_blocked:break
		await tick(1)
	check(game.ledger.stock.wood == w1, "exact settled wood balance")

func schema() -> void:
	var canonical: Dictionary = game.ledger.snapshot()
	var state: Dictionary = canonical.duplicate(true)
	state.version = 2
	state.pine_occurrences = Ledger2.MAX_PINE_OCCURRENCES
	state.stock.wood = Ledger2.MAX_PINE_OCCURRENCES
	var l := Ledger2.new()
	check(l.restore(state), "canonical upper-bound v2 accepted")
	check(not l._record_paid_pine("wood-a",Ledger2.MAX_PINE_OCCURRENCES+1,state.receipt) and l.snapshot()==state, "upper-bound overflow fails without mutation")
	for count: Variant in [null, true, "1", 0, -1, 1.5, INF, NAN, Ledger2.MAX_PINE_OCCURRENCES + 1]:
		var wrong := state.duplicate(true)
		wrong.pine_occurrences=count
		check(not l.restore(wrong) and l.snapshot()==state, "malformed occurrence rejected")
	var fake := state.duplicate(true)
	fake.receipt = {}
	check(not l.restore(fake) and l.snapshot()==state,"cannot combine v2 with unpaid receipt")
	check(l.restore(canonical) and l.snapshot()==canonical,"paid v1 reads and removes v2 occurrence")
	check(not l._record_paid_pine("wood-c",1,canonical.receipt),"wrong actual pine source denies")
	check(not l._record_paid_pine("wood-a",2,canonical.receipt),"future cut ID denies")
	check(not l._record_paid_pine("wood-a",1,{"offer":"wrong"}),"wrong receipt denies")
	check(l.snapshot()==canonical,"malformed operations do not change v1 ledger")

func run() -> void:
	game=GAME.instantiate()
	game.set_script(Observer)
	root.add_child(game)
	if not game.bound or not game.persist_requested or game.persist_blocked:
		quit(2)
		return
	await tick(10)
	for id in ["wood-b","wood-c"]:
		check(await travel(game.wood_anchors[id]),"collect exact original wood by walking")
	await approach_pine()
	await cut(2,3)
	await tick(300)
	check(game.resource_tree.phase=="rooted" and game.resource_tree.strikes==0,"existing five-second regeneration")
	# Input rejected before payment must not latch cut eligibility.
	check(await travel(game.point([0.,3.3])),"walk out of pine reach before purchase")
	check(game.ledger.receipt.is_empty() and game.resource_tree.strikes==0,"first renewed tree still uncut without payment")
	press(KEY_F)
	await tick(1)
	check(game.resource_tree.strikes==0 and game._pine_occurrence==0,"out-of-range prepayment attempt is not an accepted strike")
	check(await travel(game.pad_anchor),"normal motion reaches exact purchase")
	check(game.ledger.has_exact_paid_hearth() and game.ledger.stock.wood==0 and game.ledger.snapshot().version==1,"exact purchase remains canonical v1")
	schema()
	check(await travel(game.point([0.,2.])),"walk to South gate from paid camp")
	press(KEY_E)
	await tick(70)
	check(await travel(game.point([0.,6.])),"leave camp through normal gate")
	await approach_pine()
	await cut(0,1)
	check(game.ledger.pine_occurrences==1 and game.ledger.snapshot().version==2,"first accepted postpay cut yields one v2 occurrence")
	var events: Array = game.pine_commit_records
	check(events.size()==1 and game.extra_attempt_rejected,"one commit event, reentrant use denied")
	if events.size()==1:
		var e: Dictionary = events[0]
		check(e.commit and e.visible_before and e.visible_at_return and e.phase_before=="ready_to_credit" and e.phase_at_return=="ready_to_credit", "disk/live publication before the tree hides")
		check(e.disk_matches_live_at_return and not e.disk_unchanged and e.wood_before==0 and e.wood_return==1 and e.stable_receipt,"completed v2 on disk before visual settlement")
	check(not game.resource_tree.get_child(0).is_visible_in_tree() and game.resource_tree.phase=="credited","pine hides only following commit")
	await tick(299)
	check(game.resource_tree.phase=="credited" and game.ledger.stock.wood==1,"still hidden at 299 ticks and no repeat award")
	await tick(1)
	check(game.resource_tree.phase=="rooted" and game.ledger.stock.wood==1,"restored at 300 ticks without award")
	var primary: String = game.__profile().path_join(game.save.PRIMARY)
	var before := FileAccess.get_file_as_bytes(primary)
	var blocked: String = game.__profile().path_join(game.save.STAGING)
	check(DirAccess.make_dir_absolute(blocked)==OK,"disposable test blocks only staging")
	await approach_pine()
	await cut(1,1)
	check(game.persist_blocked and FileAccess.get_file_as_bytes(primary)==before and game.ledger.pine_occurrences==1,"abort preserves live quantity and exact durable prior bytes")
	check(game.resource_tree.phase=="ready_to_credit" and game.resource_tree.get_child(0).is_visible_in_tree(),"aborted candidate does not hide cut at publication boundary")
	check(DirAccess.remove_absolute(blocked)==OK,"remove deliberate staging blocker")
	check(events.size()==2 and not events[1].commit and events[1].disk_unchanged,"only two admitted publication attempts")
	print("INDEPENDENT_COUNT ", checks," failures ",failures)
	quit(1 if failures else 0)
