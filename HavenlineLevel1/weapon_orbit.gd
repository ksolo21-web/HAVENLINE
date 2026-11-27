extends RefCounted
const AXE = preload("res://assets/tools/axe-field-grip.glb")
const PICK = preload("res://assets/tools/pickaxe-meshy.glb")
const HeadContacts = preload("res://orbit_head_contacts.gd")
const Sweep = preload("res://orbit_surface_sweep.gd")
const Locomotion = preload("res://orbit_locomotion.gd")
const Trail = preload("res://orbit_trail.gd")
const TOOL_PLANE := Basis(Vector3.LEFT, Vector3.BACK, Vector3.UP)
# Measured on the source B 5.40–6.50 s strip. Runtime uses the normal equipment camera.
const PERIOD := .89
const UPGRADED_RADIUS := 1.23
const RADIUS_SIDE := 2.19
const RADIUS_DEPTH := 2.46
# Model-space X crosses the blade, Y follows the shaft, Z is thickness.
# Use the same local transform for the visible mesh and its swept contact samples.
const AXE_SCALE := Vector3(.68, .74, .42)
const PICK_SCALE := Vector3(.64, .83, .50)
const TRAIL_WIDTH := .235
const CAMERA_NEAR := Vector3(.53687549,0,.84366149)
const CAMERA_RIGHT := Vector3(.84366149,0,-.53687549)
const AXE_EDGE := Vector3(-.64409602,.53566498,.03264396)
const PICK_TIP := Vector3(-.87014508,.37309802,.00000797)
# Distal vertices measured on the authored exports. The shaft runs radially,
# so its farthest visible point is distinct from the leading cutting edge.
const AXE_OUTER := Vector3(-.540056, .95106995, .02607993)
const PICK_OUTER := Vector3(.352607, .94981104, .04023193)
const ARC_STEP := PI / 72.0
const AXE_HEAD := Vector3(-.15,.65,0)
const PICK_HEAD := Vector3(0,.67,0)
var locomotion = Locomotion.new()
var actor: Node3D
var perimeter: Node3D
var safe_planes := PackedVector3Array()
var model_boxes := {}
var slots: Array[Dictionary] = []
var count := 1
var reach_scale := 1.0
var active := false
var equipped := ""
var elapsed := 0.0
var duration := PERIOD
var turn_id := 0
var hit_this_turn := {}
var last_origin := Vector3.ZERO
var sweep_cache := {}
var current_tip := Vector3.ZERO
var height := .89
var hit_geometry: MeshInstance3D
var hit_position := Vector3.ZERO
var hit_travel := Vector3.ZERO

func install(scene: Node, hero: Node3D, _unused) -> bool:
	actor = hero.get_parent()
	if "field_env" in scene: perimeter = scene.field_env
	for i in 3:
		var axe := AXE.instantiate() as Node3D
		var pick := PICK.instantiate() as Node3D
		var trail := Trail.new()
		scene.add_child(axe)
		scene.add_child(pick)
		scene.add_child(trail)
		if i == 0:
			model_boxes.axe = _bounds(axe)
			model_boxes.pickaxe = _bounds(pick)
		slots.append({"axe":axe,"pickaxe":pick,"trail":trail,"before":Transform3D.IDENTITY,"after":Transform3D.IDENTITY,"spokes":PackedVector3Array()})
	rest()
	return locomotion.bind(hero)

func _bounds(tool: Node3D) -> AABB:
	var combined := AABB()
	var first := true
	var parts := tool.find_children("*","MeshInstance3D",true,false)
	if tool is MeshInstance3D: parts.append(tool)
	for part: MeshInstance3D in parts:
		var local := tool.global_transform.affine_inverse()*part.global_transform
		var box := local*part.get_aabb()
		combined = box if first else combined.merge(box)
		first = false
	return combined

func show_tools() -> void:
	for i in slots.size():
		var show_slot := active and i<count
		slots[i].axe.visible = show_slot and equipped=="axe"
		slots[i].pickaxe.visible = show_slot and equipped=="pickaxe"
		slots[i].trail.visible = show_slot

func rest() -> void:
	active=false
	hit_geometry = null
	equipped=""
	hit_this_turn.clear()
	for slot in slots: slot.spokes = PackedVector3Array()
	current_tip=Vector3.ZERO
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

