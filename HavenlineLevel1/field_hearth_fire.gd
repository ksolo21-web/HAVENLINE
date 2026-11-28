extends Node3D
## Fire and draft fitted to the two real openings in the recovered stone shell.

const FLAME := preload("res://assets/field_camp/hearth_flame.gdshader")
const FLAME_CANVAS := preload("res://assets/field_finishes/combustion_canvas.tres")
const BED := preload("res://assets/field_camp/hearth_coals.gdshader")
const DRAFT := preload("res://assets/field_camp/hearth_draft.gdshader")

var fired := false
var chamber_light: OmniLight3D
var recovery_pulse := 0.0
var burn_time := 0.0

func install(shell: Node3D, light: OmniLight3D) -> void:
	name = "HearthCombustion"
	shell.add_child(self)
	chamber_light = light
	# These coordinates are local to the recovered GLB, before it is fitted to camp.
	var bed := _effect("CoalsUnderFlue",BED,Vector2(.59,.61),Vector3(-.038,.605,-.021))
	bed.rotation.x = -PI*.5
	_effect("ArchedFirebox",FLAME,Vector2(.54,.71),Vector3(.034,-.28,.51))
	var vent := _effect("FlueFlame",FLAME,Vector2(.44,.42),Vector3(-.035,.732,-.035))
	(vent.material_override as ShaderMaterial).set_shader_parameter("phase",2.4)
	_effect("ChimneyDraft",DRAFT,Vector2(1.10,1.22),Vector3(.020,1.17,-.028))
	set_fired(false)

func _effect(part_name: String, shader: Shader, size: Vector2, at: Vector3) -> MeshInstance3D:
	var ink := ShaderMaterial.new()
	ink.shader = shader
	var part := MeshInstance3D.new()
	part.name = part_name
	part.mesh = FLAME_CANVAS
	part.scale = Vector3(size.x,size.y,1.0)
	part.position = at
	part.material_override = ink
	part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	part.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	add_child(part)
	return part

func set_fired(on: bool) -> void:
	fired = on
	visible = on
	set_physics_process(on)
	chamber_light.visible = on
	if not on:
		recovery_pulse = 0.0
		burn_time = 0.0

func restore_warmth() -> void:
	if fired:
		recovery_pulse = 1.0

func _physics_process(delta: float) -> void:
	burn_time = fmod(burn_time + delta, TAU*100.0)
	recovery_pulse = move_toward(recovery_pulse,0.0,delta*2.6)
	# Coal/wood flames breathe instead of continuously strobing the whole court.
	var flicker := .055*sin(burn_time*6.7) + .027*sin(burn_time*13.2+1.7)
	chamber_light.light_energy = .84 + flicker + .14*recovery_pulse
