extends Node3D
## Authored river cross-sections form the closed inlet; movement uses the same wet outline.
const River=preload("res://assets/lakeshore/river_geometry.gd")
const Cooker=preload("res://assets/lakeshore/cooker_camp_line.glb")
const COOKER_AT := Vector3(-.10,0,-7.22)
const APRON := Vector3(1.20,0,-5.67)
const OUTPUT_APRON := Vector3(-1.05,0,-5.67)
const ACCESS_RADIUS := .77
const LAKE_XZ:=Vector2(-33.8,16.)
const STATION_YAW := PI
const STATION_SCALE := .94
# At yaw PI the +X outfeed is on the west of the working cooker.
const BODY := Rect2(-1.75 * STATION_SCALE,-.95 * STATION_SCALE,3.05 * STATION_SCALE,1.90 * STATION_SCALE)
const SECTIONS:=108
var cooker_input:Marker3D
var cooker_output:Marker3D
var cooker:Node3D
var saw:Node3D
var smoke:GPUParticles3D
var shore:=PackedVector2Array()
var bounds:=Rect2()
var water_material:=ShaderMaterial.new()
var elapsed:=0.
var working:=false
var available := false
var guard := StaticBody3D.new()

func _init() -> void:
	# Reuse the original map's Hermite shore bends and graded width. A closed
	# pair of tapered endpoints makes this an inlet in the larger snowfield.
	for i in SECTIONS:
		var angle:=TAU*float(i)/SECTIONS
		var along:=sin(angle)
		var source_x:=along*River.TERRAIN_HALF
		var meander:float=(River.center_at_x(source_x).y+8.)*.62
		var half_width:float=River.width_at_x(source_x)*2.14
		var point:=LAKE_XZ+Vector2(meander+cos(angle)*half_width,along*16.8)
		shore.append(point)
		bounds=Rect2(point,Vector2.ZERO) if i==0 else bounds.expand(point)

func setup(host:Node3D) -> void:
	name="WestInletAndCampKitchen"
	_build_inlet()
	cooker=Cooker.instantiate()
	cooker.name="CampCooker"
	add_child(cooker)
	cooker.position=COOKER_AT+Vector3.UP*.024
	cooker.rotation.y=STATION_YAW
	cooker.scale=Vector3.ONE*STATION_SCALE
	saw=cooker.find_child("SawAxle",true,false)
	cooker_input=_socket("RawInput",Vector3(-1.10,1.06,-.02))
	cooker_output=_socket("CookedOutput",Vector3(1.40,1.045,.15))
	guard.name = "CookerBody"
	add_child(guard)
	guard.position = COOKER_AT
	var collision := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(BODY.size.x,2.31,BODY.size.y)
	collision.shape = box
	collision.position = Vector3(BODY.get_center().x,box.size.y*.5,BODY.get_center().y)
	guard.add_child(collision)
	_build_smoke()
	var camp = host.get("field_env")
	if camp:
		camp.perimeter_changed.connect(func(): set_available(camp.perimeter_stage == 3))
	set_available(camp != null and camp.perimeter_stage == 3)

func set_available(enabled:bool) -> void:
	available = enabled
	cooker.visible = enabled
	guard.collision_layer = 1 if enabled else 0
	if not enabled:
		update_activity(false)

func _socket(label:String,at:Vector3) -> Marker3D:
	var marker:=Marker3D.new()
	marker.name=label
	cooker.add_child(marker)
	marker.position=at
	return marker

func _build_smoke() -> void:
	smoke=GPUParticles3D.new()
	smoke.name="StackExhaust"
	cooker.add_child(smoke)
	smoke.position=Vector3(.18,2.45,.05)
	smoke.amount=10
	smoke.lifetime=1.48
	smoke.local_coords=true
	smoke.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	smoke.visibility_aabb=AABB(Vector3(-.9,-.1,-.9),Vector3(2.,2.7,2.))
	var plume:=ParticleProcessMaterial.new()
	plume.direction=Vector3(.19,1,.09)
	plume.spread=12.
	plume.initial_velocity_min=.62
	plume.initial_velocity_max=.83
	plume.gravity=Vector3(.18,.19,.04)
	plume.scale_min=.20
	plume.scale_max=.33
	var gradient:=Gradient.new()
	gradient.offsets=PackedFloat32Array([0.,.16,.75,1.])
	gradient.colors=PackedColorArray([Color(1,1,1,0),Color.WHITE,Color(1,1,1,.67),Color(1,1,1,0)])
	var ramp:=GradientTexture1D.new()
	ramp.gradient=gradient
	plume.color_ramp=ramp
	smoke.process_material=plume
	var puff:=QuadMesh.new()
	puff.size=Vector2.ONE
	var material:=ShaderMaterial.new()
	material.shader=preload("res://assets/lakeshore/hearth_smoke.gdshader")
	puff.material=material
	smoke.draw_pass_1=puff
	smoke.emitting=false

