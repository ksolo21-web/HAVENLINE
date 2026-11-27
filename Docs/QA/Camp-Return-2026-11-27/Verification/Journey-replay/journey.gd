extends "res://tests/world_route.gd"
var trace:FileAccess
var marks:={}
var visual:=OS.get_environment("JOURNEY_RENDER")=="1"
var held_from:Vector3
var fingerprint:={}
var compass
var captures:={}
var before_hp:=30
var first_bite:=-1
var costs_pending:={}
var recorded_frames:=0
var bite_floor:=0
var finger_target:=Vector2.ZERO
var finger_down:=false
var quarry_detour:Array=[]
var photos:={}
var movie_frames:Array=[]
var last_phase:=""
func snapshot()->Dictionary:
	var inv=field.inventory
	var hud=field.opening_hud
	var plot_labels:={}
	for k in field.carry.receivers:
		var node=field.carry.receivers[k]
		if node is Node3D and node.is_visible_in_tree():plot_labels[k]=pt(node.global_position)
	var gates:Array=[]
	for gate in field.gates:gates.append([gate.gate_id,gate.angle,gate.target_open,pt(gate.position)])
	return {"zoom":field.get_zoom_ratio(),"continue_visible":hud.level_continue.visible,"continue_label":hud.level_continue.text,"photos_taken":photos.size(),"compass":({"visible":compass.visible,"name":compass.destination,"meters":compass.meters,"needle":compass.needle.rotation,"label":compass.label.text,"gate_index":compass.route.gate_index} if is_instance_valid(compass) else {}),"tick":tick,"pos":pt(field.actor.position),"hp":field.player_hp,"max":field.MAX_HP,"inside":field.field_env.is_inside_camp(field.actor.position),"carried":inv.carried.duplicate(),"stored":inv.stored.duplicate(),"paid":inv.paid.duplicate(true),"builds":inv.build_order.duplicate(),"available":plot_labels,"flights":field.carry.flights.size(),"hud":hud.prompt.text,"gates":gates,"collected":inv.collected.size(),"survivor":field.survivor.phase,"movement":pt(field.actor.velocity),"milestones":inv.settlement.duplicate(true),"phase":phases[index].label if index<phases.size() else "done"}
func receipt(name:String):
	if marks.has(name):return
	marks[name]=snapshot()
	var path:String=OS.get_environment("JOURNEY_PROFILE").path_join("field-inventory-v1.json")
	if FileAccess.file_exists(path):
		var f:=FileAccess.open(out_dir.path_join(name+".save.json"),FileAccess.WRITE);f.store_buffer(FileAccess.get_file_as_bytes(path));f.close()
func pinch_to(ratio:float):
	var base:float=field.get_zoom_ratio()
	if absf(base-ratio)<.01:return
	var size_:Vector2=root.get_visible_rect().size
	var mid:=size_*Vector2(.60,.43)
	var spread:=size_.x*.084
	for i in 2:touch(6+i,mid+Vector2.RIGHT*spread*(-1 if i==0 else 1),true)
	for i in 2:
		var drag:=InputEventScreenDrag.new();drag.index=6+i;drag.position=mid+Vector2.RIGHT*spread*ratio/base*(-1 if i==0 else 1);root.push_input(drag,true)
	for i in 2:touch(6+i,mid+Vector2.RIGHT*spread*ratio/base*(-1 if i==0 else 1),false)
func picture_pair(label:String):
	if photos.has(label+"-1x"):return
	if touch_held:steer(Vector2.ZERO)
	for zoom_ in [1.,2.]:
		pinch_to(zoom_)
		RenderingServer.force_draw(false,0.)
		var im:Image=root.get_texture().get_image()
		var key=label+"-"+str(int(zoom_))+"x"
		im.save_jpg(out_dir.path_join(key+".jpg"),.95)
		var meta=snapshot()
		var fpaths:=[]
		for f in field.carry.flights:fpaths.append([f.kind,f.from,f.to,f.t])
		meta["flights_seen"]=fpaths
		meta["physical_size"]=[im.get_width(),im.get_height()]
		meta["same_camera"]=root.get_camera_3d()==camera
		var nums=[]
		for n in field.find_children("*","Label3D",true,false):
			if n.is_visible_in_tree() and ("HP" in n.text or "Camp gate" in n.text):nums.append([n.text,pt(n.global_position)])
		meta["visible_world_numbers"]=nums
		photos[key]=meta
	pinch_to(1.)
