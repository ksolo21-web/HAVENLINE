"""Validate actual effective Godot materials, and pair exact captures against the unpainted run."""
from hashlib import sha256
from pathlib import Path
import json
import math
import re
import sys

out, capsule = map(Path, sys.argv[1:])
def from_file(folder,name):
    return json.loads((folder/name).read_text())

def load_comparison(name):
    return from_file(capsule,"control-"+name+".json"), from_file(out,name+".json")

shape = {
    "board":(0,.42), "board_warm":(0,.73), "board_soft":(0,.57),
    "beam":(1,.70), "brace_back":(1,.58), "snow":(2,.50),
    "metal":(3,.50), "rope":(4,.70), "rope_dark":(4,.34)
}
labels = ["gate-south","gate-east"]
pivots = ["HingeLeft","HingeRight"]
writer = ["fresh-spawn","paid-first-frame","south-bidirectional","east-bidirectional","writer-v2"]
cold = ["cold-v2-no-replay"]
swing = [f"{g}-{i}" for g in labels for i in (225,450,675)]
control, actual = load_comparison("gate-evidence")
cf, af = load_comparison("functional")
cw, aw = load_comparison("frame-evidence")
cr, ar = load_comparison("r17-evidence")
assert control["candidate"] == actual["candidate"]
assert control["stock_gate_and_save_controls"] == actual["stock_gate_and_save_controls"]
assert cr["gates_transition_ticks"] == ar["gates_transition_ticks"]
assert cf["controlled_checkpoint"] == af["controlled_checkpoint"]
assert af["profile_snapshot_equal_across_cold"] and af["original_three_distinct_sources_and_single_debit"]
assert af["first_postpayment_repeat_recovered_without_rewrite"]
for phase, count in [("write",57),("cold",10)]:
    assert af["phases"][phase]["checks"]==count and af["phases"][phase]["failures"]==0
    assert cf["phases"][phase]["checkpoints"] == af["phases"][phase]["checkpoints"]
expected_labels = set(writer+cold+swing)
receipts = {}
for phase, allowed in [("write",set(writer+swing)),("cold",set(cold))]:
    lines = re.findall(r'^GATE_18591_PAINT_FRAME (.+)$',(out/(phase+".log")).read_text(),re.M)
    assert len(lines) == len(allowed)
    for row in map(json.loads,lines):
        name = row["label"]
        assert name in allowed and name not in receipts
        assert set(row["paint"])==set(labels)
        for gate in labels:
            assert set(row["paint"][gate])==set(pivots)
            for side,pivot in zip(("left","right"),pivots):
                overrides=row["paint"][gate][pivot]
                old_source=control["candidate"]["leaves"][side]["ordered_surfaces"]
                assert len(overrides)==len(old_source)==39
                for i,(actual_mat,src) in enumerate(zip(overrides,old_source)):
                    assert actual_mat["surface"]==i==src["index"]
                    assert actual_mat["label"]==src["material"]
                    family,tone=shape[src["material"]]
                    assert actual_mat["family"]==family and math.isclose(actual_mat["tone"],tone,abs_tol=1e-6,rel_tol=0)
                    assert actual_mat["effective"] is True and actual_mat["whole_instance_override_or_overlay"] is False
                    assert actual_mat["shader"]=="res://previews/clearance_gate/gate_18591_surface.gdshader"
        # Save a compact proof while preserving exact four-by-39 rows in raw logs.
        receipts[name] = {"effective_overrides":156,
                          "ordered_census_sha256":sha256(json.dumps(row["paint"],sort_keys=True,separators=(",",":")).encode()).hexdigest()}
assert set(receipts)==expected_labels
assert len({x["ordered_census_sha256"] for x in receipts.values()})==1
for frame in writer+cold:
    a,b = aw["frames"][frame],cw["frames"][frame]
    assert all(a[key]==b[key] for key in ("queued_tick","wood","paid","renewals","south_open","east_open"))
    receipts[frame].update({"baseline_native_sha256":b["matching_native_buffer_sha256"],"paint_native_sha256":a["matching_native_buffer_sha256"],
                            "baseline_png_sha256":b["png_sha256"],"paint_png_sha256":a["png_sha256"]})
for frame in swing:
    a,b = actual["swing_frames"][frame],control["swing_frames"][frame]
    assert all(a[k]==b[k] for k in ("gate","label","target_deg","queue_tick","width","height"))
    # Frame callback can land at the same or the next fixed physics step. The
    # inherited guard constrains the actual draw angle; exact native queue angles repeat.
    assert math.isclose(a["queue_deg"],b["queue_deg"],abs_tol=1e-6,rel_tol=0)
    receipts[frame].update({"baseline_native_sha256":b["native_buffer_sha256"],"paint_native_sha256":a["native_buffer_sha256"],
                            "baseline_png_sha256":b["png_sha256"],"paint_png_sha256":a["png_sha256"],
                            "baseline_draw_deg":b["draw_deg"],"paint_draw_deg":a["draw_deg"]})
assert receipts["paid-first-frame"]["baseline_native_sha256"] != receipts["paid-first-frame"]["paint_native_sha256"]
# Art quality is not settled by pixel inequality or census. Use actual paired frames.
print(json.dumps({"scope":"native exact four gate-local shader instances, recorded per surface on 12 frames; no aesthetic, device or active closing approval",
                  "unchanged_functional_checks":67,"unchanged_save":af["controlled_checkpoint"],
                  "per_capture_instance_surface_count":156,"paint_frames":receipts},indent=2,sort_keys=True))
