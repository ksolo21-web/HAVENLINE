extends Node3D
## Explicitly opt-in contact assembly. No character, water, camp, legacy or save runtime.
const TerrainSource = preload("res://terrain_source.gd")
const NeutralSnow = preload("res://materials/neutral_shore_snow.tres")
## Local preview ray bit, not an authorization to add actor contacts.
const GROUND_LAYER := 1 << 11
@onready var visual: MeshInstance3D = $GroundVisual
@onready var body: StaticBody3D = $GroundBody
@onready var ground: CollisionShape3D = $GroundBody/GroundTriangles
var bound := false

func _ready() -> void:
	var geometry := TerrainSource.terrain_mesh()
	if geometry == null or geometry.get_surface_count() != 1:
		push_error("Missing or ambiguous accepted terrain source")
		return
	# Godot expands the indexed render triangles directly; no plane, heightmap,
	# hull, second sampler, displacement or independently authored collider.
	var triangles := geometry.create_trimesh_shape()
	if triangles == null or triangles.get_faces().is_empty():
		push_error("Failed to create collider from accepted terrain triangles")
		return
	triangles.backface_collision = false
	visual.mesh = geometry
	visual.material_override = NeutralSnow
	ground.shape = triangles
	bound = true
