extends Node3D

signal perimeter_changed

const Progress = preload("res://field_progression.gd")
const BUY := Vector2(0,2.4)
const UPGRADE := Vector2(2.65,1.7)
const FILL := preload("res://assets/field_camp/payment_fill.gdshader")
const DONOR := "res://assets/field_camp/"
const PANEL := preload("res://assets/field_camp/snowbound_palisade.obj")
const DOOR := preload("res://assets/field_camp/snowbound_gate_leaf.obj")
const POST := preload("res://assets/field_camp/snowbound_gate_post.obj")
const HINGE := preload("res://assets/field_camp/snowbound_hinges.obj")
const KEEPER := preload("res://assets/field_camp/snowbound_latch_keeper.obj")
const BOLT := preload("res://assets/field_camp/snowbound_sliding_bolt.obj")
const HEARTH := preload("res://assets/field_camp/furnace.glb")
const SNOW := preload("res://assets/field_camp/field_snow.gdshader")
const TIMBER := preload("res://assets/field_camp/t03_boundary_v2.gdshader")
const GRAIN := preload("res://assets/field_camp/golden_timber_grain.png")
var world
var buy_anchor := Node3D.new()
var upgrade_anchor := Node3D.new()
var upgrade_label: Label3D
var upgrade_pending := true
var payment_ink := {}
var payment_brackets := {}
var payment_costs: Node3D
const CounterLayout = preload("res://field_counter.gd")
# The last purchase opens a work aisle along the north wall. The gates and
# the main lanes to the storehouse, hearth and eastern defense stay in place.
const COURTS := [Vector4(-5,-4,5,4),Vector4(-5.5,-5.5,7.5,5),Vector4(-10,-9,10,5.4)]
var counter_center_x := CounterLayout.CENTER_X
var perimeter_stage := -1
var wall_revision := 0
var palisades: MultiMeshInstance3D
var garage_wall_half: StaticBody3D
var perimeter_tween: Tween
var camp_state := -1
var palette := {}
var canopy_materials := {}
var pine_shapes: Array[Vector2] = []
var pine_scenes: Array[PackedScene] = []
var resource_sightline := preload("res://field_resource_sightline.gd").new()
var seasonal_pines: Array[Node3D] = []
var grove_source_aliases: Dictionary[Vector2i,String] = {}
# These coordinates name the sources in existing saves. Their planting sites
# sit farther back so the founding plot has a clear snow approach.
const SEASONAL_SOURCE_ANCHORS := [
	Vector2(-4.8,-3.7), Vector2(-3.0,-3.55), Vector2(-1.25,-3.68), Vector2(.65,-3.55), Vector2(2.55,-3.68),
	Vector2(-4.75,-1.94), Vector2(-3.18,-1.77), Vector2(-1.36,-2.11), Vector2(.40,-2.04), Vector2(2.05,-2.14),
	Vector2(-4.5,-.19), Vector2(-2.9,-.27), Vector2(-1.1,-.53), Vector2(.80,-.73),
	Vector2(-4.29,1.49), Vector2(-2.55,1.19),
]
const SEASONAL_POCKETS := [
	Vector2(-4.8,-3.7), Vector2(-3.0,-3.55), Vector2(-1.25,-3.68), Vector2(-4.5,-9.5), Vector2(-.25,-9.0),
	Vector2(-4.75,-1.94), Vector2(-3.18,-1.77), Vector2(-10.95,-11.9), Vector2(-13.8,-3.6), Vector2(-12.0,0.0),
	Vector2(-11.75,1.75), Vector2(3.0,-9.25), Vector2(3.25,-4.0), Vector2(-.5,-11.25),
	Vector2(-15.4,-2.55), Vector2(-7.2,-11.53),
]
# Five west-grove pines border the quarry work area. Their roots previously
# landed on the stone or in front of its pick contact from the fixed camera.
const QUARRY_EDGE := [
	Vector2(-10.97,.76), Vector2(-9.45,6.79), Vector2(-10.55,-.68),
	Vector2(-12.93,1.01), Vector2(-10.08,1.91)
]
# Staggered crowns frame the founding clearing and the western grove. The
# south trail and the route along the east gate divide the foreground banks
# so players and survivors can reach the individual trunks.
const FOREST_BANKS := [
	Vector2(-15.7,16.1), Vector2(-14.0,16.38), Vector2(-13.8,18.55),
	Vector2(-10.35,16.78), Vector2(-8.45,17.19), Vector2(-7.08,17.38),
	Vector2(-12.5,17.4), Vector2(-10.8,18.25), Vector2(-9.2,18.8), Vector2(-7.5,19.05),
	Vector2(-5.8,18.95), Vector2(-11.65,19.86), Vector2(-9.95,20.06), Vector2(-8.24,20.2),
	Vector2(-6.43,20.27), Vector2(-4.72,19.98),
	Vector2(2.85,16.55), Vector2(4.13,15.15), Vector2(5.64,13.95), Vector2(7.28,13.27),
	Vector2(8.95,12.6), Vector2(10.45,13.33), Vector2(12.12,12.88),
	Vector2(4.40,17.8), Vector2(5.43,16.45), Vector2(6.95,15.55), Vector2(8.55,14.62),
	Vector2(10.05,15.23), Vector2(11.7,15.04), Vector2(6.8,19.3), Vector2(7.8,17.73),
	Vector2(9.42,16.8), Vector2(11.15,17.15), Vector2(12.65,16.37),
	Vector2(-2.55,-9.48), Vector2(-.96,-9.95), Vector2(.65,-10.0),
]
# Shorter pines fill gaps between the bank rows. Keep enough root spacing
# for chop stances even where the branches overlap overhead.
const FOREST_UNDERSTORY := [
	Vector2(7.75,12.06), Vector2(9.96,12.03), Vector2(11.76,11.10),
	Vector2(-5.64,-4.92), Vector2(-4.08,-5.13),
	Vector2(1.11,-5.01), Vector2(2.41,-5.23),
	Vector2(9.49,9.69), Vector2(10.52,8.79),
	Vector2(3.58,13.89), Vector2(5.57,11.84),
]
const BANK_PINE_PROPORTIONS := Vector3(1.13,.81,1.13)
const BANK_CONIFERS := [
	preload("res://assets/reference_forest/bank_pine_1.glb"),
	preload("res://assets/reference_forest/bank_pine_2.glb"),
	preload("res://assets/reference_forest/bank_pine_3.glb"),
]
var snow := ShaderMaterial.new()
var reveal_tween: Tween
var gate_art: Array[MeshInstance3D] = []
var hearth_footprint: CollisionShape3D
var hearth_shell: Node3D
var hearth_fire := preload("res://field_hearth_fire.gd").new()
var coal_glow: OmniLight3D
var hearth_stones: Array[MeshInstance3D] = []
var ignition := ShaderMaterial.new()

