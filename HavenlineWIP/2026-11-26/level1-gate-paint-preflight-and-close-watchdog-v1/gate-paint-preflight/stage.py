#!/usr/bin/env python3
"""Materialize the sealed, disposable source stage, without invoking Godot."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
base, art = [Path(p).resolve() for p in sys.argv[1:]]
def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def require_pin(path, expected):
    assert digest(path) == expected, path

pins = (
    (base, "d6662929e793265b0bb0b7b147be2ce23cd5e5ef54643bc68ee5951b33e3d580"),
    (art, "9d03b3a5c7d11c878753e5b8befd1e9054364fb6b68343dd907489124102b3f5"),
)
for capsule, manifest in pins:
    require_pin(capsule / "SHA256SUMS", manifest)
    subprocess.run(["sha256sum", "-c", "--status", "SHA256SUMS"], cwd=capsule, check=True)

before = base / "staged/HavenlineLevel1"
subprocess.run(["sha256sum","-c","--status","../draw-source.sha256"],cwd=before,check=True)

normal = base / "graphics-evidence.h9CRsvfC"
keys = {
    "frame-evidence.json":"64281436cebe6c4e879ba461ce991a2c94c435d1f9cfe0145338499e6b1714b2",
    "gate-evidence.json":"9c101990040a7c2559f6cb9247c7e9d39ba91007bda535c709c224c14a46666e",
    "functional.json":"7ed4e4b3aa2157b85fc71799be5a7698d31c5b89cd7de41ef1a9272cb15c2290",
    "r17-evidence.json":"c00cc985896e2e54f7cf5b1a68e0c1fc278c0a4fa107df35d5a8f9de8750b2f5",
}
for name, expected in keys.items():
    require_pin(normal/name, expected)
    shutil.copyfile(normal/name, root/("control-"+name))

old_draw = (base / "clearance_draw.gd").read_text()
assert (before / "tests/hvn_l1_combined_draw.gd").read_text() == old_draw
initial = 'const WRITER :='
anchor_a = '\tprint("R17_NATIVE_DRAW_EVIDENCE ", JSON.stringify(evidence))'
anchor_b = '\tswing_ok += 1'
anchor_c = '\treturn {"source":donor_path,"material_triangles":by_material,"surface_count":observed.size(),"ordered_surfaces":observed,'
assert all(old_draw.count(x) == 1 for x in (initial,anchor_a,anchor_b,anchor_c))
additional_consts = (root/"observer_constants.inc").read_text()
primary_log = '\tprint("GATE_18591_PAINT_FRAME ", JSON.stringify({"label":phase,"paint":_paint_census(evidence)}))\n'
# The inherited swing guard has already validated angle, timing and original gate/light evidence.
# Re-read on the same callback, with no yield or time advance, and bind the paint witness to that label.
swing_log = '''\tvar paint_evidence := gate_and_light(label)
\tif paint_evidence.is_empty():
\t\tdraw_failures += 1
\t\tprint("DRAW_REJECT gate-18591-paint-swing-custody ", label)
\t\treturn
\tprint("GATE_18591_PAINT_FRAME ", JSON.stringify({"label":label,"paint":_paint_census(paint_evidence)}))
'''
leaf_probe = '''\tvar paint := _effective_gate_paint(art, observed)
\tif paint.size() != 39:
\t\treturn {}
'''
new = (old_draw.replace(initial, additional_consts+initial)
    .replace(anchor_a, primary_log+anchor_a)
    .replace(anchor_b, swing_log+anchor_b)
    .replace(anchor_c, leaf_probe+anchor_c.replace('{"source"', '{"paint_overrides":paint,"source"')))
extra = "\n"+(root/"observer_helpers.inc").read_text()
new += extra
recovered = new.removesuffix(extra).replace(additional_consts,"",1).replace(primary_log,"",1).replace(swing_log,"",1).replace(leaf_probe,"",1).replace('{"paint_overrides":paint,"source"','{"source"',1)
assert recovered == old_draw
dest = root / "staged/HavenlineLevel1"
assert not dest.parent.exists()
shutil.copytree(before,dest)
for name in ("gate_18591_paint.gd","gate_18591_surface.gdshader","clearance_gate_view.gd"):
    shutil.copyfile(art/"generated"/name,dest/"previews/clearance_gate"/name)
(dest/"tests/hvn_l1_combined_draw.gd").write_text(new)
def tree(folder):
    return {p.relative_to(folder).as_posix():digest(p) for p in folder.rglob("*") if p.is_file()}
original, final = tree(before), tree(dest)
assert len(original)==144
assert original.keys() <= final.keys()
changed=sorted(k for k in original if final[k]!=original[k])
added=sorted(final.keys()-original.keys())
assert changed==["previews/clearance_gate/clearance_gate_view.gd","tests/hvn_l1_combined_draw.gd"]
assert added==["previews/clearance_gate/gate_18591_paint.gd","previews/clearance_gate/gate_18591_surface.gdshader"]
(dest.parent/"draw-source.sha256").write_text("".join(f"{h}  ./{n}\n" for n,h in sorted(final.items())))
(root/"staged-delta.json").write_text(json.dumps({
    "baseline_manifest":pins[0][1], "paint_manifest":pins[1][1],
    "baseline_files":len(original),"staged_files":len(final),"byte_exact_unchanged_files":len(original)-len(changed),
    "changed":{n:{"before":original[n],"after":final[n]} for n in changed},
    "added":{n:final[n] for n in added},
    "old_observer_recovers_byte_for_byte_if_only_additive_paint_witness_removed":True,
    "native_baseline_evidence_pins":keys,
    "no_renderer_invoked":True
},sort_keys=True,indent=2)+"\n")
