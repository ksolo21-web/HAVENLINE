from pathlib import Path
from mathutils.bvhtree import BVHTree
import numpy as np,json
import os
q=Path(os.environ['HAVENLINE_GEAR_GEOMETRY']);out=Path(os.environ['HAVENLINE_PROBE_RESULTS'])
raw=json.loads((q/'transforms.json').read_text());src={}
for name in raw['meshes']:
 vs=np.fromfile(q/(name+'-v'),np.float32).reshape(-1,3);fs=np.fromfile(q/(name+'-f'),np.int32).reshape(-1,3);src[name]=(vs,fs.tolist())
for folder in sorted(sub for sub in q.iterdir() if sub.is_dir()):
 for path in sorted(folder.glob('*-v')):
  k=path.name[:-2]; ident=folder.name+'/'+k
  vs=np.fromfile(path,np.float32).reshape(-1,3); faces=np.fromfile(folder/(k+'-f'),np.int32).reshape(-1,3)
  src[ident]=(vs,faces.tolist())
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
 print(setting, len(samples), result[setting]['worst'],flush=True)

cargo_pairs = []
for i, (left, (lo, hi, a)) in enumerate(gear[0].items()):
 section,_,k=left.rpartition('/')
 if k=='rack' or k.startswith('divider-'):continue
 for right,(rlo,rhi,b) in list(gear[0].items())[i+1:]:
  category,_,n=right.rpartition('/')
  if category!=section or n=='rack' or n.startswith('divider-') or k.rstrip('0123456789')==n.rstrip('0123456789'):
   continue
  if (lo>rhi).any() or (hi<rlo).any():continue
  hits=a.overlap(b)
  if hits:cargo_pairs.append({'left':left,'right':right,'triangle_pairs':len(hits)})

sets={}
for ident in gear[0]:
 section,_,k=ident.rpartition('/')
 label=section or '30-mixed'
 sets.setdefault(label,[])
 if not (k=='rack' or k.startswith('divider-')):sets[label].append(k)
assert len(sets['full-72'])==72
(out/'Gear-contact-120Hz.json').write_text(json.dumps({'method':'Godot imported triangles for settled packs and the first tool slot, sampled at 120 Hz over a 0.89-second orbit. Twelve relative character headings and both starter and expanded orbit radii are tested. Additional slots occupy the same ellipse 120 degrees apart. Each load case runs in the actual normal gameplay camera.','scope':'Rendered solids. Transparent ribbons and loose items travelling through the air are excluded.','loads':{k:len(v) for k,v in sets.items()},'different_material_triangle_intersections':cargo_pairs,'mesh_counts':raw['meshes'],'tests':result},indent=2)+'\n')