func _process(_delta: float) -> void:
	if world and world.camera and world.actor:
		resource_sightline.update(world)

func _exit_tree() -> void:
	RenderingServer.global_shader_parameter_set("field_player_eye", Vector3.ZERO)

func receiver_position(kind: String) -> Vector2:
	if kind == "upgrade": return UPGRADE
	if kind in world.Inventory.KINDS: return Vector2(-3.60,-1.18)
	return BUY

func install(host: Node3D) -> void:
	world = host
	name = "SettledFieldEnvironment"
	if get_parent() == null: world.add_child(self)
	var snow_mesh: MeshInstance3D = world.get_node("SnowGround_NoPaintedPaths").find_children("*","MeshInstance3D", false, false)[0]
	# Extend the visible snow beneath the boundary drifts. The travel collider retains the playable extent.
	var snow_box := snow_mesh.mesh as BoxMesh
	if snow_box:
		var backdrop_width := 2.0 * (float(world.layout.snow_extent_half) + 76.0)
		snow_box.size = Vector3(backdrop_width, snow_box.size.y, backdrop_width)
	snow.shader = SNOW
	snow_mesh.material_override = snow
	world.camp_built.get_node("CampOnlySurface").hide()
	for child in world.camp_built.get_children():
		if "technical-marker" in str(child.name): child.hide()
	install_walls()
	install_hearth()
	install_woods.call_deferred()
	install_payment(buy_anchor,false)
	install_payment(upgrade_anchor,true)
	set_built(not world.ledger.receipt.is_empty(),false)

func donor_mesh(source: Mesh) -> MeshInstance3D:
	var vis := MeshInstance3D.new()
	vis.mesh = source
	for i in source.get_surface_count():
		var code := String(source.surface_get_name(i)).to_lower()
		var imported := source.surface_get_material(i)
		if imported and not imported.resource_name.is_empty(): code = imported.resource_name.to_lower()
		if not palette.has(code):
			var ink := ShaderMaterial.new()
			ink.shader = TIMBER
			var colors := {"timber_dark":"aa7039","iron":"343640","brass":"c69655","snow":"e8f2f6","blue":"455966","rope":"f2d299","timber":"ffffff"}
			ink.set_shader_parameter("base_color",Color(colors.get(code,"85614a")))
			ink.set_shader_parameter("detail_strength",.012)
			if code in ["timber","timber_dark"]:
				ink.set_shader_parameter("ground_bounce",.43)
				ink.set_shader_parameter("emission_color",Vector3(.048,.033,.017))
			if code == "snow":
				ink.set_shader_parameter("emission_color",Vector3(.29,.34,.40))
			elif code == "rope":
				ink.set_shader_parameter("emission_color",Vector3(.28,.216,.14))
			elif code == "iron":
				ink.set_shader_parameter("emission_color",Vector3(.038,.041,.046))
			if code == "timber":
				ink.set_shader_parameter("use_reference_grain",true)
				ink.set_shader_parameter("reference_grain",GRAIN)
			palette[code] = ink
		vis.set_surface_override_material(i,palette[code])
	return vis

func install_walls() -> void:
	var template := donor_mesh(PANEL)
	var panel_mesh := PANEL.duplicate() as Mesh
	for surface in panel_mesh.get_surface_count():
		panel_mesh.surface_set_material(surface,template.get_active_material(surface))
	template.free()
	palisades = MultiMeshInstance3D.new()
	palisades.name = "SnowboundPalisades"
	var instances := MultiMesh.new()
	instances.transform_format = MultiMesh.TRANSFORM_3D
	instances.mesh = panel_mesh
	palisades.multimesh = instances
	world.camp_built.add_child(palisades)
	garage_wall_half = StaticBody3D.new()
	garage_wall_half.name = "SnowGarageSouthFenceEnd"
	garage_wall_half.collision_layer = 0
	world.camp_built.add_child(garage_wall_half)
	garage_wall_half.add_child(Node3D.new())
	var garage_wall_shape := CollisionShape3D.new()
	garage_wall_shape.shape = BoxShape3D.new()
	garage_wall_half.add_child(garage_wall_shape)
	for i in world.layout.walls_xz.size():
		world.camp_colliders[i].get_child(0).hide()
	for gate in world.gates:
		gate.hinge_moved.connect(func(_angle: float): wall_revision+=1)
		for i in 2:
			var leaf: AnimatableBody3D = gate._leaf_bodies[i]
			for child in leaf.get_children():
				if child is MeshInstance3D: child.hide()
			var vis := donor_mesh(DOOR)
			leaf.add_child(vis)
			gate_art.append(vis)
			vis.position.y = -gate.LEAF_HEIGHT*.5
			vis.scale.x = (2.*gate.HALF_SPAN-gate.LEAF_LENGTH-.01)/1.124
			var sign_x := -1 if i == 0 else 1
			var hinge := donor_mesh(HINGE)
			leaf.add_child(hinge)
			gate_art.append(hinge)
			hinge.position = Vector3(sign_x*.505,-gate.LEAF_HEIGHT*.5,0.)
			var keeper := donor_mesh(KEEPER)
			leaf.add_child(keeper)
			gate_art.append(keeper)
			keeper.position = Vector3(-sign_x*.537,-gate.LEAF_HEIGHT*.5,0.)
			if i == 0:
				var bolt := donor_mesh(BOLT)
				leaf.add_child(bolt)
				gate_art.append(bolt)
				bolt.position = Vector3(gate.LEAF_LENGTH*.5,-gate.LEAF_HEIGHT*.5,0.)
				gate.hinge_moved.connect(func(angle: float):
					bolt.position.x = gate.LEAF_LENGTH*.5-.34*clampf(angle/.18,0.,1.))

			var post := donor_mesh(POST)
			gate.add_child(post)
			gate_art.append(post)
			post.position = Vector3(sign_x*(gate.HALF_SPAN+.15),-.045,0)
			post.scale = Vector3.ONE
	set_perimeter(0,false)

