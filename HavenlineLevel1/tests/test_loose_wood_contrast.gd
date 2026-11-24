extends SceneTree
const Piece = preload("res://starter_ground_wood_view.gd")
const Paint = preload("res://previews/loose_wood_contrast.gd")
var fails := 0
var checks := 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		fails += 1
	print(("PASS " if ok else "FAIL ") + message)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var piece := Piece.new()
	var untouched := Piece.new()
	var adverse := Piece.new()
	root.add_child(piece)
	root.add_child(untouched)
	root.add_child(adverse)
	var peers := untouched.find_children("*", "MeshInstance3D", true, false)
	var meshes := piece.find_children("*", "MeshInstance3D", true, false)
	var bad_meshes := adverse.find_children("*", "MeshInstance3D", true, false)
	var before: Array[Dictionary] = []
	for i: int in range(meshes.size()):
		var node := meshes[i] as MeshInstance3D
		for j: int in range(node.mesh.get_surface_count()):
			var material := node.mesh.surface_get_material(j) as StandardMaterial3D
			before.append({"instance":node,"source":material,"index":j,"peer":peers[i],"flag":material.vertex_color_use_as_albedo,
				"color":material.albedo_color,"roughness":material.roughness,"box":node.get_aabb(),"xform":node.transform})
	check(before.size() == 9 and meshes.size() == 6, "exact nine surface paint inventory")
	var foreign := StandardMaterial3D.new()
	(bad_meshes[bad_meshes.size()-1] as MeshInstance3D).set_surface_override_material(0, foreign)
	check(not Paint.apply(adverse), "alien pre-existing override is rejected atomically")
	var adverse_count := 0
	for item in bad_meshes:
		var node := item as MeshInstance3D
		for j: int in range(node.mesh.get_surface_count()):
			if node.get_surface_override_material(j) != null:
				adverse_count += 1
	check(adverse_count == 1, "no partial recolor after late-surface failure")
	check(Paint.apply(piece), "exact local presentation correction accepted")
	var targets := 0
	var changed := 0
	var intact := true
	for row in before:
		var node: MeshInstance3D = row.instance
		var source: StandardMaterial3D = row.source
		var resulting := node.get_active_material(row.index) as StandardMaterial3D
		var peer: MeshInstance3D = row.peer
		if source.resource_name in Paint.REPAIRED:
			targets += 1
			if not row.flag:
				intact = intact and resulting != source
				changed += 1
		else:
			intact = intact and resulting == source
		intact = intact and resulting.vertex_color_use_as_albedo and source.vertex_color_use_as_albedo == row.flag
		intact = intact and resulting.albedo_color == row.color and resulting.roughness == row.roughness
		intact = intact and node.get_aabb() == row.box and node.transform == row.xform
		intact = intact and peer.get_surface_override_material(row.index) == null and peer.mesh.surface_get_material(row.index) == source
	check(targets == 6 and intact, "only missing local vertex flags restored; end grain sibling geometry optics unchanged")
	print("LOOSE_WOOD_CONTRAST checks=", checks, " failed=", fails, " locally_changed_surfaces=", changed)
	for node in meshes:
		for i in range(node.mesh.get_surface_count()):
			node.set_surface_override_material(i, null)
	piece.free()
	untouched.free()
	adverse.free()
	quit(0 if fails == 0 else 1)
