"""One counter-local near-side stock presentation study; no scene edit."""
import contextlib,io,runpy,sys,json,hashlib
from pathlib import Path
import numpy as np
checker,root,raw=map(Path,sys.argv[1:]); argv=sys.argv[:]
assert hashlib.sha256(checker.read_bytes()).hexdigest()=="bac196184a601ef867b58baf81f9018949ca2cc46d7b2faf3f828d4ff87b8864"
sys.argv=[str(checker),str(root),str(raw)]
with contextlib.redirect_stdout(io.StringIO()): w=runpy.run_path(str(checker))
sys.argv=argv
tri=w['tri']; plank=w['surfaces'][2]; old=w['M'][2]
def pierce(O,T,G):
 D=T-O; e=G[:,1]-G[:,0]; f=G[:,2]-G[:,0]
 P=np.cross(D,f); det=np.einsum("ij,ij->i",e,P); X=O-G[:,0]; Q=np.cross(X,e)
 with np.errstate(invalid="ignore",divide="ignore"):
  a=np.einsum("ij,ij->i",X,P)/det;b=(Q@D)/det;c=np.einsum("ij,ij->i",f,Q)/det
 with np.errstate(invalid="ignore"):
  ok=(abs(det)>1e-11)&(a>=-1e-9)&(b>=-1e-9)&(a+b<=1+1e-9)&(c>0)&(c<1)
 I=np.flatnonzero(ok)
 if not len(I):return None,None
 j=int(I[np.argmin(c[I])]);return j,O+D*c[j]
inside=w['got'][0]['measurements']; pivots={key:w['infer'](np.array([inside[key+':'+name]['straight_pivot_distance_m'] for name in w['marker_names']]),1)[0] for key in ('L_Hand','R_Hand')}
def assess(pts):
 res={}
 for key,P in pivots.items():
  i,h=pierce(P,pts,tri); length=float(np.linalg.norm(pts-P))
  res[key]=dict(distance_m=length,earlier_hit_distance_m=float(np.linalg.norm(h-P)) if h is not None else None,
                earlier_hit_triangle=i, blocked_1cm=bool(h is not None and np.linalg.norm(h-P)<length-.01))
 return res
base_idx,base=pierce(old+np.array([0,.04,0]),old-np.array([0,.04,0]),plank)
assert base_idx is not None and abs(base[1]-old[1])<.001 
# Restrict above tests to the exact edge-connected source stock-board component;
# the material's same surface also contains unrelated wood/canopy pieces.
_, weld = np.unique(plank.reshape(-1,3),axis=0,return_inverse=True)
weld=weld.reshape(-1,3)
neighbors={}
for i,row in enumerate(weld):
 for a,b in zip(row,np.roll(row,-1)):
  neighbors.setdefault(tuple(sorted((a,b))),[]).append(i)
component={base_idx}; work=[base_idx]
while work:
 row=weld[work.pop()]
 for a,b in zip(row,np.roll(row,-1)):
  for n in neighbors[tuple(sorted((a,b)))]:
   if n not in component: component.add(n);work.append(n)
ids=np.array(sorted(component)); board=plank[ids]
max_board_z=float(board[:,:,2].max())
def sample(z):
 O=np.array([0.,old[1]+.04,z]); T=O-np.array([0,.08,0])
 i,p=pierce(O,T,board)
 if p is None:return
 # Physically bound to original stock board, not its underside; upper surface
 # is the first encountered hit in the near patch measured from the old rest.
 yield dict(z_m=z,surface_local_triangle=int(ids[i]),point=p.tolist(),hands=assess(p))
scanned=[q for z in np.arange(.005,max_board_z,.005) for q in sample(float(z))]
assert scanned
# Select one practical donor-board point: prefer no early ray impact, then
# shortest native straight pivot span, with at least 15 mm sampled near edge inset.
maxz=max(q['z_m'] for q in scanned)
eligible=[q for q in scanned if q['z_m']<=maxz-.0149]
best=min(eligible,key=lambda d:min((s['blocked_1cm'],s['distance_m']) for s in d['hands'].values()))
print(json.dumps(dict(disposition='HOLD: static stock-point counterfactual only; no authored interaction',selected=best,current_original_stock_rest=assess(base),original_board_point=base.tolist(),unmodified_board_surface=2,sampled_count=len(scanned),board_component_triangles=len(ids),board_component_far_z_m=max_board_z,furthest_positive_sample_m=maxz,clear_samples=sum(any(not a['blocked_1cm'] for a in q['hands'].values()) for q in eligible),evaluated_hands=2,actual_marker_edits=0,service_scope=False),indent=2))