func is_inside_camp(pos: Vector3) -> bool:
	if perimeter_stage < 1: return false
	var r: Vector4 = COURTS[perimeter_stage-1]
	return pos.x >= r.x and pos.x <= r.z and pos.z >= r.y and pos.z <= r.w

# Sweep the entire horizontal segment, including both actual moving gate leaves.
# A large timestep or a long transfer must obey the same fence as a small step.
func travel_clear(from: Vector3, to: Vector3, radius := 0.) -> bool:
	if perimeter_stage < 1: return true
	var a := Vector2(from.x, from.z)
	var b := Vector2(to.x, to.z)
	radius = maxf(0., radius)
	for i in world.layout.walls_xz.size():
		if world.encounters.has_method("wall_breached") and world.encounters.wall_breached(i):continue
		var row: Array = world.layout.walls_xz[i]
		var center := Vector2(row[0],row[1])
		var half := Vector2(float(row[2]),float(row[3]))*.5
		if _intersects_box(a,b, center-half-Vector2.ONE*radius, center+half+Vector2.ONE*radius):
			return false
	for gate in world.gates:
		if gate.get("breached") == true: continue
		var local_a: Vector3 = gate.to_local(from)
		var local_b: Vector3 = gate.to_local(to)
		var u := Vector2(local_a.x,local_a.z)
		var v := Vector2(local_b.x,local_b.z)
		var limit: float = radius + gate.LEAF_DEPTH*.5
		if not _intersects_box(u,v,Vector2(-gate.HALF_SPAN,-gate.LEAF_LENGTH)-Vector2.ONE*limit,Vector2(gate.HALF_SPAN,gate.LEAF_LENGTH)+Vector2.ONE*limit):
			continue
		for side: float in [-1.,1.]:
			var hinge := Vector2(side*gate.HALF_SPAN,0.)
			var tip := hinge + Vector2(-side*cos(gate.angle),-gate.swing_direction*sin(gate.angle))*float(gate.LEAF_LENGTH)
			if u.is_equal_approx(v):
				if u.distance_squared_to(Geometry2D.get_closest_point_to_segment(u,hinge,tip)) <= limit*limit: return false
			else:
				var closest := Geometry2D.get_closest_points_between_segments(u,v,hinge,tip)
				if closest[0].distance_squared_to(closest[1]) <= limit*limit: return false
	return not (world.snow_truck.initialized and world.snow_truck.intersects_closed_door(from,to,radius))

# Supporting planes bound a convex, walkable pocket on the runner's side
# of the nearby timber. The orbit takes one snapshot per pose, not a physics
# raycast per vertex. An open door contributes its rotated leaves only.
func orbit_planes(feet: Vector3, reach: float) -> PackedVector3Array:
	var planes := PackedVector3Array()
	if perimeter_stage < 1: return planes
	var rect: Vector4 = COURTS[perimeter_stage-1]
	if feet.x < rect.x-reach or feet.x>rect.z+reach or feet.z<rect.y-reach or feet.z>rect.w+reach: return planes
	var p := Vector2(feet.x,feet.z)
	for i in world.layout.walls_xz.size():
		if world.encounters.has_method("wall_breached") and world.encounters.wall_breached(i):continue
		var row: Array = world.layout.walls_xz[i]
		var center := Vector2(row[0],row[1])
		var half := Vector2(row[2],row[3])*.5
		_add_orbit_plane(planes,p,p.clamp(center-half,center+half),0.,reach)
	for gate in world.gates:
		if gate.get("breached") == true: continue
		var local:Vector3=gate.to_local(feet)
		if absf(local.x)>reach+gate.HALF_SPAN or absf(local.z)>reach+gate.LEAF_LENGTH: continue
		for side:float in [-1.,1.]:
			var hinge:=Vector2(side*gate.HALF_SPAN,0.)
			var tip:=hinge+Vector2(-side*cos(gate.angle),-gate.swing_direction*sin(gate.angle))*float(gate.LEAF_LENGTH)
			var point:=Geometry2D.get_closest_point_to_segment(Vector2(local.x,local.z),hinge,tip)
			var nearest:Vector3=gate.to_global(Vector3(point.x,0,point.y))
			_add_orbit_plane(planes,p,Vector2(nearest.x,nearest.z),gate.LEAF_DEPTH*.5,reach)
	if world.snow_truck.initialized and world.snow_truck.garage.visible and world.snow_truck.door.collision_layer != 0:
		var garage: Node3D = world.snow_truck.garage
		var local := garage.to_local(feet)
		var edge := garage.to_global(Vector3(clampf(local.x,-1.44,1.44),0,0))
		_add_orbit_plane(planes,p,Vector2(edge.x,edge.z),.10,reach)
	return planes

