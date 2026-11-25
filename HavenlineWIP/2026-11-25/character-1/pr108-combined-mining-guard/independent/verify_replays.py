#!/usr/bin/env python3
"""Verify this combined A/B independently alongside the sealed builder logs."""
from pathlib import Path
import json, sys

ours, builder = map(Path, sys.argv[1:3])
receipt = b"baseline\t0\nrepaired\t0\n"
assert (ours / "native-exits.tsv").read_bytes() == (builder / "restored-native-exits.tsv").read_bytes() == receipt
summary = {}
for mode, expected in {"baseline":(26,18), "repaired":(29,20)}.items():
    members = {}
    expected_repeat = mode == "baseline"
    for origin in (ours,builder):
        raw = (origin / f"{mode}.native.log").read_text()
        head, tail = raw.split(f"BEGIN {mode} wall\n",1)
        wall, tail = tail.split(f"END {mode} wall\n",1)
        _, tail = tail.split(f"BEGIN {mode} repeat\n",1)
        repeat, _ = tail.split(f"END {mode} repeat\n",1)
        assert not any(s.startswith(("ERROR:","SCRIPT ERROR:","WARNING:","BLOCKED:")) for s in (wall+"\n"+repeat).splitlines())
        assert sum(s.startswith("WARNING: OBJ: Ambient light") for s in head.splitlines()) == 18
        categories = [[s for s in text.splitlines() if s.startswith("WITNESS ")] for text in (wall,repeat)]
        assert tuple(map(len,categories)) == expected
        assert all(s.endswith("| PASS") for ls in categories for s in ls)
        wall_strike = "0 → 1" if expected_repeat else "0 → 0"
        assert f"WITNESS west-wall F | strike {wall_strike} | PASS" in categories[0]
        assert "WITNESS west-wall ledger unchanged | wood=0 | PASS" in categories[0]
        assert "WITNESS ledger unchanged since payment | wood=0 | PASS" in categories[0]
        outdoors = sum(s.startswith("WITNESS legal outdoor F advances exactly once") for s in categories[0])
        assert outdoors == (2 if expected_repeat else 3)
        assert sum(s.startswith("WITNESS legal tree F advances exactly once before camp") for s in categories[0]) == 3
        if not expected_repeat:
            assert "WITNESS blocked mining input unconsumed | sequence 0 → 0 | PASS" in categories[0]
        rows = [json.loads(s[len("TIMING "):]) for s in repeat.splitlines() if s.startswith("TIMING ")]
        assert [r["kind"] for r in rows] == ["chop","mine"]
        times = {}
        for r in rows:
            a,b = r["overlap_before"],r["overlap_after"]
            n,q = r["next_before"],r["next_after"]
            assert r["baseline"] == expected_repeat and a["cooldown"] == 0 and a["remaining_s"] > 0 and a["playing"]
            assert a["ledger"] == b["ledger"] and n["ledger"] == q["ledger"]
            for k in ("strikes","input_seq","source_seq"):
                assert b[k] - a[k] == int(expected_repeat)
                assert q[k] - n[k] == 1
            if not expected_repeat:
                assert {k:v for k,v in a.items() if k!="usec"} == {k:v for k,v in b.items() if k!="usec"}
            times[r["kind"]] = {"wall_gap_s":r["elapsed_s"],"active_remaining_s":a["remaining_s"],"repeat_strikes":[a["strikes"],b["strikes"]],"later_strikes":[n["strikes"],q["strikes"]]}
        members[origin] = [[s.split(" | ",1)[0] for s in ls] for ls in categories]
        if origin == ours:
            summary[mode] = {"wall_checks":expected[0],"repeat_checks":expected[1],"independent_wall_strikes":wall_strike,"legal_outdoor_F":outdoors,"repeat_probe":times}
    assert members[ours] == members[builder]
print(json.dumps(summary,sort_keys=True))
