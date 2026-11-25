import numpy as np,json
from pathlib import Path
from mathutils.geometry import closest_point_on_tri
from mathutils import Vector
P=Path(__file__).resolve().parent
A=np.load(P/'exact-native-witness.npz');T=A['tri'];sel=A['affected_faces']
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
rows=[]
report=json.loads((P/'native.json').read_text())
for i,(x,y) in enumerate(zip(A['before'],A['after'])):
 p=[dist(k[T[26992]],k[T[27689]])*1000 for k in (x,y)]
 z=report['cases'][i]['pair_26992_27689_before_after']; p=[0. if t else float(h) for h,t in zip(p,z)]
 new=margin(y[T[sel]],y[T],T[sel],T)
 if any(set(g)&set(sel.tolist()) for g in report['cases'][i]['new_pairs']):
  new['minimum_or_lower_bound_mm']=0.
 rows.append({'ms':[-1,0,75,150][i],'named_pair_actual_mm':p,'whole_affected_faces_against_shell':new})
(P/'clearance.json').write_text(json.dumps(rows,indent=2,default=lambda x:x.item()));print(rows,flush=True)
import bpy
bpy.ops.wm.open_mainfile(filepath=str(P/'c1-right-anterior-seam-binding-proof.blend'))
o=bpy.data.objects['Right boot visible repaired leather rest proof']
arm=next(k for k in bpy.context.scene.objects if k.type=='ARMATURE')
assert all(x.matrix_basis.is_identity for x in arm.pose.bones)
A=np.load(P/'exact-native-witness.npz')
chk={}
for i in A['i']:
 t=o.data.vertices[int(i)]
 chk[str(i)]={o.vertex_groups[g.group].name:g.weight for g in t.groups}
assert all(v=={'shin.R':1.} for v in chk.values())
(P/'saved-candidate-readback.json').write_text(json.dumps(chk,indent=2))
