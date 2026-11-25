"""Detached render stage. Never a substitute for native game lighting or pixels."""
import bpy, sys, runpy, hashlib, json, subprocess
from pathlib import Path
from mathutils import Matrix, Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_asset import bake_factory
P=Path(__file__).resolve().parent
manifest,stage,crown,actor,disposable,output=map(Path,sys.argv[sys.argv.index('--')+1:])
assert disposable.is_dir() and not output.exists()
verify=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads(manifest.read_bytes())
assert m['version']==1 and m['native_role']=='EXAMINER_SHADOW_ONLY'
assert m['actor_evidence']=='exact native evaluated skinned surfaces with imported original character materials and UV'
assert verify(stage)=='51e34077a346b0f60951d9ee18c43276c82e8a9787af8f82cdf14a1a7f84c31e'
assert verify(stage.parent/'paint-inlay.png')=='9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'
assert m['fps']==15 and len({x['age'] for x in m['original_native_source_spot_checks']})>=3
frames=m['frames']; ages=[f['age_tick'] for f in frames]
assert ages==list(range(0,265,4))+[266]
assert len(frames)==68
hold_repeats=8 # same actual endpoint frames, not eight new captures
for f in frames:
 assert f['viewport']==[1280,720] and f['camera_size']==13 and f['camera_projection']=='orthographic'
 assert len(f['crowns'])==2 and all(len(t)==4 and all(len(v)==3 for v in t) for t in [f['camera'],*f['crowns']])
 assert 'poses_by_skin_binding_slot' in f and 'mesh_world' in f
bake=bake_factory(actor,m,manifest)
sys.argv=[sys.argv[0],'--',str(stage),str(crown),'stocked',str(disposable/'review.blend')]
runpy.run_path(str(P/'import_stage_blender.py'))
scene=bpy.context.scene
cam=scene.camera
held=sorted([o for o in scene.objects if o.type=='MESH' and len(o.data.polygons)==1300],key=lambda o:o.name)
assert len(held)==2
source_B=Matrix(((1.,0.,0.),(0.,0.,-1.),(0.,1.,0.)))
def native(t):
 o,*bc=t
 R=Matrix(bc).transposed()
 T=(source_B@R@source_B.transposed()).to_4x4(); T.translation=source_B@Vector(o)
 return T
world=bpy.data.worlds.new('Neutral overcast detached diagnostic');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.70,.76,.83,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65
target=Vector((-6.18,-5.755,.012))
bpy.ops.object.light_add(type='AREA',location=target+Vector((.5,-2,5.5)));light=bpy.context.object
light.data.energy=370;light.data.shape='DISK';light.data.size=6
light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4
scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.fps=15
oldmeshes=set(bpy.data.meshes); oldimages=set(bpy.data.images); oldmats=set(bpy.data.materials)
# Original imported crown mesh is already in Blender coordinates, local from
# this source's identity glTF node. Reject glTF variants with a node transform.
assert len(held[0].data.materials)==2
assert [m.name for m in held[0].data.materials]==['Bark | painted ridges','End grain | amber']
assert len(held[0].data.color_attributes)>0 and held[0].data==held[1].data
out=disposable/'one-frame.png';scene.render.filepath=str(out)
ff=subprocess.Popen(['ffmpeg','-nostdin','-v','error','-f','image2pipe','-framerate','15','-vcodec','png','-i','pipe:0',
 '-vf','format=yuv420p','-an','-c:v','libx264','-crf','20','-preset','fast','-threads','2','-movflags','+faststart',
 '-fs','24000000',str(output)],stdin=subprocess.PIPE)
count=0
try:
 for row in frames:
  cam.matrix_world=Matrix([source_B@Vector(x) for x in row['camera'][1:]]).transposed().to_4x4()
  cam.location=source_B@Vector(row['camera'][0]); cam.data.ortho_scale=13*1280/720
  for n,tr in zip(held,row['crowns']):n.matrix_world=native(tr)
  objs=set(scene.objects)
  posed=disposable/'posed-character-LOCAL.glb'
  bake(row,posed)
  bpy.ops.import_scene.gltf(filepath=str(posed))
  posed.unlink()
  added=set(scene.objects)-objs
  meshes=[o for o in added if o.type=='MESH']
  assert meshes and all(obj.data.materials for obj in meshes)
  assert all(obj.find_armature() is None for obj in meshes)
  assert sum(len(o.data.polygons) for o in meshes)==row['actor_triangles']
  bpy.ops.render.render(write_still=True)
  png=out.read_bytes()
  if row['age_tick'] in (0,64,172,266):
   sample=P/('frame-%03d.LOCAL.png'%row['age_tick'])
   with sample.open('xb') as f:f.write(png)
   sample.chmod(0o600)
  ff.stdin.write(png)
  if row['age_tick']==266:
   for _ in range(hold_repeats):ff.stdin.write(png)
  ff.stdin.flush(); out.unlink()
  for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
  for lib,keep in [(bpy.data.meshes,oldmeshes),(bpy.data.materials,oldmats),(bpy.data.images,oldimages)]:
   for entry in list(lib):
    if entry not in keep and entry.users==0:lib.remove(entry)
  count+=1
finally:
 ff.stdin.close()
 assert ff.wait()==0 and count==len(frames)
assert output.is_file() and output.stat().st_size<=24_000_000
