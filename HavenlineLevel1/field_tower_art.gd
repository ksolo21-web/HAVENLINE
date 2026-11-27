extends Node3D

const EMPLACEMENT = preload("res://assets/field_world/camp_ballista.glb")
const Defender = preload("res://field_ballista_crew.gd")
const UPPER_BOUNDS := AABB(Vector3(-1.02,.95,-1.02),Vector3(2.04,2.30,2.04))
const TRAVERSE_RATE := 4.8
const ELEVATION_RATE := 2.8
var frame: Node3D
var swivel: Node3D
var bow: MeshInstance3D
var bolt: MeshInstance3D
var crew: Node3D
var raised := 0.0
var sightline_material := ShaderMaterial.new()
var upper_parts: Array[MeshInstance3D] = []
var cutaway_active := false
var stages: Array[Node3D] = []
var bow_rest := Vector3.ZERO
var cycle_age := 2.0
var clock := 0.0

func _ready() -> void:
	frame = EMPLACEMENT.instantiate()
	add_child(frame)
	for part_name in ["Footings","Cabin","EmplacementDeck"]:
		stages.append(frame.find_child(part_name,true,false) as Node3D)
	swivel = frame.find_child("Turntable",true,false)
	bow = swivel.find_child("BowStock",true,false)
	bolt = bow.find_child("LoadedQuarrel",true,false)
	bow_rest = bow.position
	swivel.rotation.y = PI*.5
	for part in [stages[1],stages[2]]:
		upper_parts.append(part as MeshInstance3D)
	var paint := bow.get_active_material(0).duplicate() as StandardMaterial3D
	paint.emission_enabled = true
	paint.emission = Color.WHITE
	paint.emission_texture = paint.albedo_texture
	paint.emission_energy_multiplier = .18
	for part in frame.find_children("*","MeshInstance3D",true,false):
		part.set_surface_override_material(0,paint)
	sightline_material.shader = preload("res://assets/field_world/tower_sightline.gdshader")
	sightline_material.set_shader_parameter("atlas",paint.albedo_texture)
	sightline_material.set_shader_parameter("roughness",paint.roughness)
	sightline_material.set_shader_parameter("emission_tint",Color(.18,.18,.18))
	set_build_progress(raised)

func set_build_progress(value: float) -> void:
	raised = clampf(value,0.,1.)
	if not frame:return
	for i in stages.size():
		var t := clampf(raised*4.-i,0.,1.)
		stages[i].visible = t>.001
		stages[i].position.y = lerpf(-.15,0.,smoothstep(0.,1.,t))
	swivel.visible = raised>.75
	if swivel.visible and not crew:
		crew = Defender.new()
		crew.name = "BallistaOperator"
		crew.position = Vector3(-.34,.015,-.43)
		crew.rotation.y = .38
		swivel.add_child(crew)
	if crew:
		crew.visible = raised>.84
		crew.operate(bow,0.,0.,0.)

func aim_at_world(at: Vector3, delta: float = 10.) -> bool:
	var local := to_local(at)-swivel.position
	var desired_yaw := atan2(local.x,local.z)
	var turn := angle_difference(swivel.rotation.y,desired_yaw)
	swivel.rotation.y += clampf(turn,-TRAVERSE_RATE*delta,TRAVERSE_RATE*delta)
	var local_target := swivel.to_local(at)-bow_rest
	var desired_pitch := clampf(-atan2(local_target.y-.10,Vector2(local_target.x,local_target.z).length()),-.48,.56)
	bow.rotation.x = move_toward(bow.rotation.x,desired_pitch,ELEVATION_RATE*delta)
	return absf(angle_difference(swivel.rotation.y,desired_yaw)) < .06 and absf(bow.rotation.x-desired_pitch)<.07

func animate(dt: float) -> void:
	clock += dt
	cycle_age += dt
	var kick := 1.-smoothstep(0.,.20,cycle_age)
	var draw := sin(PI*clampf((cycle_age-.16)/.91,0.,1.))
	bow.position = bow_rest+Vector3(0.,0.,-.11*kick)
	bolt.visible = cycle_age>=.87
	if crew and crew.visible:
		crew.operate(bow,draw,kick,sin(2.3*clock))

func muzzle_global_position() -> Vector3:
	return bolt.global_position

func projectile() -> Node3D:
	var shot := MeshInstance3D.new()
	shot.name = "BallistaQuarrel"
	shot.mesh = bolt.mesh
	shot.set_surface_override_material(0,bolt.get_active_material(0))
	shot.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return shot

func impact() -> Sprite3D:
	var spark := Sprite3D.new()
	spark.name = "BallistaImpact"
	spark.texture = preload("res://assets/field_world/ballista_impact.png")
	spark.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	spark.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	spark.pixel_size = .010
	spark.hframes = 6
	spark.render_priority = 2
	return spark

func play_impact(spark: Sprite3D) -> void:
	var fade := spark.create_tween()
	fade.tween_method(func(frame: float): spark.frame=mini(5,floori(frame)),0.,6.,.21)
	fade.tween_callback(spark.queue_free)

func fire(_target: Vector3) -> void:
	cycle_age = 0.
	animate(0.)

# The fixed orthographic camera projects along parallel rays at both pinch
# settings. Leave the original material in place when those rays miss the tower.
func update_sightline(feet:Vector3,camera:Camera3D) -> void:
	var local_feet := to_local(feet)
	var obstructed := false
	var eye := Vector3.ZERO
	if camera and absf(local_feet.x) < 5.5 and absf(local_feet.z) < 5.5:
		eye = camera.global_basis.z.normalized() if camera.projection==Camera3D.PROJECTION_ORTHOGONAL else camera.global_position.direction_to(feet)*-1.
		var sight := global_basis.inverse()*eye
		var bounds := UPPER_BOUNDS.grow(.60)
		for height:float in [.15,1.15,2.15]:
			var point := local_feet + Vector3.UP*height
			if bounds.intersects_segment(point,point+sight*8.) != null:
				obstructed = true
				break
	if obstructed != cutaway_active:
		for part in upper_parts:
			part.material_override = sightline_material if obstructed else null
		cutaway_active = obstructed
	if obstructed:
		sightline_material.set_shader_parameter("player_feet",feet)
		sightline_material.set_shader_parameter("toward_camera",eye)
