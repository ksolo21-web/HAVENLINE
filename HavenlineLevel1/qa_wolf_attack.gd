extends SceneTree
## Exercise both imported wolf skins with the same clock and range checks used by the pack.
const Enemy = preload("res://field_enemy.gd")
var results := {}
var observations := {}
var actor := Node3D.new()
var hits: Array = []

func _initialize() -> void:
	call_deferred("run")

func check(key:String, passed:bool) -> void:
	results[key]=passed
	if not passed: push_error("Wolf attack check failed: "+key)

func bone_angle(s:Skeleton3D, bone:String) -> float:
	return rad_to_deg(s.get_bone_pose_rotation(s.find_bone(bone)).get_angle())

func bite_pose(wolf:Enemy, s:Skeleton3D, damage:int) -> void:
	hits.append({"damage":damage,"jaw":bone_angle(s,"Jaw"), "state":wolf.state,
		"clip":wolf.animator.current_animation,"elapsed":wolf._bite_duration()-wolf.timer})

func exercise(boss:bool, dt:float) -> void:
	var wolf:=Enemy.new()
	wolf.is_boss=boss
	root.add_child(wolf)
	wolf.configure(actor)
	var label:=("alpha" if boss else "ridge")+"_"+str(roundi(1.0/dt))+"hz_"
	var s:=wolf.visual.find_children("*","Skeleton3D",true,false)[0] as Skeleton3D
	var jaw:=s.find_bone("Jaw")
	check(label+"jaw_parented_to_head",jaw>=0 and s.get_bone_parent(jaw)==s.find_bone("Head"))
	if jaw<0:
		wolf.free()
		return
	var rig_has_jaw:=false
	for bind in wolf.surface.skin.get_bind_count():
		if wolf.surface.skin.get_bind_name(bind)=="Jaw":
			var surface_arrays:=wolf.surface.mesh.surface_get_arrays(0)
			var indices:PackedInt32Array=surface_arrays[Mesh.ARRAY_BONES]
			var weights:PackedFloat32Array=surface_arrays[Mesh.ARRAY_WEIGHTS]
			for i in indices.size():
				if indices[i]==bind and weights[i]>.75: rig_has_jaw=true;break
	check(label+"jaw_weights_on_original_textured_fur",rig_has_jaw and wolf.surface.mesh.get_surface_count()>=3)
	actor.position=Vector3(0,0,2.1+(.54 if boss else 0.))
	wolf.player_hit.connect(func(amount:int):bite_pose(wolf,s,amount))
	hits.clear()
	var peak_jaw:=0.
	var hip_motion:={}
	var low_root:=INF
	var high_root:=-INF
	var first_landing:=false
	var settled_jaw:=INF
	var stages:={}
	for tick in 225:
		wolf.advance(dt)
		stages[wolf.state]=true
		if wolf.state in ["windup","lunge","recover"]:
			peak_jaw=maxf(peak_jaw,bone_angle(s,"Jaw"))
			var root_y:=s.get_bone_pose_position(s.find_bone("Root")).y
			low_root=minf(low_root,root_y)
			high_root=maxf(high_root,root_y)
			for leg:String in ["FrontL","FrontR","RearL","RearR"]:
				for joint:String in ["Hip","Knee","Hock","Paw"]:
					var key:=leg+joint
					hip_motion[key]=maxf(hip_motion.get(key,0.),bone_angle(s,key))
		if wolf.state=="recover":
			first_landing=true
			settled_jaw=bone_angle(s,"Jaw")
		if first_landing and wolf.state=="guard":break
	check(label+"every_phase_plays",stages.has_all(["windup","lunge","recover","guard"]))
	check(label+"opens_and_settles",peak_jaw>=40.0 and settled_jaw<1.0)
	check(label+"springs_through_hips_shoulder_and_four_limb_chains",high_root-low_root>.17 and hip_motion.size()==16 and hip_motion.values().min()>3.)
	var dmg:=Enemy.BOSS_BITE_DAMAGE if boss else Enemy.BITE_DAMAGE
	var contact_time:=wolf._bite_duration()*Enemy.JAW_CONTACT/Enemy.BITE_DURATION
	check(label+"one_damage_at_closed_jaw",hits.size()==1 and hits[0].damage==dmg and hits[0].state=="lunge" and hits[0].clip=="Bite" and hits[0].jaw<9. and hits[0].elapsed>=contact_time-.00001 and hits[0].elapsed<=contact_time+dt+.00001)
	observations[label.trim_suffix("_")]={"open_degrees":peak_jaw,"root_travel_m":high_root-low_root,"min_limb_rotation_degrees":hip_motion.values().min(),"contact":hits.duplicate(true)}
	for dodge:bool in [false,true]:
		wolf.reset_encounter()
		actor.position=Vector3(0,0,2.1+(.54 if boss else 0.))
		hits.clear()
		var launched:=false
		for tick in 180:
			if wolf.state=="lunge":
				launched=true
				if dodge:actor.position=Vector3(5.,0,1.)
			wolf.advance(dt,Callable(),dodge or not launched)
			if launched and wolf.state!="lunge":break
		check(label+("side_step_misses" if dodge else "sanctuary_cancels"),launched and hits.is_empty())
	wolf.free()

func run() -> void:
	root.add_child(actor)
	for boss:bool in [false,true]:
		for dt:float in [1.0/60.,1.0/20.]:
			exercise(boss,dt)
	var passed:=not results.values().has(false)
	print("WOLF_ATTACK ",JSON.stringify({"passed":passed,"checks":results,"observed":observations}))
	quit(0 if passed else 1)
