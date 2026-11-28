extends Node3D
## World One's west-to-east river uses the approved bend and width profile at
## the current map scale. All shores query the same sections drawn by the mesh.
const Profile = preload("res://assets/lakeshore/river_geometry.gd")
const WATER = preload("res://assets/lakeshore/lakeshore_water.gdshader")
const BANK = preload("res://assets/lakeshore/snow_bank.gdshader")
const MAP_CENTER_Z := -33.0
const SECTION_LENGTH := 1.0
const WATER_HEIGHT := -.19
const BANK_WIDTH := 1.45
const RESOURCE_LANE := 2.25
const CROSSING_X := 1.5
const CROSSING_HALF_WIDTH := 1.5
const LAYOUT_VERSION := "world_one_river_v1_mapspan"
const RIM := [-.08, .26, .65, 1.03, BANK_WIDTH]
const RIM_HEIGHTS := [WATER_HEIGHT, -.08, .13, .09, 0.0]
const RIM_COLORS := [Color("#88bbc9"), Color("#b5d5df"), Color("#e2f0f7"), Color("#eef6fb"), Color("#e9f4fc")]

var sections := PackedVector3Array()
var half_map := 512.0
var outside := 588.0
var corridor_min := INF
var corridor_max := -INF
var water_material := ShaderMaterial.new()
var flow_time := 0.0

func install(world: Node3D, snow: Material) -> void:
	name = "WorldOneRiver"
	half_map = float(world.layout.snow_extent_half)
	outside = half_map + 76.0
	for index in roundi(outside * 2.0 / SECTION_LENGTH) + 1:
		var x := minf(outside,-outside + SECTION_LENGTH * index)
		var historical_x := clampf(x,-Profile.TERRAIN_HALF,Profile.TERRAIN_HALF)
		var z := MAP_CENTER_Z + Profile.center_at_x(historical_x).y + 8.0
		if historical_x != x:
			# Continue the same end tangent into a broader district-wide bend.
			var distance := absf(x - historical_x)
			var tangent := Profile.tangent_at_x(historical_x)
			z += signf(x)*tangent.y/tangent.x*9.0*(1.0-exp(-distance/9.0))
			var reach := clampf(distance/(half_map-Profile.TERRAIN_HALF),0.0,1.0)
			z += signf(x)*9.0*sin(PI*reach)*smoothstep(0.0,.15,reach)
		var half_width := Profile.width_at_x(historical_x)*.5 + .06*sin(x*.47) + .045*cos(x*.82)
		sections.append(Vector3(x,z - half_width,z + half_width))
		corridor_min = minf(corridor_min,z - half_width - BANK_WIDTH)
		corridor_max = maxf(corridor_max,z + half_width + BANK_WIDTH)
	_build_surfaces(world,snow)

func banks_at(x: float) -> Vector2:
	var sample := clampf((x + outside) / SECTION_LENGTH,0.,float(sections.size()-1))
	var index := mini(floori(sample),sections.size()-2)
	var row := sections[index].lerp(sections[index+1],sample - index)
	return Vector2(row.y,row.z)

func _on_crossing(x: float, radius: float) -> bool:
	return absf(x - CROSSING_X) <= CROSSING_HALF_WIDTH - radius

func is_dry(at: Vector2, radius: float = 0.0) -> bool:
	if at.y <= corridor_min - radius or at.y >= corridor_max + radius or _on_crossing(at.x,radius):
		return true
	var banks := banks_at(at.x)
	return at.y <= banks.x - BANK_WIDTH - radius or at.y >= banks.y + BANK_WIDTH + radius

func dry_position(at: Vector2, radius: float = 0.0) -> Vector2:
	if is_dry(at,radius): return at
	var banks := banks_at(at.x)
	var pad := BANK_WIDTH + radius + .015
	return Vector2(at.x,banks.x - pad if at.y < (banks.x + banks.y) * .5 else banks.y + pad)

func safe_feet(at: Vector3, radius: float) -> Vector3:
	var dry := dry_position(Vector2(at.x,at.z),radius)
	return Vector3(dry.x,at.y,dry.y)

func travel_clear(from: Vector2, to: Vector2, radius: float = 0.0) -> bool:
	if minf(from.y,to.y) >= corridor_max + radius or maxf(from.y,to.y) <= corridor_min - radius:
		return true
	if _on_crossing(from.x,radius) and _on_crossing(to.x,radius): return true
	# Within each section the banks are linear. Test the segment at every
	# section or crossing edge it intersects so a long step cannot tunnel.
	if not is_dry(from,radius) or not is_dry(to,radius): return false
	var delta := to - from
	if is_zero_approx(delta.x):
		var banks := banks_at(to.x)
		return maxf(from.y,to.y) <= banks.x - BANK_WIDTH - radius or minf(from.y,to.y) >= banks.y + BANK_WIDTH + radius
	var split_at := PackedFloat32Array([0.0,1.0])
	var left := minf(from.x,to.x)
	var right := maxf(from.x,to.x)
	for i in range(ceili((left + outside) / SECTION_LENGTH),floori((right + outside) / SECTION_LENGTH)+1):
		var x := float(i)*SECTION_LENGTH - outside
		if x > left and x < right: split_at.append((x - from.x) / delta.x)
	for x: float in [CROSSING_X - CROSSING_HALF_WIDTH + radius,CROSSING_X + CROSSING_HALF_WIDTH - radius]:
		if x > left and x < right: split_at.append((x - from.x) / delta.x)
	split_at.sort()
	for i in range(1,split_at.size()):
		var a := from + delta * split_at[i-1]
		var b := from + delta * split_at[i]
		if _on_crossing((a.x + b.x) * .5,radius): continue
		var margins := Vector2(BANK_WIDTH + radius,-BANK_WIDTH - radius)
		var start := banks_at(a.x) - margins
		var finish := banks_at(b.x) - margins
		if (a.y > start.x or b.y > finish.x) and (a.y < start.y or b.y < finish.y): return false
	return true

