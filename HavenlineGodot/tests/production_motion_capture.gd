extends SceneTree
# Generic QA-only animation capture. It captures complete cycles and turn/contact
# viewpoints; it never modifies the source scene or claims rig approval.
var output="user://motion-capture"
var candidate=""
var task_id=""
var scene_path=""
var subject_path="."
var player_path=""
var animations:Array[String]=[]
var captures:Array=[]
var root3d:Node3D
var subject:Node3D
var player:AnimationPlayer
var camera:Camera3D

func _initialize():
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):output=arg.trim_prefix("--out=")
		elif arg.begins_with("--candidate="):candidate=arg.trim_prefix("--candidate=")
		elif arg.begins_with("--task="):task_id=arg.trim_prefix("--task=")
		elif arg.begins_with("--scene="):scene_path=arg.trim_prefix("--scene=")
		elif arg.begins_with("--subject-path="):subject_path=arg.trim_prefix("--subject-path=")
		elif arg.begins_with("--animation-player-path="):player_path=arg.trim_prefix("--animation-player-path=")
		elif arg.begins_with("--animations="):
			for name in arg.trim_prefix("--animations=").split(","):
				if not name.is_empty():animations.append(name)
	assert(candidate.length()==40 and task_id!="" and scene_path!="" and player_path!="" and not animations.is_empty())
	call_deferred("run")

func setup_scene():
	var packed=load(scene_path)
	assert(packed is PackedScene,"scene must be PackedScene")
	root3d=Node3D.new();root.add_child(root3d)
	var instance=packed.instantiate();root3d.add_child(instance)
	subject=instance if subject_path=="." else instance.get_node(subject_path)
	player=instance.get_node(player_path)
	assert(subject is Node3D and player is AnimationPlayer)
	var world=WorldEnvironment.new();var env=Environment.new()
	env.background_mode=Environment.BG_COLOR;env.background_color=Color("#172638")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("#dbeaff");env.ambient_light_energy=.9
	world.environment=env;root3d.add_child(world)
	var light=DirectionalLight3D.new();light.rotation_degrees=Vector3(-45,-30,0);light.light_energy=1.2;root3d.add_child(light)
	var ground=MeshInstance3D.new();var plane=PlaneMesh.new();plane.size=Vector2(12,12);ground.mesh=plane;ground.position.y=-.02;root3d.add_child(ground)
	camera=Camera3D.new();root3d.add_child(camera);camera.current=true
	camera.position=Vector3(4.5,2.8,6.5);camera.look_at(Vector3(0,1,0))

func snap(folder:String,name:String,evidence_type:String,animation:String,t:float,speed:float,turn:float):
	var dir=output.path_join(folder);DirAccess.make_dir_recursive_absolute(dir)
	await process_frame;await RenderingServer.frame_post_draw
	var img=get_root().get_texture().get_image()
	var path=dir.path_join(name+".png");img.save_png(path)
	captures.append({"file":folder+"/"+name+".png","evidence_type":evidence_type,"animation":animation,"time":t,"speed":speed,"turn_degrees":turn,"camera_position":str(camera.position),"resolution":[img.get_width(),img.get_height()]})

func capture_cycle(anim:String,speed:float,label:String):
	var a=player.get_animation(anim);assert(a)
	var length=maxf(a.length,.033);var fps=30.0;var count=maxi(2,ceili(length*fps))
	for i in range(count+1):
		var t=minf(length,float(i)/fps)
		player.play(anim);player.seek(t,true)
		await snap(anim+"/"+label,"%04d"%i,label,anim,t,speed,subject.rotation_degrees.y)

func run():
	DirAccess.make_dir_recursive_absolute(output);setup_scene()
	for anim in animations:
		assert(player.has_animation(anim),"missing animation "+anim)
		await capture_cycle(anim,1.0,"real-time-cycle")
		await capture_cycle(anim,.25,"slow-review-cycle")
		var a=player.get_animation(anim);var mid=a.length*.5
		for turn in [0.0,30.0,90.0,180.0]:
			subject.rotation_degrees.y=turn;player.play(anim);player.seek(mid,true)
			await snap(anim+"/turns","turn-%03d"%int(turn),"turn-"+str(int(turn)),anim,mid,1.0,turn)
		subject.rotation_degrees.y=0
		player.play(anim);player.seek(0,true);await snap(anim+"/transitions","start","transition-start",anim,0,1,0)
		player.seek(a.length,true);await snap(anim+"/transitions","end","transition-end",anim,a.length,1,0)
	var f=FileAccess.open(output.path_join("motion.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"harness":"production_motion_v1","candidate_commit":candidate,"task_id":task_id,"scene":scene_path,"subject_path":subject_path,"animation_player_path":player_path,"captures":captures,"body_checks_for_critic":["feet","toes","knees","hips","hands","gear","tails/wings/mane where applicable","ground contact","clipping"]},"\t"));f.close()
	quit()
