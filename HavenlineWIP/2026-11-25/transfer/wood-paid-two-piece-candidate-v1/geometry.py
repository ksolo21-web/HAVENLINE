import pathlib,sys,hashlib,json,runpy,subprocess
import numpy as np
p=pathlib.Path('../hvn-l1-wood-paid-carry-capture-v1')
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='af819aeb459d6835f43f1f5f015d78abc6916a561b3c3cd7190dfe08eb6a1b98'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
r=json.loads((p/'result.json').read_text())
q=r['native'];assert q['wood_stock']==2
f=q['original_fit'];low=np.array(f['position']);high=low+f['size'];center=(low+high)/2
d=runpy.run_path('../hvn-l1-transfer-crown-spacing-v1/audit.py')['decode']
T,_=d(pathlib.Path(sys.argv[1]));assert len(T)==1300
a,b=T.min((0,1)),T.max((0,1));c=(a+b)/2
mm=[]
for i in range(2):
 off=center-c+np.array([0,0,(i-.5)*.105])
 lo=a+off;hi=b+off
 assert (lo>=low).all() and (hi<=high).all()
 mm.append({'local_origin_m':off.tolist(),'bounds_m':[lo.tolist(),hi.tolist()],'margin_min_xyz_m':np.minimum(lo-low,high-hi).tolist()})
bodygap=r['actor_relative_cpu_skin_bounds'][0][2]-mm[1]['bounds_m'][1][2]
pair=mm[1]['bounds_m'][0][2]-mm[0]['bounds_m'][1][2]
assert bodygap>.077 and pair>.001
print(json.dumps({'exact_archived_paid_body_only_gap_m':bodygap,'pair_axis_gap_m':pair,'fit':mm,'source_scope':'old idle exact pulse; no native patched preview result yet'},indent=2))