func _add_orbit_plane(planes: PackedVector3Array,p:Vector2,point:Vector2,thickness:float,reach:float) -> void:
	var direction:=p-point
	var d:=direction.length()
	if d>=reach+thickness or d<.00001:return
	var n:=direction/d
	planes.append(Vector3(n.x,n.y,n.dot(point)+thickness+.04))

func _intersects_box(a: Vector2,b: Vector2,low: Vector2,high: Vector2) -> bool:
	var delta := b-a
	var enter := 0.
	var leave := 1.
	for axis in 2:
		if absf(delta[axis]) < .000001:
			if a[axis] < low[axis] or a[axis] > high[axis]: return false
		else:
			var first := (low[axis]-a[axis])/delta[axis]
			var last := (high[axis]-a[axis])/delta[axis]
			enter = maxf(enter,minf(first,last))
			leave = minf(leave,maxf(first,last))
			if enter > leave: return false
	return true

# Bound the canopy during its largest hit recoil, as well as the fence's width.
func occupies_camp_ground(pos: Vector3, crown_radius := .17) -> bool:
	if perimeter_stage < 1: return false
	var r: Vector4 = COURTS[perimeter_stage-1]
	var p := Vector2(pos.x,pos.z)
	if perimeter_stage == 3:
		var queue := Rect2(Vector2(counter_center_x-1.25,r.y-8.25),Vector2(4.79,8.25)).grow(crown_radius)
		if queue.has_point(p): return true
	var nearest := p.clamp(Vector2(r.x,r.y),Vector2(r.z,r.w))
	if p.distance_to(nearest) <= crown_radius+.19: return true
	for gate in world.gates:
		var at: Vector3 = gate.to_local(pos)
		if absf(at.x) < gate.HALF_SPAN+crown_radius and absf(at.z) < 2.15+crown_radius: return true
	return false

func tree_fall_direction(at: Vector3,wanted: Vector3,height: float,radius: float) -> Vector3:
	if perimeter_stage < 1: return wanted
	var r: Vector4 = COURTS[perimeter_stage-1]
	var p := Vector2(at.x,at.z)
	var normal := p-p.clamp(Vector2(r.x,r.y),Vector2(r.z,r.w))
	if normal.is_zero_approx(): return wanted
	var ray := Vector2(wanted.x,wanted.z)*height
	var margin := Vector2.ONE*(radius+.19)
	if not _intersects_box(p,p+ray,Vector2(r.x,r.y)-margin,Vector2(r.z,r.w)+margin): return wanted
	return Vector3(normal.x,0,normal.y).normalized()

func safe_drop_origin(p: Vector3, radius: float) -> Vector3:
	if travel_clear(p,p,radius): return p
	# A purchase can move a wall onto an existing loose resource. Return it to
	# the nearest clear spot on its own side, retaining its unique receipt.
	var inside := is_inside_camp(p)
	for ring in range(1,17):
		for i in 16:
			var direction := Vector2.RIGHT.rotated(TAU*i/16.)
			var q := p + Vector3(direction.x,0,direction.y)*(.12*ring)
			if is_inside_camp(q)==inside and travel_clear(q,q,radius): return q
	return p

func clip_travel(from: Vector3,to: Vector3,radius: float) -> Vector3:
	if travel_clear(from,to,radius): return to
	var safe := 0.
	var blocked := 1.
	for i in 12:
		var fraction := (safe+blocked)*.5
		if travel_clear(from,from.lerp(to,fraction),radius): safe=fraction
		else: blocked=fraction
	var stop := from.lerp(to,safe)
	stop.y = to.y
	return stop

