from pathlib import Path
import numpy as np,json
p=Path(__file__).resolve().parent
d=np.load(p/'pose-inputs.npz'); stats=json.loads((p/'solve-report.json').read_text())
out=[]
for i,c in enumerate(stats['source_keys']):
 row={}
 for side,ends in c['edge_provenance'].items():
  row[side]={}
  for kind,b in ends.items():
   ids=b['verts'];w=d['weights'][:,ids].T
   w=w/np.maximum(1e-12,w.sum(1,keepdims=True))
   S=d['skin_world'][i]
   X=d['rest'][ids]/d['scale']+d['offset']
   TS=np.einsum('bmn,vn->vbm',S,np.column_stack((X,np.ones(2))))[:,:,:3]
   zs=(np.einsum('vb,vbm->vm',w,TS)-d['offset'])*d['scale']
   err=float(np.linalg.norm(zs-d['xyz'][i,ids],axis=-1).max())
   # Difference with held edge-average weights versus changing row weights:
   # Delta y = avg weights·(T_j x_b−T_j x_a) +
   # delta weights·avg(T_j x_b+T_j x_a).
   mean=.5*(w[0]+w[1])
   diff=w[1]-w[0]
   same=mean@(TS[1]-TS[0])*d['scale']
   contrast=diff@((TS[0]+TS[1])*.5)*d['scale']
   assert np.linalg.norm(same+contrast-(zs[1]-zs[0]))<1e-10
   assert err<2e-6
   rv=float(np.linalg.norm(d['rest'][ids[1]]-d['rest'][ids[0]]))
   row[side][kind]={'edge_i':b['edge_i'],'identity_error_um':err*1e6,'rest_edge_mm':rv*1e3,
     'held_average_weight_ratio':float(np.linalg.norm(same)/rv),'exact_pose_ratio':b['ratio'],
     'contrast_size_to_rest_ratio':float(np.linalg.norm(contrast)/rv),'contribution_dot':float(np.dot(same,contrast)/rv**2)}
 out.append(row)
print(json.dumps(out,indent=2))
