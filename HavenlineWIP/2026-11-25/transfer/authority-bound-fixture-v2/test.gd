extends SceneTree

const Coordinator = preload("res://coordinator.gd")
var checks := 0
var failures := 0
var samples := {}

func _initialize() -> void:
	call_deferred("run")

func ck(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL ",description)

func request(ticket: String, units: int) -> Dictionary:
	return {"receiver":"receiver_test","material":"wood","ticket":ticket,"units":units}

func fresh() -> Node3D:
	var c := Coordinator.new()
	root.add_child(c)
	return c

func timing(label: String, intervals: Array[int]) -> void:
	var c := fresh()
	var ticket := "committed-" + label
	var initial: Dictionary = c.state_snapshot()
	var unaffected: Array = c.presentation_snapshot().other
	var arrivals := []
	var ends := []
	c.arrived.connect(func(ob_ticket, ordinal, due, observed, position):
		var view: Dictionary = c.presentation_snapshot()
		arrivals.append([ob_ticket,ordinal,due,observed,position, view.points[ordinal][1]])
		ck(c.state_snapshot().ledger.receipts.has(ob_ticket), "receipt already committed at observation")
	)
	c.completed.connect(func(ob_ticket, due, observed): ends.append([ob_ticket,due,observed]))
	ck(not c.has_method("admit"), "no public cue import on the coordinator")
	ck(not c.sample_elapsed(ticket,1,285000) and c.presentation_snapshot().points.is_empty(), "precommit sampling rejected")
	var false_envelope := request(ticket,52)
	false_envelope["committed_receipts"] = {ticket:["receiver_test","wood",52]}
	false_envelope["seq"] = 400
	ck(not c.submit_intent(1,false_envelope) and c.state_snapshot() == initial, "fabricated proof envelope cannot start a presentation")
	var detached: Dictionary = c.state_snapshot()
	detached.ledger.receipts[ticket] = ["receiver_test","wood",52]
	detached.sequence = 400
	ck(c.state_snapshot()==initial and not c.sample_elapsed(ticket,1,285000), "mutating read snapshot cannot create commit")
	ck(c.submit_intent(1,request(ticket,52)), "meaningful planned intent")
	var committed: Dictionary = c.state_snapshot()
	ck(committed.sequence == 1 and committed.ledger.carry.wood == 0 and committed.ledger.receivers.receiver_test.wood == 52 and committed.ledger.carry.red_test_only == 7, "commit then local presentation")
	var starts: Array = c.presentation_snapshot().points
	ck(starts.size() == 52, "52 actual transforms")
	ck(not c.submit_intent(1,request(ticket,52)) and not c.sample_elapsed(ticket,0,1), "duplicates and stale epoch denied while active")
	var frame := 0
	var elapsed := 0
	ck(c.sample_elapsed(ticket,1,elapsed), "initial zero sample")
	while elapsed < 903000 and ends.is_empty():
		elapsed += intervals[frame%intervals.size()]
		ck(c.sample_elapsed(ticket,1,elapsed), "addressed sample accepted")
		frame += 1
	ck(arrivals.size() == 52 and ends.size()==1, "exactly one set of arrivals plus completion")
	if arrivals.size() != 52 or ends.size() != 1:
		return
	var names := {}
	var points: Array = c.presentation_snapshot().points
	for i in range(52):
		var event: Array = arrivals[i]
		names[points[i][0]] = true
		ck(event[0]==ticket and event[1]==i and event[2]==285000 + i*11500 and event[3] >= event[2], "unique ordered event")
		ck(event[4].is_equal_approx(event[5]) and not event[4].is_equal_approx(starts[i][1]),"actual endpoint before event")
	var peak: int = c.presentation_snapshot().peak
	ck(names.size()==52 and peak==25, "unique nodes and actual overlap bound")
	ck(arrivals[0][3]<=301000 and arrivals[51][3]>=835000 and arrivals[51][3]<=903000, "observed proposal cadence")
	ck(ends[0] == [ticket,871500,arrivals[51][3]], "completion aligned to final endpoint")
	ck(not c.sample_elapsed(ticket,1,1000000) and not c.submit_intent(1,request(ticket,52)), "no completed replay")
	ck(c.state_snapshot()==committed and c.presentation_snapshot().other==unaffected, "presentation never changes accounting or other row")
	var fake_after := request("invented", 1)
	fake_after["committed_receipts"] = {"invented":["receiver_test","wood",1]}
	fake_after["seq"] = 401
	ck(not c.submit_intent(1,fake_after) and c.state_snapshot()==committed and ends.size()==1, "former fresh fabricated proof replay ignored")
	samples[label] = {"first_scheduled_us":arrivals[0][2],"first_observed_us":arrivals[0][3],"last_scheduled_us":871500,"last_observed_us":arrivals[51][3],"peak_in_flight":peak}
	c.queue_free()

func queue_and_replace() -> void:
	var c := fresh()
	var arrivals := []
	var ends := []
	var invalid_pre := request("A", 0)
	ck(not c.submit_intent(1,invalid_pre), "invalid typed intent denied before commit")
	invalid_pre = request("A",8)
	invalid_pre.material = "red_test_only"
	ck(not c.submit_intent(1,invalid_pre), "non-target row cannot enqueue")
	invalid_pre = request("A",8)
	invalid_pre.receiver = "elsewhere"
	ck(not c.submit_intent(1,invalid_pre), "different receiver cannot enqueue")
	c.arrived.connect(func(ticket, ordinal, _due, _obs, _pos):
		arrivals.append([ticket,ordinal])
		if ticket=="A" and ordinal==0:
			var before: Dictionary = c.state_snapshot()
			ck(not c.submit_intent(1,request("reentrant",1)) and c.state_snapshot()==before, "callback cannot reenter commit")
			ck(not c.sample_elapsed("A",1,999999), "callback cannot reenter clock")
			ck(c.reattach_view(1),"reattach invalidates visuals even during event dispatch")
	)
	c.completed.connect(func(ticket, due, seen): ends.append([ticket,due,seen]))
	ck(c.submit_intent(1,request("A",8)) and c.submit_intent(1,request("B",9)), "two independent commits while one presentation is active")
	var snapshot: Dictionary = c.state_snapshot()
	ck(snapshot.sequence==2 and snapshot.ledger.carry.wood==35 and snapshot.ledger.receivers.receiver_test.wood==17 and c.presentation_snapshot().active=="A", "queued presentation after own commit")
	ck(c.sample_elapsed("A",1,1000000) and arrivals==[["A",0]] and ends.is_empty(), "callback reattach suppresses obsolete dispatched effects")
	ck(c.state_snapshot().ledger==snapshot.ledger and c.presentation_snapshot().points.is_empty(), "reattach only drops transient visuals, never receipts")
	ck(not c.submit_intent(1,request("C",1)) and not c.reattach_view(1) and not c.submit_intent(2,request("B",9)), "old epoch and old receipt cannot reanimate")
	ck(c.submit_intent(2,request("C",3)) and c.submit_intent(2,request("D",2)), "fresh committed queue")
	ck(not c.sample_elapsed("A",1,1000000) and not c.sample_elapsed("D",2,1000000), "old or not-started cue can't advance active clock")
	ck(c.sample_elapsed("C",2,1000000) and c.presentation_snapshot().active=="D", "completion opens queued committed visual")
	ck(c.sample_elapsed("D",2,1000000) and arrivals==[["A",0],["C",0],["C",1],["C",2],["D",0],["D",1]], "ordered queue effects exactly once")
	ck(ends==[["C",308000,1000000],["D",296500,1000000]], "one completed signal per admitted and completed cue; coarse shows late")
	ck(not c.sample_elapsed("C",2,1000000) and not c.sample_elapsed("D",2,1000000), "completed queues cannot be driven again")
	var final: Dictionary = c.state_snapshot()
	ck(final.sequence==4 and final.ledger.carry.wood==30 and final.ledger.carry.red_test_only==7 and final.ledger.receivers.receiver_test.wood==22 and final.ledger.receipts.size()==4,"four legal commits remain, canceled presentation not rollback")
	c.queue_free()


func visual_callback_guard() -> void:
	var c := fresh()
	var called := {}
	var listener := func(n):
		if n.name == &"Piece_00":
			var current: Dictionary = c.state_snapshot()
			called["seen"] = true
			ck(current.sequence==1 and current.ledger.receipts.has("base"),"scene callback sees already committed receipt")
			ck(not c.submit_intent(1,request("during-child",1)), "scene-node callback cannot recursively commit while creating pieces")
			ck(not c.reattach_view(1) and not c.sample_elapsed("base",1,999999),"scene-node callback cannot reset or advance partially built visual")
	node_added.connect(listener)
	ck(c.submit_intent(1,request("base",2)), "base intent with node callback")
	node_added.disconnect(listener)
	ck(called.has("seen") and c.state_snapshot().sequence==1 and c.presentation_snapshot().points.size()==2,"callback didn't duplicate visual or change commit")
	c.queue_free()

func run() -> void:
	var not_ready := Coordinator.new()
	ck(not not_ready.submit_intent(1,request("premature",1)) and not not_ready.reattach_view(1),"unattached coordinator rejects intent/reattach")
	not_ready.free()
	timing("30Hz",[33333,33333,33334])
	timing("60Hz",[16667,16667,16666])
	timing("120Hz",[8333,8333,8334])
	timing("jitter",[10000,21000,7000,29000,11000,16000])
	queue_and_replace()
	visual_callback_guard()
	print(JSON.stringify({"status":"PASS" if failures==0 else "FAIL","checks":checks,"failures":failures,"timing":samples}))
	quit(0 if failures==0 else 1)
