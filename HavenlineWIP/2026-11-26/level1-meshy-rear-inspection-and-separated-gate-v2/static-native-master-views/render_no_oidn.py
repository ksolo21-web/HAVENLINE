"""Actual orthographic static preview of the private exact GLB masters; no game QA."""
from pathlib import Path
from mathutils import Vector
import bpy, json, hashlib
root=Path(__file__).resolve().parent
src=root.parent/'meshy-models'
assets={'fence':'352dce12b2910cf35feca462cb12a22fdef1dbe86bec8ffe83d4f89c45235908','gate':'c5256ca7ac3956c91b19654076afa80b96fede20873be704136ab89edf4709b3'}
def point(obj, at):
 obj.rotation_euler=(at-obj.location).to_track_quat('-Z','Y').to_euler()
for name,pin in assets.items():
 path=src/f'{name}-front.glb'
 assert hashlib.sha256(path.read_bytes()).hexdigest()==pin
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(path))
 sc=bpy.context.scene
 mesh=[o for o in sc.objects if o.type=='MESH']
 assert len(mesh)==1
 vv=[o.matrix_world@Vector(c) for o in mesh for c in o.bound_box]
 lo=Vector(tuple(min(p[i] for p in vv) for i in range(3)))
 hi=Vector(tuple(max(p[i] for p in vv) for i in range(3)))
 at=(lo+hi)/2
 assert hi.z-lo.z>.80 and hi.y-lo.y<.40
 sc.world=bpy.data.worlds.new('StudioGrey')
 sc.world.use_nodes=True
 sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.24,.24,.24,1)
 sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.45
 for label,loc,power,size in [('Key',(0,-3,4),320,4),('Rear',(0,3,4),335,4),('Fill',(3,0,2),110,3)]:
  d=bpy.data.lights.new(label,'AREA');d.energy=power;d.size=size
  l=bpy.data.objects.new(label,d);sc.collection.objects.link(l)
  l.location=Vector(loc)+at;point(l,at)
 camdata=bpy.data.cameras.new('Actual orthographic camera')
 camdata.type='ORTHO';camdata.ortho_scale=2.28
 cam=bpy.data.objects.new('Camera',camdata);sc.collection.objects.link(cam);sc.camera=cam
 sc.render.engine='CYCLES'
 sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=False
 sc.render.threads_mode='FIXED';sc.render.threads=8
 sc.render.resolution_x=720;sc.render.resolution_y=520;sc.render.resolution_percentage=100
 sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
 sc.view_settings.view_transform='Standard'
 sc.render.film_transparent=False
 statuses=[]
 for label,view in [('front-3q',(.45,-1.,.34)),('rear-3q',(-.45,1.,.34)),('profile',(-1,0,.15))]:
  cam.location=at+Vector(view).normalized()*5
  point(cam,at)
  p=root/f'{name}-{label}.png';sc.render.filepath=str(p)
  bpy.ops.render.render(write_still=True)
  assert p.is_file()
  statuses.append({'view':label,'src':pin,'render_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (root/f'{name}-render-receipt.json').write_text(json.dumps(statuses,indent=2)+'\n')
