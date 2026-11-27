extends SceneTree

var field
var checks := {}
var mode := OS.get_environment("HAVEN_DOORWAY_CASE")
var readings: Array = []
var touch_at := Vector2(80,560)
var first := -1
var last := -1
var start_count := 9

func _initialize():
	run.call_deferred()

func check(label: String, result: bool) -> void:
	checks[label] = result

func press(active: bool):
	var ev := InputEventScreenTouch.new()
	ev.index = 0
	ev.pressed = active
	ev.position = touch_at
	field._input(ev)

func steer(direction: Vector3):
	var heading := direction.normalized().rotated(Vector3.UP, -atan2(7.,11.))
	var ev := InputEventScreenDrag.new()
	ev.index = 0
	ev.position = touch_at + Vector2(heading.x,heading.z) * 75.
	field._input(ev)

func run():
	field = load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(field)
	for i in 3: await physics_frame
	var book = field.inventory
	check("signed game code loaded",FileAccess.file_exists("res://field_opening.gdc"))
	check("private profile valid",field.field_ready and not field.persist_blocked and not field.field_save.native_profile)
	if mode=="write":
		for plot: String in ["center_hearth","expansion_1","storage_wood"]:
			for material: String in book.costs[plot]:
				for n in int(book.costs[plot][material]):
					check(plot+material+str(n),book.collect("earned-"+plot+material+str(n),material) and book.payment(plot,material,false))
		for n in start_count:
			check("meat "+str(n),book.collect("trial-loot-"+str(n),"meat"))
		for kind in ["wood","stone"]:
			for i in 3: check("mixed "+kind+str(i),book.collect("mixed-"+kind+str(i),kind))
		field.player_hp=27
		field.actor.position=field.depot.APRON+Vector3(1.50,0,2.15)
		field._inventory_changed()
		check("v4 starter with carried meat committed",book.complete("storage_wood") and not book.complete("storage_stone") and book.carried.meat==start_count and not field.persist_blocked)
	elif mode=="reload":
		check("wood and stone survived second boot",book.stored.wood==3 and book.carried.stone==3 and book.stored.stone==0)
		check("stored meat survives second boot",book.stored.meat==start_count and book.carried.meat==0 and field.player_hp==27)
		check("no involuntary upgrade",not book.complete("storage_stone") and not book.complete("storage_meat"))
	else:
		check("continued prior signed save",field.camp_active and book.build_order.size()==3 and book.carried.meat==start_count and book.stored.meat==0 and field.player_hp==27)
		var opening_payments: Dictionary = book.paid.duplicate(true)
		var target: Vector3 = field.depot.APRON+Vector3(0,0,-1.25)
		var initial: Vector3 = field.actor.position
		press(true)
		var held := true
		var crossed := -1
		var previous := 0
		for tick in 240:
			var delta: Vector3 = target-field.actor.position
			delta.y=0
			if held:
				if delta.length()<.29:
					press(false)
					held=false
				else:
					steer(delta)
			await physics_frame
			if crossed==-1 and field.depot.at_apron(field.actor.position): crossed=tick
			var stock:=int(book.stored.meat)
			if stock!=previous:
				readings.append({"tick":tick,"stored":stock,"carried":book.carried.meat})
				if first==-1:first=tick
				last=tick
				previous=stock
		if held:press(false)
		check("used actual phone drag and entered doorway",crossed>=0 and initial.distance_to(field.actor.position)>1.0)
		check("physical stock conserved",book.stored.meat+book.carried.meat==start_count)
		check("other purchases received no units",not book.complete("storage_stone") and not book.complete("storage_meat"))
		if mode=="before":
			check("v4 reproduces reported failed meat delivery",book.stored.meat==0 and book.carried.meat==start_count)
		else:
			check("crossing side apron did not divert to upgrades",book.paid==opening_payments)
			check("eligible wood was shelved and locked stone stayed carried",book.stored.wood==3 and book.carried.stone==3 and book.stored.stone==0)
			check("all nine meat bundles arrived through normal doorway",book.stored.meat==start_count and book.carried.meat==0)
			check("arrival accelerated",first>=crossed and last>=first and (last-first)<=60 and (last-crossed)<=90)
		readings.append({"initial":str(initial),"final":str(field.actor.position),"apron_entered_tick":crossed,"first_meat_tick":first,"last_meat_tick":last,"visit":field.depot.visit})
	var result := {"stage":mode,"checks":checks,"passed":not checks.values().has(false),"stored_meat":int(book.stored.meat),"carried_meat":int(book.carried.meat),"timeline":readings,"paid":book.paid,"carried":book.carried,"stored":book.stored}
	print("DOORWAY ",JSON.stringify(result))
	field.sound.stop_playback()
	for i in 8:
		OS.delay_msec(18)
		await process_frame
	field.queue_free()
	for i in 6:await process_frame
	quit(int(not result.passed))
