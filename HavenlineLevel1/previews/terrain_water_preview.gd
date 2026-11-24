extends Node3D
## Explicit opt-in presentation only. No clock, body, cast, save, or actor.
const TerrainSource = preload("res://terrain_source.gd")
const AcceptedWaterShader = preload("res://materials/accepted_t02_river_water.gdshader")
@onready var accepted_ground: Node3D = $AcceptedGround
@onready var water: MeshInstance3D = $MapSpanningRiver
var water_bound := false

func _ready() -> void:
	if accepted_ground.get("bound") != true:
		push_error("Accepted ground fixture not bound")
		return
	var geometry := TerrainSource.water_mesh()
	if geometry == null or geometry.get_surface_count() != 1:
		push_error("Missing or ambiguous accepted water mesh")
		return
	var material := ShaderMaterial.new()
	material.shader = AcceptedWaterShader
	# Fixed authored phase. The legacy simulation clock is deliberately not wired.
	material.set_shader_parameter("sim_time", 0.0)
	water.mesh = geometry
	water.material_override = material
	water_bound = true
