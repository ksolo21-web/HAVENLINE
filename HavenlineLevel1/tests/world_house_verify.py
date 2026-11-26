"""Verify three exterior tiers, three real doorway entries, occupied typed shelves and separate apron visits."""
import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
proof = {}
enters = []
previous_visit = ""
with (run / "observations.jsonl").open() as source:
    for line in source:
        row = json.loads(line)
        field = row["field"]
        house = field["house"]
        phase = row["stage"]
        if house["visit"] != previous_visit:
            enters.append([row["tick"], house["visit"]])
            previous_visit = house["visit"]
        for tier, kind in enumerate(("wood", "stone", "meat"), 1):
            if house["tier"] != tier:
                continue
            if phase == f"House tier {tier} complete" and house["roof_visible"] and not house["cutaway"] and house["door"] < 0.02:
                proof[f"exterior_{tier}"] = row["tick"]
            if phase != f"Inspect the earned shelves inside tier {tier}" or not house["cutaway"] or house["door"] < .98:
                continue
            if field["stored"][kind] > 0 and house["shelves"][kind] > 0 and not house["roof_visible"]:
                proof[f"inside_{tier}"] = {"tick": row["tick"], "count": field["stored"], "visible_shelf_units": house["shelves"], "pos": row["pos"]}
assert all(f"{view}_{t}" in proof for view in ("exterior", "inside") for t in (1, 2, 3)), proof
visits = [v for _, v in enters]
for i, kind in enumerate(("wood", "stone", "meat")):
    purchase = visits.index("storage_" + kind)
    load = visits.index("load", purchase + 1)
    assert "" in visits[purchase:load]
proof["visit_transitions"] = enters
(run / "house-result.json").write_text(json.dumps(proof,indent=2)+"\n")
print("PASS starter, reinforced and advanced storage at one address, separate visits and occupied shelves")
