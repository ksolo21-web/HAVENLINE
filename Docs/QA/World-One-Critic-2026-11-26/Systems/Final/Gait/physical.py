"""Measure lower-leg / boot surface intersections from native Godot skin poses."""
from pathlib import Path
import json,sys
from mathutils.bvhtree import BVHTree
import numpy as np
folder,tracks,output=map(Path,sys.argv[-3:])
meta=json.loads((folder/'metadata.json').read_text())
p=np.fromfile(folder/'vertices.bin',np.float32).reshape(-1,3)
tri=np.fromfile(folder/'triangles.bin',np.int32).reshape(-1,3)
joint=np.fromfile(folder/'joints.bin',np.int32).reshape(-1,meta['weights'])
wt=np.fromfile(folder/'weights.bin',np.float32).reshape(joint.shape)
center=p[tri].mean(axis=1)
active=np.unique(tri[center[:,1]<.51])
rest=np.c_[p[active],np.ones(len(active),np.float32)]
joint,wt=joint[active],wt[active]
parts={}
for side,sign in [('L',1),('R',-1)]:
 for region,ceiling in [('boot',.211),('lower',.51)]:
  faces=tri[(center[:,0]*sign>0)&(center[:,1]<ceiling)]
  vertices,local=np.unique(faces,return_inverse=True)
  parts[side+region]=(np.searchsorted(active,vertices),local.reshape(-1,3).tolist())
n=len(meta['bones']);dtype=np.dtype([('stage','<u4'),('frame','<u4'),('m','<f4',(n,4,3))])
report={}
for row in np.fromfile(tracks,dtype=dtype):
 xyz=np.zeros_like(rest[:,:3])
 for k in range(joint.shape[1]):
  xyz+=np.einsum('nq,nqr->nr',rest,row['m'][joint[:,k]])*wt[:,k,None]
 geom={tag:xyz[ids] for tag,(ids,faces) in parts.items()}
 boxes={tag:(pos.min(axis=0),pos.max(axis=0)) for tag,pos in geom.items()}
 trees={}
 def overlap(a,b):
  lo0,hi0=boxes[a];lo1,hi1=boxes[b]
  if np.any(hi0<lo1) or np.any(hi1<lo0): return 0
  for tag in [a,b]:
   if tag not in trees:trees[tag]=BVHTree.FromPolygons(geom[tag].tolist(),parts[tag][1],all_triangles=True)
  return len(trees[a].overlap(trees[b]))
 stage=['walk','reverse','idle','run'][row['stage']]
 report.setdefault(stage,[]).append({'frame':int(row['frame']),'boot_boot':overlap('Lboot','Rboot'),'left_boot_right_lower':overlap('Lboot','Rlower'),'right_boot_left_lower':overlap('Rboot','Llower')})
output.write_text(json.dumps(report))
