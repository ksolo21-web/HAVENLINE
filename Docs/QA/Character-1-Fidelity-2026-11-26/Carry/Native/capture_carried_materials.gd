extends SceneTree
const ANCHOR := Vector2(100,300)
var world
var out := OS.get_environment("PACK_PROOF")
var stats := []
func _initialize(): call_deferred("run")
func input_stick(down:bool, dir:Vector2) -> void:
	var touch:=InputEventScreenTouch.new();touch.index=1;touch.position=ANCHOR;touch.pressed=down;world._input(touch)
	if down:
		var drag:=InputEventScreenDrag.new();drag.index=1;drag.position=ANCHOR+dir*82.;world._input(drag)
func capture(label:String, slot_mode:String, zoom:float, direction:Vector2) -> void:
	for kind in world.Inventory.KINDS:
		world.inventory.carried[kind]=2 if slot_mode=="mixed" else (42 if kind=="wood" else 0)
	world.set_zoom_ratio(zoom)
	world.carry.sync()
	world.actor.global_position=Vector3(55,0,55);world.actor.velocity=Vector3.ZERO;world.actor.rotation.y=0.
	world.camera.global_position=world.actor.global_position+Vector3(7,11,11)
	input_stick(true,direction)
	for i in 45:await physics_frame
	RenderingServer.force_draw(false)
	var im=root.get_texture().get_image();im.save_jpg(out+"/"+label+".jpg",.95)
	var mins:=Vector2(INF,INF);var maxs:=Vector2(-INF,-INF)
	var n:=0
	for k in world.Inventory.KINDS:
		for piece in world.carry.pieces["carry/"+k]:
			if not piece.is_visible_in_tree():continue
			n+=1
			for m in piece.find_children("*","MeshInstance3D",true,false):
				for idx in m.mesh.get_surface_count():
					for point in m.mesh.surface_get_arrays(idx)[Mesh.ARRAY_VERTEX]:
						var px:Vector2=world.camera.unproject_position(m.to_global(point));mins=mins.min(px);maxs=maxs.max(px)
	stats.append({"mode":slot_mode,"zoom":zoom,"stage":label,"material_packets":n,"yaw":world.actor.rotation.y,"speed":world.actor.velocity.length(),"rect":[mins.x,mins.y,maxs.x,maxs.y]})
	input_stick(false,Vector2.ZERO)
	for i in 3:await physics_frame
func run():
	world=load("res://field_opening.tscn").instantiate();root.add_child(world)
	for i in 3:await physics_frame
	for z in [1.,2.]:
		await capture("mixed-walk-"+str(int(z)),"mixed",z,Vector2(.79,.59)*.43)
		await capture("mixed-run-"+str(int(z)),"mixed",z,Vector2(-.79,-.59)*.95)
		await capture("wood-side-"+str(int(z)),"wood",z,Vector2(.95,.10))
	var f=FileAccess.open(out+"/Projection.json",FileAccess.WRITE);f.store_string(JSON.stringify(stats,"  "));f.close()
	world.queue_free()
	for i in 6:await process_frame
	quit()
