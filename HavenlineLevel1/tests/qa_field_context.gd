extends "res://tests/field_route.gd"

const Director = preload("res://field_context_director.gd")
const Session = preload("res://tests/lifecycle_test_profile.gd")
var checks := {}
var playback: Array[Dictionary] = []
var performance := {}
var proof := OS.get_environment("T07_CONTEXT_PROOF")

func _initialize() -> void:
	if not Session.isolated(self,"res://tests/qa_field_context.gd"):
		run.call_deferred()

func _check(label: String, condition: bool) -> void:
	checks[label] = condition
	if not condition: printerr("T07 failed: ",label)

func _option(kind: String,id: String,point: Vector2,priority := 0.) -> Dictionary:
	return {"kind":kind,"id":id,"position":point,"radius":1.,"eligible":true,
		"capability":Director.KIND_CAPABILITY[kind],"priority":priority,"progress":.3}

func _unit_checks() -> void:
	var runtime := Director.new()
	var at := Vector2.ZERO
	var facing := Vector2.DOWN
	var still := Vector2.ZERO
	var role := "player_lead"
	var near := _option("deposit","a",Vector2(0,.3))
	var twin := _option("deposit","b",Vector2(0,.3))
	var urgent := _option("rescue","survivor",Vector2(.80,.20))
	var goal := func(dt: float, rows: Array,input := Vector2.ZERO,point := Vector2.ZERO) -> Dictionary:
		return runtime.advance(dt,point,facing,input,still,role,rows)
	_check("equal inputs use stable lexical identity",Director.preview(at,facing,role,[twin,near]).id=="a" and Director.preview(at,facing,role,[near,twin]).id=="a")
	var malformed := near.duplicate()
	malformed.position = Vector2.INF
	var double := near.duplicate()
	_check("malformed candidates and both duplicate identities are excluded",Director.preview(at,facing,role,[malformed,near,double,twin]).id=="b")
	var behind := _option("deposit","behind",Vector2(0,-.3))
	_check("facing resolves equal eligible distances",Director.preview(at,facing,role,[behind,twin]).id=="b")
	_check("nonfinite preview fails closed",Director.preview(Vector2.INF,facing,role,[near]).state=="blocked_input")
	_check("ordinary context waits stopped dwell",goal.call(.06,[near,twin]).state=="acquiring")
	var locked: Dictionary = goal.call(.06,[near,twin])
	_check("stopped dwell activates one canonical task",locked.actionable and locked.kind=="deposit" and locked.id=="a" and locked.position==near.position and locked.progress==.3)
	_check("once active, the same request cannot earn dwell twice",goal.call(.025,[near,twin]).activation_credit_seconds==0.)
	twin.position.y = .05
	_check("hold and margin prevent an immediate nearby switch",goal.call(.025,[near,twin]).id=="a")
	_check("urgent rescue preempts ordinary work",goal.call(.015,[near,twin,urgent]).id=="survivor")
	var moving: Dictionary = goal.call(.016,[near,urgent],Vector2.RIGHT)
	_check("nonzero movement blocks an urgent action until stopping",moving.cancelled and not moving.actionable)
	var release := Director.new()
	release.advance(.10,at,facing,still,still,role,[near])
	release.advance(.03,at,facing,still,still,role,[near])
	var edge := release.advance(.016,Vector2(0,-.80),facing,still,still,role,[near])
	_check("release margin keeps the same focus without out-of-range execution",edge.id=="a" and edge.state=="blocked_range" and not edge.actionable)
	_check("focus clears beyond the release radius",release.advance(.016,Vector2(0,-1.35),facing,still,still,role,[near]).kind.is_empty())
	for helper: String in ["core_human_companion","rescued_survivor_helper"]:
		_check(helper+" may deposit but cannot act as the player rescue",Director.preview(at,facing,helper,[urgent,near]).id=="a")
	_check("readiness and presentation independently fail closed",Director.preview(at,facing,role,[near],false,true).state=="blocked_actor" and Director.preview(at,facing,role,[near],true,false).state=="blocked_actor")
	var outsized: Array = []
	for i in Director.MAX_INPUT_CANDIDATES+1:outsized.append(_option("deposit",str(i),at))
	_check("overflow caps evaluation without choosing by insertion order",Director.preview(at,facing,role,outsized).reason=="candidate_input_overflow")
	var priced := twin.duplicate()
	priced["cash"] = 999999
	priced["vip"] = 99
	priced["shop_rank"] = 99999
	priced.position=near.position
	_check("purchase metadata cannot promote a candidate",Director.preview(at,facing,role,[priced,near]).id=="a")
	# Time the selector in the headless run where rendering cannot contend
	# for the same desktop CPU. Native capture covers the actual control flow.
	if DisplayServer.get_name()!="headless":return
	outsized.pop_back()
	var samples: Array[int] = []
	for i in 500:
		var start := Time.get_ticks_usec()
		runtime.advance(.016,at,facing,still,still,role,outsized)
		samples.append(Time.get_ticks_usec()-start)
	samples.sort()
	performance = {"candidate_count":outsized.size(),"sample_count":samples.size(),
		"median_us":samples[250],"p95_us":samples[474],"max_us":samples.back()}
	_check("bounded worst-population context meets the desktop p95 budget",samples[474]<3500)

