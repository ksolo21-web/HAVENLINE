extends RefCounted
const Store = preload("res://store.gd")
const Planner = preload("res://planner_upstream.gd")
signal cue_emitted(cue: Array)
var store := Store.new()
var _committed := {}
var _policy := {Store.RECEIVER:{"enabled":true,"limits":{Store.MATERIAL:104}}}

func seed() -> bool:
	if not store.bytes(Store.PRIMARY).is_empty() or not store.bytes(Store.STAGE).is_empty():
		return false
	var state := Store.initial()
	if not store.stage(state) or not store.promote():
		return false
	_committed = state
	return true

func cold_open() -> bool:
	_committed = store.load_primary()
	return not _committed.is_empty() # No cue publication on cold open.

func snapshot() -> Dictionary:
	return _committed.duplicate(true)

func submit(request: Dictionary, cut := "") -> String:
	if _committed.is_empty() or cut not in ["","before","after"]:
		return "refused"
	var plan := Planner.plan_transfer(_committed.ledger,[Store.MATERIAL,Store.OTHER],_policy,Store.RECEIVER,request)
	if plan.is_empty():
		return "denied"
	var next := {"seq":_committed.seq+1,"ledger":plan.next_state}
	if not store.stage(next):
		return "failed"
	if cut == "before":
		return "cut" # Harness waits for real external process termination.
	if not store.promote():
		return "failed"
	if cut == "after":
		return "cut" # Disk committed; no synthetic normal-path receipt or cue emitted.
	_committed = next
	cue_emitted.emit(plan.cue_after_commit.duplicate(true))
	return "committed"
