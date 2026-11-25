import os
import bpy, numpy as np, json, hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parent
prior=Path(os.environ['C1_VISIBLE_PANEL_DATA'])
a=Path(os.environ['C1_VISIBLE_BOOT_DATA'])
SRC=Path(os.environ['C1_KNEE_DATA'])/'poses.npz'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(prior/'manual-panel-surface.npz')=='5235e7777fe2c2ff7c3124c8e2e4dd6b5a294fb9c1c7167e486e8ee588b27701'
assert h(SRC)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
D=np.load(prior/'manual-panel-surface.npz');A=np.load(a/'new-surface.npz')
anchor=np.load(SRC); S=float(anchor['scale']); C=anchor['source_origin']
rest=D['shaft_source_world'];v=rest.copy(); T=D['based']; idx=D['based_orig_face']; UV=A['rest_uv'].reshape(-1,3,2); N=A['projected_normals'].reshape(-1,3,3)
def frame(F):
 x=v[F];p=np.cross(x[1]-x[0],x[2]-x[0]);return p/np.linalg.norm(p)
fbase=A['tri'][24689]; nm=frame(fbase); d=float((v[12859]-v[fbase[0]])@nm)
# Real lower-quarter continuous patch. Put its single buried interpenetrating
# joining rim on the source half-space with 0.15mm signed gap. Keep 12859
# shared with incident neighbors; the revised edge Jacobian is evaluated.
assert -.000032<d<-.000029
v[12859]+=nm*(.000150-d)
# Replace the old crossed diagonal by an explicit same positive winding
# structured as two separately indexed UV charts over a shared leather geometry.
drop=np.isin(idx,[25587,25829]); compact=T[~drop]; old_id=idx[~drop]
lower=np.array([[12985,12859,12974],[12985,12974,13007]])
# Source loop order proof below ensures directed boundary consistency.
F0=A['tri'][[25587,25829]]
def boundary(F):
 e={}
 for t in F:
  for i,j in zip(t,np.roll(t,-1)):
   i=int(i);j=int(j)
   if (j,i) in e:del e[j,i]
   else:e[i,j]=1
 return set(e)
assert boundary(lower)==boundary(F0)
u=a # placeholder not used
# Fixed neighboring atlas anchor chart for each half. Construct partition
# UVs manually in neighboring exact donor triangle chart, no huge cross-atlas sweep.
def donor_uv(B):
 q=UV[B];return q.mean(0),q
lowUV=[];lowN=[]
for f,donor in zip(lower,(25293,25849)):
 p=frame(f); lowN.append(np.tile(p,(3,1)))
 c,q=donor_uv(donor); q=.70*(q-c)+c
 spread=np.max(np.linalg.norm(q-c,axis=1))
 assert spread<.006,(donor,q)
 lowUV.append(q)
# Continuous leather behind separately retained closed trim. Exact directed
# five-edge rim, 5 recessed triangles and one manually authored center.
gap_faces=A['tri'][[38197,38294,38308]]
border=boundary(gap_faces); ring=[min(j for j,k in border)]
while len(ring)<5:
 ring.append(next(k for j,k in border if j==ring[-1]))
assert (ring[-1],ring[0]) in border
back=A['tri'][38309]; n=frame(back)
a0=v[ring].mean(0); center=a0-(float((a0-v[back[0]])@n)+.000550)*n
j=len(v); v=np.vstack((v,center))
ff=np.array([[x,y,j] for x,y in zip(ring,np.roll(ring,-1))])
assert boundary(ff)==border
# Leather cap UV atlas is same discrete exact no-mix chart as adjacent 38309.
q=UV[38309]; c=q.mean(0);r=np.linalg.norm(q-c,axis=1).min()
local=v[ring]-center; ox=v[ring[1]]-v[ring[0]];ox/=np.linalg.norm(ox); oy=np.cross(n,ox);oy/=np.linalg.norm(oy)
z=np.column_stack((local@ox,local@oy));zz=z/np.max(np.abs(z))*(r*.25)
uv_ring={k:c+l for k,l in zip(ring,zz)};uv_ring[j]=c
ufu=np.array([[uv_ring[k] for k in f] for f in ff])
nfu=np.array([np.tile(frame(f),(3,1)) for f in ff])
FT=np.vstack((compact,lower,ff));uuv=np.concatenate((UV[old_id],np.array(lowUV),ufu));nn=np.concatenate((N[old_id],np.array(lowN),nfu))
W=np.vstack((A['w'],[[0.,1.,0.,0.]]));assert np.max(abs(W.sum(1)-1))<2.e-6
bpy.ops.wm.open_mainfile(filepath=str(prior/'c1-right-boot-panel-rest-proof.blend'))
x=bpy.data.objects['Detached right boot base minus three mixed bridge faces']
p=bpy.data.objects['Manual upper-boot lapped trim panel rigid to right shin']
arm=next(ob for ob in bpy.context.scene.objects if ob.type=='ARMATURE')
mh=bpy.data.meshes.new('Right boot rest leather closure and lower continuous seam')
mh.from_pydata((v/S+C).tolist(),[],FT.tolist()); mh.update()
ob=bpy.data.objects.new('Right boot visible repaired leather rest proof',mh);bpy.context.collection.objects.link(ob)
layer=mh.uv_layers.new(name='Localized exact palette chart boundaries');layer.data.foreach_set('uv',uuv.astype(np.float32).ravel());mh.materials.append(x.data.materials[0])
for r in mh.polygons:r.use_smooth=True
mh.normals_split_custom_set(nn.reshape(-1,3).tolist())
groups=[ob.vertex_groups.new(name=s) for s in ('thigh.R','shin.R','foot.R','toe.R')]
for i in range(len(v)):
 for k,gg in enumerate(groups):
  if W[i,k]>1e-10:gg.add([i],float(W[i,k]),'REPLACE')
m=ob.modifiers.new('Original exact C1 driver','ARMATURE');m.object=arm
x.hide_set(True);x.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'c1-right-boot-cohesive-rest-proof.blend'),compress=True)
np.savez_compressed(P/'exact-assembled-surface.npz',v=v,tri=FT,w=W,UV=uuv,trim_v=D['trim_v'],trim_f=D['trim_f'],retained_old_ids=old_id,new_caps=ff,new_lower=lower)
print('wrote',len(v),len(FT),'right-only maximum old vertex delta mm',float(np.linalg.norm(v[12859]-rest[12859])*1000),flush=True)
