extends RefCounted
## This helper is called only from the pre-existing, authenticated four-leaf construction.
## It decorates the visuals after the repaired donor guard passes; source donor resources stay immutable.
const PaintShader: Shader = preload("res://previews/clearance_gate/gate_18591_surface.gdshader")
const STYLE := {
    "board": [0, 0.42],
    "board_warm": [0, 0.73],
    "board_soft": [0, 0.57],
    "beam": [1, 0.70],
    "brace_back": [1, 0.58],
    "snow": [2, 0.50],
    "metal": [3, 0.50],
    "rope": [4, 0.70],
    "rope_dark": [4, 0.34],
}
static var _materials: Dictionary = {}

static func apply_to_leaf(art: MeshInstance3D) -> void:
    # The invoking base allows only two known ArrayMeshes with this nine-label census.
    var source := art.mesh as ArrayMesh
    assert(source != null and source.get_surface_count() == 39)
    for i in range(source.get_surface_count()):
        var label := source.surface_get_material(i).resource_name.to_lower()
        assert(STYLE.has(label))
        if not _materials.has(label):
            var mat := ShaderMaterial.new()
            mat.shader = PaintShader
            mat.resource_name = "gate_18591_" + label
            mat.set_shader_parameter("family", STYLE[label][0])
            mat.set_shader_parameter("tone", STYLE[label][1])
            _materials[label] = mat
        art.set_surface_override_material(i, _materials[label])
