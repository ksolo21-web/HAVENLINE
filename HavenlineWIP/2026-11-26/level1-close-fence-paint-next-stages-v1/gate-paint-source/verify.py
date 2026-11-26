"""Static guards only: no Godot or rendering."""
import json
import re
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
base = Path(sys.argv[1]).resolve()
script = root / "gate_18591_surface.gdshader"
source = script.read_text()
binding = (root / "gate_18591_paint.gd").read_text()
build = json.loads(subprocess.check_output([sys.executable, str(root/"apply.py"), str(base)]))
assert build == json.loads((root / "build-result.json").read_text())
def digest(p):
    return sha256(p.read_bytes()).hexdigest()
for name, value in build["generated_sha256"].items():
    assert digest(root/"generated"/name) == value
vertex = re.search(r"void vertex\(\) \{(.*?)\}", source, re.S)[1].strip()
assert vertex == "leaf_p = VERTEX;\n    leaf_n = NORMAL;"
assert not re.search(r"\b(?:ALPHA|DEPTH|POSITION|MODEL_MATRIX|LIGHT_COLOR)\s*=", source)
assert "min(ALBEDO * floor_fill, vec3(0.24))" in source
assert [float(n) for n in re.findall(r"floor_fill = ([0-9.]+);", source)] == [.38,.42,.29,.50,.35]
assert "art.set_surface_override_material(i, _materials[label])" in binding
assert not re.search(r"\b(?:transform|mesh|global_transform|material_override|visible)\s*=", binding)
contract = json.loads((base / "gate-config.json").read_text())
labels = set(re.findall(r'^    "([a-z_]+)": \[', binding, re.M))
for side in ("left","right"):
    surf = contract["leaves"][side]["ordered_surfaces"]
    assert len(surf) == 39
    assert sum(int(x["triangles"]) for x in surf) == 3226
    assert labels == {x["material"] for x in surf}
print(json.dumps({
  "ok": True, "test_type":"static only, no shader compile or rendered quality result",
  "mesh_vertices_unchanged": True, "source_surface_materials_unchanged": True,
  "no_position_or_lighting_transform_writes": True,
  "surface_override_census":{"labels":sorted(labels),"ordered_surfaces_per_leaf":39,"triangles_per_leaf":3226},
  "gate_shader_max_emission_linear_per_channel":0.24,
  "graft_only_adds_preload_and_paint_call": True,
  "runtime_checks_needed":["shader compile","actual material params/labels attached on all four leaves","gates and save regression","paid/swing/cold actual game camera","both orientations blind exact owner ref review"],
}, indent=2))
