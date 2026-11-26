extends SceneTree
func _initialize() -> void: call_deferred("capture")
func capture() -> void:
	var world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	world.set_physics_process(false)
	var depot=world.depot
	world.actor.position=depot.SITE+Vector3(-.45,0,2.40)
	world.camera.position=world.actor.position+Vector3(7,11,11)
	world.camera.reset_physics_interpolation()
	world.set_zoom_ratio(2.0)
	world.carry.sync()
	for i in 36: await physics_frame
	world._refresh_field()
	for i in 3: await process_frame
	RenderingServer.force_draw()
	var hud=world.opening_hud
	var folder=OS.get_environment("MINERAL_SHOT")
	root.get_texture().get_image().save_png(folder+".png")
	var tags={}
	for kind in world.Inventory.KINDS:
		tags[kind]={"count":hud.numbers[kind].text,"visible":hud.numbers[kind].is_visible_in_tree(),"inside_hud":hud.plate.get_global_rect().encloses(hud.numbers[kind].get_global_rect()),"shelf":str(depot.bins[kind].global_position),"stock":depot.labels[kind].text}
	var maximum=world.Inventory.EMPTY.duplicate()
	for kind in maximum: maximum[kind]=1000000
	hud.field_status(maximum,hud.prompt.text)
	await process_frame
	hud.reflow()
	await process_frame
	RenderingServer.force_draw()
	root.get_texture().get_image().save_png(folder+"-high.png")
	var high_bounds={}
	for kind in maximum: high_bounds[kind]=hud.plate.get_global_rect().encloses(hud.numbers[kind].get_global_rect())
	print(JSON.stringify({"stored":world.inventory.stored,"bounds":tags,"high_bounds":high_bounds,"panel":str(hud.plate.get_global_rect()),"minerals":str(hud.mineral_row.get_global_rect()),"interior":depot.house.is_interior_visible()}))
	quit()