func _tool_transform(center: Vector3, radial: Vector3) -> Transform3D:
	var pick := equipped == "pickaxe"
	var size := 1.92 / (1.902848 if pick else 1.903081)
	var azimuth := Basis(Vector3.UP, atan2(radial.x,radial.z))
	var basis := (azimuth * TOOL_PLANE).scaled_local((PICK_SCALE if pick else AXE_SCALE) * size)
	var head := PICK_HEAD if pick else AXE_HEAD
	return Transform3D(basis, center + radial - basis * head)

func _clear_pose(center: Vector3, radial: Vector3) -> Transform3D:
	var pose_at := _tool_transform(center,radial)
	if safe_planes.is_empty(): return pose_at
	var head: Vector3 = PICK_HEAD if equipped=="pickaxe" else AXE_HEAD
	var box: AABB = model_boxes[equipped]
	# Turn the rigid shaft along the boards as the head reaches the wall.
	# Keep the outward half of the stroke and the model's dimensions unchanged.
	var tuck := 0.
	for plane in safe_planes:
		var normal := Vector3(plane.x,0.,plane.y)
		var head_clear := normal.dot(center+radial)-plane.z
		tuck = maxf(tuck,(1.-smoothstep(-.55,.64,head_clear))*smoothstep(.05,.72,-normal.dot(radial.normalized())))
	if tuck>0.:
		var tangent := radial.rotated(Vector3.UP,PI*.5).normalized()
		var turned := radial.rotated(Vector3.UP,tuck*1.24)
		pose_at = _tool_transform(center,turned)
		pose_at.origin = center+radial+tangent*(.46*tuck)-pose_at.basis*head
	var half := box.size*.5
	# Project the whole measured mesh, including the butt and blade corners.
	# More than one plane can be active alongside a post or between open leaves.
	for iteration in 5:
		var corrected := false
		for plane in safe_planes:
			var n := Vector3(plane.x,0.,plane.y)
			var extent := half.x*absf(n.dot(pose_at.basis.x))+half.y*absf(n.dot(pose_at.basis.y))+half.z*absf(n.dot(pose_at.basis.z))
			var push := plane.z + extent - n.dot(pose_at*box.get_center())
			if push>.0001:
				pose_at.origin += n*push
				corrected = true
		if not corrected: break
	return pose_at

func _exposed(point: Vector3) -> bool:
	return not perimeter or safe_planes.is_empty() or perimeter.travel_clear(actor.global_position,point,0.)

func pose(origin := Vector3.INF) -> void:
	last_origin = actor.global_position if not origin.is_finite() else origin
	if perimeter: safe_planes = perimeter.orbit_planes(last_origin,maximum_radius()+.44)
	var center := last_origin + Vector3.UP*height
	var distal := PICK_OUTER if equipped=="pickaxe" else AXE_OUTER
	for i in count:
		var s := slots[i]
		var phase := TAU*(elapsed/PERIOD + float(i)/count)
		var radial := offset(phase)
		var node: Node3D = s[equipped]
		node.global_transform = _clear_pose(center,radial)
		s.after = node.global_transform
		if i == 0: current_tip = node.to_global(distal)
		var points := PackedVector3Array()
		var axes := PackedVector3Array()
		for j in range(Trail.SEGMENTS+1):
			var behind := deg_to_rad(57.0)*float(j)/Trail.SEGMENTS
			var r := offset(phase-behind)
			var point := center+r
			if not safe_planes.is_empty():
				point = _clear_pose(center,r)*(PICK_HEAD if equipped=="pickaxe" else AXE_HEAD)
			points.append(point+Vector3.UP*.002)
			axes.append(r.normalized())
		s.trail.redraw(points,axes,TRAIL_WIDTH,safe_planes)