func update_activity(is_cooking:bool) -> void:
	working=available and is_cooking
	if smoke:smoke.emitting=working

func tick(dt:float) -> void:
	elapsed=fmod(elapsed+dt,400.)
	water_material.set_shader_parameter("sim_time",elapsed)
	if working and saw:saw.rotate_z(dt*3.8)

func at_cooker(at:Vector3) -> bool:
	return _at_apron(at,APRON)

func at_output(at:Vector3) -> bool:
	return _at_apron(at,OUTPUT_APRON)

func _at_apron(at:Vector3,apron:Vector3) -> bool:
	var p := Vector2(at.x,at.z)
	return available and not _footprint(0.).has_point(p) and p.distance_squared_to(Vector2(apron.x,apron.z)) <= ACCESS_RADIUS * ACCESS_RADIUS

func _footprint(radius:float) -> Rect2:
	return Rect2(Vector2(COOKER_AT.x,COOKER_AT.z)+BODY.position,BODY.size).grow(radius)

func reserves(at:Vector3) -> bool:
	var p := Vector2(at.x,at.z)
	if available and (_footprint(.35).has_point(p) or at_cooker(at) or at_output(at)):
		return true
	return bounds.grow(1.45).has_point(p) and (Geometry2D.is_point_in_polygon(p,shore) or p.distance_squared_to(_closest_bank(p))<1.45*1.45)

func _closest_bank(p:Vector2) -> Vector2:
	var best:=shore[0]
	var dist:=INF
	for i in shore.size():
		var q:=Geometry2D.get_closest_point_to_segment(p,shore[i],shore[(i+1)%shore.size()])
		var test:=p.distance_squared_to(q)
		if test<dist:
			dist=test
			best=q
	return best

func _push_dry(p:Vector2,radius:float) -> Vector2:
	if not bounds.grow(radius+.02).has_point(p):return p
	var near:=_closest_bank(p)
	var inside:=Geometry2D.is_point_in_polygon(p,shore)
	if not inside and p.distance_to(near)>=radius+.005:return p
	var outward:Vector2=(near-p if inside else p-near).normalized()
	if outward.length_squared()<.5:outward=(near-LAKE_XZ).normalized()
	return near+outward*(radius+.007)

func _push_station(p:Vector2,box:Rect2) -> Vector2:
	if not available or not box.has_point(p):
		return p
	var c := p - box.get_center()
	var overlap := box.size*.5-c.abs()
	if overlap.x < overlap.y:
		p.x = box.end.x+.004 if c.x >= 0. else box.position.x-.004
	else:
		p.y = box.end.y+.004 if c.y >= 0. else box.position.y-.004
	return p

func constrain_motion(from:Vector3,to:Vector3,radius:float) -> Vector3:
	var begin := Vector2(from.x,from.z)
	var end := Vector2(to.x,to.z)
	var station := _footprint(radius)
	var search := Rect2(begin,Vector2.ZERO).expand(end).grow(.01)
	var near_lake := search.intersects(bounds.grow(radius+.05))
	if not near_lake and not (available and search.intersects(station)):
		return to
	var n := maxi(1,ceili(begin.distance_to(end)/.18))
	var d := (end-begin)/float(n)
	var current := _push_dry(begin,radius) if near_lake else begin
	if available and station.has_point(current):
		# A previous build could save here before this work bay existed.
		current.y = station.end.y+.004
	for i in n:
		current += d
		if near_lake: current = _push_dry(current,radius)
		current = _push_station(current,station)
	return Vector3(current.x,to.y,current.y)

