import os
import bpy,numpy as np,hashlib,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
A=Path(os.environ['C1_VISIBLE_BOOT_DATA'])
assert hashlib.sha256((A/'new-surface.npz').read_bytes()).hexdigest()=='727d89b863a84dd2ca1540eb74a932439b34ea1790e371b9f5ceab0aa4e0d26e'
old=np.load(A/'new-surface.npz')
pre=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz'))
C=pre['source_origin'];S=float(pre['scale'])
X=(old['v']-C)*S;T=old['tri'];uvp=old['rest_uv'].reshape(len(T),3,2)
source=old['projected_normals'].reshape(len(T),3,3)
seal=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(A/'c1-visible-right-boot-proof.blend'))
o=bpy.data.objects['Right boot-shin visible topology proof'];arm=next(z for z in bpy.context.scene.objects if z.type=='ARMATURE')
material=o.data.materials[0]
# Locked manual modeling intent: remove only the three hybrid UV/slanted
# connector triangles. Existing outer components and attachment remain.
drop=np.array([38197,38294,38308])
fan=np.arange(len(T));keep=~np.isin(fan,drop);sf=T[keep]
assert np.max(abs(old['w'][T[np.r_[drop,38309]],1]-1))<1e-8
# Existing outer seam five-corner trace, with manually oriented trim cap and
# underside. No smoothing or source nearest-point geometry projection.
rim=[19135,19210,19289,19222,19238]
bs=X[T[38309]]
N=np.cross(bs[1]-bs[0],bs[2]-bs[0]);N/=np.linalg.norm(N)
u=bs[2]-bs[0];u/=np.linalg.norm(u);v=np.cross(N,u)
Y=X[rim]
plane=Y-((Y-bs[0])@N)[:,None]*N
local=np.column_stack(((plane-bs[0])@u,(plane-bs[0])@v))
area=.5*np.sum(local[:,0]*np.roll(local[:,1],-1)-local[:,1]*np.roll(local[:,0],-1))
if area<0:
 rim=rim[::-1];plane=plane[::-1];local=local[::-1]
# Manually authored lapped trim panel: fixed signed clearance from the
# retained pure leather backing plane, no pixel/texture-driven displacement.
cap_near=.00064;cap_back=.00035
cap=plane+cap_near*N; under=plane+cap_back*N
# Retain a single atlas chart on the new trim: a checked interior triangle
# of the surviving pure trim chart, not rejected UV-bridging topology.
q=uvp[38262]; assert np.max(np.linalg.norm(q-q.mean(0),axis=1))<.003
an=q.mean(0); lo=local.min(0);hi=local.max(0)
nuv=(local-(lo+hi)*.5)/(hi-lo)
# map to small centered atlas footprint; independently verify point in donor
# triangle. Scaled inscribed radius keeps assignments out of other islands.
def medtri(p):
 hh=np.column_stack((q[1]-q[0],q[2]-q[0]))
 v=np.linalg.solve(hh,p-q[0]);return np.r_[1-v.sum(),v]
rad=min(abs(np.cross(q[(k+1)%3]-q[k],an-q[k]))/np.linalg.norm(q[(k+1)%3]-q[k]) for k in range(3))
trim_uv=an+nuv*rad*.72
assert all(medtri(z).min()>0 for z in trim_uv)
# Authored trim faces; stable single fan/closed hem lap. Use Blender library
# ear clipping for the one hand-design polygon to avoid crossing at concavity.
from mathutils.geometry import tessellate_polygon
p2=[Vector((float(z[0]),float(z[1]),0.)) for z in local]
def vindex(v):return int(v) if isinstance(v,int) else min(range(len(p2)),key=lambda i:(v-p2[i]).length)
faces= [tuple(vindex(w) for w in zz) for zz in tessellate_polygon([p2])]
for j,t in enumerate(faces):
 pp=local[list(t)]
 if np.linalg.det(np.stack((pp[1]-pp[0],pp[2]-pp[0])))<0:
  faces[j]=t[::-1]
n=len(plane)
outer=faces+[tuple(n+q for q in f[::-1]) for f in faces]
outer += [z[::-1] for i in range(n) for z in [(i,(i+1)%n,n+i),((i+1)%n,n+(i+1)%n,n+i)]]
trimV=np.concatenate((cap,under)); trimT=np.asarray(outer)
def create(name,world,T,uvs,norm,weights):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata((world/S+C).tolist(),[],T.tolist());mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
 lay=mesh.uv_layers.new(name='C1 exact source/separate authored trim UV');lay.data.foreach_set('uv',np.asarray(uvs,dtype=np.float32).ravel())
 if norm is not None:
  for f in mesh.polygons:f.use_smooth=True
  mesh.normals_split_custom_set(np.asarray(norm).reshape(-1,3).tolist())
 mesh.materials.append(material)
 g=[ob.vertex_groups.new(name=n) for n in ('thigh.R','shin.R','foot.R','toe.R')]
 for i,row in enumerate(weights):
  for a,w in zip(g,row):
   if w>1e-10:a.add([int(i)],float(w),'REPLACE')
 m=ob.modifiers.new('Original Character 1 anatomical leg source','ARMATURE');m.object=arm
 return ob
oldsplit=create('Detached right boot base minus three mixed bridge faces',X,sf,uvp[keep],source[keep],old['w'])
new=create('Manual upper-boot lapped trim panel rigid to right shin',trimV,trimT,np.vstack((trim_uv,trim_uv))[trimT],None,np.tile([0.,1.,0.,0.],(len(trimV),1)))
o.hide_set(True);o.hide_render=True
oldsplit['candidate_only']=True;new['candidate_only']=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'c1-right-boot-panel-rest-proof.blend'),compress=True)
np.savez_compressed(P/'manual-panel-surface.npz',based=sf,based_orig_face=fan[keep],trim_v=trimV,trim_f=trimT,repeated_rim_indices=np.array(rim),backing_face=T[38309],trim_uv=np.vstack((trim_uv,trim_uv))[trimT],trim_planar_normal=N,shaft_source_world=X)
print('detached rest saved', len(faces),len(trimT),cap_near,cap_back,flush=True)
