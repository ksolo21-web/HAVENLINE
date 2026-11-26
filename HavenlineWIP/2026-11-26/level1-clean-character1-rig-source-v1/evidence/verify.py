"""Reopen actual portable binding, independently numerical no-op/role/weld checks."""
import json,sys,struct,hashlib
from pathlib import Path
from scipy.spatial.transform import Rotation
import numpy as np
a,d,rec=map(Path,sys.argv[1:])
sha=lambda x:hashlib.sha256(x).hexdigest()
meta=json.loads(rec.read_text())
raw=a.read_bytes();assert sha(raw)==meta['source_asset']
rig,skin=d/'rig.LOCAL.json',d/'skin.LOCAL.npz'
assert {i.name:sha(i.read_bytes()) for i in [rig,skin]}==meta['local_payload_hashes']
b=json.loads(rig.read_text()); q=np.load(skin,allow_pickle=False)
s,t=struct.unpack_from('<II',raw,12);j=json.loads(raw[20:20+s]);offs=28+s
p=j['accessors'][j['meshes'][0]['primitives'][0]['attributes']['POSITION']];v=j['bufferViews'][p['bufferView']]
X=np.frombuffer(raw,'<f4',count=p['count']*3,offset=offs+v.get('byteOffset',0)+p.get('byteOffset',0)).reshape(-1,3)
I,W=q['joints'],q['weights'].astype(float); assert np.min(W)>=0 and np.allclose(W.sum(1),1.,atol=2e-7,rtol=0)
assert np.max(I)<len(b['weighted_slots']) and I.shape==(len(X),4)
B={k:np.asarray(x['global_bind']) for k,x in b['new_bones'].items()}
inv0=np.array([np.linalg.inv(B[k]) for k in b['weighted_slots']])
def full(overrides):
 p={}
 for n,k in b['new_bones'].items():
  if k['parent'] is None:M=B[n]
  else:M=p[k['parent']]@np.asarray(k['local_bind'])
  p[n]=(overrides[n]@M) if n in overrides else M
 return np.array([p[k] for k in b['weighted_slots']])@inv0
_,weld=np.unique(np.round(X,6),axis=0,return_inverse=True)
ii=np.zeros((max(weld)+1,4),I.dtype); ww=np.zeros((max(weld)+1,4))
ii[weld]=I;ww[weld]=W
assert np.array_equal(ii[weld],I) and np.array_equal(ww[weld],W)
A=np.column_stack([X,np.ones(len(X))])
def apply(M):
 return sum(W[:,k,None]*(M[I[:,k]]@A[:,:,None])[:,:3,0] for k in range(4))
Y=apply(full({}));err=np.max(np.linalg.norm(Y-X,axis=1))
assert err<1.2e-7
controls={}
for s in 'LR':
 ball=s+'Ball';heel=s+'Heel'
 fire=B[ball][:3,3];M=np.eye(4);M[:3,:3]=Rotation.from_euler('x',3,degrees=True).as_matrix();M[:3,3]=fire-M[:3,:3]@fire
 B0=full({ball:M});E=apply(B0)-Y
 toe_slot=b['weighted_slots'].index(ball);heel_slot=b['weighted_slots'].index(heel)
 wt=(W*(I==toe_slot)).sum(1);h=(W*(I==heel_slot)).sum(1)
 opposite=[i for i,n in enumerate(b['weighted_slots']) if n.startswith(('R' if s=='L' else 'L')) and any(n.endswith(k) for k in ('Heel','Ball','Shin','CollarFlex'))]
 other=np.sum(W*np.isin(I,opposite),axis=1)>.9999
 toe=np.linalg.norm(E[wt>.9999],axis=1)

 locked=((h>.9999)|other)&(wt==0)
 leak=float(np.max(np.abs(E[(h>.9999)|other])))
 assert len(toe)>10 and np.max(toe)>1e-3 and np.max(np.abs(E[locked]))<1e-8 and leak<1e-6
 controls[s]=dict(pure_ball_rows=len(toe),pure_heel_rows=int((h>.9999).sum()),actual_ball_max_mm_at_3deg=float(toe.max()*1000),unchanged_zero_ball_influence_heel_other_leg_rows=int(locked.sum()),near_pure_other_region_cross_signal_max_mm=leak*1000)
print(json.dumps(dict(status='NEUTRAL_AND_INDEPENDENT_TOE_CONTROL_ONLY',moved_mesh_or_weights_in_source=False,rest_noop_max_mm=float(err*1000),original_stock_asset=sha(raw),weld_joint_weight_equality=True,independent_ball_controls=controls,no_native_or_quality_score=True),indent=2))
