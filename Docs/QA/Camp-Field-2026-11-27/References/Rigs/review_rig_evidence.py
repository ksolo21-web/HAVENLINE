"""Run the documented rig gate against the original assets and the actual field measurements.

Usage: python review_rig_evidence.py /path/to/HavenlineLevel1
The score inputs are the independent reviewer's signed-off visual decisions. This script
also checks measures independently of each score and preserves a readable row ledger.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("game", type=Path)
args = parser.parse_args()
here = Path(__file__).resolve().parent
trial = here.parent.parent


def data(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def glb(path):
    with path.open("rb") as stream:
        prefix = stream.read(20)
        if prefix[0:4] != b"glTF":
            raise ValueError("Reference is not a valid GLB: " + str(path))
        return json.loads(stream.read(struct.unpack_from("<I", prefix, 12)[0]))


def available(name):
    p = (here / name).resolve()
    return p.is_file() and p.stat().st_size > 128


android = data(trial / "Verification/Android.json")
packed = data(trial / "Verification/Signed-resource-pack.json")
decision = data(here / "Rig-visual-decisions.json")
result = {
    "checker": "Independent implementation of the published rig-critic gates. Field controls, attachments and the 9.9 motion requirement extend the original GLB ledger.",
    "source": android["source"],
    "android_sha256": android["sha256"],
    "android_source_receipt": "../../Verification/Android.json",
    "minimum": 9.9,
    "actors": {},
}
stages_required = {"idle", "launch", "cruise", "steer", "brake"}
for index in range(1, 6):
    worker = index == 5
    title = "Forester" if worker else f"C{index}"
    actor = decision["actors"][title]
    if actor.get("status") == "awaiting_owner_model":
        result["actors"][title] = {
            "score": None, "joints": None, "embedded_clips": None,
            "checked_stages": [], "part_stage_rows": 0, "rows": [],
            "checks": [{"gate": "Corrected owner model and native play evidence",
                        "pass": False, "evidence": "../Owner-identity/Identity-correction.json"}],
            "pass": False,
        }
        continue
    role_root = here / actor.get("evidence_directory", "")
    path = args.game / actor["asset"]
    model = glb(path)
    joints = {model["nodes"][j]["name"] for skin in model["skins"] for j in skin["joints"]}
    clips = {clip["name"] for clip in model.get("animations", [])}
    rows = []
    checks = []

    def check(category, success, evidence, detail=None):
        if role_root != here and evidence.startswith(title + "-"):
            evidence = (role_root / evidence).relative_to(here).as_posix()
        checks.append({"gate": category, "pass": bool(success), "evidence": evidence, "detail": detail})

    def evidence(name):
        source = (role_root / name).relative_to(here).as_posix() if role_root != here and name.startswith(title + "-") else name
        check("Read review evidence", available(source), name)

    check("Source model identity", digest(path) == actor["sha256"], actor["asset"], actor["sha256"])
    check("Android gameplay source and asset binding",
          android["source"] == decision["source"] and android["sha256"] == packed["apk_sha256"]
          and packed["identical_files_verified"] == packed["packed_files"],
          "../../Verification/Signed-resource-pack.json", packed["packed_files"])
    check("Original skin joint inventory", len(joints) == actor["joint_count"], actor["asset"], sorted(joints))
    check("Original animation inventory", clips == set(actor["embedded_clips"]), actor["asset"], sorted(clips))
    for item in actor["visual_evidence"]:
        evidence(item)
    if actor.get("status") == "corrected_owner_model":
        evidence(title + "-empty-independent-motion.mp4")
        evidence(title + "-loaded-independent-motion.mp4")
    check("Independent visual score, normal camera and pinch", actor["score"] >= 9.9 and actor["seen"],
          "Rig-visual-decisions.json", actor["score"])

    if index == 1:
        src = "Character1-original-clips/"
        original = data(role_root / (src + "part-surface-and-joints.json"))
        lower = data(role_root / (src + "lower-limb-120hz.json"))
        checked = set(original["clips"]) == clips and original["finite_inverse_bind"]
        check("Original skin, inverse binds and each original clip", checked, src + "part-surface-and-joints.json")
        for name in sorted(clips):
            evidence(src + name + ".jpg")
            check(name + " lower-body inspection", set(lower[name]) == {"L", "R"},
                  src + "lower-limb-120hz.json")
            for part in sorted(joints):
                observed = original["clips"][name][part]
                rows.append([name, part, "source joint and weighted geometry",
                             bool(observed["finite"] and min(observed["det_range"]) > 0)])
            check(name + " all original joints sampled", set(original["clips"][name]) == joints,
                  src + "part-surface-and-joints.json")
        for file in ("Intersections.json", "Whole-medial-tabs.json", "Complete-cuff-material.json"):
            evidence(src + file)

    evidence_sets = ["Forester-whole.json"] if worker else [title + f"-{load}-whole.json" for load in ("empty", "loaded")]
    for name in evidence_sets:
        q = data(role_root / name)
        check("Native 120 Hz actor and source model", q["real_physics_Hz"] == 120
              and q["source_asset_sha256"] == actor["sha256"], name)
        stages = set(q["stages"])
        if not worker:
            check("Controller stages and sample coverage", stages == stages_required and q["total_frames"] == 545, name)
        else:
            mandatory = {"travel_0", "travel_1", "pivot_0", "pivot_1", "chop_0", "chop_1", "idle_0"}
            check("Loaded/unloaded autonomous travel and work", mandatory <= stages and q["total_frames"] >= 1900, name)
        for stage, o in q["stages"].items():
            check(name + " · " + stage + " complete skeleton", set(o["joints"]) == joints, name)
            for part, entry in sorted(o["joints"].items()):
                rows.append([name + "/" + stage, part, "native finite transform, temporal movement, weighted ownership",
                             bool(entry["finite_local"] and entry["det_min"] > 0 and entry["biggest_frame_rotation_deg"] < 180)])
            for material, entry in sorted(o["surfaces"].items()):
                rows.append([name + "/" + stage, material, "actual material / coarse garment region and area",
                             bool(entry["triangles"] and 0 <= entry["largest_affected_fraction"] <= 1
                                  and all(v >= 0 for v in entry["worst_pose_area_SI_5_50_95pct"]))])
    if worker:
        native = data(role_root / "Forester-natural-work.json")
        verts = data(role_root / "Forester-opposing-boots.json")
        counts = native["run"]["full_tick_counts"]
        check("90 seconds of natural work under the real controller", sum(counts.values()) == 10800
              and native["hz"] == 120, "Forester-natural-work.json", native["tasks"])
        check("Opposing footwear across every captured state", all(s["new_touch_frames"] == 0 for s in verts["modes"].values())
              and sum(s["examined_samples"] for s in verts["modes"].values()) >= 1900,
              "Forester-opposing-boots.json", verts["sampled_field_poses"])
        for side in "LR":
            for mode in ["travel_0", "travel_1", "pivot_0", "pivot_1"]:
                notes = native["sign"][side][mode]
                drift = max((v["drift_mm"] for v in native["contacts"][mode+"-"+side]), default=0)
                check(mode + " " + side + " anatomical bend and planted material",
                      not notes["negative_ticks"] and drift < (8 if "pivot" in mode else 2),
                      "Forester-natural-work.json", {"max_drift_mm": drift, "knee_deg": notes["signed_ky_deg"]})
    else:
        for load in ("empty", "loaded"):
            base = f"{title}-{load}-"
            m = data(role_root / (base+"support.json"))
            ore = data(role_root / (base+"leg-surface.json"))
            cycle = data(role_root / (base+"loop.json"))
            evidence(base+"angles.jpg")
            if actor.get("status") == "corrected_owner_model":
                floors = data(role_root / (base+"all-transition-floor.json"))
                check("Actual boot surface through launch, run, corner and full stop",
                      set(floors) == {phase + "_" + side for phase in stages_required for side in "LR"}
                      and all(value["y_mm"] >= -2 for value in floors.values()),
                      base+"all-transition-floor.json",
                      {key: value["y_mm"] for key, value in floors.items()})
                evidence(title+"-whole-contact-classification.jpg")
            check("Every distinct lower-body surface and joint", m["set_Hz"] == 120 and m["ticks"] == 545
                  and m["source"] == actor["sha256"] and set(m["joints"]) == joints and m["field_ready"],
                  base+"support.json")
            for side in "LR":
                stage = m["metrics"][side]
                drift = max(v["fixed_patch_drift_mm"] for v in m["material_contact"][side]["events"])
                check(load+" "+side+" support, arm opposition, knees and treads",
                      all(v["leg_negative_bends"] == 0 for v in stage.values()) and drift < 6
                      and stage["cruise"]["ipsilateral_arm_vs_thigh"] < -.7 and bool(ore["legs"][side]["toe_weighted_verts"]),
                      base+"support.json", {"max_drift_mm": drift, "knee_deg": stage["cruise"]["knee_bend_deg"]})
            check("Recorded source pace and real motion", all(.39 <= v <= .455 for v in cycle["actual_complete_cycle_s"])
                  and all(4.5 <= v <= 5.1 for v in cycle["ordinary_straight_projected_body_heights_per_second"]),
                  base+"loop.json")
        scan = data(role_root / (title+"-empty-clearance.json"))
        check("Idle through full stop triangle sweep", scan["ticks_scanned"] == 545,
              title+"-empty-clearance.json", scan["whole_triangles"])
        if index in (2, 3, 4):
            armfile = title+"-arm-corridor.json"
            corridor = data(role_root / armfile)
            for side in "LR":
                observed = corridor[side]
                check("Forward/backward run arm below shoulder "+side,
                      observed["true_lateral_elevation_deg"][2] < 38
                      and observed["wrist_height_vs_shoulder_m"][1] < -.13,
                      armfile, observed)
            for load in ("empty","loaded"):
                name = title+"-"+load+"-glove-physical.json"
                actual = data(role_root / name)
                witnesses = actual["maximum_each_category"]
                largest = max((c["line_mm"] for c in witnesses.values()),default=0)
                check(load+" physical glove sweep over the whole selected body",
                      actual["scanned_poses"]==545 and largest<3, name, witnesses)
                if witnesses:
                    evidence(title+"-"+load+"-contact-classification.jpg")
    result["actors"][title] = {"score":actor["score"],"joints":len(joints),"embedded_clips":sorted(clips),
        "checked_stages":evidence_sets,"part_stage_rows":len(rows),"rows":rows,"checks":checks,
        "pass":all(r[-1] for r in rows) and all(k["pass"] for k in checks)}
result["pass"] = all(v["pass"] for v in result["actors"].values())
summary={k:{f:q[f] for f in ["joints","embedded_clips","part_stage_rows","score","pass"]} for k,q in result["actors"].items()}
(here/"Rig-inspection-ledger.json").write_text(json.dumps(result,separators=(",",":"))+"\n")
(here/"Rig-release-gates.json").write_text(json.dumps({"implementation":result["checker"],"source":result["source"],
    "apk_sha256":result["android_sha256"],"minimum":9.9,"actors":summary,"passed":result["pass"]},indent=2)+"\n")
print(json.dumps(summary))
for label,entry in result["actors"].items():
    for check0 in entry["checks"]:
        if not check0["pass"]:print("Failed:",label,check0)
    for row in entry["rows"]:
        if not row[-1]:print("Failed:",label,row)
raise SystemExit(int(not result["pass"]))
