extends SceneTree
var f
func _initialize():call_deferred("run")
func run():
	f=preload("res://field_opening.tscn").instantiate()
	root.add_child(f)
	f.set_physics_process(false)
	f.carry.set_physics_process(false)
	var ledger=f.inventory
	for id in [f.Progress.HEARTH,f.Progress.FIRST]+f.Progress.STORAGE:
		for kind in ledger.costs[id]:
			for i in int(ledger.costs[id][kind]):
				ledger.collect("%s-%s-%d"%[id,kind,i],kind)
				ledger.payment(id,kind,false)
	f._apply_hearth(true,false)
	var h=f.depot.house
	f.actor.position=h.global_position+Vector3(.15,0,1.84)
	f.camera.position=f.actor.position+Vector3(7,11,11)
	for i in 36:h._physics_process(1./60)
	for qty in [9,253,999,1000,1001,99999,100001,999999,1000000]:
		for kind in ledger.KINDS:ledger.stored[kind]=qty
		f.carry.sync()
		f._refresh_field()
		f.depot._update_interior()
		for zoom:float in [1.,2.]:
			f.set_zoom_ratio(zoom)
			await process_frame
			RenderingServer.force_draw(false,1./60.)
			var boxes:={}
			for k in f.depot.labels:
				var node:Label3D=f.depot.labels[k]
				var at=f.camera.unproject_position(node.global_position)
				var extent=node.get_aabb()
				var dx=extent.size.x*.5
				var dy=extent.size.y*.5
				var px=f.camera.unproject_position(node.global_position+f.camera.global_basis.x*dx).distance_to(at)
				var py=f.camera.unproject_position(node.global_position+f.camera.global_basis.y*dy).distance_to(at)
				boxes[k]=Rect2(at-Vector2(px,py),Vector2(2.*px,2.*py))
			var overlaps:=[]
			for a in boxes:
				for b in boxes:
					if a<b and boxes[a].intersects(boxes[b]):overlaps.append([a,b,str(boxes[a].intersection(boxes[b]).get_area())])
			print("LABELS ",JSON.stringify({"quantity":qty,"zoom":zoom,"overlap":overlaps}))
			if qty in [999999,1000000] and zoom==1.:
				root.get_texture().get_image().save_jpg(OS.get_environment("STOCK_IMAGES").path_join("after-%d.jpg"%qty),.89)
	f.queue_free()
	for tick in 3:await process_frame
	quit()
