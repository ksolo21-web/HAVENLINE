extends SceneTree
const SIDE:=Vector3(.7071068,0,-.7071068)
var game
var goal:Vector3
var id:="world1/4/-1/metal/0"
var clock:=0
var markers:=[]
var held:=false
var origin:=Vector2(485,450)
var out:=OS.get_environment("MINING_MOVIE_METADATA")
func _initialize() -> void: run.call_deferred()
func event(label:String):
	markers.append({"label":label,"physics_tick":clock,"process_frame":Engine.get_process_frames()})
func steer(d:Vector2):
	if not held:
		var touch:=InputEventScreenTouch.new();touch.index=0;touch.pressed=true;touch.position=origin
		root.push_input(touch,true);held=true
	var drag:=InputEventScreenDrag.new();drag.index=0;drag.position=origin+d*82.0;drag.relative=d*82.;root.push_input(drag,true)
func release():
	if held:
		var touch:=InputEventScreenTouch.new();touch.index=0;touch.pressed=false;touch.position=origin
		root.push_input(touch,true);held=false
func run() -> void:
	if not preload("res://opening_save.gd").new().configure(OS.get_cmdline_user_args()):quit(2);return
	game=load("res://field_opening.tscn").instantiate();root.add_child(game)
	while not is_instance_valid(game.world_landscape): await physics_frame
	for row:Dictionary in game.world_landscape.describe_chunk(Vector2i(4,-1)):
		if row.id==id:goal=row.position
	if goal==Vector3.ZERO:quit(2);return
	game.actor.position=goal+SIDE*4.16;game.actor.velocity=Vector3.ZERO;game.camera.position=game.actor.position+Vector3(7,11,11)
	var hits:=0;var index:=0;var spent:=-1;var back:=-1;var moving:=false;var okay:=false
	for j in 1100:
		await physics_frame
		clock+=1
		if clock==32:event("settled intact deposit")
		if clock>51 and not moving:
			var toward:Vector3=goal+SIDE*2.48-game.actor.position
			if toward.length()<.049:
				release()
				moving=true
			else:
				var right:Vector3=game.camera.global_basis.x
				var near:Vector3=right.cross(Vector3.UP)
				steer(Vector2(toward.dot(right),toward.dot(near)).normalized()*clampf(toward.length()*1.25,.3,.90))
		while index<game.events.size():
			var e:Dictionary=game.events[index];index+=1
			if Vector2(e.x,e.z).distance_to(Vector2(goal.x,goal.z))>.04:continue
			if e.event=="impact_metal":
				hits+=1;event("pick contact "+str(hits))
			if e.event=="deplete_metal":spent=clock;event("depletion and metal ore drop")
			if e.event=="regrow_metal":back=clock;event("available")
		if spent>=0 and clock-spent==286:event("visible growing bank")
		if back>=0 and clock-back>=45:
			event("end");okay=back-spent==300 and hits>=3 and moving;break
	var receipt={"commit":"fa9d3e987859a1e46c2533f94431b4e9cae3a9e5","target":id,"camera":str(game.camera.get_path()),"native":root.get_texture().get_size(),"markers":markers,"depletion_to_available_ticks":back-spent,"passed":okay}
	var f:=FileAccess.open(out,FileAccess.WRITE);f.store_string(JSON.stringify(receipt,"  ")+"\n");f.close()
	game.set_physics_process(false);game.sound.stop_playback()
	var deadline:=Time.get_ticks_msec()+280
	while Time.get_ticks_msec()<deadline: await process_frame
	game.queue_free()
	for j in 6:await process_frame
	quit(0 if okay else 1)
