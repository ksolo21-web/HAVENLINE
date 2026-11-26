"""Read only: explain frozen collar defect; never construct weights, mesh or pose."""
import hashlib,json,os,sys
from pathlib import Path
from collections import Counter,defaultdict,deque
import numpy as np
here=Path.cwd();ward=Path('../level1-c1-right-boot-collar-local-v1').resolve()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ward/'SHA256SUMS')=='f202ef85fdd91fc1134de51ed68069c03f2d5b9d64a1108cb88a0d342ce407d2'
for line in (ward/'SHA256SUMS').read_text().splitlines():
 h,n=line.split();assert sha(ward/n)==h
sys.path.insert(0,str(ward));os.chdir(ward)
from intake import f,P,T,F,V,M
os.chdir(here)
raw=json.loads((ward/'result.json').read_text())
R=V.astype(float)*f.S+f.base
parser=Path(os.environ['HAVENLINE_ARCHIVED_GLB_PARSER']).resolve()
assert sha(parser)=='9ec09dcc6dedd4e9a978dc489cb1ad036f5e82dcc3ecb64046417275fa567d4b'
sys.path.insert(0,str(parser.parent))
from inspect_source import load
meta,v,n,u,j,w,F0=load(f.STOCK/'assets/characters/Character1.glb')
assert np.array_equal(F0,F) and np.array_equal(v,V)
names=[meta['nodes'][i]['name'] for i in meta['skins'][0]['joints']]
rigid_names=['R_BootFastener_lower_outer','R_BootFastener_upper_outer']
old_s=[names.index(x) for x in rigid_names]; new_s=[f.slots.index('Rigid_'+x) for x in rigid_names]
bind_pure=[(np.where(j==s,w,0).sum(1)==1) for s in old_s]
fresh_pure=[(np.where(f.J==s,f.W,0).sum(1)==1) for s in new_s]
Qf=f.tags[F]
def oriented_edges(i):
 return list(zip(map(int,Qf[i]),map(int,np.roll(Qf[i],-1))))
edge_face=defaultdict(list)
for i in range(len(F)):
 for a,b in oriented_edges(i):
  edge_face[tuple(sorted((a,b)))].append((i,a,b))
def vicinity(faces):
 return {g for ff in faces for a,b in oriented_edges(ff) for g,_,_ in edge_face[tuple(sorted((a,b)))] if ff!=g}
def disk_topology(pure):
 core=set(np.flatnonzero(pure[F].all(1)).tolist())
 es=Counter(tuple(sorted((a,b))) for ff in core for a,b in oriented_edges(ff))
 rim={e for e,m in es.items() if m==1}
 outs={g for b in rim for g,_,_ in edge_face[b] if g not in core}
 comps=[]
 pending=core.copy()
 while pending:
  front={pending.pop()};seen=front.copy()
  while front:
   front=vicinity(front)&pending;pending-=front;seen|=front
  comps.append(len(seen))
 return core,rim,outs,comps
D=[disk_topology(p) for p in bind_pure]
E=[disk_topology(p) for p in fresh_pure]
frames={}
for name,bp,fp,(c,r,o,com),(nc,nr,no,ncom),fs in zip(rigid_names,bind_pure,fresh_pure,D,E,new_s):
 names_i=f.slots[fs]; points=f.X
 frames[name]={'native_pure_indices':int(bp.sum()),'native_pure_core_faces':len(c),'native_pure_edge_rim':len(r),
  'native_neighbor_faces_through_welded_rim':len(o),'native_core_components_sizes':com,
  'fresh_pure_core_faces':len(nc),'fresh_pure_edge_rim':len(nr),'fresh_neighbor_faces_through_welded_rim':len(no),
  'native_rim_edges_with_single_opp_neighbor':sum(len(edge_face[k])==2 and edge_face[k][0][1:]==edge_face[k][1][1:][::-1] for k in r),
  'source_core_faces_still_exactly_pure_on_fresh':len(c&nc),
  'scoped_source_faces_in_rigid_core':list(sorted(set(raw['scoped_faces'])&c)),
  'fresh_mount_relative_to_heel_max_pos_error_m':float(np.abs(M[fs]-M[f.slots.index('RHeel')]).max()),
  'parent':f.N[names_i]['parent']}
old_pairs=[tuple(q['faces']) for q in raw['changed_face_strict_pairs_before']]
new_pairs=[tuple(q['faces']) for q in raw['newly_intersecting_pairs']]
investigated=sorted(set(x for a,b in old_pairs+new_pairs for x in (a,b)))
fd={}
def orientation(X,i):
 tri=X[F[i]];A=np.cross(tri[1]-tri[0],tri[2]-tri[0]);return A/np.linalg.norm(A)
for i in investigated:
 rows=F[i]
 p0,p1=R[rows],P[rows]
 rolled=M[f.slots.index('RHeel'),:3,:3]@orientation(R,i)
 denom=np.linalg.norm(np.roll(p0,-1,axis=0)-p0,axis=1)
 e=np.linalg.norm(np.roll(p1,-1,axis=0)-p1,axis=1)/denom
 carriers=np.where(np.isin(f.J[rows],new_s+[f.slots.index('RHeel')]),f.W[rows],0).sum(1)
 fd[i]=dict(fastener_shell_core_membership=[i in d[0] for d in D], shares_original_core_rim_edge=[i in d[2] for d in D],
            source_rows=rows.tolist(),neutral_shared_carrier_weight_range=[float(carriers.min()),float(carriers.max())],
            signed_area_projection_vs_pure_heel_carrier=float(orientation(P,i)@rolled),unloaded_to_loaded_edge_ratios=e.tolist())
r0,l0=8677,8892
a,b=P[F[r0]],P[F[l0]]
nor=np.cross(a[1]-a[0],a[2]-a[0]);nor/=np.linalg.norm(nor)
prev=(b-a[0])@nor
same_shell=bool(vicinity({r0})&vicinity({l0}))
pairs_connected={}
def dist_to_faces(start,goal):
 S=set(start);front=S.copy();k=0
 while front and k<10:
  if front&goal:return k
  front=vicinity(front)-S;S|=front;k+=1
 return None
for z in [8677,8892,8893,8916,8918,3777]:
 start={z} if z!=3777 else set(raw['scoped_faces'])
 pairs_connected[z]=[dist_to_faces(start,d[0]) for d in D]
out=dict(frozen_collar_trial_sha256='ced7cf6715e66e9824467629ea880bc71fd838a00f372cf47f9b96d313c2d455',measured_actual_source_and_held_state=True,
         fastener_core_and_adjacent_flex=frames, implicated_source_face_metrics=fd, lower_and_upper_core_edge_hops=pairs_connected,
         corrected_pose_pair_signed_distances_mm=(prev*1000).tolist(), same_welded_short_neighborhood=same_shell,
         sole_and_markers_unchanged_in_tried_scope=(raw['sole_and_held_marker_before']==raw['sole_and_held_marker_after']),
         newly_intersecting_pairs=raw['newly_intersecting_pairs'], no_pose_geometry_or_weights_changed=True)
print(json.dumps(out,indent=2))
