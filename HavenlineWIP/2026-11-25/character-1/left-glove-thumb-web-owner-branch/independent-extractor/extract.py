import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
args=sys.argv[sys.argv.index('--')+1:]
if len(args)!=3:
 raise SystemExit('Expected protected narrow rig folder, chest-pose evidence folder and existing output directory.')
P,R,out=map(Path,args)
def ack(p,h):
 sh=lambda k:hashlib.sha256(k.read_bytes()).hexdigest()
 assert sh(p/'SHA256SUMS')==h
 for line in (p/'SHA256SUMS').read_text().splitlines():
  h,f=line.split(maxsplit=1);assert sh(p/f)==h
ack(P,'ccd17840ef942d61ba891958a50c7dcfe4b1f9a9263280667ce9dabb50c389d7')
ack(R,'642a4159213aebc5457c07d0922487fcb0c0d240d8a7c34774080dc42c91adf5')
cfg=json.loads((R/'result.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'c1-narrow-ready-witness.blend'))
B=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE').pose.bones
skin=next(x for x in bpy.context.scene.objects if x.type=='MESH')
assert len(B)==52
unit=lambda x:x/np.linalg.norm(x)
for s in ('R','L'):
 for j in ('upper_arm','forearm','hand'):B[j+'.'+s].matrix_basis.identity()
bpy.context.view_layer.update()
for s in ('R','L'):
 u,e,w=(B[j+'.'+s] for j in ('upper_arm','forearm','hand'))
 uu,ee=u.matrix.copy(),e.matrix.copy()
 a,c,b=(np.array(cfg['sides'][s][j]) for j in ('shoulder','elbow','wrist'))
 assert np.linalg.norm(np.array(u.head)-a)<1e-9
 for ob,r,j,k in ((u,uu,a,c),(e,ee,c,b)):
  rotation=r.to_3x3()
  turn=(rotation@Vector((0,1,0))).rotation_difference(Vector(k-j)).to_matrix()
  t=(turn@rotation).to_4x4()
  t.translation=Vector(j); ob.matrix=t; bpy.context.view_layer.update()
 inward=-np.array(cfg['sides'][s]['outward']); v=np.array([0.,-1.,.11 if s=='R' else -.11]); f=unit(v-inward*(v@inward))
 m=Matrix(np.column_stack((np.cross(f,inward),f,inward)).tolist()).to_4x4(); m.translation=Vector(b); w.matrix=m; bpy.context.view_layer.update()
skin.data.calc_loop_triangles()
F=np.empty(3*len(skin.data.loop_triangles),dtype=np.int32);skin.data.loop_triangles.foreach_get('vertices',F)
e=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());V=np.empty(3*len(e.data.vertices),dtype=np.float32);e.data.vertices.foreach_get('co',V)
bone=lambda x:np.array(B[x+'.L'].head)
u,v,w,z=map(bone,['thumb.01','thumb.02','index.01','middle.01']); hands=np.stack([u+.6*(v-u),.44*v+.56*w,.76*w+.24*z,.5*(u+w)])
np.savez(out/'held_owner.npz',faces=F.reshape(-1,3),held=V.reshape(-1,3),anchors=hands,thumb=np.stack(list(map(bone,['thumb.01','thumb.02','thumb.03']))),index=np.stack(list(map(bone,['index.01','index.02','index.03']))))
