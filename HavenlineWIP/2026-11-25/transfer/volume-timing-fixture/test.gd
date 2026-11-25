extends SceneTree
const Presenter = preload("res://presenter.gd")
const Planner = preload("res://planner_upstream.gd")
const ROWS = ["wood", "red_test_only"]
var checks := 0
var bad := 0
var report := {}

func _initialize() -> void:
	call_deferred("run")

func ck(ok: bool, msg: String) -> void:
	checks += 1
	if not ok:
		bad += 1
		printerr("FAIL ", msg)

func setup(ticket: String) -> Dictionary:
	var before := {"carry":{"wood":52,"red_test_only":7}, "receivers":{"receiver_test":{"wood":0}}, "receipts":{}}
	var policy := {"receiver_test":{"enabled":true,"limits":{"wood":52}}}
	var plan: Dictionary = Planner.plan_transfer(before, ROWS, policy, "receiver_test", {"receiver":"receiver_test","material":"wood","ticket":ticket,"units":52})
	ck(not plan.is_empty(), "fixture comes from exact planner")
	var starts: Array[Vector3] = []
	var finishes: Array[Vector3] = []
	for k in range(52):
		starts.append(Vector3(-2.0, 1.0 + (51-k)*.035, 0.0))
		finishes.append(Vector3(2.0 + (k%8)*.035, (k/8)*.035, 0.0))
	return {"pre":before, "cue":plan.cue_after_commit, "committed":plan.next_state, "start":starts, "end":finishes}

func add_view() -> Node3D:
	var p := Presenter.new()
	root.add_child(p)
	return p

func cadence(label: String, step_pattern: Array[int]) -> void:
	var p := add_view()
	var data := setup("ticket-" + label)
	var ledger: Dictionary = data.committed
	var frozen := ledger.duplicate(true)
	var row: Node3D = Node3D.new()
	root.add_child(row)
	row.position = Vector3(-2, 1, -1)
	for k in range(7):
		var child := Node3D.new()
		row.add_child(child)
		child.position.y = k * .035
	var row_state := row.get_children().map(func(n): return n.transform)
	var events := []
	var finished := []
	var positions_match := []
	p.arrived.connect(func(ticket, ordinal, due, seen, position):
		events.append([ticket,ordinal,due,seen,position])
		positions_match.append(p.get_child(ordinal).position.is_equal_approx(data.end[ordinal])))
	p.completed.connect(func(ticket, due, seen): finished.append([ticket,due,seen]))
	ck(p.bind(1, 100, "receiver_test", "wood"), "valid binding")
	ck(not p.admit(data.cue, data.pre.receipts, 1, 101, data.start, data.end), "uncommitted cue rejected")
	ck(p.admit(data.cue, ledger.receipts, 1, 101, data.start, data.end), "committed cue starts")
	ck(p.get_child_count() == 52 and p.get_children().map(func(n): return n.name).size() == 52, "52 actual nodes")
	ck(not p.admit(data.cue, ledger.receipts, 1, 101, data.start, data.end), "same ticket while active")
	ck(p.sample_elapsed(data.cue[0],1,0), "zero sample")
	var elapsed := 0
	var frame := 0
	var last_position: Vector3 = p.get_child(0).position
	var saw_motion := false
	while elapsed < 900000 and finished.is_empty():
		elapsed += step_pattern[frame % step_pattern.size()]
		if p.sample_elapsed(data.cue[0],1,elapsed) and not last_position.is_equal_approx(p.get_child(0).position):
			saw_motion = true
		frame += 1
	ck(saw_motion, "scene nodes changed position")
	ck(events.size() == 52 and finished.size() == 1, "52 landings and one completion")
	var names := {}
	for i in range(events.size()):
		var e: Array = events[i]
		ck(e[0] == data.cue[0] and e[1] == i and e[2] == Presenter.FLIGHT_US+i*Presenter.STEP_US and e[3] >= e[2], "exact ordered unique event")
		ck(positions_match[i] and e[4].is_equal_approx(data.end[i]), "endpoint existed before observed arrival")
		names[p.get_child(i).name] = true
	ck(names.size() == 52 and p.active_peak <= Presenter.MAX_IN_FLIGHT and p.active_peak > 1, "bounded overlapping unique flyers")
	ck(events[0][3] <= 301000, "honest sampled first marker")
	ck(finished[0][1] >= 835000 and finished[0][1] <= 903000 and finished[0][2] <= 903000, "completion bracket")
	ck(finished[0][2] == events[51][3], "completion after last observed arrival")
	ck(ledger == frozen and row.get_children().map(func(n): return n.transform) == row_state and ledger.carry.red_test_only == 7, "unselected visual row and committed ledger unchanged")
	ck(not p.sample_elapsed(data.cue[0],1,elapsed) and not p.admit(data.cue, ledger.receipts, 1, 102, data.start, data.end), "no post-complete sample or replay")
	report[label] = {"first_due_us":events[0][2],"first_observed_us":events[0][3],"last_due_us":events[51][2],"last_observed_us":events[51][3],"sampled_peak":p.active_peak,"sample_count":frame+1}
	p.queue_free()
	row.queue_free()

