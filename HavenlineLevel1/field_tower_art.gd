extends Node3D
const FRAME = preload("res://assets/field_world/eastern_watchtower.glb")
const LAUNCHER = preload("res://assets/field_world/tower_launcher.glb")
const BOLT = preload("res://assets/field_world/tower_bolt.glb")
var frame:Node3D
var swivel:=Node3D.new()
var bow:Node3D
var recoil:Tween
var raised:=1.0
var sightline_material := ShaderMaterial.new()
var upper_parts: Array[MeshInstance3D] = []
var cutaway_active := false
const UPPER_BOUNDS := AABB(Vector3(-.92,1.37,-.92),Vector3(1.84,1.93,1.98))

func _ready() -> void:
	frame=FRAME.instantiate()
	add_child(frame)
	for part_name in ["Gallery","Eaves","SlateRoof"]:
		upper_parts.append(frame.find_child(part_name,true,false) as MeshInstance3D)
	var paint := upper_parts.back().get_active_material(0) as StandardMaterial3D
	sightline_material.shader = preload("res://assets/field_world/tower_sightline.gdshader")
	sightline_material.set_shader_parameter("atlas",paint.albedo_texture)
	sightline_material.set_shader_parameter("roughness",paint.roughness)
	sightline_material.set_shader_parameter("emission_tint",paint.emission)
	swivel.name="DeckSwivel"
	swivel.position=Vector3(0,2.10,0)
	add_child(swivel)
	bow=LAUNCHER.instantiate()
	swivel.add_child(bow)
	set_build_progress(raised)

func set_build_progress(value:float) -> void:
	raised=clampf(value,0.,1.)
	if not frame:return
	var stages:=["Footings","Trestle","Gallery","Eaves","SlateRoof"]
	for i in stages.size():
		var part:=frame.find_child(stages[i],true,false) as Node3D
		if part:
			var t:=clampf(raised*stages.size()-i,0.,1.)
			part.visible=t>.001
			part.position.y=lerpf(-.28,0.,smoothstep(0.,1.,t))
	swivel.visible=raised>.88

func aim_at_world(at:Vector3) -> void:
	if not swivel.is_inside_tree() or at.distance_squared_to(swivel.global_position)<.01:return
	swivel.look_at(at,Vector3.UP,true)

func muzzle_global_position() -> Vector3:
	return bow.to_global(Vector3(0,.04,.65))

func projectile() -> Node3D:
	return BOLT.instantiate() as Node3D

func fire(at:Vector3) -> void:
	aim_at_world(at)
	if recoil:recoil.kill()
	bow.position.z=-.105
	recoil=create_tween()
	recoil.tween_property(bow,"position:z",0.0,.21).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)

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