func constrain_motion(from: Vector3, to: Vector3, radius: float) -> Vector3:
	var start := Vector2(from.x,from.z)
	var target := Vector2(to.x,to.z)
	if travel_clear(start,target,radius): return to
	var current := dry_position(start,radius)
	var steps := maxi(1,ceili(start.distance_to(target)/.20))
	var delta := (target - start) / steps
	for i in steps:
		var next := current + delta
		if travel_clear(current,next,radius):
			current = next
		else:
			# Slide along the shore without carrying a blocked component across it.
			var tangent := Vector2(next.x,current.y)
			if travel_clear(current,tangent,radius): current = tangent
	return Vector3(current.x,to.y,current.y)

func crossing_approaches(radius: float) -> PackedVector2Array:
	var banks := banks_at(CROSSING_X)
	var pad := BANK_WIDTH + radius + .45
	return PackedVector2Array([Vector2(CROSSING_X,banks.x-pad),Vector2(CROSSING_X,banks.y+pad)])

func shore_detour(at: Vector2, radius: float) -> Vector2:
	var banks := banks_at(at.x)
	var pad := radius + .18
	var z := minf(at.y,corridor_min-pad) if at.y < (banks.x+banks.y)*.5 else maxf(at.y,corridor_max+pad)
	return Vector2(at.x,z)

func navigation_points(radius: float) -> PackedVector2Array:
	var points := crossing_approaches(radius)
	points.append(shore_detour(points[0],radius))
	points.append(shore_detour(points[1],radius))
	return points

func reserves(at: Vector2, extra: float = 0.0) -> bool:
	if at.y < corridor_min - RESOURCE_LANE - extra or at.y > corridor_max + RESOURCE_LANE + extra: return false
	var banks := banks_at(at.x)
	var pad := BANK_WIDTH + RESOURCE_LANE + extra
	return at.y >= banks.x - pad and at.y <= banks.y + pad

func resource_bank_position(at: Vector2, setback: float) -> Vector2:
	var banks := banks_at(at.x)
	var pad := BANK_WIDTH + RESOURCE_LANE + setback
	return Vector2(at.x,banks.x - pad if at.y < (banks.x + banks.y) * .5 else banks.y + pad)

func tick(dt: float) -> void:
	flow_time = fmod(flow_time + dt,400.)
	water_material.set_shader_parameter("sim_time",flow_time)

func _strip(surface: SurfaceTool, a: PackedVector3Array, b: PackedVector3Array, colors: Array[Color] = []) -> void:
	for i in range(a.size()-1):
		for item: Vector2i in [Vector2i(0,i),Vector2i(1,i),Vector2i(1,i+1),Vector2i(0,i),Vector2i(1,i+1),Vector2i(0,i+1)]:
			var point := a[item.y] if item.x == 0 else b[item.y]
			if not colors.is_empty(): surface.set_color(colors[item.y])
			surface.add_vertex(point)

