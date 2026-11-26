"""Single source-derived boot interface intake. No mesh/pose/weight edits."""
import contextlib,hashlib,io,json,os,sys
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from scipy.spatial import cKDTree

home=Path.cwd(); dep=Path('../level1-c1-collar-assembly-read-v1').resolve()
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert h(dep/'ASSEMBLY-READ-SHA256SUMS')=='d6a13f5c2891a905a22917e12789d2740d4124d317fafb7b700b91e9299ab966'
for line in (dep/'ASSEMBLY-READ-SHA256SUMS').read_text().splitlines():
 d,n=line.split();assert h(dep/n)==d
sys.path.insert(0,str(dep));os.chdir(dep)
with contextlib.redirect_stdout(io.StringIO()):
 from analyze import f,F,V,R,P,meta,D,edge_face,Qf,M
os.chdir(home)
right=V[:,0]<-.04
heel=f.weight('RHeel'); ball=f.weight('RBall')
dominant=(right&(V[:,1]<.3)&((heel>.5)|(ball>.5)))
rigid=np.zeros(len(V),bool)
slots=[]
for k,s in enumerate(f.slots):
 if s.startswith('Rigid_R_BootFastener_'):
  slots.append(k);rigid|=(f.weight(s)==1)
ys=float(V[dominant,1].max());ym=float(V[rigid,1].min())
assert ys<ym
y=(ys+ym)*.5
Z=V.astype(float); T=F
xsrc=Z[:,0]
# Generate only intersections/witness arrays of an analytic section; no file
# contains new mesh primitives or changed original attributes.
def tag(a,b):
 pa,pb=Z[a],Z[b]
 n=float((y-pa[1])/(pb[1]-pa[1]))
 q=(1-n)*pa+n*pb
 return q,n
edges={}
segs=[]
for i,r in enumerate(T):
 v=Z[r]
 if not (v[:,1].min()<y<v[:,1].max()):continue
 ids=[]
 for a,b in zip(r,np.roll(r,-1)):
  if (Z[a,1]-y)*(Z[b,1]-y)>=0:continue
  cv,u=tag(a,b)
  if cv[0]>-.04:continue
  key=tuple(sorted((int(f.tags[a]),int(f.tags[b]))))
  if key not in edges:edges[key]=[]
  edges[key].append((int(i),int(a),int(b),u,cv,(1-u)*P[a]+u*P[b]))
  ids.append(key)
 if not ids:continue
 if len(ids)!=2:raise RuntimeError('One section exits the exact right-foot region.')
 segs.append((int(i),*ids))
graph=defaultdict(set)
for _,a,b in segs:
 graph[a].add(b);graph[b].add(a)
components=[]
alive=set(graph)
while alive:
 front={min(alive)};component=front.copy();alive-=front
 while front:
  front=set.union(*(graph[k] for k in front))&alive
  component|=front;alive-=front
 components.append(component)
assert all(len(graph[k])==2 and len(edges[k])==2 for k in graph)
section=set.union(*components)
source_rows=np.flatnonzero(right & (Z[:,1]<y))
# Quantify alternate exported binding mismatch on exact source-edge cuts without
# authoring any skin at those points: linear dependent rig field is not always
# equivalent to the physical edge interpolant under direct fixed source skin.
mismatch=[];influence_counts=[];rest_alias=0.;loaded_alias=0.
for e in sorted(section):
 paired=edges[e]
 u,pair=paired
 rest_alias=max(rest_alias,float(np.linalg.norm(u[4]-pair[4])))
 loaded_alias=max(loaded_alias,float(np.linalg.norm(u[5]-pair[5])))
 i,a,b,t,q,loaded=u
 bag=defaultdict(float)
 for v,c in [(a,1-t),(b,t)]:
  for s,w in zip(f.J[v],f.W[v]):bag[int(s)]+=c*float(w)
 influence_counts.append(sum(x>1e-8 for x in bag.values()))
 H=np.r_[q,1.]
 rep=sum(((M[k]@H)[:3]*w) for k,w in bag.items())*f.S+f.base
 mismatch.append(np.linalg.norm(rep-loaded))
# Real fixed edge section against every retained potential outside triangle,
# categorized instead of treating replaceable cloth as protected.
def prep(X):
 tri=X[T];lo=tri.min(1);hi=tri.max(1);c=(lo+hi)*.5
 rad=np.linalg.norm(hi-c,axis=1);kd=cKDTree(c)
 return tri,lo,hi,rad,kd
