"""Source-only intake of the exact frozen paid-pine feature; never starts Godot or opens saves."""
import hashlib,json,re,subprocess,sys,tempfile
from pathlib import Path

author, independent, repo = map(lambda p: Path(p).resolve(),sys.argv[1:4])
base="11c14a1c41971067c7dc97db69375f720a408f68"
tree="d764a05246cbff96983aa27af17e2e919a946ae0"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(["git","-C",repo,*args])
def sealed(d,h):
    assert sha(d/"SHA256SUMS")==h
    for line in (d/"SHA256SUMS").read_text().splitlines():
        digest, name=line.split(maxsplit=1)
        assert sha(d/name)==digest
sealed(author,"2939ea7d5a82461840888791619fd4ecc0eb41d6f6371cfc4170554de94d5a2f")
sealed(independent,"f4ca5871f9d30c8be7c6a186a96ed8ef9d5912042336b70e6ee0d03c75b8393b")
patch=author/"renewal.patch"
assert sha(patch)=="e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd"
assert git("rev-parse",base+":HavenlineLevel1").decode().strip()==tree
remote=Path(__file__).with_name("REMOTE-RUNTIME-GIT-BLOBS")
for line in remote.read_text().splitlines():
    blob,path=line.split(maxsplit=1)
    assert git("rev-parse",f"{base}:{path}").decode().strip()==blob
old={}
for path in ("project.godot","opening_ledger.gd","opening.gd","opening_save.gd","resource_tree.gd",
             "previews/integrated_opening.gd","previews/integrated_opening.tscn","tests/test_integrated_disposable_opening.gd","tests/fixture_integrated_disposable_opening.gd"):
    old[path]=git("show",f"{base}:HavenlineLevel1/{path}")
new_paths=["tests/test_paid_pine_renewal.gd","tests/paid_pine_spy.gd"]
write=[m for m in re.findall(r"^\+\+\+ b/HavenlineLevel1/(.+)$",patch.read_text(),re.M)]
assert write==["opening_ledger.gd","previews/integrated_opening.gd",*new_paths]
with tempfile.TemporaryDirectory(prefix="detached-source-check-",dir="..") as s:
    s=Path(s)
    es=s/"HavenlineLevel1"
    for p,data in old.items():
        (es/p).parent.mkdir(parents=True,exist_ok=True)
        (es/p).write_bytes(data)
    for opt in (["--check"],[]):
        subprocess.run(["git","apply",*opt,str(patch)],cwd=s,check=True,capture_output=True)
    changed={p:sha(es/p) for p in write}
    assert sorted(p.relative_to(es).as_posix() for p in es.rglob("*") if p.is_file())==sorted(set([*old,*new_paths]))
    for p,data in old.items():
        assert ((es/p).read_bytes()!=data)==(p in write)
    target=(es/"previews/integrated_opening.gd").read_text()
    ledger=(es/"opening_ledger.gd").read_text()
    saved=(es/"opening_save.gd").read_text()
    assert 'data.version = 2' in ledger and "if pine_occurrences > 0:" in ledger
    assert 'if data.size() == 5 and _whole(data.get("version"), 2)' in ledger
    assert 'elif data.size() != 4 or not _whole(data.get("version"), 1)' in ledger
    assert '_whole(stock.get("wood"), pine_occurrences)' in ledger
    assert "func _record_paid_pine" in ledger and "stock.wood += 1" in ledger
    assert 'persist_requested = save.requested(args)' in target
    assert '"opening-v3.json"' in saved and '"opening-v3.stage"' in saved
    assert 'const PREFIX := "havenline-l1-v3-"' in saved
    assert 'const SENTINEL := "L1-DISPOSABLE"' in saved
    assert "if not ledger.restore(JSON.parse_string(payload)):" in saved
    assert "else ERR_FILE_CORRUPT" in saved
    assert "and _decode(primary_path).is_empty():\n\t\treturn ERR_FILE_CORRUPT" in saved
    assert 'data.size() != 4 or not _whole(data.get("version"), 1)' in old["opening_ledger.gd"].decode()
    assert "save.requested" not in old["previews/integrated_opening.gd"].decode()
    assert 'persist_blocked = true' in old["tests/fixture_integrated_disposable_opening.gd"].decode()
    assert re.search(r"run/main_scene=\"res://opening\.tscn\"",old["project.godot"].decode())
result=json.loads((author/"result.json").read_text())
old_counts={"late_payment":21,"nostalgic":34,"restored_cold":23,"restored_route_first":94}
for label,n in old_counts.items():
    p=author/"evidence"/(label+".txt")
    row=result["records"][label]
    assert row["author_checks_pass"]==n and row["author_checks_fail"]==row["status_code"]==0
    assert sha(p)==row["sanitized_log_sha256"] and not row["engine_errors"]
obs=(independent/"replay-sanitized.log").read_text()
assert len(re.findall(r"^PASS ",obs,re.M))==63 and "INDEPENDENT_COUNT" in obs
print(json.dumps({
    "classification":"offline pinned source/application preflight; historical native evidence not rerun",
    "baseline":base,"tree":tree,"detached_patch_only_paths_new_hashes":changed,
    "authorized_mechanic":{"source":"same original starter pine","paid_repeat_yield":1,
        "eligibility":"first accepted strike after published hearth; prepayment-started repeat cannot be relabeled",
        "regrowth_seconds":5,"receipt_cost_wood_preserved":3},
    "archived_native_checks":{"author":old_counts,"separate_independent":63,"separate_independent_cold_repeat_rerun":False},
    "bound_current_runtime_source_unchanged":True,
    "source_derived_downgrade":{
        "older_integrated_scene_no_profile_reader":True,
        "older_save_active_reader_decodes_payload_v2_as_corrupt_not_eof":True,
        "older_save_writer_does_not_replace_undecodable_primary":True,
        "patched_reader_accepts_v1_then_v2_after_first_paid_repeat":True,
        "default_scene_unchanged_by_candidate":True,
        "new_separate_profile_namespace_implemented_or_authorized":False,
        "backup_or_downgrade_conversion_implemented_or_authorized":False},
    "promotion":"HOLD: branch only holds detached proof; no shared/live profile, app promotion, downgrade data loss or new gameplay mechanism authorized"
},sort_keys=True,indent=2))