func set_perimeter(stage: int, animate: bool, refresh_wall := false) -> void:
	stage = clampi(stage,0,COURTS.size())
	if stage == perimeter_stage and not refresh_wall: return
	var previous := perimeter_stage
	perimeter_stage = stage
	wall_revision += 1
	var r: Vector4 = COURTS[maxi(0,stage-1)]
	# Wall bodies retain their identity so restore and proximity checks keep
	# using the same six collision shapes and the same two independent gates.
	var gap := float(world.gates[0].HALF_SPAN)
	var rows := [
		[(r.x-gap)*.5,r.w,-gap-r.x,.30],[(gap+r.z)*.5,r.w,r.z-gap,.30],
		[r.z,(r.y-gap)*.5,.30,-gap-r.y],[r.z,(gap+r.w)*.5,.30,r.w-gap],
		[(r.x+r.z)*.5,r.y,r.z-r.x,.30],[r.x,(r.y+r.w)*.5,.30,r.w-r.y]
	]
	garage_wall_half.collision_layer = 0
	if stage == 3 and world.inventory.complete("snow_garage"):
		var left: float = world.snow_truck.GARAGE_X-world.snow_truck.HALF_DOOR
		var right: float = world.snow_truck.GARAGE_X+world.snow_truck.HALF_DOOR
		rows[1] = [(gap+left)*.5,r.w,left-gap,.30]
		rows.append([(right+r.z)*.5,r.w,r.z-right,.30])
	world.layout.camp_rect_xz = [r.x,r.y,r.z,r.w]
	world.layout.walls_xz = rows
	world.layout.gates[0].center_xz = [0.,r.w]
	world.layout.gates[1].center_xz = [r.z,0.]
	var transforms: Array[Transform3D] = []
	for i in rows.size():
		var row: Array = rows[i]
		var body: StaticBody3D = world.camp_colliders[i] if i<6 else garage_wall_half
		body.position = Vector3(row[0],.475,row[1])
		body.collision_layer = 1 if stage > 0 else 0
		var collider: CollisionShape3D = body.get_child(1)
		(collider.shape as BoxShape3D).size = Vector3(row[2],.95,row[3])
		var along_x := float(row[2]) > float(row[3])
		var length := maxf(row[2],row[3])
		# Keep the north wall's original unbroken collider. Only split the visible
		# palisade at the two fixed timber posts when the customer counter opens.
		var spans := [Vector2(-length*.5,length*.5)]
		if i == 4 and stage == 3:
			var dock_offset := counter_center_x-float(row[0])
			spans = [Vector2(-length*.5,dock_offset-CounterLayout.HALF_BAY),Vector2(dock_offset+CounterLayout.HALF_BAY,length*.5)]
		for span: Vector2 in spans:
			var width := span.y-span.x
			var count := maxi(1,roundi(width/2.6))
			for j in count:
				var offset := span.x + width*(j+.5)/count
				var center := Vector3(row[0]+(offset if along_x else 0.),0.,row[1]+(0. if along_x else offset))
				var angle := 0.0
				if i in [2,3]: angle = PI*.5
				elif i == 4: angle = PI
				elif i == 5: angle = -PI*.5
				var axes := Basis(Vector3.UP,angle)
				axes.x *= width/(count*2.6)
				transforms.append(Transform3D(axes,center))
	var instances := palisades.multimesh
	instances.instance_count = transforms.size()
	for i in transforms.size(): instances.set_instance_transform(i,transforms[i])
	palisades.visible = stage > 0
	for i in world.gates.size():
		var gate = world.gates[i]
		gate.position = world.point(world.layout.gates[i].center_xz)
		gate.set_earned(stage > 0)
	var half_size := Vector2((r.z-r.x)*.5,(r.w-r.y)*.5)
	var center := Vector2((r.x+r.z)*.5,(r.y+r.w)*.5)
	if perimeter_tween: perimeter_tween.kill()
	if animate and previous > 0 and stage > previous:
		perimeter_tween = create_tween().set_parallel(true)
		perimeter_tween.tween_method(func(v:Vector2): snow.set_shader_parameter("half_court",v),snow.get_shader_parameter("half_court"),half_size,.46)
		perimeter_tween.tween_method(func(v:Vector2): snow.set_shader_parameter("court_center",v),snow.get_shader_parameter("court_center"),center,.46)
		palisades.scale.y = .12
		perimeter_tween.tween_property(palisades,"scale:y",1.,.38).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	else:
		palisades.scale.y = 1.
		snow.set_shader_parameter("half_court",half_size)
		snow.set_shader_parameter("court_center",center)
	if world.forest and not world.forest.records.is_empty():
		world.forest.refresh_camp(animate)
	if stage>0:
		# The first playable pine originally stood against the expanding south
		# wall. Keep its harvest ID, notches and five-second regrowth countdown.
		if world.resource_tree:
			var starter: Node3D = world.resource_tree
			var radius: float = (starter.crown_size.x+.18*starter.crown_size.y)*starter.TREE_SCALE
			if occupies_camp_ground(starter.position,radius):
				starter.position.z = maxf(starter.position.z,r.w+radius+.35)
				starter.position.x = minf(starter.position.x,-world.gates[0].HALF_SPAN-radius-.22)
		for tree: Node3D in world.trees:
			if tree.phase == "falling" and not tree.is_queued_for_deletion():
				var size: Vector2 = tree.crown_size*tree.TREE_SCALE*tree.global_basis.get_scale().abs().x
				tree.fall_direction = tree_fall_direction(tree.position,tree.fall_direction,size.y,size.x)
				var fraction: float = tree.falling_clock/tree.FALL_SECONDS
				tree._pose(tree.FALL_MAX*fraction*fraction)
		for drop: Dictionary in world.drops.values():
			var radius: float = world.loose_clearance(drop.kind)
			var start := safe_drop_origin(drop.from,radius)
			drop.from = start
			drop.at = clip_travel(start,drop.at,radius)
	perimeter_changed.emit()

func install_hearth() -> void:
	var base: Node3D = world.camp_built.get_node("CenteredHearth_StudioTrialOnly")
	for child in base.get_children():
		if not child is StaticBody3D: child.hide()
	const HEARTH_SCALE := 0.76
	var shell: Node3D = world.model(HEARTH,base,2.25 * HEARTH_SCALE)
	hearth_shell = shell
	shell.name = "RecoveredStoneFurnace"
	var fire := OmniLight3D.new()
	coal_glow = fire
	fire.name = "CoalGlow"
	fire.light_color = Color("ff9d4b")
	fire.light_energy = .84
	fire.omni_range = 3.0 * HEARTH_SCALE
	fire.position = Vector3(.03,.68,.72) * HEARTH_SCALE
	base.add_child(fire)
	ignition.shader = preload("res://assets/field_camp/hearth_ignition.gdshader")
	for m: MeshInstance3D in shell.find_children("*","MeshInstance3D",true,false):
		m.layers = 2
		hearth_stones.append(m)
	fire.light_cull_mask = 3
	hearth_fire.install(shell,fire)
	for body in base.get_children():
		if body is StaticBody3D:
			var shape: CollisionShape3D = body.get_child(0)
			var cylinder := shape.shape as CylinderShape3D
			hearth_footprint = shape
			cylinder.radius = 1.14 * HEARTH_SCALE
			cylinder.height = 1.35 * HEARTH_SCALE
			shape.position.y = cylinder.height * .5

## A reveal or a legacy save can place a stationary capsule inside the new furnace.
func clear_hearth_footprint(at: Vector3) -> Vector3:
	var center := hearth_footprint.global_position
	var offset := Vector2(at.x-center.x,at.z-center.z)
	var radius := (hearth_footprint.shape as CylinderShape3D).radius + float(world.layout.actor_radius) + .025
	if offset.length_squared() >= radius*radius: return at
	var outward := offset.normalized() if not offset.is_zero_approx() else Vector2.DOWN
	return Vector3(center.x + outward.x*radius,at.y,center.z + outward.y*radius)

