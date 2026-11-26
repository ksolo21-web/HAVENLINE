extends Node3D
## World One's outer snowfield. Storage and combat use the same source at every visit.

const CHUNK_METRES := 32
const OPENING_RADIUS := 20.5
const WORLD_SEED := 860342
const INTERACT_DISTANCE := 5.0
const RELEASE_DISTANCE := 8.0
const PINE_SCALE := 0.69
const QUARRY_SCALE := 0.68

var host
var chunks: Dictionary = {}
var templates: Array = []
var district := FastNoiseLite.new()
var center_chunk := Vector2i(99999, 99999)
var limit: int
var next_scan := 0.0

func install(world: Node3D) -> void:
	host = world
	name = "WorldOneLandscape"
	process_physics_priority = 12
	limit = ceili(float(host.layout.snow_extent_half) / CHUNK_METRES)
	district.seed = WORLD_SEED
	district.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	district.frequency = 0.027
	for pine: PackedScene in host.CONIFERS:
		templates.append(_template(pine, false))
	templates.append(_template(host.SNOW_STONE, true))
	_build_outer_drifts(float(host.layout.snow_extent_half))
	_update_neighborhood()

# The foot of the snow ridge marks the playable limit. Its outer skirt fills the
# gameplay camera beyond the last walkable cell, including at the four corners.
func _build_outer_drifts(extent: float) -> void:
	var corners := [Vector2(-1,-1), Vector2(1,-1), Vector2(1,1), Vector2(-1,1)]
	var offsets := PackedFloat32Array([-4.0, .1, 1.8, 4.5, 8.7, 14.0, 34.0, 76.0])
	var heights := PackedFloat32Array([-.12, -.015, .22, 1.35, 4.8, 3.3, .8, -.14])
	var vertices := PackedVector3Array()
	var indices := PackedInt32Array()
	var subdivisions := 256
	for side in 4:
		for column in subdivisions:
			var ray: Vector2 = corners[side].lerp(corners[(side+1)%4], float(column)/subdivisions)
			var base := ray * extent
			var wave := district.get_noise_2d(base.x*.70, base.y*.70)
			var local_drift := district.get_noise_2d(base.x*3.4+731.,base.y*3.4-553.)
			var ridge_depth := 1.0 + wave*.55 + local_drift*.34
			for band in offsets.size():
				var xz := ray * (extent + offsets[band] * ridge_depth)
				var height := heights[band] * (1.0 + wave*.78 + local_drift*.55)
				vertices.append(Vector3(xz.x,height,xz.y))
	var bands := offsets.size()
	for column in subdivisions*4:
		var next := (column+1) % (subdivisions*4)
		for band in bands-1:
			var a := column*bands + band
			var b := next*bands + band
			indices.append_array(PackedInt32Array([a,b+1,b,a,a+1,b+1]))
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	tool.set_smooth_group(0)
	for pos in vertices:
		tool.add_vertex(pos)
	for index in indices:
		tool.add_index(index)
	tool.generate_normals()
	var drifts := MeshInstance3D.new()
	drifts.name = "BoundarySnowDrifts"
	drifts.mesh = tool.commit()
	drifts.material_override = host.field_env.snow
	drifts.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(drifts)

func _template(scene: PackedScene, stone: bool) -> Array:
	var source := scene.instantiate() as Node3D
	var meshes: Array[MeshInstance3D] = []
	host.meshes(source, meshes)
	var parts: Array = []
	for part in meshes:
		var transform_from_root := part.transform
		var ancestor := part.get_parent()
		while ancestor != null and ancestor != source and ancestor is Node3D:
			transform_from_root = ancestor.transform * transform_from_root
			ancestor = ancestor.get_parent()
		if stone:
			transform_from_root.origin.y = -part.mesh.get_aabb().position.y
		var mesh: Mesh = part.mesh.duplicate()
		for i in mesh.get_surface_count():
			var material := part.get_active_material(i)
			if not stone:
				material = host.field_env.canopy_ink(material)
			mesh.surface_set_material(i, material)
		var scale_factor := QUARRY_SCALE if stone else PINE_SCALE
		parts.append({"mesh": mesh, "local": Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * scale_factor), Vector3.ZERO) * transform_from_root})
	source.free()
	return parts

func _physics_process(dt: float) -> void:
	if host == null: return
	next_scan -= dt
	if next_scan <= 0.0:
		next_scan = 0.15
		_update_neighborhood()

func chunk_for(pos: Vector3) -> Vector2i:
	return Vector2i(floori(pos.x / CHUNK_METRES), floori(pos.z / CHUNK_METRES))

