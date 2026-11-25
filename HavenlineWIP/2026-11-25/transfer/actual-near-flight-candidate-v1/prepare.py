from pathlib import Path
import subprocess,hashlib,json,re,sys
p=Path(__file__).resolve().parent;root=p.parent
stage,out=Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve()
assert not out.is_relative_to(stage)
pins={'hvn-l1-storage-two-run-admission-result-v1':'a2a143c6c1884cd4e948518668ae9080c1bc26a9672f90dda1b7616ba4ed8d4f',
'hvn-l1-storage-optin-e2e-scaffold-v1':'a40f0f20e4a2112a59970f9dcd111a07a6c28efc34c6638a0435ec1c630d71ee',
'hvn-l1-storage-two-run-admission-native-v1':'96239426d0de1d747f531b43e11eeb1568801127ab3ff03ac167fd1229e24689',
'hvn-l1-wood-storage-near-row-v1':'b8f6061ab8f7b685beda4629ade265407b7bd5e5dfc649b2197a9b902b8767d6'}
for d,sha in pins.items():
 q=root/d
 assert hashlib.sha256((q/'SHA256SUMS').read_bytes()).hexdigest()==sha
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=q,check=True)
subprocess.run([sys.executable,str(root/'hvn-l1-storage-two-run-admission-native-v1/prepare.py'),str(stage),str(out)],check=True)
old=out.read_text()
assert hashlib.sha256(old.encode()).hexdigest()=='b825ce8315f2f1a119baaac2e9f6c2dced96708ac00d04e1a6d74f19f081a524'
data=(root/'hvn-l1-storage-two-run-admission-result-v1/A.log').read_text().splitlines()
prefix=[line.split()[1:] for line in data if line.startswith('PFX_OBS ')]
assert len(prefix)==57
assert all(int(t)==1277+i and re.fullmatch('[0-9a-f]{64}',q) for i,(t,q) in enumerate(prefix))
prefix='{'+','.join(f'{t}:"{q}"' for t,q in prefix)+'}'
turns=json.loads(next(l.split(' ',1)[1] for l in data if l.startswith('PFX_A_STATUS ')))['turn_records']
assert [d['tick'] for d in turns]==[1306,1353]
def gd(d):
 v=d['foot_quantized'];x=','.join(str(e/1e5) for e in v)
 return str(d['tick'])+':{"foot":Vector3('+x+'),"sphere":'+str(d['original_safe_fraction'])+',"observed_obstacle_ids":'+json.dumps(d['ids'])+',"swept_oriented_clearance_m":'+str(d['oriented_clearance'])+'}'
cert='{'+','.join(map(gd,turns))+'}'
src=(root/'hvn-l1-storage-optin-e2e-scaffold-v1/examiner.gd').read_text().splitlines()
assert src[0]=='extends RefCounted'
exam='class Examiner:\n\textends RefCounted\n'+'\n'.join('\t'+l if l else '' for l in src[1:])
guard=(p/'guard.gdfrag').read_text().replace('@TURNS@',cert).replace('@PREFIX@',prefix)
s=old;edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a
 edits.append((a,b));s=s.replace(a,b,1)
edit('func fixed_obs(x:float) -> int:',exam+'\n'+guard+'\nfunc fixed_obs(x:float) -> int:')
a='\tprint("PFX_OBS ", tick_count, " ", JSON.stringify(row,"",true,true).sha256_text())'
edit(a,'\tprefix_trial_digest=JSON.stringify(row,"",true,true).sha256_text()\n\tphase_flight_prefix()\n'+a)
edit('\t\tquit(0 if hold else 14)\n\t\treturn','\t\tawait execute_fixture(hold)\n\t\treturn')
edit('print("PFX_B_STATUS ",','print("EXAM_ADMISSION_PREFIX ",')
edit('if OS.get_environment(OBS_MODE) not in ["A","B"]:', 'if OS.get_environment(OBS_MODE)!="B":')
out.write_text(s)
for a,b in reversed(edits):
 assert s.count(b)==1;s=s.replace(b,a,1)
assert s==old
