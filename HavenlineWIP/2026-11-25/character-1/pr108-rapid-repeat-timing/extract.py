#!/usr/bin/env python3
"""Summarize a native timing log without relying on its test verdict labels."""
import json
from pathlib import Path
import sys
lines = Path(sys.argv[1]).read_text().splitlines()
records = [json.loads(row.split(" ", 1)[1]) for row in lines if row.startswith("TIMING ")]
out = {}
for kind in ("chop", "mine"):
    clip = next((x for x in records if x["type"] == "clip" and x["kind"] == kind), None)
    row = next((x for x in records if x["type"] == "observations" and x["kind"] == kind), None)
    if not clip or not row:
        out[kind] = {"observed": False}
        continue
    before, first = row["before"], row["first_dispatch_same_stack"]
    prior, second = row["before_second"], row["second_dispatch_same_stack"]
    out[kind] = {
        "observed": True, "first_dispatch_advanced": first["strikes"] == before["strikes"] + 1,
        "second_dispatch_advanced": second["strikes"] == prior["strikes"] + 1,
        "duration_s": clip["duration_s"], "method_tracks": clip["method_tracks"],
        "wall_gap_s": row["elapsed_s"], "prior_cooldown_s": prior["cooldown"],
        "prior_action_remaining_s": prior["remaining_s"], "prior_clip_playing": prior["playing"],
        "prior_clip_position_s": prior["position_s"],
        "second_clip_position_s": second["position_s"],
        "after_clip_positions_s": [x["position_s"] for x in row["after_frames"]],
    }
print(json.dumps(out, sort_keys=True))
