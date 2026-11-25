from collections import Counter
import csv
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def read(name):
    with (ROOT/name).open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f, delimiter="\t"))
    assert rows and all(None not in r and all(isinstance(k,str) and k.strip() for k in r.values()) for r in rows)
    return rows
sources=read("sources.tsv")
rows=read("coverage.tsv")
ids={s["ID"] for s in sources}
assert len(ids)==len(sources)
assert len({r["ID"] for r in rows})==len(rows)
states={"SKETCH","L1-UNBOUND","OUT-OF-SCOPE","VERIFIED-INTENT+SKETCH","OFFLINE+INTENT"}
groups={"Lifecycle","Input","Environment","Movement","Harvest","Resources","Build","Gates","Enemy","Customer","Completion","Mix"}
layers={"UI","ALL","MUSIC","SFX","MUSIC+SFX","AMBIENCE"}
for r in rows:
    assert re.fullmatch(r"[A-Z]{3}-[0-9]{2}",r["ID"]),r["ID"]
    src=set(r["Authority"].split(","))
    assert src <= ids and src,r["ID"]
    assert r["State"] in states and r["Group"] in groups and r["Layer"] in layers
    assert r["Priority"] in {"P1","P2","P3"}
    if r["State"]=="VERIFIED-INTENT+SKETCH":
        assert {"SKETCH","SFX95"} <= src
    if r["Group"] in {"Enemy","Customer","Completion"}:
        assert r["State"]=="L1-UNBOUND" and "L1" in src
assert {r["Group"] for r in rows}==groups
counts=Counter(r["State"] for r in rows)
assert counts["VERIFIED-INTENT+SKETCH"]==2
assert "INSTALLED" not in counts
print(f"Coverage structural checks passed: {len(rows)} scenarios, {len(groups)} groups, {len(ids)} authority references.")
print("Status counts: " + ", ".join(f"{k}={v}" for k,v in sorted(counts.items())))
print("Schema/source references only; no claims of runtime routing, audible quality or physical device approval.")