func replacement() -> void:
	var p := add_view()
	var a := setup("cut")
	var b := setup("replacement")
	var arrivals := []
	var completions := []
	p.arrived.connect(func(t,i,_due,_seen,_pos):
		arrivals.append([t,i])
		if t == "cut" and i == 0:
			ck(not p.sample_elapsed("cut",11,999999), "reentrant sampling denied while dispatching")
			ck(p.bind(12,403,"receiver_test","wood"), "new epoch cancels during dispatch"))
	p.completed.connect(func(t,d,o): completions.append([t,d,o]))
	ck(p.bind(11,400,"receiver_test","wood"), "initial")
	ck(not p.admit([a.cue[0], "receiver_test", "red_test_only",52],a.committed.receipts,11,401,a.start,a.end), "wrong material")
	ck(not p.admit([a.cue[0], "other_receiver","wood",52],a.committed.receipts,11,401,a.start,a.end), "wrong receiver")
	ck(not p.admit([a.cue[0], "receiver_test","wood",51],a.committed.receipts,11,401,a.start.slice(0,51),a.end.slice(0,51)), "wrong amount")
	ck(not p.admit(a.cue,a.committed.receipts,10,401,a.start,a.end), "stale binding")
	ck(not p.admit(a.cue,a.committed.receipts,11,400,a.start,a.end), "at watermark")
	ck(not p.admit(a.cue,{"cut":["receiver_test","wood",52.0]},11,401,a.start,a.end), "untyped receipt cannot animate")
	ck(p.admit(a.cue,a.committed.receipts,11,401,a.start,a.end), "first committed ticket")
	ck(not p.bind(11,401,"receiver_test","wood"), "same binding cannot replace active cue")
	ck(not p.bind(12,400,"receiver_test","wood"), "new generation cannot lower committed floor")
	ck(p.sample_elapsed("cut",11,1234) and not p.sample_elapsed("cut",11,1233), "backward update rejected")
	ck(p.sample_elapsed("cut",11,999999) and arrivals == [["cut",0]] and completions.is_empty() and p.get_child_count() == 0, "obsolete queued markers and completion canceled")
	ck(not p.admit(a.cue,a.committed.receipts,12,404,a.start,a.end), "canceled ticket never replays")
	ck(not p.admit(b.cue,b.committed.receipts,12,402,b.start,b.end), "previously committed record cannot reanimate")
	ck(p.admit(b.cue,b.committed.receipts,12,404,b.start,b.end), "new authorized commit after replacement")
	ck(not p.sample_elapsed("cut",11,1000000) and not p.sample_elapsed("replacement",11,1000000) and not p.sample_elapsed("cut",12,1000000) and arrivals.size() == 1, "stale ticket/epoch clocks cannot advance replacement")
	ck(p.sample_elapsed("replacement",12,1000000), "single coarse skip crosses every due marker")
	ck(arrivals.size() == 53 and completions == [["replacement",871500,1000000]], "coarse frame preserves order/exact analytical due and actual late observation")
	var reopen := add_view()
	ck(reopen.bind(12,404,"receiver_test","wood") and not reopen.admit(b.cue,b.committed.receipts,12,404,b.start,b.end), "fresh view cannot consume old record at externally supplied floor; not OS restart proof")

func run() -> void:
	cadence("30Hz",[33333,33333,33334])
	cadence("60Hz",[16667,16667,16666])
	cadence("120Hz",[8333,8333,8334])
	cadence("jitter",[10000,21000,7000,29000,11000,16000])
	replacement()
	print(JSON.stringify({"status":"PASS" if bad == 0 else "FAIL","checks":checks,"failures":bad,"cadence":report}))
	quit(0 if bad == 0 else 1)