func canopy_ink(material: Material) -> Material:
	if not material is StandardMaterial3D or material.has_meta(&"snow_pine_tinted") or material.resource_name.to_lower() not in ["crown","lip"]:
		return material
	if not canopy_materials.has(material):
		var shaded := material.duplicate() as StandardMaterial3D
		var skirt := material.resource_name.to_lower() == "lip"
		var bank := material.resource_path.begins_with("res://assets/reference_forest/bank_pine_")
		if bank:
			# Wide pale snow faces sit above the shaded slate-blue branches.
			shaded.albedo_color *= Color(.53,.60,.73) if skirt else Color(.85,.90,.92)
			shaded.emission = Color("679acf")
			shaded.emission_energy_multiplier = .24 if skirt else .43
		else:
			shaded.albedo_color *= Color(.44,.51,.66) if skirt else Color(.62,.63,.72)
			shaded.emission = Color("4973b0") if skirt else Color("4c79bc")
			shaded.emission_energy_multiplier = .32 if skirt else .60
		shaded.emission_enabled = true
		shaded.emission_texture = null
		shaded.emission_operator = BaseMaterial3D.EMISSION_OP_ADD
		shaded.set_meta(&"snow_pine_tinted",true)
		canopy_materials[material] = shaded
	return canopy_materials[material]

func tint_canopy(node:Node3D) -> void:
	var parts: Array[MeshInstance3D] = []
	world.meshes(node,parts)
	for part in parts:
		for i in part.mesh.get_surface_count():
			var material := part.get_active_material(i)
			var shaded := canopy_ink(material)
			if material != shaded: part.set_surface_override_material(i,shaded)

func install_woods() -> void:
	var parent := Node3D.new()
	parent.name = "PeripheralSnowForest"
	world.add_child(parent)
	# Place trees in irregular groves, leaving the active approach and both gate corridors open.
	var positions := [Vector2(-13,3),Vector2(-15,1),Vector2(-12,-1.4),Vector2(-11.7,-5.4),Vector2(-9.7,-7.2),
		Vector2(-7.5,-9.5),Vector2(-5.7,-10.4),Vector2(-2.4,-10.8),Vector2(.4,-12.3),Vector2(3.1,-10.6),
		Vector2(6.2,-11.1),Vector2(9.2,-10.2),Vector2(11.4,-8.6),Vector2(14.8,-7.8),
		Vector2(-15,5.5),Vector2(-17,8.2),Vector2(-14.4,11.2),Vector2(-12,14),Vector2(-15,14.2),
		Vector2(-7.0,2.65),Vector2(-8.4,4.8),Vector2(-7.0,7.45),Vector2(-9.4,8.5),
		Vector2(-10.4,4.7),Vector2(-9.9,11.1),Vector2(-7.5,12.5),Vector2(-6.2,14.6),
		Vector2(7.8,-6.0),Vector2(9.55,-4.9),Vector2(11.6,-4.0),Vector2(13.4,-3.5),
		Vector2(9.8,3.95),Vector2(11.6,5.45),Vector2(12.45,7.85),Vector2(14.5,8.2),
		Vector2(10.9,10.1),Vector2(13.15,10.3),Vector2(14.1,12.25),Vector2(16.1,11.4)]
	# Two interlocking tree lines meet around the northwest corner. Three
	# staggered rows frame the portrait horizon and the paid rear wall.
	for row in 3:
		for column in 13:
			var x := -13.4 + column * 1.58 + (row % 2) * .73
			var z := -5.3 - row * 1.32 + sin(column*1.41+row)*.27
			positions.append(Vector2(x,z))
		for column in 8:
			var x := -6.15 - row*1.32 + sin(column*1.7+row)*.22
			var z := -4.25 + column*1.58 + (row % 2)*.67
			positions.append(Vector2(x,z))
	for column in 8:
		# Beyond the active woods and wolves, fill the near corners on tall screens.
		positions.append(Vector2(2.5+column*1.45,21.2+sin(column)*.45))
		positions.append(Vector2(14.8+sin(column*1.42)*.5,10.2+column*1.5))
	# Smaller companion crowns break up evenly spaced silhouettes. The actual
	# harvest and enemy anchors are set by the world before this deferred pass.
	tint_canopy(world.get_node("ExteriorExactT01Visuals"))
	var relocated: Array[Transform3D] = []
	for i in SEASONAL_POCKETS.size():
		var old_root: Vector2 = SEASONAL_SOURCE_ANCHORS[i]
		var root: Vector2 = SEASONAL_POCKETS[i]
		var source_id := "pine@%d,%d" % [roundi(old_root.x*1000),roundi(old_root.y*1000)]
		var height_scale := 1.05 + .20*fposmod(i*.618,1)
		var yaw := i*2.39996
		if root != old_root:
			# Off-site trees belong to the permanent batch and keep their save IDs.
			var key := Vector2i(roundi(root.x*1000),roundi(root.y*1000))
			grove_source_aliases[key] = source_id
			var mesh_scale: float = world.ResourceTreeScript.TREE_SCALE * height_scale
			var basis := Basis(Vector3.UP,yaw).scaled(BANK_PINE_PROPORTIONS*mesh_scale)
			relocated.append(Transform3D(basis,Vector3(root.x,0.0,root.y)))
		elif camp_state == 0 and world.has_method("_add_pine"):
			var stem: Node3D = world._add_pine(root,0,source_id)
			stem.scale = Vector3.ONE*height_scale
			stem.rotation.y = yaw
			seasonal_pines.append(stem)
	var blocked: Array[Vector2] = []
	if "trees" in world:
		for tree: Node3D in world.trees:
			tint_canopy(tree)
			if tree not in seasonal_pines:
				blocked.append(Vector2(tree.position.x,tree.position.z))
	# Retain the original exclusions when seeding the surrounding permanent groves.
	if not seasonal_pines.is_empty(): blocked.append_array(SEASONAL_SOURCE_ANCHORS)
	var permanent_roots := blocked.duplicate()
	if "enemies" in world:
		for enemy: Node3D in world.enemies:
			blocked.append(Vector2(enemy.position.x,enemy.position.z))
	pine_scenes.assign(world.CONIFERS)
	pine_scenes.append_array(BANK_CONIFERS)
	var variant_count: int = world.CONIFERS.size()
	var transforms := []
	for variant in pine_scenes.size():
		transforms.append([])
	var occupied: Array[Vector2] = []
	var initial := positions.size()
	var quarry_tree := 0
	for i in 32:
		var offset := Vector2(1.35,0).rotated(2.39996*i)
		var candidate: Vector2 = positions[i]+offset
		if absf(candidate.x)>7.5 or candidate.y < -7.: positions.append(candidate)
	var existing_count := positions.size()
	positions.append_array(FOREST_BANKS)
	var understory_start := positions.size()
	positions.append_array(FOREST_UNDERSTORY)
	for i in positions.size():
		var at: Vector2 = positions[i]
		# New roots keep their source IDs across reloads and moving enemy spawns.
		var reserved_roots := blocked if i < existing_count else permanent_roots
		var root_clearance_squared := 1.44 if i >= understory_start else 3.2
		if reserved_roots.any(func(p:Vector2): return p.distance_squared_to(at) < root_clearance_squared) or occupied.any(func(p:Vector2): return p.distance_squared_to(at) < 1.25):
			continue
		occupied.append(at)
		# Keep the accepted grove count and mesh variants. The clearing applies
		# to this occupied quarry, leaving the broader woodline intact.
		if at.distance_squared_to(Vector2(-6,3)) < 2.4*2.4 and quarry_tree < QUARRY_EDGE.size():
			at = QUARRY_EDGE[quarry_tree]
			quarry_tree += 1
		var scale_factor := (.72+.19*fposmod(i*.618,1)) if i<initial else (.48+.19*fposmod(i*.414,1))
		if i >= understory_start:
			scale_factor = .63 + .10*fposmod(i*.618,1)
		elif i >= existing_count:
			scale_factor = .75 + .15*fposmod(i*.618,1)
		var faces_clearing := i >= existing_count or at.y < -3.8
		var proportions := BANK_PINE_PROPORTIONS if faces_clearing else Vector3.ONE
		var basis := Basis(Vector3.UP,i*2.39996).scaled(proportions*scale_factor)
		var variant := i % variant_count + (variant_count if faces_clearing else 0)
		transforms[variant].append(Transform3D(basis,Vector3(at.x,0,at.y)))
	transforms[variant_count].append_array(relocated)
	for variant in pine_scenes.size():
		var scene := pine_scenes[variant]
		var tree := scene.instantiate() as Node3D
		pine_shapes.append(preload("res://resource_tree.gd").native_shape(scene,tree))
		var parts: Array[MeshInstance3D] = []
		world.meshes(tree,parts)
		for part in parts:
			var multi := MultiMesh.new()
			multi.transform_format = MultiMesh.TRANSFORM_3D
			var lit_mesh := part.mesh.duplicate() as Mesh
			for i in lit_mesh.get_surface_count(): lit_mesh.surface_set_material(i,canopy_ink(part.get_active_material(i)))
			multi.mesh = lit_mesh
			multi.instance_count = transforms[variant].size()
			for i in multi.instance_count: multi.set_instance_transform(i,transforms[variant][i]*part.transform)
			var grove := MultiMeshInstance3D.new()
			grove.multimesh = multi
			grove.set_meta("tree_variant",variant)
			grove.set_meta("tree_placements",transforms[variant])
			parent.add_child(grove)
		tree.free()

