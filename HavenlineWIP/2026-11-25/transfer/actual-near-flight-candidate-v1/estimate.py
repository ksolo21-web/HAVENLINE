import json,sys,runpy,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
p=Path('..')
A=json.loads((p/'hvn-l1-storage-optin-e2e-scaffold-v1/offline.json').read_text())
end=json.loads((p/'hvn-l1-wood-storage-near-row-v1/result.json').read_text())['detached_log_transforms']
root=np.array(json.loads((p/'hvn-l1-paid-storage-walkby-v1/result.json').read_text())['near_waypoint_sample']['world'])
B=Rotation.from_euler('y',math.atan2(-1.275,-1.10)).as_matrix()
c=json.loads((p/'hvn-l1-wood-paid-carry-capture-v1/result.json').read_text())
animal=np.array(c['actor_relative_cpu_skin_bounds'])
# Extend old donor AABB beyond the actual old measurement only for offline
# conservative screening. It does not certify the B body or a future idle pose.
animal += np.array([[-.025,-.025,-.025],[.025,.025,.025]])
tri,_=runpy.run_path(str(p/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](Path(sys.argv[1]))
V=np.unique(tri.reshape(-1,3),axis=0); rad=np.linalg.norm(V,axis=1).max()
bounds=lambda P:np.stack([P.min(0),P.max(0)])
def sep(a,b):return max(np.maximum(a[0]-b[1],b[0]-a[1]))
obs={}
for g in c['native']['gates']:
 for leaf in g['leaf_boxes']:
  m=np.abs(np.array(leaf['shape_world']['basis_cols']).T)@(.5*np.array(leaf['size']))
  u=np.array(leaf['shape_world']['origin'])
  obs[g['gate_id']+leaf['hinge']]=np.stack([u-m,u+m])
origins=[np.array(q['estimated_only_anchor_world_m']) for q in A['poses']]
ed=[np.array(x['t_source_to_source_world']) for x in end]
R=[np.array(x['R_source_to_source_world']) for x in end]
local=lambda v:(v-root)@B
out=[]
for i,z in enumerate(A['poses']):
 s,h,m,e=np.array(z['key_positions_m'])
 v0=V@B.T+s;v1=V@B.T+h;v2=V@R[i].T+m;v3=V@R[i].T+e
 fixed2=(V@B.T+origins[1]) if i==0 else (V@R[0].T+ed[0])
 world=[bounds(np.r_[v0,v1]),np.stack([np.minimum(h,m)-rad,np.maximum(h,m)+rad]),bounds(np.r_[v2,v3])]
 loc=[bounds(local(np.r_[v0,v1])),
      np.stack([np.minimum(local(h),local(m))-rad,np.maximum(local(h),local(m))+rad]),
      bounds(local(np.r_[v2,v3]))]
 row=[]
 for j,(x,y) in enumerate(zip(world,loc)):
  row.append({'actor_body_m':sep(y,animal),'leaf_m':min(sep(x,o) for o in obs.values()),
  'other_log_m':sep(y,bounds(local(fixed2))) if j==0 else sep(x,bounds(fixed2))})
 out.append(row)
print(json.dumps({'bound_guard_for_actor_lateral_design_only':out,'production_or_native_approval':False},indent=2))
