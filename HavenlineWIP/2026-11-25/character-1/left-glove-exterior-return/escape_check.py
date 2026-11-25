"""Independent plane/edge reduction of the six failed real ray probes."""
from pathlib import Path
import gzip,json,hashlib
import numpy as np
p=Path(__file__).resolve().parent
source=p.parent/'hvn-l1-c1-glove-physical-side-v1'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(source/'SHA256SUMS')=='44db716e542ece793bf1a43fb476001f091b57cbf9d938693fb8d67e0c6edefa'
for lane in (source/'SHA256SUMS').read_text().splitlines():
 h,f=lane.split(maxsplit=1);assert sha(source/f)==h
q=np.load(p/'editable_exterior_return.npz'); ids=np.r_[q['original_face_ids'],q['new_face_ids']]
D=dict(zip(ids,q['combined_faces']))
ref=json.loads(gzip.decompress((source/'ray_evidence.json.gz').read_bytes()))
res=json.loads(gzip.decompress((p/'native_rays.json.gz').read_bytes()))
Q=dict(zip(q['new_outer_vertex_ids'],q['new_outer_legacy_vertex_ids']))
assert D[138].tolist()==[115,114,113] and {Q[114],Q[115]}=={86,87}
E=[]
for phase,pose in [('neutral','bind'),('open','open')]:
 retained_old=[]
 for i,rows in res[phase]['repeat_prior_probe'].items():
  for j,(cur,old) in enumerate(zip(rows,ref[phase][i]['measures'])):
   if not cur['old_inward_skin_still_first']:continue
   retained_old.append((i,j))
   assert int(i)==111 and j in (30,32,34)
   A=q[pose]; u=np.array(old['owner_outward_direction_unit']); x=np.asarray(old['bary'])@A[D[111]]
   T=A[D[138]]; n=np.cross(T[1]-T[0],T[2]-T[0]); depth=np.dot(T[0]-x,n)/np.dot(u,n)
   assert depth>0.
   v=x+depth*u
   s,t=np.linalg.lstsq((T[1:]-T[0]).T,v-T[0],rcond=None)[0]; bc=np.array([1-s-t,s,t])
   assert t<0. and min(s,1-s-t)>0.
   ed=T[1]-T[0]; miss=1000*np.linalg.norm(v-(T[0]+ed*np.clip((v-T[0])@ed/(ed@ed),0,1)))
   E.append({'sample':j,'phase':phase,'old_barycentric':old['bary'],'outward_perturbation':old['perturbation'],
             'new_cover_face':138,'nominal_plane_intersection_barycentric':bc.tolist(),'outside_edge_clearance_mm':miss,
             'new_boundary_vertices':[114,115],'corresponding_original_web_edge':[86,87]})
 assert retained_old==[('111',30),('111',32),('111',34)]
out={'failed_original_exposure_geometry':E,'repaired_outside_rims_not_asserted':True,
     'exact_next_required_area':'Coherently author the outer/return turn with existing sheltered theta-web contour and preserved cuff/tip, crossing the measured 86–87 footprint; recheck exact prior rays, sewing polarity, folds and body/tool clearance.'}
(p/'escape_result.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
