extends Node3D
const FRAME = preload("res://assets/field_world/eastern_watchtower.glb")
const LAUNCHER = preload("res://assets/field_world/tower_launcher.glb")
const BOLT = preload("res://assets/field_world/tower_bolt.glb")
var frame:Node3D
var swivel:=Node3D.new()
var bow:Node3D
var recoil:Tween
var raised:=1.0
func _ready() -> void:
	frame=FRAME.instantiate()
	add_child(frame)
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
