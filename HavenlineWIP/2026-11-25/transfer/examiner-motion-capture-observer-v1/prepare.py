from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(__file__).resolve().parent
base=p.parent
stage,art,out=(Path(x).resolve() for x in sys.argv[1:4])
assert not out.is_relative_to(stage) and not out.is_relative_to(art)
def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for k,d in [('hvn-l1-second-turn-guard-substitution-v1','f868760e4aa23fa4c7960e30a7ceea98cc96b2f3f6bb5e0ed21a44ac4f258eec'),
 ('hvn-l1-examiner-two-piece-transfer-native-result-v1','7cfe83f2cdb2c306c7884c1cac2cfaab83e098e4f2f07448bb0232d9b408d051'),
 ('hvn-l1-examiner-uncropped-runway-v1','0f227556b4b53999658d97755160af1942d387997fea392bc98a64401673f32b')]:
 q=base/k
 assert h(q/'SHA256SUMS')==d
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=q,check=True)
assets=json.loads((p/'asset_hashes.json').read_text())
for name,sha in assets['exact_native_import_inputs'].items():assert h(stage/name)==sha
for name,sha in assets['private_conformed_floor_display_inputs'].items():assert h(art/name)==sha
subprocess.run([sys.executable,str(base/'hvn-l1-second-turn-guard-substitution-v1/prepare.py'),str(stage),str(out)],check=True)
old=out.read_text()
assert hashlib.sha256(old.encode()).hexdigest()=='c1958183820d542c862cc8defec2bd374cfa6659e509a9b22e30d24064a39646'
s=old
updates=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a
 updates.append((a,b));s=s.replace(a,b,1)
a='func execute_fixture(near_ok:bool) -> void:'
edit(a,(p/'capture.gdfrag').read_text()+'\n'+a)
a='\tif not live_owner.examine_and_commit(game,"wood",stable_ids,rest,full_proof,"EXAMINER_ONLY_WEST_V1"):'
edit(a,'\tcapture_model_start()\n'+a)
a='\tphase=""\n\tvar elapsed:=0'
edit(a,'\tcapture_flight_sample(0)\n'+a)
a='\t\telapsed+=1\n\tif live_owner._state'
edit(a,'\t\telapsed+=1\n\t\tcapture_flight_sample(elapsed)\n\tif live_owner._state')
out.write_text(s)
for a,b in reversed(updates):
 assert s.count(b)==1;s=s.replace(b,a,1)
assert s==old
