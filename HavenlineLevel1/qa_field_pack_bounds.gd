extends SceneTree
## The camera and item extents here are the actual orthographic rig and GLBs.

const Ledger = preload("res://field_inventory.gd")
const Carry = preload("res://field_carry.gd")
const Art = preload("res://field_art.gd")
const Zoom = preload("res://orbit_camera.gd")
var failures: Array[String] = []
var cases := []
var view := SubViewport.new()
var actor := Node3D.new()
var camera := Camera3D.new()
var carry := Carry.new()
var book := Ledger.new()
var zoom := Zoom.new()

func check(result: bool, name_: String) -> void:
	if not result and name_ not in failures:
		failures.append(name_)
		push_error(name_)

func _initialize() -> void: call_deferred("run")

func top(kind: String) -> Node3D:
	var pool: Array = carry.pieces["carry/"+kind]
	for i in range(pool.size()-1,-1,-1):
		if pool[i].visible: return pool[i]
	return null

func visible_count(kind: String) -> int:
	return carry.pieces["carry/"+kind].filter(func(item):return item.visible).size()

func margin(kind: String) -> float:
	var unit := top(kind)
	if not unit: return 1.0
	var edge := INF
	for m: MeshInstance3D in unit.find_children("*","MeshInstance3D",true,false):
		for j in 8:
			var vertex := m.to_global(m.mesh.get_aabb().get_endpoint(j))
			edge=minf(edge,camera.unproject_position(vertex).y)
	return edge/view.size.y

func run() -> void:
	view.own_world_3d=true
	root.add_child(view)
	view.add_child(actor)
	view.add_child(camera)
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.position=Vector3(7,11,11)
	camera.look_at(Vector3.ZERO)
	camera.current=true
	book.configure({"buy":{"wood":3,"stone":2}})
	view.add_child(carry)
	carry.setup(book,actor,Art.make)
	carry.set_physics_process(false)
	var bin := Node3D.new()
	view.add_child(bin)
	bin.position=Vector3(2,0,2)
	carry.define_storage("wood",bin)
	carry.define_receiver("buy",bin)
	for format_: Vector2i in [Vector2i(1280,720),Vector2i(720,1280)]:
		view.size=format_
		for ratio: float in [1.,2.]:
			zoom.set_ratio(camera,ratio)
			for amount: int in [3,12,37,42,1000000]:
				for kind: String in Ledger.KINDS: book.carried[kind]=amount
				carry.sync()
				var lowest := 1.0
				for pose: float in [0.,.85,3.14,4.71]:
					actor.rotation.y=pose
					actor.position=Vector3(.20*sin(pose),0,.30*cos(pose))
					carry.advance(1./60.)
					for kind in Ledger.KINDS:
						var item := top(kind)
						lowest=minf(lowest,margin(kind))
						check(item != null and item.global_position.is_equal_approx(carry._place("carry",kind,amount-1)),kind+" visible representative")
						check(visible_count(kind)==amount if amount==3 or (amount==12 and ratio==1.) else visible_count(kind)<=amount,kind+" preserves ordinary loads")
						check(book.carried[kind]==amount,kind+" count unchanged")
						check(carry.pieces["carry/"+kind].size()<(75 if kind in Ledger.ORIGINAL_KINDS else 200),kind+" bounded pool")
					check(top("wood").position.x<top("stone").position.x and top("meat").position.z<top("wood").position.z,"segregated lanes")
				check(lowest>=.08,"8 percent margin across views and turns")
				var drawn := {}
				for kind in Ledger.KINDS: drawn[kind]=visible_count(kind)
				cases.append({"viewport":str(format_),"zoom":ratio,"logical":amount,"visible":drawn,"min_headroom":snappedf(lowest,.001)})
	# A camera-only zoom update while stationary must change the visible cap.
	view.size=Vector2i(1280,720)
	zoom.set_ratio(camera,1.)
	carry.advance(.02)
	var full := visible_count("wood")
	var pool: Array=carry.pieces["carry/wood"].duplicate()
	zoom.set_ratio(camera,2.)
	carry.advance(.02)
	check(visible_count("wood")<full and carry.pieces["carry/wood"]==pool,"idle zoom reuses pool")
	# Exercise real earned tokens, overflow receipts and a reload.
	book.carried=Ledger.EMPTY.duplicate()
	for i in 60: book.collect("tree-%d"%i,"wood")
	carry.sync()
	check(carry.pickup("one-more","wood",Vector3(2,0,1)),"overflow pickup")
	var incoming: Dictionary=carry.flights[0]
	zoom.set_ratio(camera,1.3)
	carry.advance(.4)
	check(incoming.mesh.global_position.is_equal_approx(top("wood").global_position) and incoming.mesh.global_basis.is_equal_approx(top("wood").global_basis),"pickup lands at physical upper slot after zoom")
	var source := top("wood").global_transform
	check(carry.deposit_storage("wood"),"overflow deposit dispatches")
	check(carry.flights.size()==1 and carry.flights[0].mesh.global_transform.is_equal_approx(source),"deposit starts at physical upper slot")
	carry.advance(.4)
	source=top("wood").global_transform
	check(carry.contribute("buy") and carry.flights.size()==1 and carry.flights[0].mesh.global_transform.is_equal_approx(source),"spend starts at physical upper slot")
	carry.advance(.4)
	var resumed := Ledger.new()
	resumed.configure(book.costs)
	check(resumed.restore(book.snapshot()) and resumed.carried.wood==59 and resumed.stored.wood==1 and resumed.paid.buy.wood==1 and resumed.collected.size()==61,"reload conserves all 61 tokens")
	print(JSON.stringify({"cases":cases,"failures":failures}))
	quit(1 if not failures.is_empty() else 0)
