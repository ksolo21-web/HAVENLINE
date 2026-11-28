extends SceneTree
## The camera and item extents here are the actual orthographic rig and GLBs.

const Ledger = preload("res://field_inventory.gd")
const Carry = preload("res://field_carry.gd")
const Art = preload("res://field_art.gd")
const Zoom = preload("res://orbit_camera.gd")
var failures: Array[String] = []
var minimum_joint_depth := INF
var checked_joints := 0
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

func check_distinct_bays() -> void:
	var footprint := {}
	for kind: String in Ledger.KINDS:
		var packets: Array = carry.pieces.get("carry/" + kind, [])
		for i in mini(2, packets.size()):
			var packet: Node3D = packets[i]
			if not packet.visible: continue
			var size: Vector3 = carry.measured[kind]
			var box := packet.transform * AABB(Vector3(-size.x*.5, 0, -size.z*.5), size)
			var floor_rect := Rect2(box.position.x, box.position.z, box.size.x, box.size.z)
			for other_kind: String in footprint:
				if other_kind != kind:
					for other_rect: Rect2 in footprint[other_kind]:
						check(not floor_rect.intersects(other_rect), kind + " occupies a physically separate bay from " + other_kind)
			if not footprint.has(kind): footprint[kind] = []
			footprint[kind].append(floor_rect)

# A centerline leaving the inserted timber end must cross a real triangle
# of the neighboring timber inside the tolerance. Bounds overlap is insufficient.
func insertion(start: Vector3, midpoint: Vector3, timber: MeshInstance3D) -> float:
	var from := timber.to_local(start)
	var to := timber.to_local(midpoint)
	var faces := timber.mesh.get_faces()
	var depth := INF
	for i in range(0,faces.size(),3):
		var contact: Variant = Geometry3D.segment_intersects_triangle(from,to,faces[i],faces[i+1],faces[i+2])
		if contact != null:
			depth = minf(depth,start.distance_to(timber.to_global(contact)))
	return depth