all_tags=f.tags[T]
def finite(mode):
 X=R if mode=='neutral' else P
 mesh,lo,hi,rad,kd=prep(X);hits=[];checks=0
 for i,a,b in segs:
  if mode=='neutral':u=S(a);v=S(b)
  else:u=edges[a][0][5];v=edges[b][0][5]
  dq=v-u
  candidates=np.asarray(kd.query_ball_point((v+u)*.5,np.linalg.norm(dq)*.5+rad.max()+1e-10),int)
  candidates=candidates[((lo[candidates]<=np.maximum(u,v)+1e-10)&(hi[candidates]>=np.minimum(u,v)-1e-10)).all(1)]
  # Entire affected section has only these real neighbor cells. Same face and
  # immediate cut-cell fan cannot count as a strict unrelated pierce.
  near={i}|{x[0] for k in (a,b) for x in edges[k]}
  candidates=candidates[~np.isin(candidates,list(near))]
  checks+=len(candidates)
  B=mesh[candidates]; e=B[:,1]-B[:,0]; g=B[:,2]-B[:,0]
  px=np.cross(dq,g);den=(e*px).sum(1);ok=abs(den)>1e-13
  den=np.where(ok,den,1.)
  d=u-B[:,0]; qp=np.cross(d,e)
  bc=(d*px).sum(1)/den;bb=qp@dq/den;dt=(g*qp).sum(1)/den
  mm=np.minimum.reduce([bc,bb,1.-bc-bb,dt,1.-dt])
  for k in np.flatnonzero(ok&(mm>1e-7)):
   j=int(candidates[k]);ids=T[j]; yr=Z[ids,1];pole=Z[ids,0]
   geom='retained_lower' if yr.max()<y and (pole<-.04).all() else 'above_candidate_junction_or_unqualified'
   if rigid[ids].all():geom='fixed_pure_fastener'
   if (pole>-.04).any():geom='other_garment_or_other_side'
   hits.append(dict(section_parent_source_face=i,opponent_source_face=j,barycentric_min=float(mm[k]),
      section_fraction=float(dt[k]),opponent_status=geom,source_height_art_minmax=[float(yr.min()),float(yr.max())]))
 return dict(near_pairs_checked=checks,proper_hits=hits)
def S(a):return edges[a][0][4]*f.S+f.base
def path(comp):
 a=min(comp);sett=[a];prev=None
 while True:
  b=min(graph[a]-({prev} if prev is not None else set()))
  if b==sett[0]:break
  sett.append(b);prev,a=a,b
 assert len(sett)==len(comp)
 return sett
def profile(comp):
 w=path(comp)
 q=np.array([edges[a][0][4] for a in w]);p=np.array([edges[a][0][5] for a in w])
 y0=(-np.cross(q,np.roll(q,-1,axis=0),axis=-1).sum(0)[1])*.5
 pr=lambda A:(A-f.cam)@f.basis[:2].T*720/13.
 return dict(ordered_contour_edges=len(w),art_width_depth_m=np.ptp(q[:,[0,2]],axis=0).tolist(),
  rest_art_section_area_mm2=abs(float(y0))*1e6,loaded_world_y_range_m=[float(p[:,1].min()),float(p[:,1].max())],
  nominal_camera_contour_width_height_px=[np.ptp(pr(A),axis=0).tolist() for A in (q*f.S+f.base,p)])
poly=[profile(c) for c in components]
below=Z[T[:,0],1]<y # count exact untouched lower cells
mask=(Z[T,1]<y).all(1)&(Z[T,0]<-.04).all(1)
support=set(np.unique(f.bounds['R']['faces']).tolist())
assert all(Z[k,1]<y for k in support)
# Verify present primitive and detailed material identity without reading textures.
pr=meta['meshes'][0]['primitives'][0]
u=meta['materials'][pr['material']]
receipt=dict(source_rig_seal='ce9551d2f34a90c9f5b1dd08c7854ecf471e8ba5965f3be99a41dfd6bb15943c',
 source_glb_sha256='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099',
 exact_single_source_y_section_rule='midpoint between highest real right heel/ball-majority vertex and lowest pure right original fastener vertex',
 y_above_dominant_heel_ball_max_below_metal_min_art_m=[ys,y,ym],art_gap_mm=(ym-ys)*1000,
 right_majority_heel_ball_rows=len(np.flatnonzero(dominant)),right_pure_metal_rows=int(rigid.sum()),
 fixed_right_articulated_support_rows=len(support),unchanged_strictly_lower_full_source_faces=int(mask.sum()),
 untouched_source_primitive_material_slot=pr['material'],
 original_face_side_uv_and_normals_required=True,
 section_geometry=poly,section_count=len(components),scoped_inside_faces=len(segs),
 exact_rest_load_weld_alias_residual_max_m=[rest_alias,loaded_alias],
 linear_uv_aliases_are_not_carrier_frames=True,
 four_slot_export_unqualified_number_of_endpoints_gt4=sum(n>4 for n in influence_counts),
 hypothetical_full_influence_interpolated_lbs_vs_fixed_loaded_source_rail_difference_mm_max=float(max(mismatch)*1000),
 intersections={x:finite(x) for x in ['neutral','loaded']},
 original_fused_source_has_no_independent_clearance_surface=True,no_engine_rig_geometry_or_attrs_edited=True)
print(json.dumps(receipt,indent=2))
