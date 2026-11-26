extends SceneTree

var w
var token := 0
var vertices := {}
var out := OS.get_environment("PACK_OUT")
var old := OS.get_environment("PACK_OLD")=="1"

func _initialize(): run.call_deferred()

func credit(kind):
	token += 1
	assert(w.inventory.collect("qa/" + str(token), kind))

func pay(id):
	for kind in w.inventory.costs[id]:
		for i in w.inventory.costs[id][kind]:
			credit(kind)
			assert(w.inventory.payment(id,kind,false))

func points(mesh):
	var rid := mesh.get_instance_id() as int
	if not vertices.has(rid):
		var list := PackedVector3Array()
		for s in mesh.get_surface_count():
			list.append_array(mesh.surface_get_arrays(s)[Mesh.ARRAY_VERTEX])
		vertices[rid]=list
	return vertices[rid]

func packet_rect(node):
	var rect := Rect2()
	var fresh := true
	var all_parts: Array=[node] if node is MeshInstance3D else []
	all_parts.append_array(node.find_children("*","MeshInstance3D",true,false))
	for part in all_parts:
		if not part.is_visible_in_tree() or not part.mesh: continue
		var transform:Transform3D=part.global_transform
		for local in points(part.mesh):
			var loc:Vector2=w.camera.unproject_position(transform*local)
			rect=Rect2(loc,Vector2.ZERO) if fresh else rect.expand(loc)
			fresh=false
	return rect

func pinch():
	var middle:=root.get_visible_rect().size*Vector2(.65,.60)
	for i in 2:
		var e:=InputEventScreenTouch.new()
		e.index=40+i
		e.pressed=true
		e.position=middle+Vector2.RIGHT*(i*60-30)
		root.push_input(e,true)
	for i in 2:
		var e:=InputEventScreenDrag.new()
		e.index=40+i
		e.position=middle+Vector2.RIGHT*(i*150-75)
		root.push_input(e,true)
	for i in 2:
		var e:=InputEventScreenTouch.new()
		e.index=40+i
		e.pressed=false
		e.position=middle+Vector2.RIGHT*(i*150-75)
		root.push_input(e,true)
	assert(w.get_zoom_ratio()==2.0)

func run():
	var path:=out+"/measurements.jsonl"
	var data:=FileAccess.open(path,FileAccess.WRITE)
	w=load("res://field_opening.tscn").instantiate()
	root.add_child(w)
	for i in 5: await process_frame
	w.process_mode=Node.PROCESS_MODE_DISABLED
	w.set_process_input(true)
	var baseline:Dictionary=w.inventory.snapshot()
	for scenario in ["east","house"]:
		var house:bool=scenario=="house"
		var loads:Array=[[37,8,4]] if house else [[3,0,0],[12,0,0],[37,0,0],[42,0,0],[42,9,4]]
		if old and not house: loads=[[42,9,4]]
		for loadout in loads:
			assert(w.inventory.restore(baseline))
			pay("center_hearth")
			if house:
				pay("expansion_1")
				pay("storage_wood")
			var pos:=Vector3(-2.509429,0,.172711) if house else Vector3(5.050497,0,.00749546)
			w.actor.position=pos
			w.actor.rotation.y=.0739433 if house else 1.576126
			w.camera.position=pos+Vector3(7,11,11)
			w.camera.look_at(pos)
			w._apply_hearth(true,false)
			for gate in w.gates:
				gate.target_open=true
				gate.advance(1.,Vector3(55,0,55),.3)
			for i in 60: w.depot.house._physics_process(1./60.)
			for idx in 3:
				for i in loadout[idx]:credit(["wood","stone","meat"][idx])
			w._refresh_field()
			for zoom in [1,2]:
				w.set_zoom_ratio(1.)
				if zoom==2:
					w.process_mode=Node.PROCESS_MODE_INHERIT
					pinch()
					w.process_mode=Node.PROCESS_MODE_DISABLED
				w.carry.sync()
				await process_frame
				RenderingServer.force_draw(false)
				var img:=root.get_texture().get_image()
				var basename:="%s-%dW-%dS-%dM-%dx"%[scenario,loadout[0],loadout[1],loadout[2],zoom]
				assert(img.save_jpg(out+"/"+basename+".jpg",.93)==OK)
				var rect:=Rect2()
				var counts:={}
				for kind in ["wood","stone","meat"]:
					counts[kind]=0
					for piece in w.carry.pieces.get("carry/"+kind,[]):
						if piece.is_visible_in_tree():
							var r:Rect2=packet_rect(piece)
							rect=r if rect.size==Vector2.ZERO else rect.merge(r)
							counts[kind]+=1
				var sz:=root.get_visible_rect().size
				var row={"name":basename,"frame":[img.get_width(),img.get_height()],"logical":[sz.x,sz.y],"zoom":w.get_zoom_ratio(),"camera_span":w.camera.size,"inventory":w.inventory.carried.duplicate(),"visible":counts,"rack_bounds_normalized":[rect.position.x/sz.x,rect.position.y/sz.y,rect.end.x/sz.x,rect.end.y/sz.y],"house_tier":w.depot.house.tier,"house_open":w.depot.house.doors_open,"inside_view":w.depot.house.inside_view,"camera":str(w.camera.global_transform),"actor":str(w.actor.global_transform)}
				data.store_line(JSON.stringify(row))
				data.flush()
				print("MATRIX ",basename, " ",row.rack_bounds_normalized)
	quit()
