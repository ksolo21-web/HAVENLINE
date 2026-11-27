extends "res://tests/world_route.gd"
const FieldScene = preload("res://field_opening.tscn")
const Session = preload("res://tests/lifecycle_test_profile.gd")
var frame := 0
var render_path := OS.get_environment("CAPTURE_DIR")
var marks := []
var checks := {}
var heard := []
var build_just_seen := false
var prev_paid := 0
var crossings := []
var inside_last := false

func check(label:String,value:bool)->void:
	checks[label]=value
	if not value: push_error(label)

func stamp(label:String)->void:
	var gs:={}
	var levels:={}
	for loop in field.sound._loops:
		var node=field.sound._loops[loop]
		levels[loop]={"playing":node.playing,"db":snappedf(node.volume_db,.1)}
	for g in field.gates:
		gs[g.gate_id]={"open":g.target_open,"angle_degrees":snappedf(rad_to_deg(g.angle),.1)}
	marks.append({"action":label,"seconds":snappedf(frame/60.,.001),"position":[field.actor.position.x,field.actor.position.y,field.actor.position.z],"camp":field.camp_active,"inside":field.field_env.is_inside_camp(field.actor.position),"orbit":field.character_kit.active,"wood_packs":int(field.inventory.carried.wood),"wood_paid":int(field.inventory.paid.center_hearth.wood),"gates":gs,"layers":levels})
	print("MARK ",marks.back())

func hear(id:String,_clock:float,_voice:int)->void:
	heard.append([id,frame])

var drawn:=0
var first_engine_frame:=-1
var last_engine_frame:=-1
var recording:=false
func capture_displayed()->void:
	if not recording or render_path.is_empty():return
	if first_engine_frame<0:first_engine_frame=Engine.get_process_frames()
	last_engine_frame=Engine.get_process_frames()
	root.get_texture().get_image().save_jpg(render_path.path_join("f%05d.jpg"%drawn),.89)
	drawn+=1

func sample()->void:
	await physics_frame
	var paid:int=field.inventory.paid.center_hearth.wood
	if paid and not prev_paid: stamp("first wood landed at unpaid hearth")
	prev_paid=paid
	if field.camp_active:
		if not build_just_seen:
			stamp("furnace and perimeter visible")
			build_just_seen=true
		else:
			var interior:bool=field.field_env.is_inside_camp(field.actor.position)
			if interior!=inside_last:
				var likely:String="east" if field.actor.position.x>absf(field.actor.position.z) else "south"
				stamp(likely + " plane " + ("in" if interior else "out"))
				crossings.append(marks.back().duplicate(true))
	inside_last=field.field_env.is_inside_camp(field.actor.position)
	frame+=1

func hold(steps:int)->void:
	steer(Vector2.ZERO)
	for i in steps: await sample()

func go(label:String,point:Vector2)->void:
	var arrived:=false
	for step in 360:
		arrived=move_to([point.x,point.y],.22)
		await sample()
		if arrived: break
	check(label,arrived)
	stamp(label)
	await hold(12)

func run()->void:
	field=FieldScene.instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=Vector2(root.size.x*.28,root.size.y*.7)
	field.sound.cue_started.connect(hear)
	RenderingServer.frame_post_draw.connect(capture_displayed)
	recording=true
	await hold(12)
	check("disposable fresh profile",field.field_ready and not field.persist_blocked and not field.camp_active and field.inventory.carried.wood==0)
	stamp("untouched opening in snow")
	await hold(35)
	await go("approach the southwestern tree line",Vector2(-4.8,8.0))
	var order={"kind":"wood","count":20,"choose_nearest":true,"region":[-13.7,5.5,-5.2,16.0]}
	var earned:=false
	for step in 6000:
		if field.inventory.carried.wood>=20:
			earned=true
			break
		_farm(order)
		await sample()
		if field.camp_active: break
		if step%600==0: print("FARM ",frame," ",field.inventory.carried.wood," ",field.actor.position)
	check("earned twenty wood packs through field harvesting",earned)
	stamp("gathered wood in snow")
	if earned:
		await go("return across southern snow",Vector2(-4.3,7.1))
		await go("bring timber south of first plot",Vector2(.05,5.40))
		await go("pay on southern lip",Vector2(.05,3.40))
		for i in 140:
			await sample()
			if field.camp_active:break
		check("camp unlocked by real payment",field.camp_active and prev_paid==20)
		await hold(44)
		await go("south gate exterior snow",Vector2(0,6.55))
		await go("south gate inside safety",Vector2(0,2.25))
		await go("cross clear courtyard",Vector2(2.10,1.55))
		await go("approach east gate",Vector2(3.6,0))
		await go("east gate exterior snow",Vector2(7.6,0))
		await go("east gate inside safety",Vector2(3.3,0))
		await hold(35)
		for m:Dictionary in marks:
			if "exterior snow" in m.action:check(m.action+" releases orbit",not m.inside and m.orbit)
			if "inside safety" in m.action:check(m.action+" holsters orbit",m.inside and not m.orbit)
		check("four threshold crossings",crossings.size()==4)
	recording=false
	print("GATE_FILM ",JSON.stringify({"frame_post_draw_samples":drawn,"first_render_frame":first_engine_frame,"last_render_frame":last_engine_frame,"scene":field.scene_file_path,"checks":checks,"timeline":marks,"crossings":crossings,"sound_cues":heard,"render_sample_hz":12,"physics_hz":60,"duration":frame/60.,"device_renderer":RenderingServer.get_video_adapter_name(),"gameplay_viewport":str(root.size),"zoom":field.get_zoom_ratio()}))
	field.set_physics_process(false)
	field.carry.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 4:await process_frame
	quit(int(checks.values().has(false)))