func _build_surfaces(world: Node3D, snow: Material) -> void:
	var land := SurfaceTool.new()
	land.begin(Mesh.PRIMITIVE_TRIANGLES)
	var support := SurfaceTool.new()
	support.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rim := SurfaceTool.new()
	rim.begin(Mesh.PRIMITIVE_TRIANGLES)
	var flow := SurfaceTool.new()
	flow.begin(Mesh.PRIMITIVE_TRIANGLES)
	water_material.shader = WATER
	water_material.set_shader_parameter("world_river_style",1.0)
	var rim_material := ShaderMaterial.new()
	rim_material.shader = BANK
	rim_material.set_shader_parameter("river_snow_fill",1.0)
	rim_material.set_shader_parameter("river_crossing",Vector2(CROSSING_X,CROSSING_HALF_WIDTH))
	var left := CROSSING_X-CROSSING_HALF_WIDTH
	var right := CROSSING_X+CROSSING_HALF_WIDTH
	for index in range(1,sections.size()):
		var a := sections[index-1]
		var b := sections[index]
		var crossing := a.x >= left and b.x <= right
		var fade_a := smoothstep(CROSSING_HALF_WIDTH,CROSSING_HALF_WIDTH+1.0,absf(a.x-CROSSING_X))
		var fade_b := smoothstep(CROSSING_HALF_WIDTH,CROSSING_HALF_WIDTH+1.0,absf(b.x-CROSSING_X))
		for row: Vector2i in [Vector2i(0,0),Vector2i(1,0),Vector2i(1,1),Vector2i(0,0),Vector2i(1,1),Vector2i(0,1)]:
			var at := a if row.x == 0 else b
			var shore := at.y if row.y == 0 else at.z
			flow.set_normal(Vector3.UP)
			flow.set_tangent(Plane(Vector3.RIGHT,1.0))
			flow.set_uv(Vector2(at.x*.15,float(row.y)))
			flow.add_vertex(Vector3(at.x,WATER_HEIGHT,shore))
		for side in [-1.0,1.0]:
			var first := a.y if side < 0.0 else a.z
			var next := b.y if side < 0.0 else b.z
			var rail_a := PackedVector3Array()
			var rail_b := PackedVector3Array()
			var colors: Array[Color] = []
			for band in RIM.size():
				var y: float = RIM_HEIGHTS[band]
				var offset: float = RIM[band]*side
				var shoulder := 1.0 if band in [1,2,3] else 0.0
				var first_wave := shoulder * .035 * sin(a.x*1.13+side)
				var next_wave := shoulder * .035 * sin(b.x*1.13+side)
				rail_a.append(Vector3(a.x,minf(0.0,y+first_wave)+maxf(0.0,y+first_wave)*fade_a,first+offset))
				rail_b.append(Vector3(b.x,minf(0.0,y+next_wave)+maxf(0.0,y+next_wave)*fade_b,next+offset))
				colors.append(RIM_COLORS[band])
			var slope_a := PackedVector3Array([rail_a[-1],Vector3(a.x,0.,outside*side)])
			var slope_b := PackedVector3Array([rail_b[-1],Vector3(b.x,0.,outside*side)])
			if side < 0.0:
				if not crossing: _strip(rim,rail_b,rail_a,colors)
				_strip(land,slope_b,slope_a)
			else:
				if not crossing: _strip(rim,rail_a,rail_b,colors)
				_strip(land,slope_a,slope_b)
			if a.x >= -half_map and b.x <= half_map:
				slope_a[1].z = half_map * side
				slope_b[1].z = half_map * side
				if side < 0.0: _strip(support,slope_b,slope_a)
				else: _strip(support,slope_a,slope_b)
		if crossing:
			# The snow deck shares the dry ground's edge and height. There
			# is no raised crest under the clear drive width.
			var deck_a := PackedVector3Array([Vector3(a.x,0.,a.y-BANK_WIDTH),Vector3(a.x,0.,a.z+BANK_WIDTH)])
			var deck_b := PackedVector3Array([Vector3(b.x,0.,b.y-BANK_WIDTH),Vector3(b.x,0.,b.z+BANK_WIDTH)])
			_strip(land,deck_a,deck_b)
			_strip(support,deck_a,deck_b)
	_crossing_edge(rim,left,-1.0)
	_crossing_edge(rim,right,1.0)
	land.generate_normals()
	land.index()
	rim.generate_normals()
	rim.index()
	flow.index()
	var ground: Node3D = world.get_node("SnowGround_NoPaintedPaths")
	var visible_ground: MeshInstance3D = ground.find_children("*","MeshInstance3D",false,false)[0]
	visible_ground.mesh = land.commit()
	visible_ground.global_position = Vector3.ZERO
	visible_ground.material_override = snow
	var floor_shape: CollisionShape3D = ground.find_children("*","CollisionShape3D",false,false)[0]
	floor_shape.shape = support.commit().create_trimesh_shape()
	floor_shape.global_position = Vector3.ZERO
	var bank := _add_surface("SculptedRiverBanks",rim.commit(),rim_material)
	bank.create_trimesh_collision()
	_add_surface("FlowingRiver",flow.commit(),water_material)

func _crossing_edge(rim: SurfaceTool, x: float, side: float) -> void:
	var banks := banks_at(x)
	var snow_edge := PackedVector3Array()
	var ice_edge := PackedVector3Array()
	var pigment: Array[Color] = []
	for sample in 17:
		var portion := float(sample)/16.0
		var z := lerpf(banks.x-BANK_WIDTH,banks.y+BANK_WIDTH,portion)
		var curve := sin(PI*portion)
		var span := .009+(.16+.041*sin(portion*19.0))*curve*curve
		snow_edge.append(Vector3(x,0.,z))
		ice_edge.append(Vector3(x+side*span,-.006-.13*curve,z))
		pigment.append(Color("#d7e9f3").lerp(Color("#a8d7e7"),curve*.46))
	if side < 0.0: _strip(rim,ice_edge,snow_edge,pigment)
	else: _strip(rim,snow_edge,ice_edge,pigment)

func _add_surface(label: String, mesh: ArrayMesh, material: Material) -> MeshInstance3D:
	var visible := MeshInstance3D.new()
	visible.name = label
	visible.mesh = mesh
	visible.material_override = material
	visible.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(visible)
	return visible
