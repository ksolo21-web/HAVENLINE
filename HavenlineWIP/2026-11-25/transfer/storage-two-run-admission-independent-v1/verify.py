from pathlib import Path
import json,hashlib,subprocess,tempfile,runpy,re,sys
B=Path(__file__).resolve().parent.parent
def packet(n,h):
 d=B/n
 assert hashlib.sha256((d/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=d,check=True)
 return d
n=packet('hvn-l1-storage-two-run-admission-native-v1','96239426d0de1d747f531b43e11eeb1568801127ab3ff03ac167fd1229e24689')
r=packet('hvn-l1-storage-two-run-admission-result-v1','a2a143c6c1884cd4e948518668ae9080c1bc26a9672f90dda1b7616ba4ed8d4f')
assert (r/'exits.txt').read_text().strip()=='A=1 B=0 wrapper=0'
with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
 s=Path(t)/'bridge.gd'; subprocess.run([sys.executable,str(n/'prepare.py'),sys.argv[1],str(s)],check=True)
 raw=s.read_bytes(); assert hashlib.sha256(raw).hexdigest()==(r/'bridge.sha256').read_text().strip()
s=raw.decode(); assert 'game.fixture_publish_owned_deposit' not in s and '.reparent(' not in s
assert '_turn_frames[j]==TURN_EXPECTED.frames[j]' in s and '_turn_warnings[0]==TURN_EXPECTED.warnings[0]' in s
launch=(n/'run.sh').read_text();assert 'run_native B' in launch and launch.index('run_native A') < launch.index('--require-a') < launch.index('run_native B')
assert 'HVN_EXAMINER_FIXTURE_MODE="$k"' in launch and '"$w/"' not in launch
A=(r/'A.log').read_text(); B2=(r/'B.log').read_text()
def parsed(src,tag):return [json.loads(l[len(tag)+1:]) for l in src.splitlines() if l.startswith(tag+' ')]
def pfx(src):return {int(j):h for l in src.splitlines() if l.startswith('PFX_OBS ') for _,j,h in [l.split()]}
a,b=pfx(A),pfx(B2);assert list(a)==list(b)==list(range(1277,1334)) and a==b
old,=parsed(A,'WALK_SUM'); assert old['checks']-old['failures']==25 and old['obstructed_ticks']==2
warnings=parsed(A,'WALK_OBSTRUCTION');assert [w['tick'] for w in warnings]==[1306,1353] and parsed(B2,'WALK_OBSTRUCTION')==warnings[:1]
sa,=parsed(A,'PFX_A_STATUS');sb,=parsed(B2,'PFX_B_STATUS')
for z in sa,sb:assert z['request_dispatched'] is False
left,right=sa['turn_records']; assert '/gate-south/HingeLeft/' in left['ids'][0] and '/@StaticBody3D@18#shape:0' in right['ids'][0]
assert all(len(z['ids'])==1 for z in [left,right])
assert abs(left['oriented_clearance']-.06017768240300922)<1e-12 and abs(right['oriented_clearance']-.5362512348739141)<1e-12
assert parsed(A,'PFX_NEAR')==parsed(B2,'PFX_NEAR') and sb['native_tick_end']==1333
co=runpy.run_path(str(n/'compare.py'))['phases']; assert co(A,B2)==json.loads((r/'result.json').read_text())
# Targeted anti-evidence substitution: same ordinary hashes/status and warning count,
# but the reported B event becomes the other later warning. Standalone reducer is
# not an authority; the native B live context comparison would not admit it.
bad=re.sub(r'(?m)^WALK_OBSTRUCTION .+$','WALK_OBSTRUCTION '+json.dumps(warnings[1],separators=(',',':')),B2)
assert parsed(bad,'WALK_OBSTRUCTION')==warnings[1:] and co(A,bad)==co(A,B2)
print(json.dumps(dict(independent_source_identity=True,A_exit_1_historical_25_of_26=True,A_two_narrow_boxes_only=True,B_fresh_no_cross_process_ids=True,matched_quantized_prefix_ticks=57,
 observed_admission_only_no_dispatch=True,mutated_B_wrong_warning_accepted_by_standalone_reducer=True,mutated_B_wrong_warning_disagrees_with_strict_native_context=True),indent=2))