func camera_work(row:Dictionary):
	var stamp:String=row.get("view","")
	if stamp=="offer" and tick-stage_tick>5:picture_pair("Upgrade-offer")
	if stamp=="pay" and not photos.has("Upgrade-paying-1x"):
		var kinds:={}
		for f in field.carry.flights:
			if f.to=="storage_stone" and f.t>.03:kinds[f.kind]=true
		if kinds.size()>1:picture_pair("Upgrade-paying")
	if stamp=="east" and tick-stage_tick>6 and is_instance_valid(compass) and compass.visible:picture_pair("Home-compass")
	if stamp=="heal" and not photos.has("Camp-healing-1x"):
		for e in field.events.slice(-10):
			if e.event=="camp_heal" and field.simulation_time-e.t>.085 and field.simulation_time-e.t<.36:
				picture_pair("Camp-healing");break
	if OS.get_environment("JOURNEY_PHOTOS_ONLY")=="1" or tick%5!=0:return
	var seconds:float=(tick-stage_tick)/60.
	var take=stamp in ["pay","offer","upgraded","east","heal","sprint"] and seconds<float(row.get("film_s",1.4))
	if stamp=="home":take=is_instance_valid(compass) and compass.visible and compass.meters<10
	if take and recorded_frames<260:
		RenderingServer.force_draw(false,1./12.)
		var im:Image=root.get_texture().get_image()
		var h=roundi(im.get_height()*360./im.get_width())
		im.resize(360,h,Image.INTERPOLATE_LANCZOS);im.save_jpg(out_dir.path_join("frame-%04d.jpg"%recorded_frames),.88)
		movie_frames.append([recorded_frames,tick,stamp,field.player_hp,field.inventory.build_order.size(),compass.meters if compass else -1]);recorded_frames+=1
func departure() -> void:
	var starts=field.inventory.build_order
	for b in starts:receipt("built-"+String(b))
	if field.inventory.paid.get("center_hearth",{}).get("wood",0) in range(1,19):receipt("partial-hearth")
func move_to(dest:Array,tol:float)->bool:
	var xy:=Vector3(dest[0],0,dest[1])
	var dist:Vector3=xy-field.actor.position
	dist.y=0.0
	if dist.length()<=tol:steer(Vector2.ZERO);return true
	var vel:Vector3=field.actor.velocity
	var stopping:=vel.length_squared()/(2.*55.)
	if vel.length()>.45 and (vel.normalized().dot(dist.normalized())<.80 or (dist.length()<=stopping+.06 and tol<.30)):
		steer(Vector2.ZERO);return false
	var right:=camera.global_basis.x
	var near:=right.cross(Vector3.UP)
	steer(Vector2(dist.dot(right),dist.dot(near)).normalized()*clampf(dist.length()/1.8,.20,1.))
	return false
