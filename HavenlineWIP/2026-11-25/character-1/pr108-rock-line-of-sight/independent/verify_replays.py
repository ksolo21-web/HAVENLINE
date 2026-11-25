#!/usr/bin/env python3
import json
from pathlib import Path
import sys
review, original = map(Path, sys.argv[1:])
expected = {
    "baseline": ["WITNESS wall target selection | target=true; baseline=true | PASS", "WITNESS west-wall F | strike 0 → 1 | PASS"],
    "repaired": ["WITNESS wall target selection | target=false; baseline=false | PASS", "WITNESS west-wall F | strike 0 → 0 | PASS", "WITNESS blocked mining input unconsumed | sequence 0 → 0 | PASS"],
}
report = {}
assert (review / "native-exits.tsv").read_bytes() == (original / "native-exits.tsv").read_bytes() == b"baseline\t0\nrepaired\t0\n"
for mode, wanted in expected.items():
    q = review / f"{mode}.native.log"
    e = original / f"{mode}.native.log"
    assert q.read_bytes() == e.read_bytes(), mode
    lines = q.read_text().splitlines()
    ws = [s for s in lines if s.startswith("WITNESS ")]
    outdoor = [s for s in ws if s.startswith("WITNESS legal outdoor F advances exactly once")]
    expected_outdoor = 2 if mode == "baseline" else 3
    count = 18 if mode == "baseline" else 20
    assert len(outdoor) == expected_outdoor and len(ws) == count and all(s.endswith("| PASS") for s in ws)
    assert all(s in ws for s in wanted)
    assert "WITNESS stone exhausted after three accepted hits | phase=mined tally=3 | PASS" in ws
    assert "WITNESS ledger unchanged since payment | wood=0 | PASS" in ws
    assert sum(x.startswith("WARNING: OBJ: Ambient light") for x in lines) == 18
    report[mode] = {"assertions":len(ws),"legal_outdoor_strikes": len(outdoor), "same_log_bytes_as_repair_agent": True}
print(json.dumps(report, sort_keys=True))