func check_mount() -> void:
	var frame_mesh := carry.frame.find_children("*","MeshInstance3D",true,false)[0] as MeshInstance3D
	for row in carry.shelves.size():
		var shelf: MeshInstance3D = carry.shelves[row]
		for side in 2:
			var brace: MeshInstance3D = carry.braces[row*2+side]
			check(brace.visible==shelf.visible,"empty rows retract both supports")
			if not shelf.visible: continue
			var box := brace.mesh.get_aabb()
			var heel := brace.to_global(Vector3(box.position.x,0,0))
			var seat := brace.to_global(Vector3(box.end.x,0,0))
			var middle := (heel+seat)*.5
			for depth: float in [insertion(heel,middle,frame_mesh),insertion(seat,middle,shelf)]:
				check(depth>=.002 and depth<.105,"brace ends meet actual frame and shelf triangles by at least 2 mm")
				minimum_joint_depth=minf(minimum_joint_depth,depth)
				checked_joints+=1

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
						var shown := visible_count(kind)
						check(shown==amount if amount==3 else shown<=amount,kind+" preserves ordinary loads")
						var geometry_top:float = item.position.y+carry.measured[kind].y
						check(geometry_top<=Carry.PACK_TOP+.001,kind+" keeps the top of the actual mesh at the standing keeper's crown")
						if amount>=37:
							check(geometry_top+carry.tier_height[kind]>Carry.PACK_TOP-.01 or ratio>1.,kind+" fills its physical bay before grouping surplus")
						check(book.carried[kind]==amount,kind+" count unchanged")
						check(carry.pieces["carry/"+kind].size()<(75 if kind in Ledger.ORIGINAL_KINDS else 200),kind+" bounded pool")
					check(top("wood").position.x < top("stone").position.x, "wood and stone occupy separate columns")
					check_distinct_bays()

				check(lowest>=.20,"full rack clears the objective area across views and turns")
				var drawn := {}
				for kind in Ledger.KINDS: drawn[kind]=visible_count(kind)
				cases.append({"viewport":str(format_),"zoom":ratio,"logical":amount,"visible":drawn,"min_headroom":snappedf(lowest,.001)})
	# A camera-only zoom update while stationary must preserve the bounded pool.
	view.size=Vector2i(1280,720)
	zoom.set_ratio(camera,1.)
	carry.advance(.02)
	var full := visible_count("wood")
	var pool: Array=carry.pieces["carry/wood"].duplicate()
	zoom.set_ratio(camera,2.)
	carry.advance(.02)
	check(visible_count("wood")<=full and carry.pieces["carry/wood"]==pool,"idle zoom reuses pool")
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
	# With a single family both columns carry whole bundles, bark outward.
	book.carried = Ledger.EMPTY.duplicate()
	book.stored = Ledger.EMPTY.duplicate()
	book.carried.wood = 6
	actor.position = Vector3.ZERO
	actor.rotation = Vector3.ZERO
	zoom.set_ratio(camera, 1.0)
	carry.sync()
	var wood: Array = carry.pieces["carry/wood"]
	check(wood[0].position.x < 0 and wood[1].position.x > 0 and is_equal_approx(wood[0].position.y, wood[1].position.y), "pure timber uses paired courses")
	check(absf(sin(wood[0].rotation.y)) < .001 and wood[2].position.y > wood[0].position.y, "timber course presents broad bark faces")
	var old_pos: Vector3 = wood[1].position
	check(carry.pickup("switch-to-mixed", "stone", Vector3(2,0,1), .85), "typed stone pickup reserves the other column")
	var entering: Dictionary = carry.flights[0]
	check(is_equal_approx(entering.mesh.rotation.y,.85) and is_equal_approx(entering.mesh.scale.x,Art.GROUND_WIDTHS.stone/Carry.WIDTH.stone), "flight starts at the real dropped heading and size")
	check(wood[1].position.is_equal_approx(old_pos), "an incoming stone leaves the wood course in its bay")
	carry.advance(.4)
	check(wood[1].position.is_equal_approx(old_pos) and entering.mesh.global_transform.is_equal_approx(top("stone").global_transform), "mixed pickup reaches its separate physical slot")
	check(carry.pickup("while-depositing","wood",Vector3(1,0,2)), "same-kind token in flight")
	var inbound: Node3D = carry.flights[0].mesh
	check(carry.deposit_storage("wood"), "loaded wood departs during incoming wood")
	carry.advance(.4)
	check(inbound.global_transform.is_equal_approx(top("wood").global_transform), "overlapping deposit preserves incoming physical slot")
	check(book.carried.wood == 6 and book.stored.wood == 1, "overlapping transfers preserve exact balances")
	# Any combination of the six live resource types must keep its bays when
	# another family is unloaded. Enumerate the full subset including every pair.
	var combinations := 0
	for mask in range(1, 1 << Ledger.KINDS.size()):
		book.carried = Ledger.EMPTY.duplicate()
		for i in Ledger.KINDS.size():
			if mask & (1 << i): book.carried[Ledger.KINDS[i]] = 3
		carry.sync()
		check_distinct_bays()
		check_mount()
		var footprints := {}
		for kind: String in Ledger.KINDS:
			if book.carried[kind] > 0:
				footprints[kind] = top(kind).transform
		for removed: String in footprints:
			book.carried[removed] = 0
			carry.sync()
			for kind: String in footprints:
				if kind != removed:
					check(top(kind).transform.is_equal_approx(footprints[kind]), "removing another family keeps " + kind + " stable")
			book.carried[removed] = 3
			carry.sync()
		combinations += 1
	check(combinations == 63, "all fifteen pairs and all six material families exercised")
	# Rebuild all six different stacks from actual earned tokens, then unload
	# just the top packet of each type before restoring an independent ledger.
	book = Ledger.new()
	book.configure({"buy":{"wood":3,"stone":2}})
	carry.inventory = book
	for kind: String in Ledger.KINDS:
		carry.define_storage(kind, bin)
		for i in 3:
			check(carry.pickup("mixed-%s-%d" % [kind,i],kind,bin.position), kind+" pickup earned")
			carry.advance(.5)
		check(visible_count(kind)==3,kind+" three transfers seated")
	for kind: String in Ledger.KINDS:
		var departing := top(kind).global_transform
		check(carry.deposit_storage(kind),kind+" deposit dispatched")
		check(carry.flights.size()==1 and carry.flights[0].mesh.global_transform.is_equal_approx(departing),kind+" deposit starts at top of its bay")
		carry.advance(.5)
		check(visible_count(kind)==2 and book.carried[kind]==2 and book.stored[kind]==1,kind+" balances after one deposit")
	var restored_book := Ledger.new()
	restored_book.configure(book.costs)
	check(restored_book.restore(book.snapshot()),"six-type earned inventory restores")
	var restored_carry := Carry.new()
	view.add_child(restored_carry)
	restored_carry.setup(restored_book,actor,Art.make)
	restored_carry.set_physics_process(false)
	for kind: String in Ledger.KINDS:
		for i in 2:
			var original: Node3D = carry.pieces["carry/"+kind][i]
			var reloaded: Node3D = restored_carry.pieces["carry/"+kind][i]
			check(reloaded.visible and reloaded.transform.is_equal_approx(original.transform),kind+" reload preserves physical packet and heading")
	print(JSON.stringify({"cases":cases,"minimum_joint_insertion_mm":snappedf(minimum_joint_depth*1000,.001),"joint_checks":checked_joints,"mixed_subsets":combinations,"earned_reload_counts":restored_book.carried,"earned_reload_storage":restored_book.stored,"failures":failures}))
	quit(1 if not failures.is_empty() else 0)
