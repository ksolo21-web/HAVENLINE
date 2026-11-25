from pathlib import Path
import hashlib,subprocess,sys,tempfile,json,re
r=Path(__file__).resolve().parent.parent
def pin(n,h):
 p=r/n
 assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
 return p
s=pin('hvn-l1-second-turn-guard-substitution-v1','f868760e4aa23fa4c7960e30a7ceea98cc96b2f3f6bb5e0ed21a44ac4f258eec')
o=pin('hvn-l1-examiner-two-piece-transfer-native-result-v1','7cfe83f2cdb2c306c7884c1cac2cfaab83e098e4f2f07448bb0232d9b408d051')
with tempfile.TemporaryDirectory(dir=Path.cwd()) as t:
 f=Path(t)/'examiner.gd'; subprocess.run([sys.executable,str(s/'prepare.py'),str(Path(sys.argv[1]).resolve()),str(f)],check=True,stdout=subprocess.DEVNULL)
 assert hashlib.sha256(f.read_bytes()).hexdigest()==(o/'compiled.sha256').read_text().strip()=='c1958183820d542c862cc8defec2bd374cfa6659e509a9b22e30d24064a39646'
 code=f.read_text()
assert code.count('.reparent(')==1 and '_pieces=local_nodes' in code and '_piece_ids=expected_ids.duplicate()' in code
assert 'child.get_instance_id()!=expected_ids[i]' in code and '_pieces[i].get_instance_id()!=_piece_ids[i]' in code
assert 'item.global_transform!=Examiner.FROZEN_REST[i]' in code and '_frame>=t0+int(_story[1].ages[3])' in code
assert 'exact_obstacles()!=expected_world_obstacles' in code and 'not expected_body.encloses(actor[0])' in code
assert 'before!=var_to_bytes(game.ledger.snapshot())' in code and '_native_bytes!=var_to_bytes(_native_game.ledger.snapshot())' in code
assert 'var wrong: Array[int]=[stable_ids[1],stable_ids[0]]' in code and '"stone",stable_ids' in code and ',rest,Callable(),' in code and 'EXAM_HOLD duplicate' in code
assert all(f'if i=={i} and k==1:' in code for i in range(2))
txt=(o/'native.log').read_text()
previous=(r/'hvn-l1-actual-near-flight-first-result-v1/native.log').read_text()
assert not re.search(r'(?m)^(?:SCRIPT ERROR|ERROR:|WARNING:|EXAM_HOLD|FAIL )',txt)
pfx=lambda x:re.findall(r'(?m)^PFX_OBS (\d+) ([a-f0-9]{64})$',x)
assert pfx(txt)==pfx(previous) and [int(i) for i,_ in pfx(txt)]==list(range(1277,1334))
def row(tag):
 x,=re.findall(r'(?m)^'+tag+r' (.*)$',txt); return json.loads(x)
p1,p2=[row('EXAM_'+i+'_MID_SUPPORT') for i in ('FIRST','SECOND')]
assert p1['unchanged_input_sha256']==p2['unchanged_input_sha256']=='b7342b6936f2d203d29587c9302d60c7a6e43b67a4113c52971b84a3bef28716'
for p in (p1,p2):
 assert p['old_bound_still_negative_m']<0 and p['minimum_fixed_local_minus_x_clearance_m']>.098 and p['cell_count']==2048 and p['vertices']==834
 assert all(abs(x-.025)<1e-8 for x in p['pad_m'])
q=row('EXAM_QUALIFIED'); assert q==json.loads((o/'result.json').read_text())['qualified']
assert q['mode']=='EXAMINER_SHADOW_ONLY' and q['same_two_view_objects'] and q['no_native_book_delta']
assert (q['shadow_carry_wood'],q['shadow_stored_wood'],q['typed_claim_highwater'])==(0,2,1)
assert q['nominal_ticks']==130+6+130==266
assert q['park_view']=={'headless_sample_no_pixel_readability':True,'hull_gap_native_screen_units':6.8028564453125,'vertex_clear_rays':1682}
print(json.dumps(dict(bridge_matches=True,prior_hash_match=57,guard_narrow_at_each_middle_turn=True,one_reparent_per_original=True,
 actual_book_unchanged=True,shadow=[0,2,1],nominal_60hz_ticks=266,diagnostic_seconds=266/60,graphics_or_runtime_promotion=False),indent=2))
