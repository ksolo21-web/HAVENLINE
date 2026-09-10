extends Node3D
const Surface = preload("res://scripts/outpost_surface.gd")
var terrain: MeshInstance3D
var lake: MeshInstance3D
var lake_material: ShaderMaterial
var snow: MultiMeshInstance3D
var ground_material: ShaderMaterial
var snow_material: ShaderMaterial
var environment: Environment
var sunlight: DirectionalLight3D
var current_radius := 4.5
var current_heat := 1.0
var furnace_node: Node3D
var heat_light: OmniLight3D

func configure(env: Environment, sun: DirectionalLight3D, furnace: Node3D, light: OmniLight3D, sim):
	environment=env; sunlight=sun; furnace_node=furnace; heat_light=light
	current_radius=sim.warmth()
	current_heat=1.0 if sim.durability > 0 else 0.0
	terrain=MeshInstance3D.new()
	terrain.name="SculptedSnowfield"
	terrain.mesh=Surface.mesh()
	ground_material=ShaderMaterial.new()
	ground_material.shader=load("res://shaders/outpost_snow.gdshader")
	terrain.material_override=ground_material
	add_child(terrain)
	lake=MeshInstance3D.new()
	lake.name="TurquoiseLakeshore"
	lake.mesh=Surface.water_mesh()
	lake_material=ShaderMaterial.new()
	lake_material.shader=load("res://shaders/lakeshore_water.gdshader")
	lake.material_override=lake_material
	lake.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(lake)
	snow=MultiMeshInstance3D.new()
	snow.name="InstancedSnowfall"
	var particles:=MultiMesh.new()
	particles.transform_format=MultiMesh.TRANSFORM_3D
	particles.use_custom_data=true
	particles.mesh=QuadMesh.new()
	particles.instance_count=640
	var rng:=RandomNumberGenerator.new()
	rng.seed=754219
	for index in range(particles.instance_count):
		particles.set_instance_transform(index,Transform3D(Basis.IDENTITY,Vector3(rng.randf()*24.,rng.randf()*13.,rng.randf()*24.)))
		particles.set_instance_custom_data(index,Color(rng.randf(),rng.randf(),rng.randf(),1.0))
	snow.multimesh=particles
	snow.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	snow_material=ShaderMaterial.new()
	snow_material.shader=load("res://shaders/outpost_snowfall.gdshader")
	snow.material_override=snow_material
	add_child(snow)
	sync(sim,0.0,true)

func sync(sim, dt: float, paused: bool):
	var weather: Dictionary=sim.climate.weather()
	var daylight: float=sim.climate.daylight()
	var target_heat:=1.0 if sim.durability > 0 else 0.0
	if not paused:
		current_radius=move_toward(current_radius,sim.warmth(),dt*2.2)
		current_heat=move_toward(current_heat,target_heat,dt*.55)
	ground_material.set_shader_parameter("warmth_radius",current_radius)
	ground_material.set_shader_parameter("heat_strength",current_heat)
	ground_material.set_shader_parameter("snow_amount",weather.snow)
	ground_material.set_shader_parameter("daylight_fill",daylight)
	lake_material.set_shader_parameter("sim_time",sim.climate.seconds)
	snow_material.set_shader_parameter("sim_time",sim.climate.seconds)
	snow_material.set_shader_parameter("snow_amount",weather.snow)
	snow_material.set_shader_parameter("wind",weather.wind)
	var center:=Vector3(sim.position.x,0,sim.position.y)
	snow_material.set_shader_parameter("follow_center",center)
	snow.custom_aabb=AABB(center-Vector3(15,2,15),Vector3(30,19,30))
	var dusk:=1.0-absf(daylight*2.0-1.0)
	environment.background_color=Color("14243e").lerp(Color("89b9d5"),daylight)
	environment.ambient_light_color=Color("8ea6d4").lerp(Color("c9e0f1"),daylight)
	environment.ambient_light_energy=lerpf(.19,.38,daylight)
	environment.fog_light_color=Color("283d61").lerp(Color("bbd8e8"),daylight)
	# Depth fog is anchored beyond the near gameplay plane, not to the old camera origin.
	environment.fog_mode=Environment.FOG_MODE_DEPTH
	environment.fog_depth_begin=27.0
	environment.fog_depth_end=67.0
	environment.fog_depth_curve=1.35
	environment.fog_density=lerpf(.12,.63,float(weather.snow))
	sunlight.light_energy=lerpf(.17,.61,daylight)*(1.0-float(weather.snow)*.38)
	sunlight.light_color=Color("97b7ed").lerp(Color("fff0d6"),daylight).lerp(Color("ffb076"),dusk*.5)
	sunlight.rotation_degrees=Vector3(lerpf(-28.0,-56.0,daylight),-32.0+sin(sim.climate.hour()*PI/12.)*18.,0)
	heat_light.omni_range=sim.warmth()+1.5
	heat_light.light_energy=(2.1+sim.level*.6+sin(sim.elapsed*6.3)*.12)*target_heat*lerpf(1.0,.62,daylight)
	# Only the supplied furnace mesh is resized; no invisible upgrade/currency.
	var target_scale:=Vector3.ONE*(1.0+float(sim.level-1)*.085)
	if not paused: furnace_node.scale=furnace_node.scale.lerp(target_scale,1.0-exp(-dt*4.0))

func evidence(sim) -> Dictionary:
	return {"clock":sim.climate.snapshot(), "hour":sim.climate.hour(), "weather":sim.climate.weather(),
		"warmth_gameplay_radius":sim.warmth(), "warmth_visual_radius":current_radius,
		"heat_strength":current_heat, "snow_instances":snow.multimesh.instance_count,
		"surface_triangles":terrain.mesh.get_faces().size()/3,
		"terrain_revision":"T02-rounded-bank-and-snow-finish", "lake_triangles":lake.mesh.get_faces().size()/3,
		"water_y":Surface.WATER_Y,"lake_center":[Surface.LAKE_CENTER.x,Surface.LAKE_CENTER.y],
		"shared_actor_surface":true,
		"native_4k60_certified":false}
