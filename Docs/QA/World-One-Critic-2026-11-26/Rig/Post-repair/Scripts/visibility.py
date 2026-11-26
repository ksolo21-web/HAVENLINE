from pathlib import Path
import sys,numpy as np,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_ray_tri
d=Path(sys.argv[sys.argv.index('--')+1]); tri=np.load(d/'faces.npy');rest=np.load(d/'rest.npy');weld=np.unique(np.round(rest,5),axis=0,return_inverse=True)[1];fw=weld[tri];ft=tri.tolist()
def rawpairs(tree):
 a=np.array(tree.overlap(tree),int);a=a[a[:,0]<a[:,1]];a=a[~(fw[a[:,0],:,None]==fw[a[:,1],None,:]).any(axis=(1,2))];return set(map(tuple,a.tolist()))
before=rawpairs(BVHTree.FromPolygons(rest.tolist(),ft,all_triangles=True));stats=json.loads((d/'cross.json').read_text());reports={}
for name,index in [(n,i) for n in ['Walk','Run'] for i in range(0,len(np.load(d/(n+'.npy'),mmap_mode='r'))-1)]:
 phases=np.load(d/(name+'.npy'),mmap_mode='r');p=phases[index];tree=BVHTree.FromPolygons(p.tolist(),ft,all_triangles=True);pairs=rawpairs(tree)-before
 cameras={}
 for facing in [('right',1,0),('right toward',.84,.54),('half-away right',.84,-.54)]:
  tag,lateral,forward=facing;flat=np.array([11,0,-7])*lateral+np.array([7,0,11])*forward;yw=np.arctan2(flat[0],flat[2]);eye=Vector((7*np.cos(yw)-11*np.sin(yw),11,7*np.sin(yw)+11*np.cos(yw))).normalized()
  records=[]
  for a,b in pairs:
   el=[]
   for t,u in ((tri[a],tri[b]),(tri[b],tri[a])):
    t=[Vector(q) for q in p[t]];u=[Vector(q) for q in p[u]]
    for i in range(3):
     ray=t[(i+1)%3]-t[i];hit=intersect_ray_tri(*u,ray,t[i],True)
     if hit is not None and (hit-t[i]).dot(ray)>=0 and (hit-t[i]).length<=ray.length+1e-6:el.append(hit)
   if not el:continue
   mi=sum(el,Vector((0,0,0)))/len(el);nearest,normal,idx,dist=tree.ray_cast(mi+2*eye,-eye,2.002)
   if nearest is not None and (nearest-mi).length < .0015:
    records.append({'point':list(mi),'length':max((k-j).length for k in el for j in el),'rest_triangle_ids':[int(a),int(b)],'rest_centers':rest[tri[[a,b]]].mean(1).tolist()})
  cameras[tag]=records
 reports[name+':'+str(index)]={'time':float(index/120),'candidate_pairs':len(pairs),'camera_views':cameras}
 print(name,index/120,len(pairs),{k:(len(r),round(max([rec['length'] for rec in r]+[0])*1000,1)) for k,r in cameras.items()},flush=True)
(Path(sys.argv[-1])).write_text(json.dumps(reports))