func advance(dt: float, at := Vector3.INF) -> void:
	if not active: return
	var standalone := not at.is_finite()
	if standalone: at = actor.global_position
	var start_origin := last_origin
	var initial_height := height
	var initial_scale := reach_scale
	var initial_time := elapsed
	for s in slots: s.before=s.after
	# Carry fractional time across loop boundaries so the measured period is not rounded to ticks.
	reach_scale = move_toward(reach_scale, UPGRADED_RADIUS if count == 3 else 1.0, dt)
	elapsed+=dt
	height=move_toward(height,desired_height(),2.*dt)
	pose(at)
	# Repositioning a save, testing, or a respawn must never cut the space
	# between unrelated positions. The new pose still has a live local spoke.
	var warp := discontinuous(start_origin,at,dt)
	var travel := TAU * dt / PERIOD
	var steps := maxi(1, ceili(absf(travel) / ARC_STEP))
	var distal := PICK_OUTER if equipped == "pickaxe" else AXE_OUTER
	for i in count:
		var slot := slots[i]
		if warp: slot.before = slot.after
		var points := PackedVector3Array()
		var phi := TAU * (initial_time / PERIOD + float(i) / count)
		for j in range(steps+1):
			var t := 1.0 if warp else float(j) / steps
			var origin := start_origin.lerp(at,t)
			var center := origin + Vector3.UP * lerpf(initial_height,height,t)
			var r := offset(phi + travel*t) * lerpf(initial_scale,reach_scale,t) / reach_scale
			var tip := _clear_pose(center,r) * distal
			points.append(Vector3(center.x,tip.y,center.z))
			points.append(tip)
		slot.spokes = points
	if standalone:
		finish_turn()

func maximum_radius() -> float:
	# Conservative upper bound of both measured tool tips, independent of phase.
	return RADIUS_DEPTH * reach_scale + .25

func discontinuous(start: Vector3, end: Vector3, dt: float) -> bool:
	return start.distance_to(end) > maxf(.24,6.0 * dt + .06)

func finish_turn() -> void:
	if elapsed >= PERIOD - .0000001:
		elapsed = maxf(0., fmod(elapsed + .0000001, PERIOD) - .0000001)
		turn_id += 1
		hit_this_turn.clear()

func _spoke_contact(mesh: TriangleMesh, part: MeshInstance3D, local: Transform3D, points: PackedVector3Array) -> Vector3:
	var box := part.mesh.get_aabb().grow(.00001)
	for j in range(2, points.size(), 2):
		var a := local * points[j-2]
		var b := local * points[j-1]
		var c := local * points[j+1]
		var d := local * points[j]
		var span := AABB(a,Vector3.ZERO).expand(b).expand(c).expand(d).grow(.00001)
		if not span.intersects(box): continue
		for pair in [[a,b],[c,d],[b,c],[d,a],[a,c]]:
			if (pair[0] as Vector3).is_equal_approx(pair[1]): continue
			var edge := mesh.intersect_segment(pair[0],pair[1])
			if not edge.is_empty(): return edge.position
		if not sweep_cache.has(mesh):
			sweep_cache[mesh] = Sweep.new(mesh)
		var cut = sweep_cache[mesh]
		var hit: Vector3 = cut.triangle_contact(a,b,c)
		if not hit.is_finite(): hit = cut.triangle_contact(a,c,d)
		if hit.is_finite(): return hit
	return Vector3.INF

func crosses_surface(part: MeshInstance3D, mesh: TriangleMesh) -> bool:
	hit_geometry = null
	if not active: return false
	var local := part.global_transform.affine_inverse()
	var samples: Array = HeadContacts.PICKAXE if equipped=="pickaxe" else HeadContacts.AXE
	for i in count:
		var before: Transform3D = local * slots[i].before
		var after: Transform3D = local * slots[i].after
		var points: PackedVector3Array = slots[i].spokes
		var spoke_hit := _spoke_contact(mesh,part,local,points)
		if spoke_hit.is_finite() and _exposed(part.to_global(spoke_hit)):
			hit_geometry = part
			hit_position = part.to_global(spoke_hit)
			hit_travel = after * (PICK_TIP if equipped=="pickaxe" else AXE_EDGE) - before * (PICK_TIP if equipped=="pickaxe" else AXE_EDGE)
			hit_travel = part.global_basis * hit_travel
			return true
		for p: Vector3 in samples:
			var intersection := mesh.intersect_segment(before*p,after*p)
			if not intersection.is_empty() and _exposed(part.to_global(intersection.position)):
				hit_geometry = part
				hit_position = part.to_global(intersection.position)
				hit_travel = part.global_basis*((after*p)-(before*p))
				return true
	return false
