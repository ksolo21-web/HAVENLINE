extends SceneTree
const Session := preload("res://tests/lifecycle_test_profile.gd")
func _initialize()->void:call_deferred("go")
func go()->void:
	var profile = preload("res://tests/lifecycle_test_profile.gd").Profile.new()
	if not profile.configure(OS.get_cmdline_user_args()):
		quit(2)
		return
	var game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	for tick in 4:await physics_frame
	if game.persist_blocked:
		quit(2)
		return
	var tower=game.defense_tower
	var at:Vector3=tower.global_position+Vector3(4.,0.,1.1)
	var data:={}
	var pass_all:=true
	for boss:bool in [false,true]:
		var wolf=game.encounters._add(at,boss,990+int(boss),at)
		for yaw:float in [0.,PI*.5,PI]:
			wolf.rotation.y=yaw
			var target:Vector3=wolf.global_position+Vector3.UP*.72*wolf.size_factor()
			var actual:Vector3=tower._visible_contact(wolf,target)
			var facing:Vector3=game.camera.global_basis.z.normalized()
			var advance:=facing.dot(actual-target)
			var pixel_error:float=game.camera.unproject_position(actual).distance_to(game.camera.unproject_position(target))
			data[("boss" if boss else "wolf")+" "+str(snappedf(rad_to_deg(yaw),.1))]={"depth_m":advance,"projected_error_px":pixel_error}
			pass_all=pass_all and advance>.3 and pixel_error<.01
	var f:=FileAccess.open(OS.get_environment("CONTACT_JSON"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"source":"6f35a670bac57a0002aa44b9abedbb257848fd30","pass":pass_all,"samples":data},"  ")+"\n")
	f.close()
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for i in 5:await process_frame
	quit(0 if pass_all else 1)
