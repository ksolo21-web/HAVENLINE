extends SceneTree
var game
var folder:=OS.get_environment("MOTION_OUT")
var pick:=int(OS.get_environment("MOTION_ID"))
var graphics:=OS.get_environment("MOTION_RENDER")=="1"
var start:=Vector2(150,455)
var gameplay_interval:=2 if int(OS.get_environment("MOTION_ID"))==1 else 4
var rows:=[]
var camera:Camera3D
var victim
var rig:Skeleton3D
var mapping={}
var worker_mode:bool
func _initialize()->void: call_deferred("go")
func point_input(d:Vector2, active:bool)->void:
	var touch:=InputEventScreenTouch.new()
	touch.index=3; touch.pressed=active;touch.position=start;game._input(touch)
	if active:
		var drag:=InputEventScreenDrag.new();drag.index=3;drag.position=start+d;game._input(drag)
func shot(file:String)->void:
	RenderingServer.force_draw(false,0.)
	root.get_texture().get_image().save_jpg(folder.path_join(file+".jpg"),.87)
func go()->void:
	game=load("res://field_opening.tscn").instantiate();root.add_child(game);current_scene=game
	for i in 5:await physics_frame
	if not game.field_ready or game.persist_blocked:quit(3);return
	worker_mode=pick==5
	if not worker_mode and not game.set_player_character(pick):quit(4);return
	camera=game.camera
	if worker_mode:
		victim=game.survivor.actor;rig=victim.skeleton
		game.survivor.phase="recorded_walk"
		game.hero_model.hide()
		game.carry.rack.hide()
	else:
		victim=game.actor;rig=game.gait_motor.skeleton if pick==1 else game.player_wardrobe.target
	var visual:Node3D = victim if worker_mode else (game.hero_model if pick==1 else game.player_wardrobe.visual)
	for node in visual.find_children("*","MeshInstance3D",true,false):
		node.set_layer_mask_value(20,true)
	var plane:=MeshInstance3D.new()
	var sheet:=PlaneMesh.new()
	sheet.size=Vector2(195,195)
	plane.mesh=sheet
	var ground:=Shader.new()
	ground.code="shader_type spatial; varying vec3 project_at; void vertex(){project_at=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;} void fragment(){vec2 cell=abs(fract(project_at.xz*4.0+.5)-.5)/max(fwidth(project_at.xz*4.0),vec2(.0001)); float line=1.0-clamp(min(cell.x,cell.y),0.0,1.0); ALBEDO=mix(vec3(.76,.80,.81),vec3(.48,.56,.59),line*.55); ROUGHNESS=1.0;}"
	var mat:=ShaderMaterial.new();mat.shader=ground;plane.material_override=mat
	plane.layers=1<<19;plane.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	game.add_child(plane);plane.position.y=-.003
	var prefix:="mixamorig" if pick in [2,3,4] else ""
	for side in ["L","R"]:
		var side_name: String="Left" if side=="L" else "Right"
		for pair in [["Thigh","UpLeg"],["Shin","Leg"],["Foot","Foot"],["Toe","ToeBase"],["UpperArm","Arm"],["Forearm","ForeArm"],["Hand","Hand"]]:
			var src: String=prefix+side_name+pair[1] if prefix!="" else pair[0]+"."+side
			if worker_mode and pair[0]=="Hand":src="Palm."+side
			mapping[pair[0]+side]=rig.find_bone(src)
	for z in [1,2]:
		if z==2:
			for k in ["wood","stone"]:
				if worker_mode:
					game.inventory.settlement.worker_load[k]=6
				else:
					for i in 6: game.inventory.collect("motion-test-"+k+str(i),k)
			if worker_mode:game.survivor._sync_pack()
			else:game.carry.sync(true)
		game.set_zoom_ratio(z)
		victim.position=Vector3(21,0,22)
		if worker_mode:
			game.actor.position=victim.position+Vector3(.4,0,.5)
			game.survivor.travel_speed=0.
			victim.rotation.y=PI*.35
		else:
			game.actor.velocity=Vector3.ZERO
			game.clear_touch()
		camera.position=game.actor.position+game.camera_follow_offset
		for i in 12:await physics_frame
		if not worker_mode: point_input(Vector2(93,-15),true)
		for tick in 114:
			if worker_mode:
				var to:Vector3=victim.position+Vector3(.82,0,.54)*12.
				if tick>=82:to=victim.position-Vector3(.75,0,.66)*6.
				game.survivor._walk(to,1./60.,z==2)
				if victim.mode=="travel":victim.forester_gait.settle_contact(1./60.,victim)
				game.actor.position=victim.position+Vector3(.5,0,.7)
			elif tick==84:
				point_input(Vector2(-80,-36),true)
			elif tick==103:point_input(Vector2.ZERO,false)
			await physics_frame
			var joints:={}
			for key:String in mapping:
				var b:int=mapping[key]
				if b>=0:
					var world:Vector3=rig.to_global(rig.get_bone_global_pose(b).origin)
					var local:Vector3=victim.to_local(world)
					joints[key]=[local.x,local.y,local.z]
			var row:={"zoom":z,"tick":tick,"joints":joints,"feet":[victim.position.x,victim.position.y,victim.position.z],"angle":victim.rotation.y}
			rows.append(row)
			if graphics and tick%gameplay_interval==0:
				shot("live-%d-%03d"%[z,tick])
			if graphics and z==1 and tick in [45,54,63,72]:
				var original:=camera.global_transform
				var size_before:=camera.size
				var mask_before:=camera.cull_mask
				var hidden: Array=[]
				for n in game.find_children("*","CanvasLayer",true,false):
					if n.visible: hidden.append(n);n.hide()
				paused=true
				camera.cull_mask=mask_before | (1<<19)
				camera.size=2.18
				for view in [["front",Vector3(0,.08,1)],["rear",Vector3(0,.08,-1)],["left",Vector3(1,.08,0)],["right",Vector3(-1,.08,0)],["front_oblique",Vector3(1,.34,1)],["rear_oblique",Vector3(-1,.34,-1)]]:
					var center:Vector3=victim.global_position+Vector3.UP*(.80 if worker_mode else .90)
					var eye:Vector3=center+victim.global_basis*Vector3(view[1]).normalized()*3.2
					camera.global_position=eye
					camera.look_at(center)
					camera.force_update_transform()
					await process_frame
					RenderingServer.camera_set_transform(camera.get_camera_rid(),camera.global_transform)
					shot("studio-%03d-%s"%[tick,view[0]])
				camera.global_transform=original
				camera.size=size_before;camera.cull_mask=mask_before
				camera.force_update_transform();await process_frame
				for n in hidden:n.show()
				paused=false


		if not worker_mode: point_input(Vector2.ZERO,false)
	var f:=FileAccess.open(folder.path_join("travel.json"),FileAccess.WRITE);f.store_string(JSON.stringify(rows));f.close()
	game.carry.set_physics_process(false);game.set_physics_process(false);game.sound.stop_playback()
	for i in 12:OS.delay_msec(20);await process_frame
	game.queue_free()
	for i in 4:await process_frame
	quit()
