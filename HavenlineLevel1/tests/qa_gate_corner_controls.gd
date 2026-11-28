extends "res://tests/field_route.gd"
const Profile=preload("res://tests/lifecycle_test_profile.gd")
var samples: Array = []
var media := OS.get_environment("HL_GATE_MEDIA")
var shot_num:=0
func _initialize() -> void:
	var guard := preload("res://opening_save.gd").new()
	if guard.configure(OS.get_cmdline_user_args()):call_deferred("run")
	elif not Profile.isolated(self,"res://tests/qa_gate_corner_controls.gd"):call_deferred("run")

func pay(station:String)->void:
	for k:String in field.inventory.remaining(station):
		var qty:int=field.inventory.remaining(station)[k]
		for i in qty: field.inventory.collect("gate9-"+station+k+str(i),k)
		field.inventory.payment(station,k,false,qty)
	field._finish_purchase(station)

func capture(tag:String)->void:
	if media.is_empty():return
	await process_frame
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(media.path_join("%s-%03d.jpg"%[tag,shot_num]),.83)
	shot_num+=1

func travel(stage:int, g, side:float,sign_x:float, spec:Array, filmmable:bool)->void:
	steer(Vector2.ZERO)
	# Each independent approach starts with healthy feet and a neutral release.
	for i in 18: await physics_frame
	field.player_hp=field.MAX_HP
	var far:=Vector3(50,0,48)
	var empty:Array[Vector4]=[]
	for i in 100:g.advance_automatic(1./60.,far,.31,Vector3.INF,empty)
	var startx:float=spec[0]*sign_x
	var distance:float=spec[1]
	var slope:float=spec[2]*sign_x
	var offset:=Vector3(startx,0,side*distance)
	var start:Vector3=g.to_global(offset)
	var dir:Vector3=(g.global_basis*Vector3(slope,0,-side)).normalized()
	field.actor.global_position=start
	field.previous_dry_position=start
	field.actor.velocity=Vector3.ZERO
	field.actor.rotation.y=atan2(dir.x,dir.z)
	field.gait_motor.travel_speed=0
	field.camera.position=start+field.camera_follow_offset
	var right:Vector3=camera.global_basis.x
	var u:=Vector2(dir.dot(right),dir.dot(right.cross(Vector3.UP))).normalized()
	var progress:=0.
	var blocked:=0
	var max_hold:=0
	var max_still:=0
	var peak_step:=0.
	var reset_seen:=false
	var solid_crossings:=0
	var seam_step:=0.
	var stationary_obstacles:Dictionary={}
	var still:=0
	var crossed:=false
	var tick_index:=0
	var first:=Vector3.INF
	var inspect:=filmmable and not media.is_empty()
	if inspect:
		if OS.get_environment("HL_GATE_PINCH")=="1":field.set_zoom_ratio(2)
		shot_num=0
	for i in 132:
		steer(u)
		var last_pos:Vector3=field.actor.position
		await physics_frame
		tick_index=i
		var l:Vector3=g.to_local(field.actor.global_position)
		progress=distance-side*l.z
		if g.holding_for_occupancy:blocked+=1
		max_hold=maxi(max_hold,blocked)
		peak_step=maxf(peak_step,field.actor.position.distance_to(last_pos))
		reset_seen=reset_seen or field.reset_time>0.
		if not field.field_env.travel_clear(last_pos,field.actor.position,0.): solid_crossings+=1
		if field.actor.position.distance_squared_to(last_pos)<.00004:
			still+=1
			if still>3:
				for c in field.actor.get_slide_collision_count():
					var collider=field.actor.get_slide_collision(c).get_collider()
					if collider:stationary_obstacles[String(collider.name)]=true
		else:still=0
		max_still=maxi(max_still,still)
		if not first.is_finite() and l.z*side<=0:
			first=l
			seam_step=field.actor.position.distance_to(last_pos)
		if inspect and i%5==0:await capture("cross")
		if l.z*side<=-1.65:
			crossed=true;break
	steer(Vector2.ZERO)
	samples.append({"stage":stage,"gate":g.gate_id,"from":int(side),"sign":int(sign_x),"style":spec[3],"crossed":crossed,"ticks":tick_index+1,"advance":snappedf(progress,.01),"still":max_still,"held":max_hold,"peak_step":snappedf(peak_step,.001),"seam_step":snappedf(seam_step,.001),"solid_crossings":solid_crossings,"reset_seen":reset_seen,"stationary_obstacles":stationary_obstacles.keys(),"lateral_at_plane":snappedf(first.x,.01) if first.is_finite() else null,"end":str(g.to_local(field.actor.position))})

func run()->void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field);camera=field.camera
	origin=root.get_visible_rect().size*Vector2(.30,.72)
	for i in 4:await physics_frame
	if OS.get_environment("HL_GATE_LOADED") == "1":
		for kind in ["wood","stone","meat"]:
			for unit in 6: field.inventory.collect("gate-cargo-%s-%d" % [kind,unit],kind)
		field.carry.sync()
	var stg:=OS.get_environment("HL_GATE_STAGE").to_int()
	var only:=not media.is_empty() or OS.get_environment("HL_GATE_SINGLE")=="1"
	for stage in [1,2,3]:
		if stage==1:pay("center_hearth");field._apply_hearth(true,false)
		if stage==2:pay("expansion_1")
		if stage==3:
			for id in ["storage_wood","storage_stone","storage_meat","expansion_2"]:pay(id)
		for i in 5:await physics_frame
		if stg!=0 and stage!=stg:continue
		for g in field.gates:
			if only and g!=field.gates[1]:continue
			for side:float in [-1.,1.]:
				if only and side!=1.:continue
				for sign_x:float in [-1.,1.]:
					if only and sign_x!=1.:continue
					for entry:Array in [[1.06,2.50,.0,"grazing-post"],[1.64,2.48,-.22,"grazing-diagonal"],[.0,2.5,.0,"straight"],[.78,2.6,.02,"near-hinge"],[2.40,2.60,-.64,"corner"],[-1.36,2.4,.85,"held-diagonal"],[-.42,2.45,.56,"outer-tip"]]:
						if only and entry[3]!="grazing-diagonal":continue
						await travel(stage,g,side,sign_x,entry,only)
	var blocked:=samples.filter(func(pass_sample):return not pass_sample.crossed or pass_sample.reset_seen or pass_sample.solid_crossings>0 or pass_sample.seam_step>.24 or pass_sample.lateral_at_plane==null or absf(pass_sample.lateral_at_plane)>1.05)
	print("PERIMETER_ROUTE ",JSON.stringify(samples))
	print("GATE_CONTROLS cases=",samples.size()," failed=",blocked.size()," cargo=",JSON.stringify(field.inventory.carried))
	field.set_physics_process(false);field.carry.set_physics_process(false)
	await Profile.drain_field_audio(self,field)
	field.queue_free()
	for i in 4:await process_frame
	quit(0 if blocked.is_empty() and not samples.is_empty() else 1)
