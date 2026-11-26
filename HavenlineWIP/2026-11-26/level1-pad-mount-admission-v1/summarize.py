"""Check opted-in, baseline-bound runtime logs and emit only portable aggregate evidence."""
import json
import re
import sys
from pathlib import Path

run = Path(sys.argv[1])
modes = {"default": 106, "write": 108, "cold": 31, "fail": 98, "recover": 17}
stock_tags = {"spawn": 0, "wood-b": 1, "wood-c": 2, "occupied-pine": 2,
              "settled-pine": 3, "unpaid-approach": 3}
expected = {
    "default": [*stock_tags, "first-published", "holding-paid"],
    "write": [*stock_tags, "first-published", "holding-paid"],
    "fail": [*stock_tags, "failed-save"],
    "cold": ["cold-before-input", "cold-after-input"],
    "recover": ["recovered-unpaid"],
}
annotations = re.compile(
    r"^WARNING: OBJ: Ambient light for material '(board|board_warm|board_soft|beam|"
    r"brace_back|snow|metal|rope|rope_dark)' is ignored in PBR$", re.M)
diagnostic = re.compile(r"(?mi)^.*(?:ERROR|WARNING):.*$")
engine = re.compile(r"(?m)^Godot Engine (v4\.7\.2\.stable\.official\.[0-9a-f]+) ")
import_log = (run / "import/log").read_text()
assert len(annotations.findall(import_log)) == 18 and not diagnostic.search(annotations.sub("", import_log))
out = {}
for phase, count in modes.items():
    log = (run / phase / "log").read_text()
    assert engine.search(log) and engine.search(log)[1] == engine.search(import_log)[1]
    assert not diagnostic.search(log)
    assert f"purchase mount admission checks={count} failures=0" in log.splitlines()
    assert len(re.findall(r"^PASS .* tick=\d+$", log, flags=re.M)) == count
    assert not re.search(r"^FAIL ", log, flags=re.M)
    rows = [(k, v) for k, v in re.findall(r"^WITNESS ([a-z-]+) (.+)$", log, flags=re.M)]
    assert [tag for tag, _ in rows] == expected[phase]
    for tag, value in rows:
        n = stock_tags.get(tag, 3 if tag in {"failed-save", "recovered-unpaid"} else None)
        if n is not None:
            assert value == (f"stock={n} sources={n} cover={6 if n else 0}"
                             f" branches={1 if n else 0} representative_finite=true")
        else:
            assert value == "stock=0 receipt=exact live_marker=false mount_meshes=0"
    first = re.findall(r"^PASS first-published exact one-time receipt tick=(\d+)$", log, flags=re.M)
    assert len(first) == (1 if phase in {"default", "write"} else 0)
    out[phase] = {"checks": count, "failures": 0, "first_paid_observed_tick": int(first[0]) if first else None}
assert out["default"]["first_paid_observed_tick"] == out["write"]["first_paid_observed_tick"]
print(json.dumps({
    "baseline": "11c14a1c41971067c7dc97db69375f720a408f68",
    "project_tree": "d764a05246cbff96983aa27af17e2e919a946ae0",
    "engine": engine.search(import_log)[1], "exact_import_only_obj_annotations": 18,
    "native_execution": "opt-in, isolated headless input, no actual device smoke",
    "phases": out, "checks_total": sum(modes.values()),
    "findings": {"original_source_order": ["wood-b", "wood-c", "wood-a"],
                 "visible_mesh_count_from_0_to_3": [0, 6, 6, 6],
                 "direct_mount_count_from_0_to_3": [0, 1, 1, 1],
                 "independent_source_bound_visuals": 0,
                 "observed_paid_native_colliders_live_furnace": True,
                 "eligible_for_three_log_arrival_effect": False},
    "unverified": ["three distinct native carry bindings", "physical deck arrivals", "optional fill and shrink",
                   "visual readability", "phone performance", "release approval"],
}, indent=2, sort_keys=True))
