import os
import numpy as np,json,bpy
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
from mathutils import Vector
P=Path(__file__).resolve().parent;D=np.load(P/'exact-assembled-surface.npz')
v=D['v'];T=D['tri'];q=D['trim_v'];Q=D['trim_f']; F=D['retained_old_ids'];A=v[T];B=q[Q]
look=lambda x,t:BVHTree.FromPolygons(x.tolist(),t.tolist(),all_triangles=True,epsilon=0.)
a=look(v,T);b=look(q,Q)
pairs=lambda a,t:[(int(i),int(j)) for i,j in a.overlap(a) if i<j and not np.isin(t[i],t[j]).any()]
sv=pairs(a,T);st=pairs(b,Q);pst=[(int(i),int(j)) for i,j in a.overlap(b)]
def topology(T):
 e=T[:,((0,1),(1,2),(2,0))].reshape(-1,2); E=np.sort(e,axis=1)
 _,i,c=np.unique(E,axis=0,return_inverse=True,return_counts=True)
 d=np.bincount(i,weights=np.where(e[:,1]>e[:,0],1,-1),minlength=len(c))
 return [int(sum(c==1)),int(sum(c>2)),int(sum((c==2)&(d!=0)))]
def seg(a,b,c,d):
 u=b-a;v=d-c; w=a-c
 aa=u@u;bb=u@v;cc=v@v;dd=u@w;ee=v@w
 D=aa*cc-bb*bb
 vals=[]
 # all four constrained rectangle edges and the unconstrained interior stationary point
 for s in (0.,1.):
  t=np.clip((ee+s*bb)/max(cc,1e-30),0,1); vals.append(np.linalg.norm(w+s*u-t*v))
 for t in (0.,1.):
  s=np.clip((t*bb-dd)/max(aa,1e-30),0,1); vals.append(np.linalg.norm(w+s*u-t*v))
 if D>1e-30:
  s=(bb*ee-cc*dd)/D;t=(aa*ee-bb*dd)/D
  if 0<s<1 and 0<t<1:vals.append(np.linalg.norm(w+s*u-t*v))
 return min(vals)
def dist(A,B):
 a=[Vector(x) for x in A];b=[Vector(x) for x in B]
 values=[(x-closest_point_on_tri(x,*b)).length for x in a]+[(x-closest_point_on_tri(x,*a)).length for x in b]
 values.extend(seg(A[i],A[(i+1)%3],B[j],B[(j+1)%3]) for i in range(3) for j in range(3))
 return min(values)
# Full meshes are BVH tested; distance explicitly covers all geometrically
# plausible close pairs between whole independent surfaces, and new named
# patch faces vs entire retained basemesh excluding shared vertices.
def margin(PA,PB,iA=None,iB=None):
 lo=PB.min(1);hi=PB.max(1);best=.006;pair=None;cc=0
 for i,X in enumerate(PA):
  hu=X.max(0);lu=X.min(0)
  m=np.where(np.all(hi>=lu-best,axis=1)&np.all(lo<=hu+best,axis=1))[0]
  for j in m:
   if iA is not None and np.isin(iA[i],iB[j]).any():continue
   di=dist(X,PB[j]);cc+=1
   if di<best:best=di;pair=[i,int(j)]
 return {'minimum_or_lower_bound_mm':best*1000,'number_exact_pairs':cc,'observed_pair':pair}
tri_new=T[-7:]
# No distance between logically intersecting groups is callable "positive".
m=margin(B,A); u=margin(v[tri_new],A,tri_new,T)
if pst:m['minimum_or_lower_bound_mm']=0.
if any(i>=len(T)-7 or j>=len(T)-7 for i,j in sv):u['minimum_or_lower_bound_mm']=0.
signed=np.linalg.norm(np.cross(A[:,1]-A[:,0],A[:,2]-A[:,0]),axis=1)
S=lambda k: np.array([tuple(vv.uv) for vv in k.data.uv_layers.active.data])
bpy.ops.wm.open_mainfile(filepath=str(P/'c1-right-boot-layered-assembly-proof.blend'))
o=bpy.data.objects['Right boot visible repaired leather rest proof'];p=bpy.data.objects['Manual upper-boot lapped trim panel rigid to right shin']
sha=lambda img: __import__('hashlib').sha256(img.packed_file.data).hexdigest()
ret={'actual_neutral_main_nonadjacent_pairs':sv,'actual_neutral_trim_nonadjacent_pairs':st,'actual_neutral_trim_vs_main_pairs':pst,'rest_main_boundary_excess_winding':topology(T),'trim_boundary_excess_winding':topology(Q),'least_actual_trim_to_shell_mm':m,'least_actual_new_patches_to_nonadjacent_shell_mm':u,'minimum_main_face_double_area_m2':float(signed.min()),'saved_base_trim_share_original_material':o.data.materials[0]==p.data.materials[0],'saved_uv_finite_and_legal':bool(all(np.isfinite(S(i)).all() and ((S(i)>=0)&(S(i)<=1)).all() for i in (o,p))),'pose_not_run':True}
ret['neutral_gate']=not (sv or st or pst) and topology(T)==[162,0,0] and topology(Q)==[0,0,0] and m['minimum_or_lower_bound_mm']>1e-4 and u['minimum_or_lower_bound_mm']>1e-4 and signed.min()>1.e-12
(P/'preflight.json').write_text(json.dumps(ret,indent=2,default=lambda n:n.item()));print(ret,flush=True)
