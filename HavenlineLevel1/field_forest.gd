extends RefCounted

# Full groves share renderer instances. A nearby pine temporarily uses the
# identical mesh as a harvest object so its trunk can take individual hits.
var world: Node3D
var records: Array[Dictionary] = []
var last_scan := Vector3.INF
var elapsed := 0.0

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
	advance(0.25)

func _show_pine(row: Dictionary, show: bool) -> void:
	if row.index < 0:
		row.source.visible = show
		return
	var batch: MultiMeshInstance3D = row.source
	var local := batch.global_transform.affine_inverse() * (row.transform as Transform3D)
	if not show:
		local.basis = local.basis.scaled(Vector3.ONE*.001)
		local.origin.y -= 12.0
	batch.multimesh.set_instance_transform(row.index,local)

func advance(dt: float) -> void:
	if not world: return
	elapsed += dt
	if elapsed < .16: return
	elapsed = 0.0
	var here: Vector3 = world.actor.global_position
	if here.distance_squared_to(last_scan)<.04: return
	last_scan = here
	for row in records:
		var at: Transform3D = row.transform
		var distance := at.origin.distance_squared_to(here)
		if distance < 18.5 and not is_instance_valid(row.live):
			var tree = world._add_pine(Vector2(at.origin.x,at.origin.z),row.variant)
			tree.global_transform = Transform3D(at.basis.scaled(Vector3.ONE/tree.TREE_SCALE),at.origin)
			world.field_env.tint_canopy(tree)
			row.live = tree
			_show_pine(row,false)
		elif distance > 40.0 and is_instance_valid(row.live):
			var tree = row.live
			if tree.phase == "rooted" and tree.strikes == 0:
				world.retire_tree(tree,false)
				row.live = null
				_show_pine(row,true)
