extends SceneTree
## Headless Godot 4 technical import test of an isolated synthetic GLB.
## This does not render game pixels or certify any production Havenline assets.

func _initialize() -> void:
    call_deferred("_check")

func _check() -> void:
    var model_path: String = "res://assets/smoke_test_LOD0.glb"
    var packed: PackedScene = load(model_path) as PackedScene
    if packed == null:
        push_error("GODOT_IMPORT_FAIL: synthetic GLB cannot load as PackedScene")
        quit(1)
        return
    var instance: Node = packed.instantiate()
    if instance == null:
        push_error("GODOT_IMPORT_FAIL: synthetic GLB cannot instantiate")
        quit(1)
        return
    root.add_child(instance)
    var meshes: Array = []
    _find_meshes(instance, meshes)
    if meshes.is_empty():
        push_error("GODOT_IMPORT_FAIL: imported mesh instances missing")
        quit(1)
        return
    var material_count: int = 0
    var normal_bound_count: int = 0
    for mesh_node in meshes:
        var node3d: MeshInstance3D = mesh_node as MeshInstance3D
        if node3d.mesh == null:
            continue
        for surface_index in range(node3d.mesh.get_surface_count()):
            var mat: Material = node3d.get_active_material(surface_index)
            if mat == null:
                continue
            material_count += 1
            if mat is BaseMaterial3D:
                var pbr: BaseMaterial3D = mat as BaseMaterial3D
                if pbr.normal_enabled and pbr.normal_texture != null:
                    normal_bound_count += 1
    if material_count == 0 or normal_bound_count == 0:
        push_error("GODOT_IMPORT_FAIL: GLB material/normal map binding missing")
        quit(1)
        return
    var report: Dictionary = {
        "state": "ISOLATED_HEADLESS_IMPORT_ONLY",
        "source": model_path,
        "engine_version": Engine.get_version_info().get("string", "unknown"),
        "mesh_instances": meshes.size(),
        "material_surfaces": material_count,
        "normal_mapped_surfaces": normal_bound_count,
        "rendered_in_game": false,
        "physical_android_tested": false,
        "owner_visual_approved": false
    }
    print("HAVENLINE_GODOT_IMPORT_PASS ", JSON.stringify(report))
    quit(0)

func _find_meshes(node: Node, collection: Array) -> void:
    if node is MeshInstance3D:
        collection.append(node)
    for child in node.get_children():
        _find_meshes(child, collection)
