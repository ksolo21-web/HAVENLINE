extends SceneTree

var failures := 0

func _initialize() -> void:
	call_deferred("_run")

func check(ok: bool, message: String) -> void:
	if not ok:
		failures += 1
		push_error(message)

func collect(node: Node, out: Array[MeshInstance3D]) -> void:
	check(not node is CollisionObject3D and not node is CollisionShape3D, "pickup visual unexpectedly adds collision")
	if node is MeshInstance3D:
		out.append(node as MeshInstance3D)
	for child in node.get_children():
		collect(child, out)

func _run() -> void:
	var game = load("res://opening.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	check(game.wood_visuals.size() == 2 and game.wood_visuals.has("wood-b") and game.wood_visuals.has("wood-c"), "starter IDs changed")
	for row in game.layout.wood_nodes:
		if row.id == "wood-a":
			continue
		var marker: Node3D = game.wood_visuals[row.id]
		check(marker.visible and marker.position.is_equal_approx(game.point(row.xz)), "pickup position or uncollected visibility changed")
		var found: Array[MeshInstance3D] = []
		collect(marker, found)
		check(found.size() == 6, "expected all six derivative components")
		for m in found:
			var local_bounds: AABB = (marker.global_transform.affine_inverse() * m.global_transform) * m.get_aabb()
			check(local_bounds.position.y >= .001 and local_bounds.end.y <= .26, "ground sizing changed")
			check(local_bounds.position.x >= -.3001 and local_bounds.end.x <= .3001 and local_bounds.position.z >= -.1251 and local_bounds.end.z <= .1251, "source footprint exceeded")
	check(game._collect_wood_source("wood-b"), "could not collect existing source")
	check(not game.wood_visuals["wood-b"].visible and game.wood_visuals["wood-c"].visible, "collected visibility is no longer typed by source")
	check(int(game.ledger.stock.wood) == 1 and not game._collect_wood_source("wood-b"), "count or duplicate handling changed")
	check(game._collect_wood_source("wood-c"), "second existing source did not collect")
	check(not game.wood_visuals["wood-c"].visible and int(game.ledger.stock.wood) == 2, "second accepted source visibility changed")
	print("Starter ground wood fixture failures: ", failures)
	quit(1 if failures else 0)
