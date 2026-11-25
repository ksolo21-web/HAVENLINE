import os
import bpy,numpy as np,hashlib,json, math
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
from pathlib import Path
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent
src=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
assert hashlib.sha256(src.read_bytes()).hexdigest()=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
d=np.load(src); data=np.load(P/'new-surface.npz'); T=data['tri']; C=d['source_origin']; S=float(d['scale'])
bpy.ops.wm.open_mainfile(filepath=str(P/'c1-visible-right-boot-proof.blend'))
obj=bpy.data.objects['Right boot-shin visible topology proof']
a=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE')
ids=['thigh.R','shin.R','foot.R','toe.R']
origR=d['rest']; origT=d['tri'][data['original_face_ids']]
old_w=d['weights'][:,6:8].sum(1);z=origR[:,2]
v0=(data['v']-C)*S
S0=v0[T]; N0=np.cross(S0[:,1]-S0[:,0],S0[:,2]-S0[:,0])
den=np.linalg.norm(N0,axis=1); nz=den>1e-10
E=np.unique(np.sort(T[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1),axis=0)
len0=np.linalg.norm(v0[E[:,1]]-v0[E[:,0]],axis=1)
E=E[len0>.0008];len0=len0[len0>.0008]
U=bpy.context.view_layer.update
def posed():
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); n=len(e.data.vertices)
 p=np.empty((n,3),np.float32);e.data.vertices.foreach_get('co',p.ravel());return (p-C)*S
def clip(p,z,sgn):
 q=[]
 for i,a in enumerate(p):
  b=p[(i+1)%len(p)];u=sgn*(a[2]-z);v=sgn*(b[2]-z)
  if u>=0:q.append(a)
  if (u<0)!=(v<0):q.append(a+u/(u-v)*(b-a))
 return q
def contact(v,tri,zone):
 face=tri[zone[tri].all(1)]
 vv=v[face]; z=vv[:,:,2]
 near=(z.max(1)>=-.001)&(z.min(1)<=.002)
 val=0;part=[];nn=0
 for t in vv[near]:
  p=clip(clip(t,-.001,1),.002,-1)
  if len(p)<3:continue
  p=np.array(p);a=abs(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))*.5
  if a>0:val+=a;nn+=1
 return (val*1e6,nn)
old_loop=(z<.065)&(origR[:,0]<-.026)&(old_w>.35)
same_quant=np.quantile(-origR[old_loop,1],.68)
old_zone=old_loop&(-origR[:,1]>=same_quant)
new_zone=(v0[:,2]<.065)&(v0[:,0]<-.026)&(data['w'][:,2:].sum(1)>.35)&(-v0[:,1]>=same_quant)
new_boot=(v0[:,2]<.38)&(data['w'][:,2:].sum(1)>.35)
old_boot=(z<.38)&(origR[:,0]<-.026)&(old_w>.35)
base=posed();neutral=float(np.linalg.norm(base-v0,axis=1).max()*1000)
cases=[]
for k in range(3):
 for s,mat in zip(ids,d['bones'][k,1]):
  pb=a.pose.bones[s];pb.matrix=Matrix(mat.tolist())@pb.bone.matrix_local;U()
 x=posed(); p=d['frames'][k]
 edge=np.linalg.norm(x[E[:,1]]-x[E[:,0]],axis=1)/len0
 pq=x[T]; n=np.cross(pq[:,1]-pq[:,0],pq[:,2]-pq[:,0])
 # Positive face orientation against nearest dominant original bone's
 # proper transformed reference normal, not a global unposed normal.
 typ=data['w'][T].mean(1).argmax(1)
 bases=Rotation.from_matrix(d['bones'][k,1,:,:3,:3]).as_matrix()
 expected=np.einsum('nij,nj->ni',bases[typ],N0)
 sgn=(expected[nz]*n[nz]).sum(1)/(den[nz]**2)
 b=BVHTree.FromPolygons(x.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
 pairs=[(i,j) for i,j in b.overlap(b) if i<j and not np.isin(T[i],T[j]).any()]
 fl=(x[new_boot,2].min()*1000,p[old_boot,2].min()*1000)
 cases.append(dict(t_ms=[0,75,150][k],base_sole_mm=float(fl[1]),new_sole_mm=float(fl[0]),base_actual_near_floor_zone=contact(p,origT,old_zone),new_actual_near_floor_zone=contact(x,T,new_zone),edges_bad=int(sum((edge<.5)|(edge>2))),edges_range=[float(edge.min()),float(edge.max())],guard_edges=len(edge),signed_below_point1=int(sum(sgn<.1)),signed_nonpositive=int(sum(sgn<=0)),local_nonadjacent_self_pairs=len(pairs),sample_collision_pair=list(pairs[0]) if pairs else None))
# Actual toe control sensitivity of *the exposed topology*. Inherit narrow
# new shape from final key and change only isolated local toe angle by 8 degrees.
x=posed();pb=a.pose.bones['toe.R'];old=pb.matrix.copy();M=Quaternion((1,0,0),math.radians(8)).to_matrix().to_4x4()@old;M.translation=old.translation;pb.matrix=M;U()
dx=np.linalg.norm(posed()-x,axis=1)*1000
toepose=dict(exposed_forefoot_rows=int(sum(new_zone)), moved_gt_point1=int(sum(dx[new_zone]>.1)),max_mm=float(dx[new_zone].max()),zero_weight_vertices_max_mm=float(dx[data['w'][:,3]<1e-9].max()),heel_vertices_mm=float(dx[(v0[:,2]<.065)&(v0[:,1]>d['joints'][1,2,1]+.02)].max()))
(P/'candidate-audit.json').write_text(json.dumps({'pose_source':str(src.name),'actual_neutral_rig_delta_mm':neutral,'cases':cases,'visible_toe_activation':toepose},indent=2,default=lambda x:x.item()))
print(cases,toepose,flush=True)
