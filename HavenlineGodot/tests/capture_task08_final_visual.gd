extends "res://tests/capture_task08_inventory.gd"

var route_index := 0

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--route-index="):
			route_index = int(argument.trim_prefix("--route-index="))
	super._initialize()

func capture_jpg(frame: int) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_jpg(output.path_join("frames/frame-%05d.jpg" % frame), 0.92)

func capture_routes() -> void:
	DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	var furnace: Vector2 = game.sim.point(game.sim.contract.world.furnace)
	var storage: Vector2 = game.sim.point(game.sim.contract.world.storage)
	var north: Vector2 = game.sim.defenses.north.position
	var south: Vector2 = game.sim.defenses.south.position
	var cases := [
		{"route":"deposit","actor":game.sim.lead,"helper":false,"target":furnace,"destination":"furnace_storage"},
		{"route":"deposit","actor":2,"helper":true,"target":storage,"destination":"camp_storage"},
		{"route":"build","actor":game.sim.lead,"helper":false,"target":north,"destination":"defense:north"},
		{"route":"build","actor":2,"helper":true,"target":south,"destination":"defense:south"},
		{"route":"repair","actor":game.sim.lead,"helper":false,"target":furnace,"destination":"repair:furnace"},
		{"route":"repair","actor":2,"helper":true,"target":north,"destination":"repair:north"},
	]
	if route_index < 0 or route_index >= cases.size():
		push_error("T08 final visual route index out of range")
		quit(2)
		return
	var row: Dictionary = cases[route_index]
	var actor_id := int(row.actor)
	var target: Vector2 = row.target
	var destination_id := String(row.destination)
	configure_route_camera(actor_point(actor_id), target_point(target), destination_id)
	for frame in 80:
		if frame == 4:
			commit_route(String(row.route), actor_id, bool(row.helper), target, destination_id)
		await sample(frame)
		await capture_jpg(frame)
		if frame in [24, 50, 70]:
			await capture_png("route-%d-frame-%03d" % [route_index, frame])
	for frame in range(80, 84):
		await sample(frame)
