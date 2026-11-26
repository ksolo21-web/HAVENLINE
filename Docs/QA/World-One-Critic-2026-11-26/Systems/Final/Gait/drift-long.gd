extends SceneTree
func _initialize():call_deferred("run")
func run():
	var world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await physics_frame
	world.actor.position=Vector3(55,0,55)
	var touch:=InputEventScreenTouch.new()
	touch.index=5;touch.position=Vector2(80,620);touch.pressed=true;world._input(touch)
	var rng:=RandomNumberGenerator.new();rng.seed=146835
	var until:=0
	while not world.gait_motor.skeleton: await physics_frame
	var sk:Skeleton3D=world.gait_motor.skeleton
	var minv=1.;var maxv=1.;var first=-1
	for t in 13000:
		if t==until:
			var drag:=InputEventScreenDrag.new()
			drag.index=5;drag.position=touch.position+Vector2.RIGHT.rotated(rng.randf_range(-PI,PI))*rng.randf_range(32,82)
			world._input(drag)
			until+=rng.randi_range(10,48)
		await physics_frame
		for side in world.gait_motor.leg_chains:
			for index in side:
				var a=sk.get_bone_pose_scale(index)
				var minscale=minf(a.x,minf(a.y,a.z));var maxscale=maxf(a.x,maxf(a.y,a.z))
				if minscale<minv:minv=minscale
				if maxscale>maxv:maxv=maxscale
				if first<0 and (minscale<.8 or maxscale>1.2 or not a.is_finite()):
					first=t;print("FIRST ",t," ",sk.get_bone_name(index)," ",a," action ",world.gait_motor.special)
		if t%700==0:print("TRACE ",t," ",minv," ",maxv)
		if minv < 0.01 or maxv>80.:break
	print("RESULT ",JSON.stringify({"bad_at":first,"min":minv,"max":maxv}))
	world.sound.stop_playback()
	world.queue_free()
	for i in 8:await process_frame
	quit()
