"""Read-only existing source/failed pose face topology. No construction or edited mesh."""
import contextlib,hashlib,io,json,sys
from collections import Counter
from pathlib import Path
from runpy import run_path
import numpy as np
root=Path(__file__).resolve().parents[1]
p=root/'hvn-l1-clean-character-grounded-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(p/'SHA256SUMS')=='35481eb615f9b1feed5f98c097607ccb778c64f546b126534ed16d3761e40018'
for ln in (p/'SHA256SUMS').read_text().splitlines():
 h,f=ln.split();assert sha(p/f)==h
i=root/'hvn-l1-clean-v3-independent-mesh-v1'
assert sha(i/'full-candidate.json')=='738cee678cad7a353045b44ea3e72ee777f9ddbd6adadcdcf264b18ebbc46beb'
sys.path.insert(0,str(p))
with contextlib.redirect_stdout(io.StringIO()):E=run_path(str(p/'evaluate.py'))
original=json.loads((i/'full-candidate.json').read_text())
V,TR,I,W,slots,Weld=[E[k] for k in ('V','TR','indices','weights','slots','Weld')]
N=E['N'];Y=E['Y']; rest=E['rest']; sc=E['stock']
P=sorted(E['na']-E['nb']);assert len(P)==original['independent_lower_mesh']['new_pairs']==366
all_fails=np.unique(np.asarray(P).ravel())
G=np.zeros((len(V),len(slots)),float);np.add.at(G,(np.arange(len(V))[:,None],I),W)
Gm=G[TR].mean(1)
j=np.argmax(Gm,axis=1)
regions={}
wids=int(Weld.max()+1)
source_e=np.sort(Weld[TR][:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1)
source_edge_id,source_e_n=np.unique(source_e[:,0].astype(np.int64)*wids+source_e[:,1],return_counts=True)
alldef=set()
for name in slots:
 if name.startswith('Rigid_') and 'Fastener' in name:
  k=slots.index(name)
  # True indexed pure core-to-fabric edge, not nearby AABB or loose visual prop.
  ids=np.flatnonzero((G[TR,k]>.9999).all(1))
  if len(ids):
   e=np.sort(Weld[TR[ids][:,[[0,1],[1,2],[2,0]]]].reshape(-1,2),axis=1)
   unique,c=np.unique(e,axis=0,return_counts=True)
   one=unique[c==1]
   source_n=source_e_n[np.searchsorted(source_edge_id,one[:,0].astype(np.int64)*wids+one[:,1])]
   nboundary=int((source_n>1).sum())
   pure_open_boundary=int((source_n==1).sum())
   regions[name]=dict(pure_core_faces=len(ids),weld_edges_to_neighboring_non_core_faces=nboundary,open_in_original_full_source_edge_count=pure_open_boundary,strict_v3_incident_core_faces=int(np.isin(ids,all_fails).sum()))
T=rest[sc.edges]; X=Y[sc.edges]; lens=np.linalg.norm(T[:,1]-T[:,0],axis=1)
ratio=np.linalg.norm(X[:,1]-X[:,0],axis=1)/np.maximum(lens,1e-12)
arth={};GUARD={}
for side,(boot,_,mass) in E['masks'].items():
 # Scope matches exact previous rig shape gate.
 ok=(mass[sc.edges].mean(1)>.90)&(V[sc.edges,1].mean(1)<.270)&(lens>.0008)
 ed=sc.edges[ok&((ratio<.5)|(ratio>2.))]
 GUARD[side]=ed
 bc=np.sum(G[:,[slots.index(side+'Heel'),slots.index(side+'Ball')]],axis=1)
 articulations={m:N[side+m]['global_bind'][1][3] for m in ['Heel','Ball','CollarFlex','Shin','Hip']}
 arth[side]=dict(original_pose_tail_role_authored_rest_y_m=articulations,actual_bad_strain_edges=len(ed),bad_edges_touch_any_pure_original_heel_or_ball_count=int((bc[ed]>.9999).any(1).sum()))
hood=(V[TR,1]>.330).all(1)
cross=TR[all_fails]
locked_slots=[s for s in slots if s.endswith(('Heel','Ball'))]
fixed=np.max(G[:,[slots.index(k) for k in locked_slots]],axis=1)>.9999
blocked_faces=(fixed[cross]).any(1)
geo=V[TR].mean(1)
coarse=lambda f:('proximal/hem' if geo[f,1]>=.265 else ('ankle/cuff' if geo[f,1]<.131 else 'shin/knee'))
b=Counter(' / '.join(sorted([coarse(a),coarse(c)])) for a,c in P)
end=np.unique(cross)
out=dict(status='READY_SCOPE_MAP_ONLY_NO_APPROVAL_NO_CONSTRUCTION',witnessed_pose_seal=sha(p/'SHA256SUMS'),strict_original_pair_counts=366,exact_failed_union_faces=len(cross),region_pair_counts=dict(b),exact_failed_faces_with_fully_upper_gate=int(hood[all_fails].sum()),exact_failed_faces_touch_pure_locked_heel_or_ball=int(blocked_faces.sum()),exact_failed_vertex_count=len(end),protected_joint_roles=arth,rigid_attachment_core_edge_certificates=regions,exact_first_aperture_witness_faces=[8794,8891],exact_knee_edge_anchor_rows=[36861,36961],no_source_files_modified=True)
print(json.dumps(out,indent=2))
