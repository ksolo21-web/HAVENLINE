"""Validate native checkpoints and digest allowed scratch; never emit exact save bytes."""
import hashlib
import json
import re
import sys
from pathlib import Path

source="11c14a1c41971067c7dc97db69375f720a408f68"
patch="e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd"
def sha(data):return hashlib.sha256(data).hexdigest()

if len(sys.argv)==3 and sys.argv[1]=="--validate-live-disposable":
    d=Path(sys.argv[2])
    assert d.parent==Path("/tmp") and d.name.startswith("havenline-l1-v3-l1-e2e-") and d.is_dir() and not d.is_symlink()
    assert (d/"L1-DISPOSABLE").read_text()=="HAVENLINE-ALFRED-V3-DISPOSABLE\n"
    assert (d/"L1-E2E-ROUTE").read_text()=="HAVENLINE-L1-E2E-ROUTE-V1\n"
    primary=d/"opening-v3.json"
    assert primary.is_file() and not primary.is_symlink() and primary.stat().st_nlink==1
    data=primary.read_bytes(); envelope=json.loads(data)
    assert set(envelope)=={"version","payload","sha256"} and envelope["version"]==1 and sha(envelope["payload"].encode())==envelope["sha256"]
    q=json.loads(envelope["payload"])
    assert q=={"version":2,"pine_occurrences":1,"stock":{"wood":1},"collected":["wood-b","wood-c","wood-a"],"receipt":{"offer":"center-hearth","grant":"center-hearth","typed_debit":{"wood":3},"revision":1}}
    print(json.dumps({"byte_count":len(data),"primary_sha256":sha(data),"outer_version":1,"payload_version":2,"wood":1,"renewals":1,"receipt_cost_wood":3},sort_keys=True))
    sys.exit()

assert len(sys.argv)==2
d=Path(sys.argv[1])
import_log=(d/"import.log").read_text()
diag=[x for x in import_log.splitlines() if re.search(r"(?:ERROR|WARNING):|Parse Error",x,re.I)]
assert len(diag)==18 and all(re.fullmatch(r"WARNING: OBJ: Ambient light for material '(board|board_warm|board_soft|beam|brace_back|snow|metal|rope|rope_dark)' is ignored in PBR",l) for l in diag)
assert (d/"disposable.before").read_bytes()==(d/"disposable.after").read_bytes()
state=json.loads((d/"writer-digest.json").read_text())
assert state["primary_sha256"] in (d/"disposable.before").read_text()
results={}; versions=set()
for phase in ("write","cold"):
    data=(d/(phase+".log")).read_bytes(); text=data.decode()
    assert not re.search(r"FAIL |ERROR:|WARNING:|Parse Error",text)
    version=re.search(r"^Godot Engine (v4\.7\.2\.stable\.official\.[a-zA-Z0-9]+) ",text)[1]
    versions.add(version)
    count=int(re.search(r"^L1_COMBINED_ROUTE phase="+phase+r" checks=(\d+) failures=0$",text,re.M)[1])
    assert count==len(re.findall(r"^PASS ",text,re.M))
    observed=[json.loads(l.split(" ",1)[1]) for l in text.splitlines() if l.startswith("L1_COMBINED_CHECKPOINT ")]
    idx={e["phase"]:e for e in observed}
    assert len(observed)==len(idx)
    assert all(v["tick"]>=0 for v in observed) and sorted(v["tick"] for v in observed)==[v["tick"] for v in observed]
    assert idx["pine-regrown"]["renewals"]==(0 if phase=="write" else 1)
    if phase=="write":
        ordered=("fresh-spawn","three-original-wood","paid-first-frame","south-bidirectional","east-bidirectional","writer-v2")
        assert set(idx)==set(ordered)|{"pine-regrown"} and list(x["phase"] for x in observed if x["phase"]!="pine-regrown")==list(ordered)
        for tag,n,r,m in zip(ordered,(0,3,0,0,0,1),(0,0,0,0,0,1),(False,False,True,True,True,True)):
            assert idx[tag]["published_wood"]==n and idx[tag]["renewals"]==r and idx[tag]["paid"] is m
        for gate in ("South","East"):
            for leg in ("physical outward traversal","physical return traversal"):
                assert f"PASS {gate} gate {leg}" in text
    else:
        assert list(idx)==["pine-regrown","cold-v2-no-replay"]
        assert idx["cold-v2-no-replay"]["published_wood"]==idx["cold-v2-no-replay"]["renewals"]==1 and idx["cold-v2-no-replay"]["paid"]
    results[phase]={"checks":count,"failures":0,"log_sha256":sha(data),"checkpoints":observed}
assert len(versions)==1
print(json.dumps({"scope":"one exact detached revision and one controlled checkpoint across two fresh process environments; headless handler input only",
    "baseline":source,"paid_pine_patch":patch,"engine":next(iter(versions)),"import_only_existing_obj_warnings":18,
    "phases":results,"first_postpayment_repeat_recovered_without_rewrite":True,
    "original_three_distinct_sources_and_single_debit":True,
    "owner_save_live_game_release_or_device_proof":False,"profile_snapshot_equal_across_cold":True,"controlled_checkpoint":state},
    sort_keys=True,indent=2))
