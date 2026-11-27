extends SceneTree
const Session=preload("res://tests/lifecycle_test_profile.gd")
var world
var record:={}
const XS:=[-1.91,-1.72,-.85,0.,.85,1.72,1.91]
func _initialize()->void:call_deferred("run")
func qpos(p:Vector3)->Array:return [snappedf(p.x,.001),snappedf(p.y,.001),snappedf(p.z,.001)]
func run()->void:
	var profile=Session.Profile.new()
	if not profile.configure(OS.get_cmdline_user_args()):quit(2);return
	world=load("res://field_opening.tscn").instantiate();root.add_child(world);current_scene=world
	for i in 5:await physics_frame
	if world.persist_blocked or not world.counter.active:
		printerr("Need a paid fixture in an isolated profile, ",world.persist_error)
		quit(2);return
	world.set_physics_process(false)
	var counter=world.counter
	var valid:=true
	for moved in [false,true]:
		if moved:
			var bay:=Vector2(4.,world.field_env.COURTS[-1].y)
			world.actor.global_position=Vector3(1.7,0,1.8)
			var actual_reason:String=world.camp_layout.reason("north_counter",bay)
			record["relocation_validation"]=actual_reason
			if not actual_reason.is_empty():valid=false
			counter.move_to_bay(bay.x)
			await physics_frame
		for elevation:float in [0.,1.10]:
			for side:float in [1.,-1.]:
				for x:float in XS:
					var at:Vector3=counter.to_global(Vector3(x,elevation,side*1.91))
					var far:Vector3=counter.to_global(Vector3(x,elevation,-side*1.91))
					world.actor.position=at;world.actor.velocity=Vector3.ZERO
					var result=world.actor.move_and_collide(far-at)
					var only_physics:Vector3=counter.to_local(world.actor.global_position)
					world.previous_dry_position=at
					world.constrain_private_snow_travel()
					var local:Vector3=counter.to_local(world.actor.global_position)
					var okay:=local.z*side>=.955 and only_physics.z*side>=.955
					if not okay:valid=false
					record["%s,%0.2f,%d,%0.2f"%["moved" if moved else "original",elevation,int(side),x]]={"body_end_xz":[only_physics.x,only_physics.z],"constrained_end":qpos(local),"hit":str(result.get_collider().name) if result else "","pass":okay}
		for side:float in [-1.,1.]:
			var saved:Vector3=counter.to_global(Vector3(.75,0.,side*.79))
			world.lifecycle._restore_actor({"x":saved.x,"z":saved.z,"yaw":0.,"hp":world.MAX_HP})
			var local:Vector3=counter.to_local(world.actor.position)
			var recovered:bool=local.z*side>=1.26 and absf(local.y)<.001
			record["restored %s %d"%[moved,int(side)]]={"local":qpos(local),"pass":recovered}
			if not recovered:valid=false
	# Public counter transactions, belt deliveries, cashier, and both technical gates
	# have separate dedicated witnesses which use these same runtime bodies.
	record["staff_point_in_front"]=counter.at_service(counter.service_point.global_position)
	record["visitors_outside"]=not counter.at_service(counter.customer_point.global_position)
	record["pass"]=valid and record.staff_point_in_front and record.visitors_outside
	var f=FileAccess.open(OS.get_environment("CAMP_OUT").path_join("Counter-collision.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(record," ")+"\n");f.close()
	await Session.drain_field_audio(self,world);world.queue_free()
	for i in 3:await process_frame
	quit(0 if record["pass"] else 1)
