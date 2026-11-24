extends SceneTree
var game
var updates := 0
var fails := 0
var checks := 0
var gesture_id := 10
const CENTER:=Vector2(450,375)
const STEP:=4.0/60.0
func _initialize():
	call_deferred("run")
func tick(n:int):
	for i in range(n):
		await physics_frame
		updates+=1
func check(ok:bool,label:String):
	checks+=1
	print("%s %s tick=%d" % ["PASS" if ok else "FAIL",label,updates])
	if not ok:
		fails+=1
func press(code:Key):
	var ev:=InputEventKey.new()
	ev.physical_keycode=code
	ev.pressed=true
	game._input(ev)
	ev.pressed=false
	game._input(ev)
func touch(down:bool):
	var ev:=InputEventScreenTouch.new()
	ev.position=CENTER
	ev.index=gesture_id
	ev.pressed=down
	game._input(ev)
func drag(world_delta:Vector3):
	var local:=world_delta.rotated(Vector3.UP,-atan2(7.0,11.0))
	var ev:=InputEventScreenDrag.new()
	ev.index=gesture_id
	ev.position=CENTER+Vector2(local.x,local.z).limit_length()*82.0
	game._input(ev)
func travel(label:String,to:Vector3,max_ticks:int,per_tick:bool=false)->bool:
	gesture_id+=1
	touch(true)
	var hit_count:=0
	var traces:Array[Dictionary]=[]
	for i in range(max_ticks):
		var before:Vector3=game.actor.position
		var err:=to-before
		err.y=0
		if err.length()<.008:
			break
		# Last step shortens joystick vector according to remaining signed distance.
		drag(err/STEP)
		await tick(1)
		var p:Vector3=game.actor.position
		var b:Basis=game.actor.global_basis
		var hit:=int(game.actor.get_slide_collision_count())
		hit_count+=hit
		for j in range(hit):
			var hit_obj=game.actor.get_slide_collision(j).get_collider()
			if hit_obj is Node:
				print("slide collider path ",hit_obj.get_path()," tick=",updates)
		if per_tick:
			traces.append({"tick":updates,"pos":[p.x,p.y,p.z],"basis":[[b.x.x,b.x.y,b.x.z],[b.y.x,b.y.y,b.y.z],[b.z.x,b.z.y,b.z.z]],"collisions":hit})
		if i>2 and p.distance_to(before)<.001 and hit>0:
			break
	touch(false)
	await tick(2)
	var end:Vector3=game.actor.position
	print("route ",JSON.stringify({"label":label,"target":[to.x,to.y,to.z],"to_observed_error":end.distance_to(to),"collisions":hit_count,"traces":traces}))
	return end.distance_to(to)<.02 and hit_count==0
func run():
	game=load("res://opening.tscn").instantiate()
	root.add_child(game)
	await tick(3)
	check(not game.persist_requested and game.actor.position.distance_to(Vector3(0,0,6))<.001,"fresh shell at real spawn")
	check(game.wood_visuals["wood-b"].visible and game.wood_visuals["wood-c"].visible and game.ledger.stock.wood==0,"both uncollected and visible")
	check(await travel("approach but outside real trigger",Vector3(-2.25,0,7),100),"outside controlled movement")
	check(game.wood_visuals["wood-b"].visible and game.ledger.stock.wood==0 and game.ledger.collected.is_empty(),"outside reached without early award")
	check(await travel("walk into existing wood-b",Vector3(-3,0,7),100),"trigger reached through routed motion")
	check(not game.wood_visuals["wood-b"].visible and game.wood_visuals["wood-c"].visible and game.ledger.stock.wood==1 and game.ledger.collected==["wood-b"],"one typed pickup hides only first actual marker")
	await tick(8)
	check(game.ledger.stock.wood==1 and game.ledger.receipt.is_empty() and game.ledger.collected==["wood-b"],"standing on consumed source awards no duplicate")
	print("ordinary wood checks=",checks," failures=",fails)
	quit(1 if fails else 0)
