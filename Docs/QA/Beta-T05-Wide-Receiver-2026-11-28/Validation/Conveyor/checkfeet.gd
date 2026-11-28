extends SceneTree
func _initialize():call_deferred("run")
func run():
	var world=load("res://field_opening.tscn").instantiate()
	root.add_child(world);world.set_physics_process(false)
	var b=world.settlement_loop.conveyors
	b.refresh_paths()
	var ais=b.network.aisles
	for p:Vector3 in [Vector3(2.92,0,-5.4),Vector3(5.64,0,-5.01),Vector3(2.52,0,-7.48),Vector3(5.10,0,-8.4),Vector3(5.35,0,-8.43),Vector3(2.65,0,-5.25)]:
		print("FOOT ",p," rect ",ais._body_clear(Vector2(p.x,p.z),.31)," hardware ",ais.disc_clear(Vector2(p.x,p.z),.31)," public ",ais.resume_position(p,.31))
	quit()
