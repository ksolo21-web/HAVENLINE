import sys,json,hashlib,subprocess
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent; sys.path.insert(0,str(P))
from pose_asset import bake_factory
mP,tP,hero,work,video=map(Path,sys.argv[sys.argv.index('--')+1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(mP)=='9164395ec5280788b0cdc772a638856a4283ef835ff31ea93e668ccc3c4b50ee'
assert sha(tP)=='a7a9c19f1a0b3c25ba893a761863a12217e5272b1903a4c2e58f64b65a2b2e14'
source=json.loads(mP.read_bytes()); assert source['native_array_sha256']=='40e5a494bcf7c8df60cfe0ce6b2716f2f72c25f979cb8c8a354f00874633c449'
samples=source['samples']; assert [r['age_tick'] for r in samples]==list(range(0,177,4))
assert list(dict.fromkeys(r['phase'] for r in samples))==['idle','walk','run','turn','stop']
assert all(r['viewport']==[1280,720] and r['camera_size']==13 for r in samples)
source['actor_source_glb_sha256']=source['source_actor_glb_sha256']
bake=bake_factory(hero,source,mP)
C=np.array([[1,0,0],[0,0,-1],[0,1,0]],float)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
a=np.load(tP); terrain=bpy.data.meshes.new('Pinned-source numerical quarter-grid snow surface')
terrain.from_pydata((a['points']@C.T).tolist(),[],a['faces'].tolist());terrain.update()
ground=bpy.data.objects.new('Snow geometry only; no scene props',terrain);scene.collection.objects.link(ground)
for p in terrain.polygons:p.use_smooth=True
mat=bpy.data.materials.new('Source snow palette – detached neutral appearance')
mat.use_nodes=True; bs=mat.node_tree.nodes.get('Principled BSDF')
sRGB=lambda t:((t+.055)/1.055)**2.4
bs.inputs['Base Color'].default_value=(*map(sRGB,[.88,.93,.98]),1)
bs.inputs['Roughness'].default_value=.95; bs.inputs['Specular IOR Level'].default_value=.2
terrain.materials.append(mat)
world=bpy.data.worlds.new('Neutral study light');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.70,.76,.83,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65
# Neutral detached light only, no faux sun, post-effect/audio, snow noise or sky props.
target=Vector((0,-13,0)); bpy.ops.object.light_add(type='AREA',location=target+Vector((2,-3,8)))
light=bpy.context.object;light.data.energy=650;light.data.shape='DISK';light.data.size=10
light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
cdata=bpy.data.cameras.new('Exact stock orthographic camera');cam=bpy.data.objects.new('Native camera',cdata);scene.collection.objects.link(cam)
cdata.type='ORTHO';cdata.ortho_scale=13*1280/720;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.fps=15
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
frame=work/'one-frame.png';scene.render.filepath=str(frame)
oldsets=[(v,set(v)) for v in (bpy.data.meshes,bpy.data.materials,bpy.data.images)]
ff=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-f','image2pipe','-framerate','15','-vcodec','png','-i','pipe:0','-vf','format=yuv420p','-an','-c:v','libx264','-crf','21','-threads','2','-movflags','+faststart','-fs','16000000',str(video)],stdin=subprocess.PIPE)
n=0
keepers={52:'walk',108:'run',144:'turn'}
try:
 for s in samples:
  o,*cols=s['camera']; assert np.max(abs(np.array(cols)@np.array(cols).T-np.eye(3)))<1e-5
  T=Matrix(np.array(cols)@C.T).transposed().to_4x4(); T.translation=Vector(C@np.array(o));cam.matrix_world=T
  # Keep exact native mesh-world and animation-time matrices. No retarget or smoothing.
  row=dict(age_tick=s['age_tick'],**s['character']); posed=work/'one-posed.glb'; bake(row,posed)
  old=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(posed));posed.unlink()
  added=set(scene.objects)-old; body,=[o for o in added if o.type=='MESH']
  assert len(body.data.polygons)==96001 and len(body.data.materials)==1 and body.find_armature() is None
  images=[node.image for node in body.data.materials[0].node_tree.nodes if node.type=='TEX_IMAGE']
  assert len(images)>=3 and all(im and tuple(im.size)==(4096,4096) for im in images)
  bpy.ops.render.render(write_still=True)
  png=frame.read_bytes(); frame.unlink(); n+=1
  tag=keepers.get(s['age_tick'])
  if tag:
   assert s['phase']==tag
   with (P/(tag+'-stock.LOCAL.png')).open('xb') as f:f.write(png)
  ff.stdin.write(png);ff.stdin.flush()
  for o in added:bpy.data.objects.remove(o,do_unlink=True)
  for lib,original in oldsets:
   for entry in list(lib):
    if entry not in original and entry.users==0:lib.remove(entry)
finally:
 ff.stdin.close()
 assert ff.wait()==0 and n==45
assert video.stat().st_size<=16000000
