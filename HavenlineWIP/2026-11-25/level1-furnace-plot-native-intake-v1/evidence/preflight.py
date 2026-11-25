"""Source-only intake of exact 11c14a1c opening inventory presentation; no scene calls."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

PINS = {
    "wood_stock_view.gd": "559234eb3f17060c9319a1166e3c9a9239cffb1d",
    "opening_ledger.gd": "873def40c950279b210e2b2d0bed5d85625ea189",
    "opening.gd": "8de9499b0a48d920516d3b07c889cfb8a0808038",
    "previews/integrated_opening.gd": "cc54fb10b5270f513baa2c3743d4879e29ebb41a",
    "assets/studio/wood_bundle_v3.glb": "0e2325a683518050efed4232da9159adb34a566f",
}
SOURCE_HOOKS = (
    "TechnicalWoodBundleRepresentative", "var candidate := Wood.instantiate() as Node3D",
    "payload = candidate", "payload.visible = presented_units > 0",
)
NAMES = ["Lower log | knot side", "Lower log | far side", "Crown log",
         "One flax lashing | continuous perimeter", "Hitch | left tail", "Hitch | right tail"]

def git_blob(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def glb_scene(b):
    if len(b) < 20 or b[:12] != struct.pack("<4sII", b"glTF", 2, len(b)):
        raise ValueError("invalid GLB header")
    n, kind = struct.unpack_from("<I4s", b, 12)
    if kind != b"JSON" or n + 20 > len(b):
        raise ValueError("invalid GLB JSON")
    d = json.loads(b[20:20+n])
    nodes = d["nodes"]
    if (d["scenes"][d["scene"]]["nodes"] != list(range(6))
        or [node["name"] for node in nodes] != NAMES
        or [node["mesh"] for node in nodes] != list(range(6))
        or any("children" in node for node in nodes)):
        raise ValueError("unexpected representative GLB layout")
    return [node["name"] for node in nodes]

def audit(project):
    source = {}
    for rel, sha in PINS.items():
        raw = (project / rel).read_bytes()
        if git_blob(raw) != sha:
            raise ValueError(f"exact source pin failed: {rel}")
        source[rel] = raw if rel.endswith(".glb") else raw.decode()
    stock = source["wood_stock_view.gd"]
    if not all(s in stock for s in SOURCE_HOOKS) or stock.count("Wood.instantiate()") != 1:
        raise ValueError("wrong representative implementation")
    ledger = source["opening_ledger.gd"]
    if 'const COST := {"wood": 3}' not in ledger or 'const KNOWN_WOOD := ["wood-a", "wood-b", "wood-c"]' not in ledger:
        raise ValueError("unexpected source lineage/cost")
    opening = source["opening.gd"]
    flow = opening.split("func _commit_opening_progress(",1)[1].split("func tree_facing(",1)[0]
    markers = ("save.commit(next)", "if result != OK:", "ledger = next", "sync_progress_visuals()",
               "wood_stock_view.reflect_stock(int(ledger.stock.wood))", "purchase_pad_view.reflect_published_state(built)")
    indices = [flow.index(s) for s in markers]
    if indices != sorted(indices):
        raise ValueError("unexpected commit/presentation order")
    objects = glb_scene(source["assets/studio/wood_bundle_v3.glb"])
    rows = []
    for total in range(4):
        # This is the exact successful-install visibility rule in reflect_stock.
        # An installation failure makes the visible root count zero for all rows.
        visible = int(total > 0)
        rows.append({"wood": total, "affordable_by_count_only": total >= 3,
                     "visible_representative_roots_if_install_succeeds": visible,
                     "visible_internal_mesh_parts": visible * len(objects),
                     "source_bound_visual_units": 0, "render_only_3_arrival_handoff_admitted": False})
    return {"source_pin": "11c14a1c41971067c7dc97db69375f720a408f68",
            "proof_type": "source deduction, no engine run or generated instance IDs",
            "preexisting_mesh_parts": objects, "all_visible_install_failure": 0,
            "original_logic_unchanged": True, "rows": rows}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.project), indent=2))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
