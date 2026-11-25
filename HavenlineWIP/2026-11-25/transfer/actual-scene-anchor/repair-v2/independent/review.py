#!/usr/bin/env python3
"""Audit frozen runner receipts; does not launch Godot or handle art."""
import hashlib
import json
import math
import pathlib
import sys

def digest(data):
    return hashlib.sha256(data).hexdigest()

def verified(path, pin):
    manifest = path.joinpath("SHA256SUMS").read_bytes()
    assert digest(manifest) == pin
    for line in manifest.decode().splitlines():
        want, name = line.split(maxsplit=1)
        assert pathlib.PurePath(name).name == name
        assert digest((path / name).read_bytes()) == want

def parse(path):
    rows = {}
    fails = []
    for ln in path.read_text().splitlines():
        if ln.startswith("ANCHOR_RESULT "):
            row = json.loads(ln.split(" ",1)[1])
            assert row["scenario"] not in rows
            rows[row["scenario"]] = row
        if ln.startswith("FAIL "):
            fails.append(ln.split(" tick=")[0])
    return rows, fails

old, new, spacing, fit = map(pathlib.Path, sys.argv[1:])
verified(old, "adc581aeb3c58cd3c456e1b42a35c13a887fde07f78a341dda0f2908b9749489")
new_pin = digest((new / "SHA256SUMS").read_bytes())
assert new_pin == "db8872b992dc84c09eb146a5ef90dae0e7f0c160bc453583254bc432a725e47f"
verified(new, new_pin)
for name in ["run.sh","sources.txt"]:
    assert (old / name).read_bytes() == (new / name).read_bytes(), name
prior, _ = parse(old / "result.log")
now, fail = parse(new / "replay.log")
assert 'ERROR:' in (old / "result.log").read_text()
assert set(now) == set(prior) == {"clean","cached-origin","surface-override"}
assert fail == [
    "FAIL launch 1 preserves live origin and basis (not request-time)",
    "FAIL launch 1 retains both active materials/surface roles",
    "FAIL landing 1 retains both active materials/surface roles",
]
assert "ERROR:" not in (new / "replay.log").read_text()
for key, checks, failures in [("clean",157,0),("cached-origin",157,1),("surface-override",158,2)]:
    n, p = now[key], prior[key]
    assert [n["checks"], n["failures"], n["active_material_checks"]] == [checks, failures, 12]
    assert all(p[k] == n[k] for k in n if k != "checks")
    assert n["selected_shift_m"] == [0.0, 0.600000023841858]
    assert n["surface_roles"] == ["Bark | painted ridges","End grain | amber"]
    assert [t["tick"] for t in n["launches"] if "launch" in t] == [0,11]
near = now["cached-origin"]["launches"][-1]
late = now["clean"]["launches"][-1]
motion = now["clean"]["launches"][1]
shift = math.dist(near["expected"],near["actual"])
assert math.isclose(shift, near["origin_error_m"], abs_tol=2e-6)
assert math.isclose(shift, motion["late_live_displacement_m"], abs_tol=2e-6)
assert math.dist(late["expected"],late["actual"]) < 0.00001
assert motion["actor_displacement_m"] > .30
raw = json.loads(spacing.read_text())["crown_aabb_extents_m"]
box = (.30211,.19934,.24000)
assert all(s < b for s,b in zip((raw[0],raw[1],raw[2]+.105),box))
assert "0.30211 × 0.19934 × 0.24000" in fit.read_text()
print(json.dumps({"manifest_v2":new_pin,"phase_receipts":{k:[v["checks"],v["failures"]] for k,v in now.items()},"actor_step_m":motion["actor_displacement_m"],"stale_launch_delta_reconstructed_m":shift,"clean_late_delta_m":math.dist(late["expected"],late["actual"]),"launch_ticks":[0,11],"geometry_only_two_crown_pair":(raw[0],raw[1],raw[2]+.105),"prior_actor_local_bundle_envelope_approx_m":box,"scope":"receipt and source review only, no independent native rerun, rendered evidence, receiver, actual inventory, clip/collision or integration"},indent=2))