func flat_label(parent:Node3D, at:Vector3, px:float) -> Label3D:
	var label := Label3D.new()
	label.position = at
	label.rotation.x = -PI/2
	label.font_size = 48
	label.pixel_size = px
	label.outline_size = 9
	label.modulate = Color("fff5db")
	label.outline_modulate = Color("332824")
	label.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(label)
	return label

# Use the authored resource portraits on the floor so a player can read costs
# without rotating to the screen HUD. Keep a material's slot stable as units land.
func cost_row(parent:Node3D, kinds:Array, z:float) -> Node3D:
	var row := Node3D.new()
	row.position = Vector3(0,.009,z)
	parent.add_child(row)
	for i in kinds.size():
		var kind: String = kinds[i]
		var center := (i - (kinds.size()-1)*.5)*.88
		var icon := Sprite3D.new()
		icon.axis = Vector3.AXIS_Y
		if kind in ["planks","blocks"]:
			const Atlas = preload("res://assets/field_ui/camp_goods.png")
			var glyph := AtlasTexture.new()
			glyph.atlas = Atlas
			var side := Atlas.get_width()/4.
			var index := 9 if kind=="planks" else 10
			glyph.region = Rect2((index%4)*side, floori(index/4.)*side,side,side)
			icon.texture = glyph
		else:
			icon.texture = preload("res://field_hud.gd").MATERIAL_ICONS[kind]
		icon.pixel_size = .0046
		icon.position.x = center-.17
		icon.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		row.add_child(icon)
		var number := flat_label(row,Vector3(center+.21,0,0),.0092)
		number.modulate = Color.WHITE
		number.name = kind
	return row

func show_costs(row:Node3D, due:Dictionary) -> void:
	for kind in due:
		var number := row.get_node_or_null(NodePath(kind)) as Label3D
		if number: number.text = str(int(due[kind]) if kind in ["planks","blocks"] else Progress.units(due[kind]))

