"""Read frozen private harness logs, emitting only derived counts and digests."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import sys

root=Path(sys.argv[1])
summaries={}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
expected={"candidate":r"PINE_ROLLBACK_CANDIDATE checks=(\d+) failures=0",
          "legacy-v1":r"PINE_ROLLBACK_LEGACY mode=v1 checks=(\d+) failures=0",
          "legacy-v2":r"PINE_ROLLBACK_LEGACY mode=v2 checks=(\d+) failures=0"}
need_results=[
    "older reader actually accepts candidate-produced paid v1",
    "older reader refuses genuine v2 without mutating target ledger",
    "older valid commit refuses to replace undecodable primary"]
engine=None
for phase,pattern in expected.items():
    log=root/(phase+".log"); raw=log.read_text()
    version=re.search(r"^Godot Engine (v4\.7\.2\.stable\.official\.[0-9a-f]+) ",raw,re.M)[1]
    if engine is None: engine=version
    assert engine==version and not re.search(r"^(FAIL|ERROR:|WARNING:|SCRIPT ERROR:)",raw,re.M|re.I)
    m=re.search("^"+pattern+"$",raw,re.M)
    n=len(re.findall(r"^PASS ",raw,re.M))
    assert int(m[1])==n and n>0
    summaries[phase]={"checks":n,"failures":0,"log_sha256":digest(log)}
    if phase=="legacy-v1":
        assert need_results[0] in raw and all(x not in raw for x in need_results[1:])
    if phase=="legacy-v2":
        assert need_results[0] not in raw and all(x in raw for x in need_results[1:])
        codes=re.search(r"^PINE_ROLLBACK_CODES load=(\d+) commit=(\d+) expected=(\d+)$",raw,re.M)
        assert codes[1]==codes[2]==codes[3] and int(codes[1])>0
        summaries[phase]["load_commit_err_file_corrupt"]=int(codes[1])
import_log=(root/"import.log").read_text()
allow=re.compile(r"^WARNING: OBJ: Ambient light for material '([a-z_]+)' is ignored in PBR$")
diagnostics=[l for l in import_log.splitlines() if re.search(r"(?:ERROR|WARNING):",l,re.I)]
assert len(diagnostics)==18 and all(allow.fullmatch(l) for l in diagnostics)
assert Counter(allow.fullmatch(l)[1] for l in diagnostics)==Counter({x:2 for x in "board board_warm board_soft beam brace_back snow metal rope rope_dark".split()})
assert (root/"no_unexpected_save_paths").stat().st_size==0
save=json.loads((root/"writer-digests.json").read_text())
assert set(save)=={"v1","v2"}
for key in save:
    input=root/("legacy-"+key+".before");output=root/("legacy-"+key+".after")
    assert input.read_bytes()==output.read_bytes()
    assert len(input.read_text().splitlines())==6
    filenames={"opening-v3.json","L1-DISPOSABLE","PINE-ROLLBACK-LEGACY"}
    for line in input.read_text().splitlines():
        if line.startswith("f "):
            assert line.split()[-1] in filenames
        else:
            hash_=line.split(maxsplit=1)[0]
            file_=line.split(maxsplit=1)[1][2:]
            assert file_ in filenames and re.fullmatch(r"[0-9a-f]{64}",hash_)
            if file_=="opening-v3.json": assert hash_==save[key]["file_sha256"]
    version=int(key[1])
    assert save[key]["save_envelope_version"]==1 and save[key]["payload_version"]==version
    assert save[key]["wood"]==save[key]["repeat_occurrences"]==version-1
    summaries["legacy-"+key]["scratch_all_files_and_modes_unchanged"]=True
    summaries["legacy-"+key]["matched_real_candidate_bytes"]=True
print(json.dumps({
    "route":"exact patched integrated scene for candidate; legacy is only exact old Save/Ledger in a scratch script project",
    "proof_scope":"functional headless with real disposable save operations; no app/production/user-save/profile migration or visual device claim",
    "engine":engine,"checks_total":sum(s["checks"] for s in summaries.values()),"phases":summaries,
    "candidate_earnings":save,"legacy_load_v1":"OK","legacy_load_v2":"ERR_FILE_CORRUPT","legacy_valid_write_over_v2":"ERR_FILE_CORRUPT",
    "legacy_stage_created":False,"unexpected_scoped_save_paths":False,"import_only_existing_obj_annotations":18,
    "durable_installation":"HOLD, test confirms non-destructive old refusal, not an approved application rollback or namespace",
},indent=2,sort_keys=True))