func execute(row:Dictionary):
	var elapsed=(tick-stage_tick)/60.
	if elapsed>row.get("timeout",80):event("timeout",snapshot());finished=true;quit(4);return
	match row.action:
		"farm":
			if row.kind=="stone" and field.field_env.perimeter_stage>0 and field.inventory.carried.stone<int(row.count):
				var rock:Vector3=field.resource_rock.position
				if quarry_detour.is_empty() and field.actor.position.x>rock.x+1.85 and absf(field.actor.position.z-rock.z)<2.:
					quarry_detour=[[field.actor.position.x,rock.z+4.2],[rock.x-1.25,rock.z+4.2],[rock.x-1.7,rock.z+1.35]]
				if not quarry_detour.is_empty():
					if move_to(quarry_detour[0],.27):quarry_detour.pop_front()
					return
			super.execute(row)
		"pay_part":
			if field.inventory.paid[row.id].get(row.get("kind","wood"),0)>=row.count and field.carry.flights.is_empty():advance()
			else:
				var p:Vector3=field.carry.receivers[row.id].global_position
				move_to([p.x,p.z],.17)
		"upgrade":
			if field.inventory.complete(row.id) and field.carry.flights.is_empty():advance();return
			var p:Vector3=field.carry.receivers[row.id].global_position
			if field.depot.has_method("on_upgrade_side") and row.get("legacy_side",false):p=field.depot.APRON+Vector3(.62,0,.06)
			move_to([p.x,p.z],.11)
		"buy":
			if field.inventory.complete(row.id) and field.carry.flights.is_empty():advance();return
			var p:Vector3=field.carry.receivers[row.id].global_position
			move_to([p.x,p.z],.17)
		"wait_bite":
			if elapsed<.04:bite_floor=field.player_hp
			if field.player_hp>0 and field.player_hp<bite_floor:receipt("hazard-hit");advance();return
			var closest=null;var distance:=INF
			for w in field.enemies:
				if is_instance_valid(w) and w.hp>0 and w.position.distance_to(field.actor.position)<distance:closest=w;distance=w.position.distance_to(field.actor.position)
			if closest:move_to([closest.position.x,closest.position.z],.14)
			else:move_to(row.get("p",[13.,-.3]),.25)
		"tap_continue":
			var button=field.opening_hud.level_continue
			if field.inventory.settlement.level>=2:receipt("terminal-click");advance();return
			if button.visible and not finger_down:
				finger_target=button.get_global_rect().get_center();touch(8,finger_target,true);finger_down=true
			elif finger_down:
				touch(8,finger_target,false);finger_down=false
		"inspect":
			steer(Vector2.ZERO)
			if elapsed>=row.get("seconds",.35):advance()
		"follow_compass":
			if field.field_env.is_inside_camp(field.actor.position):steer(Vector2.ZERO);receipt("compass-arrival");advance();return
			if not compass or not compass.visible:steer(Vector2.ZERO);return
			var pitch:float=absf(camera.global_basis.z.y)
			var screen:=Vector2.RIGHT.rotated(compass.needle.rotation)
			steer(Vector2(screen.x,screen.y/maxf(.12,pitch)).normalized()*.86)
		"rest":
			steer(Vector2.ZERO)
			if field.player_hp>=field.MAX_HP or elapsed>=row.get("seconds",20.0):receipt("rested");advance()
		_:
			super.execute(row)
func advance():
	event("complete",snapshot())
	index+=1
	harvest_body=null
	if index>=phases.size():steer(Vector2.ZERO);finished=true;return
	stage_tick=tick
	event("enter",phases[index])
func run():
	phases=JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("FIELD_QA_PLAN")))
	events=FileAccess.open(out_dir.path_join("events.jsonl"),FileAccess.WRITE)
	trace=FileAccess.open(out_dir.path_join("trace.jsonl"),FileAccess.WRITE)
	field=load(String(ProjectSettings.get_setting("application/run/main_scene"))).instantiate();root.add_child(field);current_scene=field;camera=field.camera
	for j in 12:await physics_frame
	compass=field.opening_hud.get_node_or_null("HomeCompass")
	origin=root.get_visible_rect().size*Vector2(.20,.70)
	first_tick=Engine.get_physics_frames()
	begin_phase()
	while not finished:
		tick=Engine.get_physics_frames()-first_tick
		departure()
		if tick%60==0:trace.store_line(JSON.stringify(snapshot()));trace.flush()
		if visual:camera_work(phases[index])
		execute(phases[index])
		if not finished:await physics_frame
	if index>=phases.size():
		var rr=FileAccess.open(out_dir.path_join("journey.json"),FileAccess.WRITE)
		rr.store_string(JSON.stringify({"seconds":tick/60.,"final":snapshot(),"checkpoints":marks,"photos":photos,"movie_frames":movie_frames,"actions":phases,"inputs":"InputEventScreenDrag and InputEventScreenTouch only","game_events":complete_log},'  '));rr.close()
		field.queue_free();for j in 4:await process_frame
		quit(0)
