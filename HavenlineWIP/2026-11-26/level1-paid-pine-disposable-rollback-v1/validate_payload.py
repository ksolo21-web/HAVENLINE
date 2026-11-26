"""Read only admitted disposable captures; emit digests and semantic counts, not payload bytes."""
import hashlib
import json
import sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
assert root.parent==Path("/tmp") and root.name.startswith("havenline-l1-v3-pine-rollback-candidate-")
assert (root/"PINE-ROLLBACK-CANDIDATE").read_text()=="PINE-ROLLBACK-CANDIDATE-V1\n"
primary=root/"opening-v3.json"
v1=root/"v1-frozen.json"
data={}
proof={}
for version, path in ((1,v1),(2,primary)):
    assert path.is_file() and not path.is_symlink()
    raw=path.read_bytes()
    j=json.loads(raw)
    assert set(j)=={"version","payload","sha256"} and j["version"]==1
    assert hashlib.sha256(j["payload"].encode()).hexdigest()==j["sha256"]
    p=json.loads(j["payload"])
    assert p["version"]==version and p["stock"]=={"wood":version-1}
    assert p["collected"]==["wood-b","wood-c","wood-a"]
    assert p["receipt"]=={"offer":"center-hearth","grant":"center-hearth","typed_debit":{"wood":3},"revision":1}
    assert set(p)=={"version","stock","collected","receipt"}|({"pine_occurrences"} if version==2 else set())
    assert (version==1) or p["pine_occurrences"]==1
    data[version]=p
    proof[f"v{version}"]={"file_sha256":hashlib.sha256(raw).hexdigest(),"file_bytes":len(raw),
                         "save_envelope_version":1,"payload_version":version,
                         "wood":version-1,"repeat_occurrences":p.get("pine_occurrences",0)}
assert data[1]["receipt"]==data[2]["receipt"]
print(json.dumps(proof,indent=2,sort_keys=True))
