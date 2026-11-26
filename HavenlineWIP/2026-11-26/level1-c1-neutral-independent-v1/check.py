import sys,json,struct,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.spatial import cKDTree
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old,new,out=map(Path,sys.argv[1:])
assert sha(old)=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
assert sha(new)=='3661168a8762e3afa48997c3d62d8091e9643163ba6ed75f91b6e4a75c28afe8'
def get_glb(p):
 b=p.read_bytes(); n=struct.unpack_from('<I',b,12)[0]
 j=json.loads(b[20:20+n]); data=b[28+n:]
 def read(i):
  a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]
  dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
  k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  assert 'byteStride' not in bv
  return np.frombuffer(data,dtype=dt,count=k*a['count'],offset=bv.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,k)
 pr=j['meshes'][0]['primitives'][0]
 return j,data,{**{k:read(v) for k,v in pr['attributes'].items()},'t':read(pr['indices']).reshape(-1,3)},read(j['skins'][0]['inverseBindMatrices']),pr
a,aa,p,ib,pa=get_glb(old); b,bb,q,jb,pb=get_glb(new)
assert bb.startswith(aa) and np.array_equal(ib,jb) and len(ib)==66 and np.isfinite(jb).all()
assert all(a[k]==b[k] for k in a if k not in ('bufferViews','accessors','buffers','meshes')) and pa.get('material')==pb.get('material')
assert set(p)==set(q)=={'POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0','t'}
v,t=p['POSITION'],p['t']; w,u=q['POSITION'],q['t']
assert all(np.array_equal(p[k],q[k][:len(p[k])]) for k in p if k!='t')
edit=np.where(np.any(t!=u[:len(t)],axis=1))[0]
# Derive each child's source face from barycentric membership in changed source parents.
newidx=np.r_[edit,np.arange(len(t),len(u))]
parents={int(c):int(c) for c in edit}
for c,parent in zip(range(len(t),len(u)),np.repeat(edit,2)):
 parents[c]=int(parent)
assert len(parents)==len(newidx) and set(Counter(parents.values()).values())=={3}
maxdist=0; maxuv=0; minsigned=1.; areas=Counter(); target=set(range(58,62))|{64,65}
for c,parent in parents.items():
 orig=t[parent]; child=u[c]; pp=v[orig].astype(float); coords=[]
 for x in child:
  if x in orig:
   bary=np.eye(3)[list(orig).index(x)]
  else:
   rs=[(np.linalg.norm(w[x]-(pp[i]+pp[j])/2),i,j) for i,j in ((0,1),(1,2),(0,2))]
   dist,i,j=min(rs); assert dist<3e-8
   bary=np.zeros(3); bary[[i,j]]=.5
  coords.append(bary)
 coords=np.array(coords)
 maxdist=max(maxdist,float(np.linalg.norm(coords@pp-w[child],axis=1).max()))
 maxuv=max(maxuv,float(np.abs(coords@p['TEXCOORD_0'][orig]-q['TEXCOORD_0'][child]).max()))
 n0=np.cross(pp[1]-pp[0],pp[2]-pp[0]); vv=w[child].astype(float); nn=np.cross(vv[1]-vv[0],vv[2]-vv[0])
 ratio=float(nn@n0/(n0@n0)); minsigned=min(minsigned,ratio); areas[parent]+=ratio
assert minsigned>0 and maxuv<1e-7 and max(abs(x-1) for x in areas.values())<.00005
def welded(V,F,active):
 _,k=np.unique(V,return_inverse=True,axis=0); wf=k[F]
 ed=lambda row:tuple(zip(row,np.roll(row,-1)))
 keys={tuple(sorted(e)) for f in active for e in ed(wf[f])}
 c=Counter((i,j) for row in wf for i,j in ed(row) if tuple(sorted((i,j))) in keys)
 assert all(c[x,y]==c[y,x]==1 for x,y in keys)
 return wf,len(keys)
t0,old_edges=welded(v,t,edit); u0,new_edges=welded(w,u,newidx)
slots={}
for k in sorted(target):
 gains=(q['WEIGHTS_0']*(q['JOINTS_0']==k)).sum(1)
 f=np.flatnonzero(np.min(gains[u],1)==1)
 assert len(f)>0 and np.array_equal(t[f],u[f])
 owned=Counter(tuple(sorted(e)) for i in f for e in zip(u0[i],np.roll(u0[i],-1)))
 rim={e for e,n in owned.items() if n==1}
 # Authored translation response: same pure displacement in all three trim corners, zero at new fabric midpoint.
 affected_adj=[i for i in newidx if np.any(gains[u[i]]>0)]
 assert len(affected_adj)>0 and not np.any(gains[len(v):])
 assert np.allclose(np.linalg.det(jb[k].reshape(4,4)),1,atol=.01)
 slots[str(k)]={'node':b['nodes'][b['skins'][0]['joints'][k]]['name'],'pure_faces':len(f),'open_rim':len(rim),'transition_faces_with_this_channel':len(affected_adj)}