func _heading(direction: Vector3) -> Vector2:
	var right := camera.global_basis.x
	return Vector2(direction.dot(right),direction.dot(right.cross(Vector3.UP))).normalized()

func _record(beat: String) -> void:
	var row: Dictionary = field.context.descriptor
	playback.append({"beat":beat,"physics_frame":Engine.get_physics_frames(),"id":row.get("id",""),
		"kind":row.get("kind",""),"state":row.get("state",""),"token":row.get("action_token",0),
		"progress":row.get("progress",0.),"actionable":row.get("actionable",false),
		"feet":pt(field.actor.position),"apron_paid":field.inventory.paid.center_hearth.wood,"hud":field.opening_hud.prompt.text})
	if proof.is_empty() or DisplayServer.get_name()=="headless":return
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(proof.path_join(beat+".jpg"),.87)

func _frame(index: int) -> void:
	if proof.is_empty() or DisplayServer.get_name()=="headless":return
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(proof.path_join("payment-%03d.jpg"%index),.81)

func run() -> void:
	_unit_checks()
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	origin = root.get_visible_rect().size*Vector2(.28,.71)
	for frame in 8:await physics_frame
	var at: Vector3 = field.field_env.buy_anchor.global_position
	field.actor.global_position = at + Vector3(-.4,0.,0.)
	var fuel: int = field.inventory.remaining("center_hearth").wood
	for i in fuel: field.inventory.collect("context-foundation-"+str(i),"wood")
	field.carry.sync(true)
	var x_heading := _heading(Vector3.RIGHT)
	steer(x_heading)
	await physics_frame
	await physics_frame
	_check("real moving touch cannot start a plot payment",field.runner_requested_motion and field.context.descriptor.state=="blocked_movement" and field.carry.flights.is_empty())
	await _record("01-moving-near-plot")
	steer(Vector2.ZERO)
	var entered := false
	var observed_flight := false
	var image_index := 0
	for frame in 160:
		await physics_frame
		if frame%4 == 0 and root.size.x<1800:
			await _frame(image_index)
			image_index += 1
		if field.context.descriptor.get("state","")=="active" and not entered:
			entered = true
			await _record("02-stopped-focus")
		if not observed_flight and not field.carry.flights.is_empty():
			observed_flight = true
			await _record("03-paying")
		if field.inventory.complete("center_hearth"):break
	_check("the same accessible joystick approach pays and builds after stopping",entered and observed_flight and field.inventory.complete("center_hearth"))
	for frame in 45:await physics_frame
	_check("one authoritative camp purchase activates and future progress survives",field.camp_active and field.inventory.paid.center_hearth.wood==fuel and not field.persist_blocked)
	_check("only one primary on-foot movement binding remains",field.touch_id < 0 and not field.tree_button.visible)
	field.set_zoom_ratio(2.)
	await _record("04-built-pinch")
	var save: Dictionary = field.inventory.snapshot()
	_check("selection and tokens are ephemeral across persisted progress",not save.has("context") and not save.settlement.has("context") and not save.has("action_token"))
	field.set_physics_process(false)
	field.carry.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	var result := {"checks":checks,"timeline":playback,"performance":performance,
		"viewport":[root.size.x,root.size.y],"renderer":RenderingServer.get_video_adapter_name(),
		"payment_captures":image_index,
		"director_sha256":FileAccess.get_sha256("res://field_context_director.gd"),"adapter_sha256":FileAccess.get_sha256("res://field_context.gd")}
	if not proof.is_empty():
		var out := FileAccess.open(proof.path_join("Context.json"),FileAccess.WRITE)
		out.store_string(JSON.stringify(result,"  "))
		out.close()
	print("T07_CONTEXT ",JSON.stringify(result))
	quit(int(not checks.values().all(func(ok):return ok)))
