extends RefCounted
const AXE = preload("res://assets/tools/axe-meshy.glb")
const PICK = preload("res://assets/tools/pickaxe-meshy.glb")
const HeadContacts = preload("res://orbit_head_contacts.gd")
const Locomotion = preload("res://orbit_locomotion.gd")
const Trail = preload("res://orbit_trail.gd")
const TOOL_PLANE := Basis(Vector3.LEFT, Vector3.BACK, Vector3.UP)
# Measured on the source B 5.40–6.50 s strip. Runtime uses the normal equipment camera.
const PERIOD := .89
const UPGRADED_RADIUS := 1.23
const RADIUS_SIDE := 2.51
const RADIUS_DEPTH := 2.80
const CAMERA_NEAR := Vector3(.53687549,0,.84366149)
const CAMERA_RIGHT := Vector3(.84366149,0,-.53687549)
const AXE_EDGE := Vector3(-.64409602,.53566498,.03264396)
const PICK_TIP := Vector3(-.87014508,.37309802,.00000797)
const AXE_HEAD := Vector3(-.15,.65,0)
const PICK_HEAD := Vector3(0,.67,0)
var locomotion = Locomotion.new()
var actor: Node3D
var slots: Array[Dictionary] = []
var count := 1
var reach_scale := 1.0
var active := false
var equipped := ""
var elapsed := 0.0
var duration := PERIOD
var turn_id := 0
var hit_this_turn := {}
var current_tip := Vector3.ZERO
var height := .89

func install(scene: Node, hero: Node3D, _unused) -> bool:
	actor = hero.get_parent()
	for i in 3:
		var axe := AXE.instantiate() as Node3D
		var pick := PICK.instantiate() as Node3D
		var trail := Trail.new()
		scene.add_child(axe)
		scene.add_child(pick)
		scene.add_child(trail)
		slots.append({"axe":axe,"pickaxe":pick,"trail":trail,"before":Transform3D.IDENTITY,"after":Transform3D.IDENTITY})
	rest()
	return locomotion.bind(hero)

func show_tools() -> void:
	for i in slots.size():
		var show_slot := active and i<count
		slots[i].axe.visible = show_slot and equipped=="axe"
		slots[i].pickaxe.visible = show_slot and equipped=="pickaxe"
		slots[i].trail.visible = show_slot

func rest() -> void:
	active=false
	equipped=""
	show_tools()

func set_upgraded(upgraded: bool) -> void:
	var next := 3 if upgraded else 1
	if count==next: return
	count=next
	if active:
		show_tools()
		pose()
		for s in slots: s.before=s.after

func begin(tool: String) -> void:
	var first := not active
	active=true
	equipped=tool
	turn_id+=1
	hit_this_turn.clear()
	elapsed=0
	if first: height=desired_height()
	show_tools()
	pose()
	for s in slots: s.before=s.after

func desired_height() -> float:
	return .28 if equipped=="pickaxe" else .89

func offset(angle: float) -> Vector3:
	return (CAMERA_RIGHT*(sin(angle)*RADIUS_SIDE) + CAMERA_NEAR*(cos(angle)*RADIUS_DEPTH)) * reach_scale

func pose() -> void:
	var center := actor.global_position + Vector3.UP*height
	var edge := PICK_TIP if equipped=="pickaxe" else AXE_EDGE
	var size := 1.92/(1.902848 if equipped=="pickaxe" else 1.903081)
	for i in count:
		var s := slots[i]
		var phase := TAU*(elapsed/PERIOD + float(i)/count)
		var radial := offset(phase)
		var azimuth := Basis(Vector3.UP, atan2(radial.x,radial.z))
		var basis := (azimuth * TOOL_PLANE).scaled(Vector3.ONE*size)
		var head_at := center+radial
		var head := PICK_HEAD if equipped=="pickaxe" else AXE_HEAD
		var node: Node3D = s[equipped]
		node.global_transform = Transform3D(basis,head_at-basis*head)
		s.after=node.global_transform
		if i==0: current_tip=node.to_global(edge)
		var points := PackedVector3Array()
		var axes := PackedVector3Array()
		for j in range(Trail.SEGMENTS+1):
			var behind := deg_to_rad(57.0)*float(j)/Trail.SEGMENTS
			var r := offset(phase-behind)
			points.append(center+r+Vector3.UP*.002)
			axes.append(r.normalized())
		s.trail.redraw(points,axes,.285)

func advance(dt: float) -> void:
	for s in slots: s.before=s.after
	# Carry fractional time across loop boundaries so the measured period is not rounded to ticks.
	reach_scale = move_toward(reach_scale, UPGRADED_RADIUS if count == 3 else 1.0, dt)
	elapsed+=dt
	if elapsed>=PERIOD:
		elapsed=fmod(elapsed,PERIOD)
		turn_id+=1
		hit_this_turn.clear()
	height=move_toward(height,desired_height(),2.*dt)
	pose()

func crosses_surface(part: MeshInstance3D, mesh: TriangleMesh) -> bool:
	var local := part.global_transform.affine_inverse()
	var samples: Array = HeadContacts.PICKAXE if equipped=="pickaxe" else HeadContacts.AXE
	for i in count:
		var before: Transform3D = local * slots[i].before
		var after: Transform3D = local * slots[i].after
		for p: Vector3 in samples:
			if not mesh.intersect_segment(before*p,after*p).is_empty():return true
	return false
