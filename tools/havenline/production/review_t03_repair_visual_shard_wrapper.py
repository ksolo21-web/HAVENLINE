#!/usr/bin/env python3
"""Shard the exact T03 C1/C2 reviewer without changing its pixels, rubric, model, seed or thresholds."""
from pathlib import Path
import os,hashlib
base=Path("tools/havenline/production/review_t03_repair_visual.py")
data=base.read_bytes()
source=data.decode()
needle='manifest={\n "schema_version":1'
assert source.count(needle)==1,source.count(needle)
groups=[x.strip() for x in os.environ["GROUP_FILTER"].split(",") if x.strip()]
assert groups
insertion='GROUPS={k:v for k,v in GROUPS.items() if k in '+repr(groups)+'}\nassert set(GROUPS)==set('+repr(groups)+')\n'
source=source.replace(needle,insertion+needle,1)
out=Path(os.environ.get("OUT_DIR","task03-shard"))
out.mkdir(parents=True,exist_ok=True)
executed=out/"executed-reviewer.py"
executed.write_text(source)
(out/"wrapper-provenance.txt").write_text(
    "base_sha256="+hashlib.sha256(data).hexdigest()+"\n"
    "change=group_filter_only\n"
    "group_filter="+",".join(groups)+"\n"
    "pixels_unchanged=true\n"
    "rubric_unchanged=true\n"
    "model_unchanged=true\n"
    "thresholds_unchanged=true\n"
)
exec(compile(source,str(executed),"exec"),{"__name__":"__main__","__file__":str(executed.resolve())})
