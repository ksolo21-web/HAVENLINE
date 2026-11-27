extends Node3D

const EMPLACEMENT = preload("res://assets/field_world/camp_ballista.glb")
const Defender = preload("res://field_ballista_crew.gd")
const GUARD_SIGHTLINE = preload("res://assets/field_world/guard_sightline.gdshader")
const GuardSightline = preload("res://field_guard_sightline.gd")
const TRAVERSE_RATE := 4.8
const ELEVATION_RATE := 2.8
var frame: Node3D
var swivel: Node3D
var bow: MeshInstance3D
var bolt: MeshInstance3D
var crew: Node3D
var viewer: Camera3D
var raised := 0.0
var stages: Array[Node3D] = []
var occluders: Array[MeshInstance3D] = []
var guard_occluders: Array[MeshInstance3D] = []
var faces: Array[TriangleMesh] = []
var player_marker := Label3D.new()
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
	# The rear breech sits in front of the operator. The bearing stays on its
	# original axle and the projecting deck supports both feet through a turn.
	bow_rest = bow.position + Vector3(0.,0.,.29)
	bow.position = bow_rest
	stages[2].scale = Vector3(1.18,1.,1.18)
	swivel.rotation.y = PI*.5
	for part: MeshInstance3D in frame.find_children("*","MeshInstance3D",true,false):
		guard_occluders.append(part)
	for part: MeshInstance3D in [stages[0],stages[1],stages[2],swivel,bow]:
		occluders.append(part)
		faces.append(part.mesh.generate_triangle_mesh())
	player_marker.name = "PlayerBehindTower"
	player_marker.text = "▼"
	player_marker.font_size = 24
	player_marker.outline_size = 5
	player_marker.modulate = Color("#79e5ef")
	player_marker.outline_modulate = Color("#123b51")
	player_marker.pixel_size = .0085
	player_marker.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	player_marker.no_depth_test = true
	player_marker.hide()
	add_child(player_marker)
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
		crew.position = Vector3(0.,.016,-.85)
		crew.scale = Vector3.ONE*.90
		swivel.add_child(crew)
		var sightline := ShaderMaterial.new()
		sightline.shader = GUARD_SIGHTLINE
		var pass_controller := GuardSightline.new()
		add_child(pass_controller)
		pass_controller.setup(viewer,crew,self,guard_occluders,sightline)
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
	bow.position = bow_rest+Vector3(0.,0.,-.048*kick)
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

func update_sightline(feet: Vector3, camera: Camera3D, height := 1.75) -> void:
	var local_feet := to_local(feet)
	if not camera or absf(local_feet.x) > 4.0 or absf(local_feet.z) > 4.0:
		player_marker.hide()
		return
	# Test the drawn tower, so gaps between supports and the clear side of
	# the platform never trigger a cue just because their bounding boxes overlap.
	for body_fraction: float in [.50, .28, .74]:
		var body_point := feet + Vector3.UP * height * body_fraction
		var eye := body_point + camera.global_basis.z * 8.
		if camera.projection != Camera3D.PROJECTION_ORTHOGONAL:
			eye = body_point.move_toward(camera.global_position, 8.)
		if _tower_blocks(body_point, eye):
			player_marker.global_position = feet + Vector3.UP * (height + .21)
			player_marker.show()
			return
	player_marker.hide()

func _tower_blocks(point: Vector3, eye: Vector3) -> bool:
	for i in occluders.size():
		var part := occluders[i]
		if not part.is_visible_in_tree(): continue
		var from := part.to_local(point)
		var to := part.to_local(eye)
		if part.get_aabb().intersects_segment(from, to) != null and not faces[i].intersect_segment(from, to).is_empty():
			return true
	if is_instance_valid(crew) and crew.is_visible_in_tree():
		var base := crew.global_position
		var nearest := Geometry3D.get_closest_points_between_segments(point, eye, base + Vector3.UP * .42, base + Vector3.UP * 1.20)
		return nearest[0].distance_squared_to(nearest[1]) < .23 * .23
	return false
