#!/usr/bin/env python3
"""Create a format-identical legacy logical envelope ONLY within our temp fixture."""
import hashlib,json,re,sys
from pathlib import Path
p=Path(sys.argv[1]); mode=sys.argv[2]
assert p.parent==Path("/tmp") and re.fullmatch(r"havenline-pine-store-fixture-[A-Za-z0-9_-]{8,48}",p.name)
assert not p.is_symlink() and (p/"PINE-STORE-TEST-OWNER").is_file()
x={"version":1 if mode=="v1" else 2,"collected":["wood-b","wood-c","wood-a"],"stock":{"wood":0 if mode=="v1" else 2},
   "receipt":{"offer":"center-hearth","typed_debit":{"wood":3},"grant":"center-hearth","revision":1}}
if mode=="v2":x["pine_occurrences"]=2
payload=json.dumps(x,separators=(",",":"))
with (p/"pine-store-fixture.json").open("x") as file:
    json.dump({"version":1,"payload":payload,"sha256":hashlib.sha256(payload.encode()).hexdigest()},file)
