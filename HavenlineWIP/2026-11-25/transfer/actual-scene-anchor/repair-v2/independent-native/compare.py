#!/usr/bin/env python3
import hashlib, json, math, pathlib, sys
run, source = map(pathlib.Path, sys.argv[1:])
old = source.read_bytes()
new = run.read_bytes()
assert b"ERROR:" not in new and b"WARNING:" not in new
assert old == new, "Replay differs from builder log"
data = {r["scenario"]:r for line in new.decode().splitlines() if line.startswith("ANCHOR_RESULT ") for r in [json.loads(line.split(" ",1)[1])]}
fail = [line.split(" tick=")[0] for line in new.decode().splitlines() if line.startswith("FAIL ")]
assert fail == [
    "FAIL launch 1 preserves live origin and basis (not request-time)",
    "FAIL launch 1 retains both active materials/surface roles",
    "FAIL landing 1 retains both active materials/surface roles",
]
for key, expected in [("clean",[157,0]),("cached-origin",[157,1]),("surface-override",[158,2])]:
    d=data[key]
    assert [d["checks"],d["failures"]] == expected
    assert d["active_material_checks"] == 12
clean=data["clean"]["launches"][-1]
cached=data["cached-origin"]["launches"][-1]
assert math.dist(clean["actual"],clean["expected"]) < 1e-5
assert math.isclose(math.dist(cached["actual"],cached["expected"]),.477453,abs_tol=1e-5)
print(json.dumps({"native_replay_identical":True,"log_sha256":hashlib.sha256(new).hexdigest(),"scenario_checks":{k:[v["checks"],v["failures"]] for k,v in data.items()},"intended_failures":fail,"actor_movement_m":data["clean"]["launches"][1]["actor_displacement_m"],"late_stale_jump_m":math.dist(cached["actual"],cached["expected"]),"late_clean_error_m":math.dist(clean["actual"],clean["expected"])},indent=2))
