from pathlib import Path
from mathutils.bvhtree import BVHTree
import numpy as np,json
q=Path('/tmp/havenline-critic95-post/geom');out=Path('/workspace/shared/downloads/Havenline/critic-95/Rig/Post-repair')
raw=json.loads((q/'transforms.json').read_text());src={}
for name in raw['meshes']:
 vs=np.fromfile(q/(name+'-v'),np.float32).reshape(-1,3);fs=np.fromfile(q/(name+'-f'),np.int32).reshape(-1,3);src[name]=(vs,fs.tolist())
def tree(v,f):return BVHTree.FromPolygons(v.tolist(),f,all_triangles=True)
def box(v):return v.min(0),v.max(0)
gear={}
for yaw in range(0,360,30):
 a=np.deg2rad(yaw);c=np.cos(a);s=np.sin(a);rot=np.array([[c,0,s],[0,1,0],[-s,0,c]])
 gear[yaw]={}
 for k,(v,f) in src.items():
  if k in ['axe','pickaxe']:continue
  vv=v@rot.T;lo,hi=box(vv);gear[yaw][k]=(lo,hi,tree(vv,f))
result={};csv=[]
for setting,samples in raw['samples'].items():
 kind=setting[:-1];v,f=src[kind];head=0;rows=[];keys={}
 for row in samples:
  t=row[0];M=np.array(row[1:]).reshape(3,4);vv=v@M[:,:3].T+M[:,3];lo,hi=box(vv);bt=None
  for yaw,collection in gear.items():
   for k,(b0,b1,bvh) in collection.items():
    if (lo>b1).any() or (hi<b0).any():continue
    if bt is None:bt=tree(vv,f)
    pairs=bt.overlap(bvh)
    if pairs:
     key=f'{yaw}/{k}';keys[key]=keys.get(key,0)+1
     rows.append((len(pairs),float(t),yaw,k,pairs[0]));head+=len(pairs)
 result[setting]={'phase_samples':len(samples),'headings':len(gear),'collision_sample_pairs':len(rows),'triangle_pairs_with_repetitions':head,'affected':keys,'worst':sorted(rows,reverse=True)[:5]}
 print(setting,result[setting]['worst'],flush=True)
(out/'Gear-contact-120Hz.json').write_text(json.dumps({'method':'Godot actual source geometry, fully transformed real rendered cargo triangles and first weapon slot at 120Hz over a .89s turn; 12 relative actor headings, 1 and 3 tool orbit radii. Additional tools are 120 degrees apart on same path. Five carried units credited per kind. Tall-rack extent changes on zoom; first slots here are the near-body tiers. Positive pairs are surface intersections within the gameplay fixture.','stage':'Current mining build. Transparent ribbons and outgoing item flights are not solids in this check.','mesh_counts':raw['meshes'],'tests':result},indent=2)+'\n')
