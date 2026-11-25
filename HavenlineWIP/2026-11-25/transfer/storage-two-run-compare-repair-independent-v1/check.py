from pathlib import Path
import hashlib,subprocess,json,runpy
root=Path(__file__).resolve().parent.parent
p=root/'hvn-l1-storage-two-run-compare-repair-v1'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='6db033c0878089d7cccc82092a4b79d43cd672bdecc8261418922124af162346'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
r=root/'hvn-l1-storage-two-run-admission-result-v1'
assert hashlib.sha256((r/'SHA256SUMS').read_bytes()).hexdigest()=='a2a143c6c1884cd4e948518668ae9080c1bc26a9672f90dda1b7616ba4ed8d4f'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=r,check=True)
a,b=((r/k).read_text() for k in ['A.log','B.log'])
new=runpy.run_path(str(p/'compare.py'))['phases']
old=runpy.run_path(str(root/'hvn-l1-storage-two-run-admission-native-v1/compare.py'))['phases']
assert new(a,b)==old(a,b)==json.loads((r/'result.json').read_text())
w=[l for l in a.splitlines() if l.startswith('WALK_OBSTRUCTION ')]
b2=b.replace(w[0],w[1]); assert old(a,b2)==old(a,b)
def denied(a,b,msg):
 try:new(a,b)
 except ValueError as e:assert msg in str(e),e
 else:raise AssertionError('accepted')
denied(a,b2,'B warning differs')
sl=[l for l in a.splitlines() if l.startswith('PFX_A_STATUS ')][0]
s=json.loads(sl.split(' ',1)[1]); x,y=s['turn_records']
# Same exact two genuine collider paths (including shape indices), wrong pairing to otherwise real warnings.
x['ids'],y['ids']=y['ids'],x['ids']
a2=a.replace(sl,'PFX_A_STATUS '+json.dumps(s,separators=(',',':')))
assert old(a2,b)==old(a,b); denied(a2,b,'A obstacle differs')
print(json.dumps({'genuine_output_identical':True,'later_warning_rejected':True,'swapping_expected_A_shape_associations_rejected':True,'dispatch':False},indent=2))
