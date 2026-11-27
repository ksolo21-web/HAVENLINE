extends SceneTree

var game
var checks := {}
var trace := []
var mode := OS.get_environment("CAMP_RETURN_CASE")
var origin := Vector2(85,550)
var sequence := 0

func _initialize() -> void:
	run.call_deferred()

func collect(kind: String, amount: int) -> bool:
	for i in amount:
		sequence += 1
		if not game.inventory.collect("migration-%s-%d" % [kind,sequence],kind): return false
	return true

func touch(pressed: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index=1
	e.position=origin
	e.pressed=pressed
	game._input(e)

func walk_to(point: Vector3) -> bool:
	touch(true)
	for i in 300:
		var d: Vector3 = point - game.actor.position
		d.y=0
		if d.length()<.30:
			touch(false)
			return true
		var heading := d.normalized().rotated(Vector3.UP,-atan2(7.,11.))
		var drag := InputEventScreenDrag.new()
		drag.index=1
		drag.position=origin+Vector2(heading.x,heading.z)*72
		game._input(drag)
		await physics_frame
	touch(false)
	return false

func observation():
	var ledger = game.inventory
	return {"hp":game.player_hp,"position":str(game.actor.position),"storage":ledger.stored.duplicate(),"back":ledger.carried.duplicate(),"built":ledger.build_order.duplicate(),"reinforcement_remaining":ledger.remaining("storage_stone"),"advanced_remaining":ledger.remaining("storage_meat")}

func run() -> void:
	game=load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(game)
	for i in 4: await physics_frame
	var ledger = game.inventory
	checks["shipping field code"]=FileAccess.file_exists("res://field_opening.gdc")
	checks["disposable save healthy"]=game.field_ready and not game.persist_blocked and not game.field_save.native_profile
	if mode=="seed":
		var valid:=true
		for plot: String in ["center_hearth","expansion_1","storage_wood"]:
			for kind: String in ledger.costs[plot]:
				var n := int(ledger.costs[plot][kind])
				valid = collect(kind,n) and ledger.payment(plot,kind,false,n) and valid
		valid=collect("wood",8) and collect("stone",6) and valid
		valid=ledger.deposit("wood",4) and ledger.payment("storage_stone","wood",false,3) and ledger.payment("storage_stone","stone",false,2) and valid
		game._apply_hearth(true,false)
		game.player_hp=15
		game.actor.position=Vector3(.10,0,2.25)
		game._inventory_changed()
		checks["previous signed build committed partial costs and stock"]=valid and not game.persist_blocked
	elif mode=="buy":
		trace.append(observation())
		checks["old prices and balances survive update"]=ledger.paid["storage_stone"]=={"wood":3,"stone":2} and ledger.stored.wood==4 and ledger.carried.wood==1 and ledger.carried.stone==4 and game.player_hp==15
		var tile: Node3D=game.carry.receivers["storage_stone"]
		var target:=tile.global_position
		checks["offered reinforcement has a separate world destination"]=target.distance_to(game.depot.APRON)>1.5
		checks["ordinary drag reached active construction tile"]=await walk_to(target)
		for i in 240: await physics_frame
		trace.append(observation())
		checks["reinforcement paid exactly from carried and stored stock"]=ledger.complete("storage_stone") and ledger.stored.wood==0 and ledger.carried.wood==0 and ledger.carried.stone==0
		checks["standing on completed tier did not double-spend"]=ledger.build_order.count("storage_stone")==1 and ledger.remaining("storage_meat")==ledger.costs["storage_meat"]
		checks["home healed automatically"]=game.player_hp>15
		game.notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	elif mode=="reload":
		checks["reinforced house survives second launch"]=ledger.complete("storage_stone") and ledger.build_order.count("storage_stone")==1
		checks["next visible offer survives cold launch"]=game.depot.offer=="storage_meat" and ledger.offer_open("storage_meat")
		for i in 320: await physics_frame
		checks["healing resumes up to full"]=game.player_hp==game.MAX_HP
	checks["no save errors"]=not game.persist_blocked
	trace.append(observation())
	print("CAMP_RETURN ",JSON.stringify({"case":mode,"checks":checks,"observations":trace,"passed":not checks.values().has(false)}))
	game.sound.stop_playback()
	for i in 13:
		OS.delay_msec(20)
		await process_frame
	game.queue_free()
	for i in 5: await process_frame
	quit(int(checks.values().has(false)))
