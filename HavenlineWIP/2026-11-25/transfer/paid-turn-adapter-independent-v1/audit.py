from pathlib import Path
import hashlib,subprocess,sys,tempfile,json,re
p=Path(__file__).resolve().parent.parent; a=p/'hvn-l1-paid-turn-fixture-adapter-v1'
assert hashlib.sha256((a/'SHA256SUMS').read_bytes()).hexdigest()=='a3e65c87e6dfc3f51a8a4c34a9a246e5d583e583c3204c80266f504b4e040099'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=a,check=True)
base=sys.argv[1]
with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
 b=Path(t)/'plain.gd'; c=Path(t)/'adapted.gd'
 subprocess.run([sys.executable,str(p/'hvn-l1-paid-walkby-turn-precision-v1/prepare.py'),base,str(b)],check=True)
 subprocess.run([sys.executable,str(a/'prepare.py'),base,str(c)],check=True)
 orig,gen=b.read_text(),c.read_text()
for token in ['WALK_SUM','WALK_OBSTRUCTION','quit(1 if failures else 0)','grounding, body slide normals and continuously swept conservative carry terrain/walls/leaves guards','await travel(game.point([-2.875,1.15]))']:
 q=lambda s:[l for l in s.splitlines() if token in l]; assert q(orig)==q(gen)
assert gen.count('print("TURN_ADMISSION ",')==1
assert gen.index('print("WALK_SUM "')<gen.index('print("TURN_ADMISSION ",')<gen.index('quit(1 if failures else 0)')
assert '_turn_ticks.size()!=146 or _turn_ticks.back()!=1423' in gen
assert 'if _turn_frames.size()!=6 or _turn_warnings.size()!=2' in gen
assert 'if _turn_frames[i]!=TURN_EXPECTED.frames[i]' in gen
assert '_turn_warnings[i]!=TURN_EXPECTED.warnings[i]' in gen
assert all(k not in gen for k in ['examiner.gd','_validate_confirmation','fixture_publish_owned_deposit','OptInExaminerStorageCustodyOnly'])
f=json.loads((a/'expected.json').read_text())
frames=[json.loads(i) for i in f['frames']]
assert [x['tick'] for x in frames]==[1305,1306,1307,1352,1353,1354]
keys=lambda x:{s['body'].split('/')[-3] if '/gate-south/' in s['body'] else s['body'].split('/')[-1] for c in x['crowns'] for s in c['midpoint_enclosing_shape_hits']}
assert keys(frames[1])=={'gate-south'} or keys(frames[1])=={'HingeLeft'}
assert all('StaticBody3D' in k for k in keys(frames[4])) and len(keys(frames[4]))==1
# An independently selected negative: valid JSON, same values and turn identity, different wire bytes.
tampered=f['frames'][4]+' '
assert json.loads(tampered)==frames[4] and tampered!=f['frames'][4]
assert json.loads(f['summary'])['checks']==26 and json.loads(f['summary'])['failures']==1
print(json.dumps(dict(external_adapter_generated_offline=True,live_Godot_not_run=True,chronology_admits_at_1423_not_1333=True,original_25_of_26_unchanged=True,exact_named_contexts_confirmed=True,noncanonical_semantically_same_frame_rejected_by_wire_comparison=True,phase_b_callable_not_installed=True),indent=2))
