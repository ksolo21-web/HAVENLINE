extends RefCounted

# Full groves share renderer instances. A nearby pine temporarily uses the
# identical mesh as a harvest object so its trunk can take individual hits.
# The tallest near-field crown can project 3.73 m from its roots. Include the
# cutaway rim and one 0.16 s scan interval at full running speed.
const LIVE_RADIUS := 5.0
var world: Node3D
var records: Array[Dictionary] = []
var last_scan := Vector3.INF
var last_worker_scan := Vector3.INF
var elapsed := 0.0
var last_availability := -1
var worker_probe_offset := 0

func install(host: Node3D) -> void:
	world = host
	var placements: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://conifers.json"))
	var singles := world.get_node("ExteriorExactT01Visuals")
	for row in placements.instances:
		var visual := singles.get_node(String(row.id)) as Node3D
		records.append({"source":visual,"index":-1,"variant":int(row.variant)-1,"transform":visual.global_transform,"live":null})
	var groves := world.get_node("PeripheralSnowForest")
	for batch: MultiMeshInstance3D in groves.find_children("*","MultiMeshInstance3D",true,false):
		var variant := int(batch.get_meta("tree_variant",-1))
		var placements_cpu: Array = batch.get_meta("tree_placements",[])
		if variant < 0 or placements_cpu.size() != batch.multimesh.instance_count:
			push_error("Forest batch is missing authored transforms for simulation.")
			continue
		for i in placements_cpu.size():
			var at: Transform3D = batch.global_transform * placements_cpu[i]
			records.append({"source":batch,"index":i,"variant":variant,"transform":at,"live":null})
	for row in records:
		var p:Vector3=row.transform.origin
		row["id"]="grove@%d,%d" % [roundi(p.x*1000),roundi(p.z*1000)]
		row["proxy_visible"]=true
	refresh_camp(false)
	advance(0.25)

func _show_pine(row: Dictionary, show: bool) -> void:
	row.proxy_visible=show
	if row.index < 0:
		row.source.visible = show
		return
	var batch: MultiMeshInstance3D = row.source
	var local := batch.global_transform.affine_inverse() * (row.transform as Transform3D)
	if not show:
		local.basis = local.basis.scaled(Vector3.ONE*.001)
		local.origin.y -= 12.0
	batch.multimesh.set_instance_transform(row.index,local)

func refresh_camp(_animate: bool) -> void:
	for row in records:
		var size: Vector2 = world.field_env.pine_shapes[row.variant]
		var at: Transform3D = row.transform
		var radius := (size.x+.18*size.y)*at.basis.get_scale().abs().x
		var occupied: bool = world.field_env.occupies_camp_ground(at.origin,radius)
		if (world.lakeshore and world.lakeshore.reserves(row.transform.origin)) or (world.processors and world.processors.reserves(row.transform.origin)):
			occupied = true
		if occupied == row.get("occupied",false): continue
		row["occupied"] = occupied
		if occupied and is_instance_valid(row.live):
			row.live.hide()
			world.retire_tree(row.live,false)
			row.live = null
		_show_pine(row,not occupied)
	last_scan = Vector3.INF

func _open_pine(row: Dictionary) -> void:
	var at: Transform3D = row.transform
	var tree = world.add_resource_source(row.id,"wood",Vector2(at.origin.x,at.origin.z),row.variant)
	tree.global_transform = Transform3D(at.basis.scaled(Vector3.ONE/tree.TREE_SCALE),at.origin)
	world.field_env.tint_canopy(tree)
	row.live = tree
	_show_pine(row,false)

func offer_worker_trees(origin: Vector3) -> bool:
	# When the live set has no reachable job, offer the nearest standing
	# batched pines. Only the selected worksite stays live at a distance.
	var candidates: Array[Dictionary] = []
	for row in records:
		if row.get("occupied",false) or is_instance_valid(row.live) or not world.is_source_available(row.id): continue
		candidates.append(row)
	if candidates.is_empty(): return false
	candidates.sort_custom(func(a,b): return origin.distance_squared_to(a.transform.origin)<origin.distance_squared_to(b.transform.origin))
	var count := mini(4,candidates.size())
	for i in count: _open_pine(candidates[posmod(worker_probe_offset+i,candidates.size())])
	worker_probe_offset = posmod(worker_probe_offset+count,candidates.size())
	last_scan = Vector3.INF
	return true

func advance(dt: float) -> void:
	if not world: return
	elapsed += dt
	if elapsed < .16: return
	elapsed = 0.0
	var here: Vector3 = world.actor.global_position
	var worker: Vector3 = world.survivor.resource_observer() if is_instance_valid(world.survivor) else Vector3.INF
	var worksite: Node3D = world.survivor.active_worksite() if is_instance_valid(world.survivor) else null
	var worker_unchanged := worker == last_worker_scan or worker.distance_squared_to(last_worker_scan)<.04
	if here.distance_squared_to(last_scan)<.04 and worker_unchanged and last_availability==world.lifecycle.availability_revision: return
	last_availability=world.lifecycle.availability_revision
	last_scan = here
	last_worker_scan = worker
	for row in records:
		if row.get("occupied",false): continue
		var at: Transform3D = row.transform
		var distance := minf(at.origin.distance_squared_to(here),at.origin.distance_squared_to(worker))
		if distance < LIVE_RADIUS * LIVE_RADIUS and not is_instance_valid(row.live):
			_open_pine(row)
		elif distance > 40.0 and is_instance_valid(row.live) and row.live != worksite:
			world.unload_resource_source(row.id)
			row.live = null
		var show_proxy:bool=not is_instance_valid(row.live) and world.is_source_available(row.id)
		if show_proxy!=row.proxy_visible: _show_pine(row,show_proxy)
