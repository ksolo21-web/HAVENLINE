#!/usr/bin/env python3
"""Verify selected bytes and retained review evidence, not artistic quality."""
from pathlib import Path
import hashlib
import json
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[5]
    machine = root / "Docs/Design/ProcessingMachines/2026-11-27"
    resource = root / "Docs/Design/ResourceTurnarounds/2026-11-27-completion"
    errors = []
    def check(condition, message):
        if not condition:
            errors.append(message)

    selected_machines = json.loads((machine / "MACHINE_SELECTED_MANIFEST.json").read_text())["machines"]
    machine_review = json.loads((machine / "reviews/MACHINE_FINAL_REVIEW.json").read_text())
    review_by_id = {row["machine_id"]: row for row in machine_review["machines"]}
    check(len(selected_machines) == len(review_by_id) == 6, "Machine coverage must be 6/6")
    for item in selected_machines:
        reviewed = review_by_id[item["id"]]
        target = root / item["selected_path"]
        check(digest(target) == item["sha256"] == reviewed["sha256"], item["id"] + ": selected/review hash mismatch")
        check(target.read_bytes() == (root / item["retained_attempt"]).read_bytes(), item["id"] + ": selected copy differs")
        check(reviewed["score"] == 10 and all(x == 10 for x in reviewed["dimension_scores"].values()), item["id"] + ": required score not retained")
        check(not reviewed["unresolved_mandatory_defects"] and not reviewed["missing_mandatory_static_evidence"], item["id"] + ": unresolved review requirement")
        check(reviewed["angles_reviewed"] == [0, 45, 90, 135, 180, 225, 270, 315], item["id"] + ": incomplete intended view coverage")
        for closeup in reviewed["inspected_closeups"]:
            original = Path(closeup)
            retained = machine / "evidence/critic" / original.parent.name / original.name
            check(retained.is_file(), item["id"] + ": missing retained closeup " + retained.name)

    resource_manifest = json.loads((resource / "RESOURCE_SELECTED_MANIFEST.json").read_text())
    fresh = json.loads((resource / "reviews/RESOURCE_SELECTED_FRESH_REVIEW.json").read_text())
    fresh_by_id = {row["resource_id"]: row for row in fresh["reviews"]}
    check(len(resource_manifest["resources"]) == len(fresh_by_id) == 9, "Resource coverage must be 9/9")
    for item in resource_manifest["resources"]:
        reviewed = fresh_by_id[item["id"]]
        check(digest(root / item["selected"]["path"]) == item["selected"]["sha256"] == reviewed["identity"]["sha256"], item["id"] + ": resource hash mismatch")
        check(digest(root / item["fresh_review"]["path"]) == item["fresh_review"]["sha256"], item["id"] + ": fresh review changed")
        check(reviewed["score"] == 10 and all(x == 10 for x in reviewed["scores"].values()), item["id"] + ": resource score not retained")
        check(not reviewed["open_mandatory_defects"], item["id"] + ": unresolved resource defect")
        for evidence in item["fresh_review"]["closeups"]:
            check(digest(root / evidence["path"]) == evidence["sha256"], item["id"] + ": closeup changed")

    result = {
        "scope": "Selected-byte identity, review binding and evidence custody only; no new visual or runtime approval",
        "resource_sheets": len(resource_manifest["resources"]),
        "machine_sheets": len(selected_machines),
        "total_selected_sheets": len(selected_machines) + len(resource_manifest["resources"]),
        "illustrated_views": 8 * (len(selected_machines) + len(resource_manifest["resources"])),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    print(json.dumps(result, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