func _build_inlet() -> void:
	water_material.shader=preload("res://assets/lakeshore/lakeshore_water.gdshader")
	var wet:=SurfaceTool.new()
	wet.begin(Mesh.PRIMITIVE_TRIANGLES)
	wet.set_material(water_material)
	var lip:=SurfaceTool.new()
	lip.begin(Mesh.PRIMITIVE_TRIANGLES)
	var bank_material:=ShaderMaterial.new()
	bank_material.shader=preload("res://assets/lakeshore/snow_bank.gdshader")
	lip.set_material(bank_material)
	var blocking_faces:=PackedVector3Array()
	var center:=Vector3(LAKE_XZ.x,.047,LAKE_XZ.y)
	for i in SECTIONS:
		var j:=(i+1)%SECTIONS
		var a:=Vector3(shore[i].x,.047,shore[i].y)
		var b:=Vector3(shore[j].x,.047,shore[j].y)
		# The recovered water shader expects cross-channel UVs with ice at 0/1.
		for pt:Vector3 in [center,a,b]:
			var t:=clampf((pt.z-LAKE_XZ.y)/16.8,-1.,1.)
			var bend:=River.center_at_x(t*River.TERRAIN_HALF).y
			var mid:=LAKE_XZ.x+(bend+8.)*.62
			var width:=maxf(.01,River.width_at_x(t*River.TERRAIN_HALF)*2.14*sqrt(maxf(0.,1.-t*t)))
			wet.set_uv(Vector2((pt.z-LAKE_XZ.y)*.15,clampf(.5+(pt.x-mid)/(2.*width),0.,1.)))
			wet.set_normal(Vector3.UP);wet.set_tangent(Plane(Vector3.BACK,1.));wet.add_vertex(pt)
		var base_a:=Vector3(a.x,-.25,a.z)
		var base_b:=Vector3(b.x,-.25,b.z)
		var top_a:=base_a+Vector3.UP*2.45
		var top_b:=base_b+Vector3.UP*2.45
		blocking_faces.append_array(PackedVector3Array([base_a,top_a,top_b,base_a,top_b,base_b]))
		var rows_a:=_bank_row(i)
		var rows_b:=_bank_row(j)
		for k in range(rows_a.size()-1):
			var vertices:Array=[rows_a[k],rows_b[k+1],rows_b[k],rows_a[k],rows_a[k+1],rows_b[k+1]]
			for item in vertices:
				lip.set_color(item[1]);lip.set_normal(item[2]);lip.add_vertex(item[0])
	var bank_body:=StaticBody3D.new()
	bank_body.name="SolidWaterline"
	add_child(bank_body)
	var wall:=ConcavePolygonShape3D.new()
	wall.backface_collision=true
	wall.set_faces(blocking_faces)
	var collision:=CollisionShape3D.new()
	collision.shape=wall
	bank_body.add_child(collision)
	var water:=MeshInstance3D.new()
	water.name="FlowingWater"
	add_child(water)
	water.mesh=wet.commit()
	water.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var rim:=MeshInstance3D.new()
	rim.name="SculptedIceAndSnow"
	add_child(rim)
	rim.mesh=lip.commit()
	rim.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _bank_row(i:int) -> Array:
	var p:=shore[i]
	var tangent:Vector2=(shore[(i+1)%SECTIONS]-shore[posmod(i-1,SECTIONS)]).normalized()
	var out:=Vector2(tangent.y,-tangent.x)
	var phase:=TAU*float(i)/SECTIONS
	var ledge:=.17+.045*sin(phase*7.+.8)+.028*sin(phase*19.)
	var rough:=.89+.16*sin(phase*4.8)+.10*cos(phase*11.)
	var levels:=[]
	for row in [[-.16,.032,Color("#93c6d1"),.24],[0.,.076,Color("#c0e1e6"),.36],[.14,ledge*.81,Color("#d2e8ef"),.29],[.32,ledge,Color("#f0f7fa"),0.],[.56,ledge*.80,Color("#f0f7fa"),-.20],[1.22,.002,Color("#edf5f9"),0.]]:
		var at:Vector2=p+out*float(row[0])*rough
		var normal:=Vector3(-out.x*float(row[3]),1.,-out.y*float(row[3])).normalized()
		levels.append([Vector3(at.x,row[1],at.y),row[2],normal])
	return levels