func _update_neighborhood() -> void:
	var here: Vector3 = host.actor.global_position
	var center := chunk_for(here)
	if center != center_chunk:
		center_chunk = center
		for key: Vector2i in chunks.keys():
			if absi(key.x-center.x) > 1 or absi(key.y-center.y) > 1:
				_unload_chunk(key)
		for z in range(maxi(-limit, center.y-1), mini(limit, center.y+2)):
			for x in range(maxi(-limit, center.x-1), mini(limit, center.x+2)):
				var key := Vector2i(x, z)
				if not chunks.has(key):
					_load_chunk(key)
	for chunk: Dictionary in chunks.values():
		for row: Dictionary in chunk.sources:
			var distance := here.distance_squared_to(row.position)
			if distance <= INTERACT_DISTANCE * INTERACT_DISTANCE and not is_instance_valid(row.live):
				row.live = host.add_resource_source(row.id, row.kind, Vector2(row.position.x, row.position.z), mini(2, row.variant))
				if is_instance_valid(row.live):
					row.live.rotation.y = row.yaw
					row.live.scale = Vector3.ONE * float(row.scale)
					if row.kind == "wood": host.field_env.tint_canopy(row.live)
			elif distance > RELEASE_DISTANCE * RELEASE_DISTANCE and is_instance_valid(row.live):
				host.unload_resource_source(row.id)
				row.live = null
			var show_proxy: bool = not is_instance_valid(row.live) and host.is_source_available(row.id)
			if show_proxy != row.proxy_visible:
				_set_proxy(chunk, row, show_proxy)

func _unload_chunk(key: Vector2i) -> void:
	var chunk: Dictionary = chunks[key]
	for row: Dictionary in chunk.sources:
		if is_instance_valid(row.live):
			host.unload_resource_source(row.id)
	chunk.node.queue_free()
	chunks.erase(key)

func _load_chunk(key: Vector2i) -> void:
	var root := Node3D.new()
	root.name = "Snow_%d_%d" % [key.x, key.y]
	root.position = Vector3(key.x*CHUNK_METRES, 0, key.y*CHUNK_METRES)
	add_child(root)
	var rows := describe_chunk(key)
	var chunk := {"node":root, "sources":rows, "batches":[[], [], [], []]}
	for variant in templates.size():
		var count := 0
		for row in rows:
			if row.variant == variant:
				row.index = count
				count += 1
		if count == 0: continue
		for part: Dictionary in templates[variant]:
			var batch := MultiMesh.new()
			batch.transform_format = MultiMesh.TRANSFORM_3D
			batch.mesh = part.mesh
			batch.instance_count = count
			var visual := MultiMeshInstance3D.new()
			visual.multimesh = batch
			root.add_child(visual)
			chunk.batches[variant].append({"mesh":batch, "local":part.local})
	for row in rows:
		_set_proxy(chunk, row, true)
	chunks[key] = chunk

func _set_proxy(chunk: Dictionary, row: Dictionary, shown: bool) -> void:
	var basis := Basis(Vector3.UP, row.yaw).scaled(Vector3.ONE * float(row.scale))
	var local: Vector3 = row.position - chunk.node.position
	if not shown:
		local.y = -10.0
		basis = basis.scaled(Vector3.ONE * 0.001)
	var pose := Transform3D(basis, local)
	for part: Dictionary in chunk.batches[row.variant]:
		part.mesh.set_instance_transform(row.index, pose * part.local)
	row.proxy_visible = shown

func _outside_opening(at: Vector2) -> bool:
	return maxf(absf(at.x), absf(at.y)) > OPENING_RADIUS

func describe_chunk(key: Vector2i) -> Array[Dictionary]:
	var rng := RandomNumberGenerator.new()
	# String hashing is stable across fresh processes and negative cell coordinates.
	rng.seed = ("%s/%s/%s" % [WORLD_SEED, key.x, key.y]).sha256_text().left(15).hex_to_int()
	var origin := Vector2(key) * CHUNK_METRES
	var rows: Array[Dictionary] = []
	var rocks: Array[Vector2] = []
	var geology := district.get_noise_2d(origin.x-199.0, origin.y+427.0)
	var deposits := 4 if geology > 0.1 else 2
	for i in deposits:
		var at := origin + Vector2(rng.randf_range(4.0, 28.0), rng.randf_range(4.0, 28.0))
		if not _outside_opening(at) or rocks.any(func(p: Vector2): return p.distance_squared_to(at)<11): continue
		rocks.append(at)
		rows.append(_source(key, "stone", i, at, 3, rng))
	for z in 8:
		for x in 8:
			var at := origin + Vector2(x*4+rng.randf_range(.4, 3.6), z*4+rng.randf_range(.4, 3.6))
			var canopy := district.get_noise_2d(at.x, at.y)
			var density := lerpf(.10, .94, smoothstep(-.37, .37, canopy))
			if rng.randf() > density or not _outside_opening(at): continue
			if rocks.any(func(p: Vector2): return p.distance_squared_to(at)<9.0): continue
			rows.append(_source(key, "wood", z*8+x, at, rng.randi_range(0, 2), rng))
	return rows

func _source(key: Vector2i, kind: String, i: int, at: Vector2, variant: int, rng: RandomNumberGenerator) -> Dictionary:
	return {"id":"world1/%d/%d/%s/%d" % [key.x,key.y,kind,i], "kind":kind,
		"variant":variant, "position":Vector3(at.x,0,at.y), "yaw":rng.randf_range(-PI, PI),
		"scale":rng.randf_range(.86,1.16), "index":-1, "live":null, "proxy_visible":false}
