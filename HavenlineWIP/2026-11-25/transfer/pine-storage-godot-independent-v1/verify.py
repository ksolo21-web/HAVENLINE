from pathlib import Path
import collections, subprocess, tempfile, hashlib,json,re
B=Path(__file__).resolve().parent.parent
P=B/'hvn-l1-pine-storage-godot-fixture-v1'; R=B/'havenline-tree-regrow.IVOMrj/repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'SHA256SUMS')=='f91cda1421f9f8cc43932edc1435d7f26bde4c1d01a8e220e77c6b3d695f35f6'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=P,check=True)
pin='11c14a1c41971067c7dc97db69375f720a408f68'; path='HavenlineLevel1/'
paths=[path+'previews/integrated_opening.gd',path+'opening_ledger.gd']
patch=B/'hvn-l1-paid-pine-renewal-v1/renewal.patch'
assert sha(patch)=='e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd'
def run(a,**kw):return subprocess.check_output(a,**kw)
with tempfile.TemporaryDirectory(prefix='offline-source-',dir=Path.cwd()) as raw:
 d=Path(raw)
 for rel in paths:
  f=d/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(run(['git','-C',str(R),'show',pin+':'+rel]))
 run(['git','apply',*['--include='+x for x in paths],str(patch)],cwd=d)
 before=(d/paths[0]).read_bytes()
 run(['git','apply',str(P/'fixture.patch')],cwd=d)
 q=d/path/'fixtures/pine_store'; run(['python3',str(P/'source_seam.py'),str(d/path)],cwd=d)
 assert before==(d/paths[0]).read_bytes()
 c=(q/'under_test.gd').read_bytes(); helper=b'\nfunc _fixture_next_ledger() -> Ledger:\n\treturn Ledger.new()\n'
 # Independently ignore added helper and compare individual lines.
 assert c.endswith(helper)
 a,z=before.splitlines(),c[:-len(helper)].splitlines()
 assert len(a)==len(z)
 diff=[(i+1,x.decode().strip(),y.decode().strip()) for i,(x,y) in enumerate(zip(a,z)) if x!=y]
 assert len(diff)==2 and all(x=='var next := Ledger.new()' and y=='var next := _fixture_next_ledger()' for i,x,y in diff)
 assert all('/fixtures/pine_store/' in s for s in re.findall(r'(?m)^\+\+\+ b/(\S+)',(P/'fixture.patch').read_text()))
 ledger=(q/'ledger.gd').read_text(); store=(q/'store.gd').read_text(); output=(q/'opening.gd').read_text()
 assert 'super.restore(data)' in ledger and 'super.restore(legacy)' in ledger
 assert store.index('f.flush()') < store.index('_decode(stage_path())') < store.index('DirAccess.rename_absolute') < store.index('_published_hash = raw.sha256_text()')
 assert 'previous.get("epoch") != _epoch or previous.get("identity") != _published_hash' in store
 assert output.index('save.requested(args)') < output.index('var restored := storage.boot()')
 assert output.index('storage.commit(proposal)') < output.index('return super._commit_opening_progress(proposal)')
 # Actual auth source currently admits deposit only after two, but shape reader is a broader numeric check.
 assert 'ledger.pine_occurrences != 2' in output and 'int(harvest) < 1' in ledger
reports={}
for f in (P/'evidence').glob('*.txt'):
 s=f.read_text(); assert not re.search(r'(?im)^FAIL |^SCRIPT ERROR|^ERROR:|Parse Error',s)
 reports[f.stem]=len(re.findall(r'(?m)^PASS ',s))
 if reports[f.stem] and f.stem!='invalid_owner': assert f'checks={reports[f.stem]} failures=0' in s
assert sum(reports.values())==150
fresh=(P/'evidence/fresh_process_next.txt').read_text(); warm=(P/'evidence/ordinary_deposit.txt').read_text()
assert 'restored five seconds offers no passive award tick=300' in fresh and 'rooted after the final cold-start callback adds no wood tick=301' in fresh
assert 'absent at 299/300 with no reward tick=1245' in warm and 'exact 300 ticks restores visibility only tick=1246' in warm
assert (P/'evidence/native_v2.txt').read_bytes()==(P/'evidence/restart_aborted.txt').read_bytes() # same logical output, not same invocation
print(json.dumps(dict(sealed_source_and_evidence=True,line_changes=diff,total_source_verified_author_checks=150,separate_phase_counts=reports,
 conservative_unreachable_noncanonical_v3_payload=dict(harvest_through=1,carried=0,stored=1,deposit_through=1),
 independent_native_replay=False, fixture_writer_OS_lock_in_launcher_only=True, runtime_ready=False),indent=2))