# Independent Moller-Trumbore segment-plane test. Interior crossing lines can
# have their ends on either triangle, so retain edge/face hits in both directions.
def cuts(A,B):
 e1=B[1]-B[0];e2=B[2]-B[0];xs=[]
 for a,b in zip(A,np.roll(A,-1,axis=0)):
  vec=b-a; h=np.cross(vec,e2); det=e1@h
  if abs(det)<1e-14: continue
  s=a-B[0]; r=s@h/det; z=np.cross(s,e1); v=vec@z/det; u=e2@z/det
  if min(r,v,1-r-v,u,1-u)>=-1e-8:xs.append(a+u*vec)
 return xs
def intersections(V,F,WF,active):
 G=V[F].astype(float); lo=G.min(1);hi=G.max(1); ctr=(lo+hi)*.5; radii=np.linalg.norm(hi-ctr,axis=1); kd=cKDTree(ctr); seen=set(); hit=[]
 for a in active:
  for b in kd.query_ball_point(ctr[a],radii[a]+radii.max()+1e-9):
   k=tuple(sorted((int(a),int(b))))
   if k in seen or any(x in WF[a] for x in WF[b]) or not np.all(np.minimum(hi[a],hi[b])+1e-9>=np.maximum(lo[a],lo[b])):continue
   seen.add(k); X,Y=G[a],G[b]; ps=cuts(X,Y)+cuts(Y,X)
   if len(ps)>1 and max(np.linalg.norm(x-y) for x in ps for y in ps)>1e-7:
    na=np.cross(X[1]-X[0],X[2]-X[0]); nb=np.cross(Y[1]-Y[0],Y[2]-Y[0]);
    if np.min((X-Y[0])@nb)<-1e-14 and np.max((X-Y[0])@nb)>1e-14 and np.min((Y-X[0])@na)<-1e-14 and np.max((Y-X[0])@na)>1e-14:hit.append(k)
 return len(seen),hit
rw=np.flatnonzero(np.isin(q['JOINTS_0'][u],list(target)).any(axis=(1,2)))
n0,h0=intersections(v,t,t0,np.union1d(edit,rw[rw<len(t)]));n1,h1=intersections(w,u,u0,np.union1d(newidx,rw))
assert not h0 and not h1,(h0,h1)

# Geometric weld continuity under skinning: equal bind position alone is insufficient
# if duplicate new rows have different effective joint gains.
uniq, idx=np.unique(w,axis=0,return_inverse=True)
midgrp=np.unique(idx[len(v):]); worst=0.; mismatch=0
G=np.zeros((len(w),66))
for col in range(4):
 np.add.at(G,(np.arange(len(w)),q['JOINTS_0'][:,col]),q['WEIGHTS_0'][:,col])
for k in midgrp:
 rows=np.flatnonzero(idx==k)
 delta=np.ptp(G[rows],axis=0).max()
 worst=max(worst,float(delta))
 mismatch+=int(delta>1e-7)
for k in sorted(target):
 gains=G[:,k]
 specific={}
 touched=np.flatnonzero(np.any(gains[u]>0.,axis=1))
 neutral=w[u[touched]].astype(float)
 norm=lambda mesh:np.cross(mesh[:,1]-mesh[:,0],mesh[:,2]-mesh[:,0])
 base_norm=norm(neutral)
 for millimetres in (.1,.5,1.):
  flips=[]
  for move in np.vstack([np.eye(3),-np.eye(3)])*(millimetres/1000):
   deformed=neutral+gains[u[touched]][:,:,None]*move
   flips.append(int(np.count_nonzero(np.sum(norm(deformed)*base_norm,axis=1)<=0)))
  specific[str(millimetres)]=flips
 slots[str(k)]['synthetic_global_translation_negative_orientation_by_axis_mm']=specific
print(json.dumps(dict(old=sha(old),candidate=sha(new),old_faces=len(t),old_vertices=len(v),changed_parents=len(edit),children=len(parents),unchanged_original_vertex_rows=len(v),new_welded_edges=new_edges,max_barycentric_position_error_m=maxdist,max_barycentric_uv_error=maxuv,minimum_signed_subarea_fraction=minsigned,baseline_nonadjacent_candidate_pairs=n0,edited_nonadjacent_candidate_pairs=n1,welded_midpoints=len(midgrp),weight_disagreeing_welds=mismatch,max_welded_skin_gain_delta=worst,slots=slots),indent=2))
