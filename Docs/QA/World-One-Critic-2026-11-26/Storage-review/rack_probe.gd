extends SceneTree
## Serialize actual first-tier packet/frame triangles in common Godot coordinates.
const Ledger = preload("res://field_inventory.gd")
const Carry = preload("res://field_carry.gd")
const Art = preload("res://field_art.gd")

func _initialize() -> void: call_deferred("run")

func save_faces(model:Node3D, file_name:String) -> void:
	var all := PackedVector3Array()
	for part:MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		if part.is_visible_in_tree() and part.mesh:
			all.append_array(part.global_transform * part.mesh.get_faces())
	if model is MeshInstance3D and model.mesh:
		all.append_array(model.global_transform * model.mesh.get_faces())
	var sink := FileAccess.open(OS.get_environment("STOCK_TRIANGLES").path_join(file_name + ".f32"),FileAccess.WRITE)
	sink.store_buffer(all.to_byte_array())

func run() -> void:
	var actor := Node3D.new()
	var ledger := Ledger.new()
	var pack := Carry.new()
	var bay := Node3D.new()
	bay.position = Vector3(2,0,3)
	root.add_child(actor)
	root.add_child(pack)
	root.add_child(bay)
	ledger.configure({"trial":{"wood":1}})
	pack.setup(ledger,actor,Art.make)
	pack.set_physics_process(false)
	var checks := {}
	checks["empty rack invisible"] = not pack.frame.is_visible_in_tree()
	for kind: String in Ledger.KINDS:
		pack.define_storage(kind,bay)
		for n in 2:
			checks[kind+" collect "+str(n)] = ledger.collect("earned-"+kind+"-"+str(n),kind)
	pack.sync()
	save_faces(pack.frame,"rack")
	for kind: String in Ledger.KINDS:
		var pool: Array = pack.pieces["carry/"+kind]
		for i in 2: save_faces(pool[i],kind+str(i))
	for kind: String in ["metal","slate","coal","meat","stone","wood"]:
		for n in 2:
			var old_stock:int = ledger.stored[kind]
			var last_position: Vector3 = pack.pieces["carry/"+kind][1-n].global_position
			checks[kind+" send "+str(n)] = pack.deposit_storage(kind)
			var flight: Dictionary = pack.flights[0]
			checks[kind+" launch from previously visible unit "+str(n)] = flight.mesh.global_position.distance_to(last_position)<.0001
			pack.advance(.14)
			checks[kind+" held in transit "+str(n)] = ledger.stored[kind]==old_stock and pack.flights.size()==1
			var has_rear:bool = pack.hand_visible["slate"]+pack.hand_visible["metal"]>0
			var has_middle:bool = has_rear or pack.hand_visible["meat"]+pack.hand_visible["coal"]>0
			checks[kind+" support during transit "+str(n)] = pack.rear_support.is_visible_in_tree()==has_rear and pack.middle_support.is_visible_in_tree()==has_middle
			pack.advance(.16)
			checks[kind+" completes once "+str(n)] = ledger.stored[kind]==old_stock+1 and pack.flights.size()==0
	checks["last unit retires rack"] = not pack.frame.is_visible_in_tree()
	print(JSON.stringify(checks))
	quit(int(false in checks.values()))
