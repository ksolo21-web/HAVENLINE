from pathlib import Path
import sys,hashlib,json,numpy as np
src,ref,out=map(Path,sys.argv[1:4])
out.mkdir(exist_ok=True)
# Reuse the critic's independent strict plane/section primitive and per-post heights;
# preserve its exact reference results, with no new state/mesh from the engine.
pfx=(ref/"triangles.py").read_text().split("results={}")[0]
sys.argv=[sys.argv[0],str(src)]
env={}; exec(pfx,env)
post=np.asarray(env['post'])
H=json.loads((ref/"result.json").read_text())["results"]
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def split(poly,axis,mark):
 vals=np.asarray([a[axis]-mark for a in poly]); eps=1e-10
 if vals.min()>=-eps or vals.max()<=eps:return [poly]
 parts=[[],[]]
 for a,b,da,db in zip(poly,np.roll(poly,-1,axis=0),vals,np.roll(vals,-1)):
  if da<=eps:parts[0].append(a)
  if da>=-eps:parts[1].append(a)
  if da*db<0 and min(abs(da),abs(db))>eps:
   v=a+(b-a)*(da/(da-db));v[axis]=mark
   for arr in parts:arr.append(v)
 return [a for a in parts if len(a)>=3]
xs,x1=.194,.225; zlim=.006
assert post[:,:,2].__abs__().max() <= .19308800001
assert post[:,:,0].__abs__().max() <= .18816000001
def plane_probe(f,right):
 s=-1 if right else 1
 srcT,mats=env['obj'](f)
 srcT=srcT*np.array([s,1,1])
 assert srcT[:,:,0].min()>=0
 alpha=zlim/(-srcT[:,:,2].min())
 dst=[];orig=[];ms=[]
 for t,mat in zip(srcT,mats):
  cells=[t]
  for a,x in [(0,xs),(0,x1),(2,0.)]:
   cells=[q for p in cells for q in split(p,a,x)]
  for p in cells:
   r=np.array(p);q=r.copy()
   q[:,2]=np.where(r[:,2]<0,r[:,2]*(alpha+(1-alpha)*np.clip((r[:,0]-xs)/(x1-xs),0,1)),r[:,2])
   for i in range(1,len(r)-1):
    tri=(0,i,i+1)
    orig.append(r[list(tri)]);dst.append(q[list(tri)]);ms.append(mat)
 dst=np.asarray(dst);orig=np.asarray(orig)
 # Across <=194mm polygon intervals, x>=0 and z>=-6 mm, so x' >=-6 mm
 # at every angle; across >=194 mm intervals |z'|>=x whenever x'<0.
 # Their separation includes both triangles, not only vertex sample checks.
 T=dst[:,:,0]
 assert np.all((T.max(1)<=xs+1e-9)|(T.min(1)>=xs-1e-9))
 near=(T.max(1)<=xs+1e-9)
 assert dst[near,:,2].min()>=-zlim-1e-9
 assert np.max(abs(dst[:,:,:2]-orig[:,:,:2]))<1e-9
 retained=orig[:,:,2]>=0
 assert np.allclose(dst[retained],orig[retained],atol=1e-9)
 far=orig[:,:,0]>=x1-1e-9
 assert np.allclose(dst[far],orig[far],atol=1e-9)
 cross=lambda t: np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
 C,D=cross(orig),cross(dst)
 assert min(np.linalg.norm(C,axis=1))>1e-12 and min(np.linalg.norm(D,axis=1))>1e-12
 # Map keeps positive XY projection exactly; extremely slanted new end-strip
 # normals must still face in compatible directions vs their source triangles.
 dots=np.einsum("ij,ij->i",C,D)/np.linalg.norm(C,axis=1)/np.linalg.norm(D,axis=1)
 changed=np.any(np.abs(dst-orig)>1e-8,axis=(1,2))
 colors={}
 for k in sorted(set(ms)):
  mi=np.array(ms)==k; before,after=orig[mi],dst[mi]
  left=before[:,:,0]<=xs+1e-9
  colors[k]=dict(triangles_changed=int(sum(mi&changed)),source_hinge_z_bounds=[float(before[left,2].min()),float(before[left,2].max())] if left.any() else None,candidate_hinge_z_bounds=[float(after[left,2].min()),float(after[left,2].max())] if left.any() else None)
 # Source switch sets exact imported triangle count to 1360. For this 
 # computational witness, no OBJ is written or native admission bypassed.
 return dict(source_sha=sha(f),source_triangles=len(srcT),witness_triangles=len(dst),changed_triangles=int(sum(changed)),materials=colors,max_depth_change_m=float(np.max(abs(dst-orig))),min_normal_dot=float(min(dots)),normals_dot_le_zero=int(sum(dots<=0)),min_separation_x_m=.008-zlim,min_separation_z_m=xs-.193088)
result={n:plane_probe(src/"donor"/f,k) for n,f,k in [('left','GateLeaf.obj',False),('right','GateLeaf_Right.obj',True)]}
print(json.dumps(dict(graft=sha(src/'SHA256SUMS'),critic=sha(ref/'SHA256SUMS'),post_terrain_offsets={k:v['post_minus_hinge_height_m'] for k,v in H.items()},proof=result),indent=2))
