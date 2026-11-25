extends SceneTree
const Store = preload("res://store.gd")
const Commit = preload("res://commit_fixture.gd")
const Planner = preload("res://planner_upstream.gd")
const ORIGINAL := "op-52"
const NEW := "op-52-fresh"
var checks := 0
var failures := 0

func _initialize() -> void:
	call_deferred("run")

func ck(ok: bool, name: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("FAIL: ",name)

func summary(phase: String, shape := {}) -> void:
	print(JSON.stringify({"phase":phase,"pid":OS.get_process_id(),"checks":checks,"failures":failures,"evidence":shape}))

func request(ticket: String, units := 52) -> Dictionary:
	return {"receiver":Store.RECEIVER,"material":Store.MATERIAL,"ticket":ticket,"units":units}

func expected(old: Dictionary, ticket: String) -> Dictionary:
	# Hand-write expected result, independent of the candidate planner/state commit path.
	var next := old.duplicate(true)
	next.seq += 1
	next.ledger.carry[Store.MATERIAL] -= 52
	next.ledger.receivers[Store.RECEIVER][Store.MATERIAL] += 52
	next.ledger.receipts[ticket] = [Store.RECEIVER,Store.MATERIAL,52]
	return next

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2 or args[0] not in ["writer-before","writer-after","reader-before","reader-after"]:
		ck(false,"exact fixture cut phase and disposable path required")
		summary("invalid")
		quit(1)
		return
	var phase := args[0]
	var cut := "before" if phase.ends_with("before") else "after"
	var tx := Commit.new()
	ck(tx.store.configure(args[1]),"valid explicitly marked, disjoint disposable path")
	if failures:
		summary(phase)
		quit(1)
		return
	var cues := []
	tx.cue_emitted.connect(func(cue): cues.append(cue))
	var old := Store.initial()
	var once := expected(old,ORIGINAL)
	var twice := expected(once,NEW)
	var old_raw := Store.encode(old)
	var once_raw := Store.encode(once)
	var before_path: PackedByteArray
	var staged_path: PackedByteArray

	if phase.begins_with("writer"):
		ck(tx.seed() and tx.snapshot() == old and tx.store.bytes(Store.PRIMARY) == old_raw,"seed exact old primary and in-memory ledger")
		ck(tx.submit(request(ORIGINAL),cut) == "cut","stop after exactly requested filesystem boundary")
		before_path = tx.store.bytes(Store.PRIMARY)
		staged_path = tx.store.bytes(Store.STAGE)
		ck(tx.snapshot() == old and cues.is_empty(),"no memory publication or cue while waiting at cut")
		ck(before_path == (old_raw if cut == "before" else once_raw),"exact primary at cut")
		ck(staged_path == once_raw if cut == "before" else staged_path.is_empty(),"exact stage presence at cut")
		ck(tx.store.load_primary() == (old if cut == "before" else once),"native read-back decodes correct primary")
		summary(phase,{"primary":Store.digest(before_path),"stage":Store.digest(staged_path) if not staged_path.is_empty() else null,"cues":cues.size()})
		if failures:
			quit(1)
			return
		if not tx.store.signal_cut_ready("%d %s\n" % [OS.get_process_id(),phase]):
			quit(2)
			return
		while true:
			await create_timer(1.0).timeout
		return

	before_path = tx.store.bytes(Store.PRIMARY)
	staged_path = tx.store.bytes(Store.STAGE)
	ck(before_path == (old_raw if cut == "before" else once_raw) and (staged_path == once_raw if cut == "before" else staged_path.is_empty()),"new process sees exact primary and expected orphan")
	ck(tx.cold_open() and tx.snapshot() == (old if cut == "before" else once),"cold load uses only exact primary")
	ck(cues.is_empty() and tx.store.bytes(Store.PRIMARY) == before_path and tx.store.bytes(Store.STAGE) == staged_path,"cold load does not replay, promote, rewrite or remove anything")
	ck(Planner.project_rows(tx.snapshot().ledger,[Store.MATERIAL,Store.OTHER]) == [[Store.MATERIAL,104 if cut=="before" else 52],[Store.OTHER,7]], "typed quantities and row order retained")

	if cut == "before":
		ck(tx.submit(request(ORIGINAL)) == "committed","legitimate original ticket retry after stage-only crash")
		ck(tx.snapshot() == once and tx.store.bytes(Store.PRIMARY) == once_raw and tx.store.bytes(Store.STAGE).is_empty(), "orphan staged state replaced by exactly one legal promotion")
		ck(cues == [[ORIGINAL,Store.RECEIVER,Store.MATERIAL,52]],"one cue for actual fresh retry only")
		ck(tx.submit(request(ORIGINAL,1)) == "denied" and tx.store.bytes(Store.PRIMARY) == once_raw and tx.store.bytes(Store.STAGE).is_empty(),"completed retry ticket cannot reapply modified payload")
		ck(cues.size() == 1 and tx.snapshot() == once,"replayed intent leaves state alone")
	else:
		ck(tx.submit(request(ORIGINAL)) == "denied" and tx.submit(request(ORIGINAL,1)) == "denied","old ticket and changed payload rejected after cold promote")
		ck(cues.is_empty() and tx.snapshot() == once and tx.store.bytes(Store.PRIMARY) == once_raw and tx.store.bytes(Store.STAGE).is_empty(),"replays cannot re-debit, re-credit, emit cue or write")
		ck(tx.submit(request(NEW)) == "committed","fresh equivalent ticket stays legal when trusted fixture has stock")
		ck(tx.snapshot() == twice and tx.store.bytes(Store.PRIMARY) == Store.encode(twice) and tx.store.bytes(Store.STAGE).is_empty(),"fresh exact new snapshot and typed debit-credit")
		ck(cues == [[NEW,Store.RECEIVER,Store.MATERIAL,52]],"only new ticket publishes a cue")
	ck(tx.snapshot().ledger.carry[Store.OTHER] == 7,"other row untouched at terminal state")
	summary(phase,{"primary_before_load":Store.digest(before_path),"primary_after_attempt":Store.digest(tx.store.bytes(Store.PRIMARY)),"incoming_stage":Store.digest(staged_path) if not staged_path.is_empty() else null,"cues":cues,"final_seq":tx.snapshot().get("seq",-1)})
	quit(0 if failures == 0 else 1)
