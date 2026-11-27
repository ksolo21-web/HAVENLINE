extends SceneTree

var field
var camera: Camera3D

func touch(id:int,pos:Vector2,pressed:bool)->void:
	var e:=InputEventScreenTouch.new()
	e.index=id
	e.position=pos
	e.pressed=pressed
	root.push_input(e,true)


## Uses both actual workshop menu input and the normal physical transfer path.

const Store = preload("res://field_save.gd")
var checks := {}

func _initialize() -> void:
	run.call_deferred()

func verify(label: String, condition: bool) -> void:
	checks[label] = condition
	if not condition:
		print("WORKSHOP FAILURE ",label)

func wait_ticks(ticks: int) -> void:
	for tick in ticks:
		await physics_frame

func tap(control: Control) -> bool:
	if not is_instance_valid(control) or not control.is_visible_in_tree():
		return false
	var rect := control.get_global_rect()
	if not root.get_visible_rect().encloses(rect):
		return false
	touch(5,rect.get_center(),true)
	await process_frame
	touch(5,rect.get_center(),false)
	await process_frame
	return true

func command(id: String) -> bool:
	var dock = field.opening_hud.camp_dock
	for pair in dock.commands:
		if pair[1] == id:
			return await tap(pair[0])
	return false

func workshop(kind: String) -> bool:
	var dock = field.opening_hud.camp_dock
	if not await tap(dock.tabs["Camp"]): return false
	if not await command("workshops"): return false
	return await command("workshop:"+kind)

func run() -> void:
	if not Store.Profile.new().configure(OS.get_cmdline_user_args()):
		quit(2)
		return
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene = field
	camera = field.camera
	await wait_ticks(5)
	var dock = field.opening_hud.camp_dock
	var works = field.settlement_loop.works
	var journal: Dictionary = field.inventory.settlement
	var product: Dictionary = field.settlement_loop.Rules.Logistics.PRODUCT
	var safe := Vector3(1.72,0,1.8)
	verify("existing workshop save loads",field.field_ready and not field.persist_blocked)
	for kind: String in ["meat","wood","stone"]:
		var goods: String = product[kind]
		var apron: Vector3 = field.lakeshore.apron_position() if kind=="meat" else field.processors.apron_position(kind)
		field.actor.global_position = safe
		field.previous_dry_position = safe
		await wait_ticks(4)
		verify(kind+" is a paid workshop",field.inventory.is_machine_owned(kind))
		verify(kind+" is reachable through Camp then Workshops",await workshop(kind))
		verify(kind+" cannot operate remotely",not works.can_operate(kind) and not works.request_machine(kind) and not field.settlement_loop.exchange.collect_station(kind))
		verify(kind+" can opt out of walk-up handoff",await command("machine_mode:"+kind) and not works.automatic_handoff(kind))
		if dock.sheet.visible:
			await tap(dock.close)
		var before: int = field.inventory.hand_goods()[goods]
		var raw_before: int = field.inventory.carried[kind]
		for count in 2:
			field.inventory.collect("manual-workshop-%s-%d"%[kind,count],kind)
		field.carry.sync()
		field.actor.global_position = apron
		field.previous_dry_position = apron
		await wait_ticks(22)
		verify(kind+" reaches the apron and waits for the chosen action",works.can_operate(kind) and field.inventory.carried[kind]==raw_before+2)
		verify(kind+" opens its station again",await workshop(kind))
		var receipt := "cooked" if kind=="meat" else "processed_"+kind
		var produced_before:int=journal[receipt]
		verify(kind+" loads through the real touch command",await command("machine_load:"+kind))
		for count in 420:
			await physics_frame
			if field.inventory.carried[kind]<raw_before+2 and int(journal[receipt])>produced_before:break
		verify(kind+" manually loaded input produces a finished item",field.inventory.carried[kind]<raw_before+2 and int(journal[receipt])>produced_before and field.settlement_loop.Rules.Logistics.rack(journal,kind)>0)
		verify(kind+" completed goods wait on the output tray",int(field.inventory.hand_goods()[goods])==before)
		verify(kind+" can revisit the station sheet",await workshop(kind))
		verify(kind+" collects through the real touch command",await command("machine_take:"+kind) and int(field.inventory.hand_goods()[goods])>before and not field.persist_blocked)
	verify("normal save succeeds",not field.persist_blocked)
	field.set_physics_process(false)
	field.carry.set_physics_process(false)
	field.sound.stop_playback()
	for count in 12:
		OS.delay_msec(20)
		await process_frame
	field.queue_free()
	await process_frame
	print("WORKSHOP_HANDOFF ",JSON.stringify({"checks":checks}))
	quit(0 if checks.values().all(func(value): return value) else 2)
