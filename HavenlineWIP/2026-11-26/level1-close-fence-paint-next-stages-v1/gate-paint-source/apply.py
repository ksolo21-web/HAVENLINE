"""Create a preview-only shader bridge under this package's output directory.

No write to a live or baseline checkout. baseline argument is the exact staged
import-v2 capsule root; output is always the adjacent generated/ directory.
"""
from pathlib import Path
from hashlib import sha256
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
DONORS = {
    "GateLeaf.obj": "cb175b54faef4d554b9ee0b7c9572da7f9ad356521132b33bf63ecba31303edd",
    "GateLeaf_Right.obj": "fb3dd965af23b7e3cc9dd81f3d89c29964ea415bac42fe4691f5b702a00e3f20",
    "GateLeaf.mtl": "93084c44ec4d2060898fafb46559733492eb879b3b90294e3f7949336ea43372",
}
BASE_SCRIPT = "5feb9e339a09990a8b54f193991ebd3670c91bb210a692121943ee136413deb0"

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

base = Path(sys.argv[1]).resolve()
orig = base / "clearance_gate_view.gd"
assert digest(orig) == BASE_SCRIPT
prefixes = tuple(base.glob("staged/**/previews/clearance_gate/assets/GateLeaf.obj"))
assert len(prefixes) == 1
assets = prefixes[0].parent
assert all(digest(assets / n) == h for n,h in DONORS.items())
config = json.loads((base / "gate-config.json").read_text())
assert len(config["leaves"]["left"]["ordered_surfaces"]) == 39
assert len(config["leaves"]["right"]["ordered_surfaces"]) == 39

file = orig.read_text()
constants = 'const GateArt = preload("res://previews/clearance_gate/gate_18591_paint.gd")\n'
sentinel = "const EXACT_TRIANGLES :="
assert file.count(sentinel) == 1
candidate = file.replace(sentinel, constants + sentinel)
needle = "\t\tart.mesh = row.visual\n\t\trow.pivot.add_child(art)\n"
add = "\t\tGateArt.apply_to_leaf(art)\n"
assert candidate.count(needle) == 1
candidate = candidate.replace(needle, "\t\tart.mesh = row.visual\n" + add + "\t\trow.pivot.add_child(art)\n")
assert candidate.replace(constants, "", 1).replace(add, "", 1) == file

out = ROOT / "generated"
out.mkdir(exist_ok=True)
(out / "clearance_gate_view.gd").write_text(candidate)
for name in ("gate_18591_surface.gdshader", "gate_18591_paint.gd"):
    shutil.copyfile(ROOT / name, out / name)
names = sorted(p.name for p in out.iterdir() if p.is_file())
print(json.dumps({
  "scope": "generated overlay files only; no stage or render",
  "source_gate_script_sha256": digest(orig),
  "source_authored_donors_unchanged": DONORS,
  "same_protected_guard_script_after_removing_two_added_lines": True,
  "art_mount_node_unchanged": True,
  "surface_override_only": True,
  "generated_sha256": { n:digest(out / n) for n in names },
}, indent=2))
