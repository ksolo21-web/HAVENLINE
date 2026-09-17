extends SceneTree
# T09-owned C5 capture of immutable shipping Character 1 clips.
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
const INITIALIZATION_SETTLE_FRAMES:=2
const FIRST_USE_WARMUP_FRAMES:=8
const TURN_ANGLES:=[-135.0,-90.0,-45.0,0.0,30.0,45.0,90.0,135.0,180.0]
const REVIEW_CAMERA_POSITION:=Vector3(4.5,2.8,6.5)
const REVIEW_CAMERA_TARGET:=Vector3(0,1,0)

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
	assert(candidate.length()==40 and task_id=="T09" and scene_path!="" and player_path!="" and not animations.is_empty())
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
	set_camera(REVIEW_CAMERA_POSITION,REVIEW_CAMERA_TARGET)

func set_camera(position:Vector3,target:Vector3):
	camera.position=position;camera.look_at(target)

func set_pose(anim:String,t:float):
	player.stop();player.play(anim,0.0);player.seek(t,true);player.advance(0.0)

func settle_pose(anim:String,t:float,frames:int=INITIALIZATION_SETTLE_FRAMES):
	for _frame in range(frames):
		set_pose(anim,t);await process_frame;await RenderingServer.frame_post_draw
	set_pose(anim,t)

func warm_pose(anim:String,t:float,frames:int):
	# Do not restart the player between warm-up frames. This allows skeleton
	# modifiers installed by the shipping Character 1 fixture to converge.
	set_pose(anim,t)
	for _frame in range(frames):
		player.advance(0.0);await process_frame;await RenderingServer.frame_post_draw
	set_pose(anim,t)

func _append_skeleton_pose(node:Node,rows:Array):
	if node is Skeleton3D:
		var skeleton:=node as Skeleton3D
		var skeleton_path:=str(subject.get_path_to(skeleton))
		for bone_index in range(skeleton.get_bone_count()):
			var pose:=skeleton.get_bone_global_pose(bone_index)
			var rotation:=pose.basis.get_rotation_quaternion().normalized()
			rows.append({
				"skeleton":skeleton_path,
				"bone_index":bone_index,
				"bone":str(skeleton.get_bone_name(bone_index)),
				"origin":[pose.origin.x,pose.origin.y,pose.origin.z],
				"rotation":[rotation.x,rotation.y,rotation.z,rotation.w],
			})
	for child in node.get_children():
		_append_skeleton_pose(child,rows)

func pose_signature()->Array:
	# Deterministic initialization checks operate on final skeleton transforms,
	# not whole rendered PNG bytes. Camera, AA and lighting are evidence concerns,
	# not animation-pose identity.
	var rows:Array=[]
	_append_skeleton_pose(subject,rows)
	assert(not rows.is_empty(),"C5 pose signature requires a Skeleton3D")
	return rows

func snap(folder:String,name:String,evidence_type:String,animation:String,t:float,speed:float,turn:float):
	var dir=output.path_join(folder);DirAccess.make_dir_recursive_absolute(dir)
	await process_frame;await RenderingServer.frame_post_draw
	var img=get_root().get_texture().get_image()
	var path=dir.path_join(name+".png");img.save_png(path)
	var row={"file":folder+"/"+name+".png","evidence_type":evidence_type,"animation":animation,"time":t,"speed":speed,"turn_degrees":turn,"camera_position":str(camera.position),"resolution":[img.get_width(),img.get_height()]}
	var initialization_probe=(evidence_type in ["real-time-cycle","slow-review-cycle"] and name in ["0000","0001"]) or evidence_type=="transition-start"
	if initialization_probe:
		row["pose_signature"]=pose_signature()
	captures.append(row)

func capture_cycle(anim:String,speed:float,label:String):
	var a=player.get_animation(anim);assert(a)
	var length=maxf(a.length,.033);var fps=30.0;var count=maxi(2,ceili(length*fps))
	set_camera(REVIEW_CAMERA_POSITION,REVIEW_CAMERA_TARGET);await settle_pose(anim,0.0)
	for i in range(count+1):
		var t=minf(length,float(i)/fps);set_pose(anim,t)
		await snap(anim+"/"+label,"%04d"%i,label,anim,t,speed,subject.rotation_degrees.y)

func turn_name(turn:float)->String:
	return "neg-%03d"%absi(int(turn)) if turn<0.0 else "%03d"%int(turn)

func capture_close_contacts(anim:String,mid:float):
	var views=[
		{"name":"upper-front","position":Vector3(2.35,2.35,3.3),"target":Vector3(0,1.75,0),"turn":0.0},
		{"name":"upper-opposite","position":Vector3(2.35,2.35,3.3),"target":Vector3(0,1.75,0),"turn":-90.0},
		{"name":"waist-rear","position":Vector3(2.15,1.55,3.0),"target":Vector3(0,1.15,0),"turn":135.0},
		{"name":"lower-front","position":Vector3(2.0,.85,2.8),"target":Vector3(0,.55,0),"turn":0.0},
		{"name":"lower-rear","position":Vector3(2.0,.85,2.8),"target":Vector3(0,.55,0),"turn":-135.0},
	]
	for view in views:
		subject.rotation_degrees.y=view.turn;set_camera(view.position,view.target)
		await settle_pose(anim,mid)
		await snap(anim+"/close-contacts",view.name,"close-"+view.name,anim,mid,1.0,view.turn)
	subject.rotation_degrees.y=0.0;set_camera(REVIEW_CAMERA_POSITION,REVIEW_CAMERA_TARGET)

func run():
	DirAccess.make_dir_recursive_absolute(output);setup_scene()
	for anim in animations:
		assert(player.has_animation(anim),"missing animation "+anim)
		# The first animation evaluated after scene construction can require more
		# than two rendered frames for SkeletonModifier3D state to converge.
		await warm_pose(anim,0.0,FIRST_USE_WARMUP_FRAMES)
		await capture_cycle(anim,1.0,"real-time-cycle");await capture_cycle(anim,.25,"slow-review-cycle")
		var a=player.get_animation(anim);var mid=a.length*.5
		for turn in TURN_ANGLES:
			subject.rotation_degrees.y=turn;set_pose(anim,mid)
			var label=turn_name(turn)
			await snap(anim+"/turns","turn-"+label,"turn-"+label,anim,mid,1.0,turn)
		subject.rotation_degrees.y=0
		await settle_pose(anim,0.0);await snap(anim+"/transitions","start","transition-start",anim,0,1,0)
		await settle_pose(anim,a.length);await snap(anim+"/transitions","end","transition-end",anim,a.length,1,0)
		await capture_close_contacts(anim,mid)
	var f=FileAccess.open(output.path_join("motion.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"harness":"production_motion_v2","candidate_commit":candidate,"task_id":task_id,"scene":scene_path,"subject_path":subject_path,"animation_player_path":player_path,"initialization_settle_frames":INITIALIZATION_SETTLE_FRAMES,"first_use_warmup_frames":FIRST_USE_WARMUP_FRAMES,"initialization_pose_schema":"skeleton_global_pose_v1","turn_angles_degrees":TURN_ANGLES,"captures":captures,"body_checks_for_critic":["feet","toes","knees","hips","hands","cuffs","belt/pouches","inner legs","boots","gear","ground contact","clipping"]},"\t"));f.close()
	quit()