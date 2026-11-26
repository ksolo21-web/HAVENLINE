extends RefCounted

# Full groves share renderer instances. A nearby pine temporarily uses the
# identical mesh as a harvest object so its trunk can take individual hits.
var world: Node3D
var records: Array[Dictionary] = []
var last_scan := Vector3.INF
var elapsed := 0.0
var last_availability := -1

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

func refresh_camp(animate: bool) -> void:
	for row in records:
		var occupied: bool = world.field_env.occupies_camp_ground(row.transform.origin)
		if (world.lakeshore and world.lakeshore.reserves(row.transform.origin)) or (world.processors and world.processors.reserves(row.transform.origin)):
			occupied = true
		if occupied == row.get("occupied",false): continue
		row["occupied"] = occupied
		if occupied and is_instance_valid(row.live):
			world.retire_tree(row.live,animate)
			row.live = null
		_show_pine(row,not occupied)
	last_scan = Vector3.INF

func advance(dt: float) -> void:
	if not world: return
	elapsed += dt
	if elapsed < .16: return
	elapsed = 0.0
	var here: Vector3 = world.actor.global_position
	if here.distance_squared_to(last_scan)<.04 and last_availability==world.lifecycle.availability_revision: return
	last_availability=world.lifecycle.availability_revision
	last_scan = here
	for row in records:
		if row.get("occupied",false): continue
		var at: Transform3D = row.transform
		var distance := at.origin.distance_squared_to(here)
		if distance < 18.5 and not is_instance_valid(row.live):
			var tree = world.add_resource_source(row.id,"wood",Vector2(at.origin.x,at.origin.z),row.variant)
			tree.global_transform = Transform3D(at.basis.scaled(Vector3.ONE/tree.TREE_SCALE),at.origin)
			world.field_env.tint_canopy(tree)
			row.live = tree
			_show_pine(row,false)
		elif distance > 40.0 and is_instance_valid(row.live):
			world.unload_resource_source(row.id)
			row.live = null
		var show_proxy:bool=not is_instance_valid(row.live) and world.is_source_available(row.id)
		if show_proxy!=row.proxy_visible: _show_pine(row,show_proxy)
