"""Check all twelve physical crossings on the extended touch route after world_route_verify.py."""
import json
import sys
from collections import defaultdict
from pathlib import Path

report = json.loads((Path(sys.argv[1]) / "route-result.json").read_text())
crossings = defaultdict(list)
for crossing in report["crossings"]:
    key = (crossing["stage"], crossing["gate"], crossing["direction"])
    crossings[key].append(crossing)
for stage in (1, 2, 3):
    for gate in ("gate-south", "gate-east"):
        for direction in ("out", "in"):
            matches = crossings[(stage, gate, direction)]
            assert matches, (stage, gate, direction)
            for crossing in matches:
                assert abs(crossing["center_offset_m"]) <= 1.1
                assert crossing["from_orbit_active"] == (direction == "in")
                assert crossing["to_orbit_active"] == (direction == "out")
                heads = 3 if stage == 3 else 1
                assert crossing["from_visible_heads"] == (heads if direction == "in" else 0)
                assert crossing["to_visible_heads"] == (heads if direction == "out" else 0)
print("PASS both gates, both directions on all three paid perimeters")