func install_payment(anchor:Node3D, upgrade:bool) -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DONOR+"build_inlay.json"))
	anchor.name = "OrbitUpgradeFloor" if upgrade else "ConstructionPaymentFloor"
	add_child(anchor)
	var at := UPGRADE if upgrade else BUY
	anchor.position = Vector3(at.x,.008,at.y)
	if upgrade: anchor.scale = Vector3(.84,1.,.84)
	for role in ["gray","brackets"]:
		var brush := SurfaceTool.new()
		brush.begin(Mesh.PRIMITIVE_TRIANGLES)
		var layer := 0. if role=="gray" else .002
		for p in data.vertices[role]:
			brush.set_normal(Vector3.UP)
			var point := Vector2(float(p[0]),float(p[2]))
			if role == "brackets":
				# Measure along and across the donor stroke independently. The
				# original has a circular elbow and a short straight tail on each arm.
				var uv := point.abs()
				var elbow := Vector2(.43,.43)
				var centerline: Vector2
				if uv.x < elbow.x:
					centerline = Vector2(maxf(uv.x,.332),.506)
				elif uv.y < elbow.y:
					centerline = Vector2(.506,maxf(uv.y,.332))
				else:
					centerline = elbow + (uv-elbow).normalized()*.076
				var pivot := Vector2(.506,.506)
				point = point.sign()*(pivot+Vector2(.035,.035)+(centerline-pivot)*1.04+(uv-centerline)*2.65)
			brush.add_vertex(Vector3(point.x*2.64,layer,-point.y*2.18))
		var ink := StandardMaterial3D.new()
		ink.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		ink.cull_mode = BaseMaterial3D.CULL_DISABLED
		ink.albedo_color = Color({"gray":"51bd37","brackets":"5be72e"}[role])
		var mark := MeshInstance3D.new()
		mark.name = role.capitalize()
		mark.mesh = brush.commit()
		if role=="gray":
			var fill := ShaderMaterial.new()
			fill.shader = FILL
			fill.set_shader_parameter("grounded",Color("9eabb6") if not upgrade else Color("5d5147"))
			fill.set_shader_parameter("funded",Color("3bc615"))
			payment_ink["upgrade" if upgrade else "buy"] = fill
			mark.material_override = fill
		else:
			ink.albedo_color = Color("f8fbff")
			payment_brackets["upgrade" if upgrade else "buy"] = ink
			mark.material_override = ink
		mark.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		anchor.add_child(mark)
	if upgrade:
		var icon := Sprite3D.new()
		icon.texture = preload("res://assets/field_camp/orbit_upgrade.svg")
		icon.axis = Vector3.AXIS_Y
		icon.pixel_size = .005
		icon.position = Vector3(0,.006,-.24)
		icon.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		anchor.add_child(icon)
		upgrade_label = flat_label(anchor,Vector3(0,.007,.53),.0068)
		set_upgrade_payment(Progress.OFFERS[Progress.AXES])
	else:
		var castle := Sprite3D.new()
		castle.name = "Castle"
		castle.axis = Vector3.AXIS_Y
		castle.texture = preload("res://assets/field_camp/hearth_mark.svg")
		castle.pixel_size = .0084
		castle.position = Vector3(0,.006,-.29)
		castle.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		anchor.add_child(castle)
		payment_costs = cost_row(anchor,["wood"],.49)
		show_costs(payment_costs,Progress.OFFERS[Progress.HEARTH])

func set_payment(remaining: Dictionary) -> void:
	show_costs(payment_costs,remaining)

func set_payment_progress(fraction:float, receiver: String = "buy") -> void:
	if payment_ink.has(receiver):
		payment_ink[receiver].set_shader_parameter("paid",clampf(fraction,0,1))
		payment_brackets[receiver].albedo_color = Color("5be72e") if fraction > 0. else Color("f8fbff")

func set_upgrade_payment(remaining: Dictionary) -> void:
	var stone := int(remaining.get("stone",0))
	var meat := int(remaining.get("meat",0))
	upgrade_pending = stone + meat > 0
	upgrade_label.text = "Stone  %d    Meat  %d" % [Progress.units(stone),Progress.units(meat)]
	upgrade_anchor.hide()

func set_built(built: bool, animate := true) -> void:
	if camp_state == int(built): return
	camp_state = int(built)
	hearth_fire.set_fired(built)
	set_perimeter(maxi(1,perimeter_stage) if built else 0,animate)
	if built:
		for tree in seasonal_pines:
			tree.hide()
			world.retire_tree(tree,false)
		seasonal_pines.clear()
	world.purchase_pad_view.hide()
	buy_anchor.visible = not built
	upgrade_anchor.hide()
	if reveal_tween: reveal_tween.kill()
	if built and animate:
		# B 6.20–6.60 s: stone first, amber ignition, thaw from the hearth,
		# then the perimeter appears. Only authored visuals follow this tween.
		var final_height := hearth_shell.scale.y
		reveal_tween = create_tween().set_parallel(true).set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
		hearth_shell.scale.y = final_height*.78
		reveal_tween.tween_property(hearth_shell,"scale:y",final_height,.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		for mesh in hearth_stones:
			mesh.material_overlay = ignition
		ignition.set_shader_parameter("heat",0.)
		reveal_tween.tween_method(func(t:float): ignition.set_shader_parameter("heat",t),0.,1.,.06).set_delay(.035)
		reveal_tween.tween_method(func(t:float): ignition.set_shader_parameter("heat",t),1.,0.,.33).set_delay(.18)
		reveal_tween.tween_method(func(t:float): snow.set_shader_parameter("reveal",t),0.,1.,.34).set_delay(.075)
		palisades.position.y = -1.55
		reveal_tween.tween_property(palisades,"position:y",0.,.23).set_delay(.23).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		for mesh in gate_art:
			var y := mesh.position.y
			mesh.position.y = y-1.55
			reveal_tween.tween_property(mesh,"position:y",y,.23).set_delay(.23).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		reveal_tween.chain().tween_callback(_clear_ignition)
	else:
		_clear_ignition()
		snow.set_shader_parameter("reveal",1. if built else 0.)

func _clear_ignition() -> void:
	for mesh in hearth_stones:
		mesh.material_overlay = null
