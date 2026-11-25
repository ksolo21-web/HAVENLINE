#!/usr/bin/env python3
"""Compare repaired and baseline behavior with builder receipts, not wall-clock bytes."""
from pathlib import Path
import json, sys
mine, builder = map(Path, sys.argv[1:3])
assert (mine/"native-exits.tsv").read_bytes() == (builder/"native-exits.tsv").read_bytes() == b"baseline\t0\nrepaired\t0\n"
out = {}
for mode, count in [("baseline",18), ("repaired",20)]:
    results = []
    normalized = []
    for directory in (mine, builder):
        text = (directory/(mode+".native.log")).read_text()
        lines = text.splitlines()
        ws = [s for s in lines if s.startswith("WITNESS ")]
        assert len(ws)==count and all(s.endswith("| PASS") for s in ws),(mode,count,ws)
        assert not any(s.startswith(("ERROR:", "SCRIPT ERROR:", "BLOCKED:")) for s in lines)
        normalized.append([s.split(" | ",1)[0] for s in ws])
        records = [json.loads(p.removeprefix("TIMING ")) for p in lines if p.startswith("TIMING ")]
        assert [x["kind"] for x in records] == ["chop","mine"]
        summary = {"witnesses":len(ws), "timings":{}}
        for x in records:
            a,b=x["overlap_before"],x["overlap_after"]
            n,q=x["next_before"],x["next_after"]
            assert x["baseline"] == (mode=="baseline"),x
            assert a["cooldown"] == 0 and a["remaining_s"] > 0 and a["playing"],x
            assert x["first_after"]["strikes"] == x["first_before"]["strikes"] + 1,x
            for k in ("strikes","input_seq","source_seq"):
                assert b[k] - a[k] == (mode=="baseline"), (k,x)
                assert q[k] - n[k] == 1,(k,x)
            assert a["ledger"]==b["ledger"] and n["ledger"]==q["ledger"]
            if mode=="repaired":
                assert {k:v for k,v in a.items() if k!="usec"}=={k:v for k,v in b.items() if k!="usec"},x
            summary["timings"][x["kind"]]={"wall_gap_s":x["elapsed_s"],"active_remaining_s":a["remaining_s"],"repeat_strike":f'{a["strikes"]}→{b["strikes"]}',"next_strike":f'{n["strikes"]}→{q["strikes"]}'}
        results.append(summary)
    assert normalized[0]==normalized[1],mode
    out[mode]=results[0]
print(json.dumps(out,sort_keys=True))
