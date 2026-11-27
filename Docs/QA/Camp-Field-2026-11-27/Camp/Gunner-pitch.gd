extends SceneTree
const Session=preload("res://tests/lifecycle_test_profile.gd")
func _initialize()->void:call_deferred("run")
func xyz(p:Vector3)->Array:return [p.x,p.y,p.z]
func tf(t:Transform3D)->Array:return [xyz(t.basis.x),xyz(t.basis.y),xyz(t.basis.z),xyz(t.origin)]
func run()->void:
	var guard=Session.Profile.new()
	if not guard.configure(OS.get_cmdline_user_args()):quit(2);return
	var game=load("res://field_opening.tscn").instantiate()
	root.add_child(game);current_scene=game
	for i in 4:await physics_frame
	game.set_physics_process(false)
	var tower=game.defense_tower
	if not tower.active or game.persist_blocked:quit(2);return
	var art=tower.art;var rig:Skeleton3D=art.crew.rig
	var poses:Array=[]
	var base:Vector3=tower.global_position
	var dt:=1./120.
	for i in range(18):
		var a:=TAU*floori(i/6.)/3.
		var y:=4.0 if i%6<3 else -2.0
		var target:=base+Vector3(5.6*sin(a),y,5.6*cos(a))
		art.cycle_age = [0.,.21,.64][i%3]
		for t in 80:art.aim_at_world(target,dt)
		art.animate(0.)
		
		var forms:=[]
		var U:Transform3D=art.swivel.global_transform.affine_inverse()*rig.global_transform
		for j in rig.get_bone_count():
			forms.append([String(rig.get_bone_name(j)),tf(U*rig.get_bone_global_pose(j))])
		var palms:=[]

		for side in ["R","L"]:
			var at:Vector3=art.crew.grip_position(side)
			palms.append(at.distance_to(rig.to_global(rig.get_bone_global_pose(art.crew.bones["Palm."+side]).origin)))
		var parts:={}
		for part_name:String in ["RightWindlass","RightWindlassHandle","LeftBreechControl","LeftBreechControlHandle","GunnerTread","Turntable","BowStock","LoadedQuarrel"]:
			var part:Node3D=art.swivel if part_name=="Turntable" else art.swivel.find_child(part_name,true,false)
			parts[part_name]=tf(art.swivel.global_transform.affine_inverse()*part.global_transform)
		poses.append({"id":[i,snappedf(rad_to_deg(art.swivel.rotation.y),.01),snappedf(rad_to_deg(art.bow.rotation.x),.01)],"bones":forms,"mount":tf(art.bow.transform),"bolt":tf(art.bolt.transform),"gloves":palms,"parts":parts})
	var f=FileAccess.open(OS.get_environment("CAMP_OUT").path_join("extrema.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(poses));f.close()
	await Session.drain_field_audio(self,game);game.queue_free()
	for i in 3:await process_frame
	quit()
