"""Reduce controller's successful result and native stdout into independent portable custody facts."""
import hashlib
import json
import re
import sys
from pathlib import Path

p=Path(sys.argv[1])
result=json.loads((p/"result.json").read_text())
files={"old-import","new-import","old-generate","new-earn","new-cold","old-read-a"}
assert {x.stem for x in p.glob("*.log")}==files
assert all(result[k] is True for k in ("a_original_v1_read_unchanged","backup_v_verified_unchanged","b_copied_v1_byte_for_byte","b_cold_v2_once","no_cross_role_launch","no_raw_profiles_in_result"))
S=result["state_hashes"]
assert S["a_preserved_paid_v1_sha256"]==S["v_backup_sha256"]!=S["b_upgraded_v2_sha256"]
assert all(re.fullmatch(r"[0-9a-f]{64}",v) for v in S.values())
assert len(result["guard_explicit_denials_before_launch"])==11
assert result["guard_explicit_denials_before_launch"]["upgraded-b-rejected-by-old-router"]=="wrong-minted-role-path"
assert result["guard_explicit_denials_before_launch"]["wrong-b-digest"]=="wrong-provenance-digest"
checks=[("old-generate","old_writer","combined cold fixture"),("new-earn","new_earn","PINE_FORK_CANDIDATE"),("new-cold","new_cold","PINE_FORK_CANDIDATE")]
versions=set(); out={"import_only_diagnostics":{},"engine_logs_sha256":{}}
for name in files:
    raw=(p/(name+".log")).read_bytes();log=raw.decode("utf-8")
    bits=re.findall(r"^Godot Engine (v4\.7\.2\.stable\.official\.[a-z0-9]+) ",log,re.M)
    assert len(bits)==1
    versions.add(bits[0])
    bad=[x for x in log.splitlines() if re.search(r"ERROR:|WARNING:|^FAIL |Parse Error",x,re.I)]
    if name.endswith("-import"):
        assert len(bad)==18 and all(re.fullmatch(r"WARNING: OBJ: Ambient light for material '(board|board_warm|board_soft|beam|brace_back|snow|metal|rope|rope_dark)' is ignored in PBR",l) for l in bad)
        out["import_only_diagnostics"][name]=len(bad)
    else:
        assert not bad
    out["engine_logs_sha256"][name]=hashlib.sha256(raw).hexdigest()
assert len(versions)==1
for name,key,expected in checks:
    log=(p/(name+".log")).read_text()
    m=re.findall("^"+expected+r" checks=(\d+) failures=0$",log,re.M)
    assert len(m)==1 and int(m[0])==result["checks"][key]==len(re.findall(r"^PASS ",log,re.M))
assert "PINE_FORK_OLD_READ preserved_paid_v1=true" in (p/"old-read-a.log").read_text()
assert "first actual paid repeat advances cloned profile to v2 plus one" in (p/"new-earn.log").read_text()
assert "fresh candidate restores earned +1 without regrowth credit or rewrites" in (p/"new-cold.log").read_text()
assert "last hidden tick to rooted transition at the exact timer boundary" in (p/"new-earn.log").read_text() and "last hidden tick to rooted transition at the exact timer boundary" in (p/"new-cold.log").read_text()
out.update(result);out["engine"]=next(iter(versions))
out["functional_assertions_total"]=sum(result["checks"].values())
out["scope"]="disposable branch selection, not legacy v2 upgrade/downgrade, production namespacing, or old-app test"
print(json.dumps(out,indent=2,sort_keys=True))
