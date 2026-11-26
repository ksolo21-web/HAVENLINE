import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
d=Path(sys.argv[-2]);out=Path(sys.argv[-1]);tri=np.load(d/'faces.npy');rest=np.load(d/'rest.npy');e=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[0,2]]]),axis=1),axis=0);ds=np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1);e=e[ds>.005];ds=ds[ds>.005];directions=[Vector((13*np.sin(i*np.pi/4),11,13*np.cos(i*np.pi/4))).normalized() for i in range(8)];report={}
for clip in ['Idle','Walk','Run']:
 a=np.load(d/(clip+'.npy'),mmap_mode='r');worst={};global_max=[0,0,0]
 for frame,p in enumerate(a):
  lens=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1);ratio=lens/ds; candidates=np.where((ratio>1.8)&(lens-ds>.01))[0];oi=int(ratio.argmax())
  if ratio[oi]>global_max[0]:global_max=[float(ratio[oi]),frame,e[oi].tolist()]
  if len(candidates)==0:continue
  tree=BVHTree.FromPolygons(p.tolist(),tri.tolist(),all_triangles=True)
  for i in candidates:
   center=Vector(p[e[i]].mean(0))
   for ai,eye in enumerate(directions):
    h,_,_,dist=tree.ray_cast(center+2*eye,-eye,2.001)
    if h is None or (h-center).length>.001:continue
    if worst.get(str(ai),{}).get('ratio',0)<ratio[i]:
     worst[str(ai)]={'frame':frame,'ratio':float(ratio[i]),'ids':e[i].tolist(),'rest_length':float(ds[i]),'posed_length':float(lens[i]),'rest_center':rest[e[i]].mean(0).tolist(),'center':list(center)}
 report[clip]={'worst':global_max,'visible_by_heading':worst}
 print(clip,global_max,[(h,round(r['ratio'],2),r['frame']) for h,r in worst.items()],flush=True)
out.write_text(json.dumps(report,indent=2))
