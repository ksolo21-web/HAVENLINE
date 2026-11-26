"""BVH narrow-phase checks on real game poses in the player's frame."""
from pathlib import Path
import json,os
import numpy as np
from mathutils.bvhtree import BVHTree
folder=Path(os.environ['HAVENLINE_GEAR_GEOMETRY'])
out=Path(os.environ['HAVENLINE_PROBE_RESULTS'])
meta=json.loads((folder/'transforms.json').read_text())
bi=json.loads((folder/'body-info.json').read_text())
p=np.fromfile(folder/'body-v',np.float32).reshape(-1,3)
tri=np.fromfile(folder/'body-f',np.int32).reshape(-1,3)
jnt=np.fromfile(folder/'body-bone-ids',np.int32).reshape(-1,bi['weights_per_vertex'])
weights=np.fromfile(folder/'body-weights',np.float32).reshape(jnt.shape)
rest=np.c_[p,np.ones(len(p),np.float32)]
prop={}
hashes={}
import hashlib
def add_prop(k,v,f):
 h=hashlib.sha256(v.tobytes()+f.tobytes()).hexdigest()
 if h in hashes:
  hashes[h][1].append(k)
  return
 used,local=np.unique(f,return_inverse=True)
 vertices=v[used]
 hashes[h]=(k,[k]);prop[k]=(vertices.min(0),vertices.max(0),BVHTree.FromPolygons(vertices.tolist(),local.reshape(-1,3).tolist(),all_triangles=True))
def load_props(where,items,prefix):
 for k in items:
  if k in ('axe','pickaxe'):continue
  v=np.fromfile(where/(k+'-v'),np.float32).reshape(-1,3)
  f=np.fromfile(where/(k+'-f'),np.int32).reshape(-1,3)
  if k=='rack':
   for m in json.loads((where/'rack-classes.json').read_text()):
    fs=f[m['first_face']:m['first_face']+m['count']]
    if m['name']!='ExpeditionPackFrame':
     add_prop(prefix+'rack.'+m['name'],v,fs);continue
    # Split connected, welded donor components into shoulder webbing & buckles, rails, and shelf slats.
    import mathutils
    x=np.asarray([float(z) for z in m['local_to_world'][len('Transform3D('):-1].split(',')]).reshape(4,3)
    vloc=(v-x[3])@np.linalg.inv(x[:3])
    welded,order=np.unique(np.round(vloc,4),axis=0,return_inverse=True)
    wf=order[fs]
    parent=list(range(len(welded)))
    def find(i):
     while parent[i]!=i:
      parent[i]=parent[parent[i]];i=parent[i]
     return i
    for a,b,c in wf:
     parent[find(b)]=find(a);parent[find(c)]=find(a)
    groups={}
    for i,face in enumerate(wf):groups.setdefault(find(face[0]),[]).append(i)
    for ids in groups.values():
     sel=fs[ids];vpart=vloc[sel.reshape(-1)]
     ext=vpart.max(0)-vpart.min(0);zmean=vpart[:,2].mean();side='L' if vpart[:,0].mean()>0 else 'R'
     if ext[0]<.08 and ext[2]>.45:cat='webbing.'+side
     elif zmean>.66 and ext[1]<.1:cat='buckle.'+side
     elif ext[1]>.5:cat='backrail.'+side
     elif ext[0]>.4:cat='crossbar.'+str(round(float(vpart[:,1].mean()),2))
     else:cat='fitting.'+side
     add_prop(prefix+'rack.'+cat,v,sel)
   continue
  add_prop(prefix+k,v,f)
load_props(folder,meta['meshes'],'')
for section in sorted(folder.iterdir()):
 if section.is_dir() and section.name.startswith(('single-','timber-','full-')):
  load_props(section,[p.name[:-2] for p in section.glob('*-v')],section.name+'/')
r={}
names=['idle','walk','run','hard_turn','brake']
dtype=np.dtype([('stage','<u4'),('tick','<u4'),('m','<f4',(len(bi['bones']),4,3))])
faces=tri.tolist()
for row in np.fromfile(folder/'body-poses',dtype=dtype):
 stage=names[row['stage']]
 info=r.setdefault(stage,dict(frames=0,overlapping_props={},worst={}));info['frames']+=1
 xyz=np.zeros_like(p)
 for i in range(jnt.shape[1]):
  xyz+=np.einsum('nq,nqr->nr',rest,row['m'][jnt[:,i]])*weights[:,i,None]
 lo=xyz.min(0);hi=xyz.max(0)
 # The normalized player frame gives all poses the same local frame as the staged cargo.
 # Restrict the broad phase to the imported real triangles with any overlap in actor coordinates.
 minx=xyz[tri].min(1);maxx=xyz[tri].max(1)
 for k,(a,b,bvh) in prop.items():
  if np.any(lo>b) or np.any(hi<a):continue
  idx=np.flatnonzero((maxx>=a).all(1)&(minx<=b).all(1))
  if len(idx)==0:continue
  vertices,inds=np.unique(tri[idx],return_inverse=True)
  bt=BVHTree.FromPolygons(xyz[vertices].tolist(),inds.reshape(-1,3).tolist(),all_triangles=True)
  hits=bt.overlap(bvh)
  if not hits:continue
  inf=info['overlapping_props'].setdefault(k,{'frames':0,'triangle_pairs':0,'worst_frame_pairs':0,'bone_groups':[]})
  inf['frames']+=1;inf['triangle_pairs']+=len(hits)
  if len(hits)>inf['worst_frame_pairs']:
   inf['worst_frame_pairs']=len(hits);inf['worst_frame']=int(row['tick'])
   bfaces=tri[idx[list({q[0] for q in hits})]]
   verts=np.unique(bfaces)
   scores=np.bincount(jnt[verts].reshape(-1),weights=weights[verts].reshape(-1),minlength=len(bi['bones']))
   inf['bone_groups']=[bi['bones'][i] for i in np.argsort(-scores)[:3] if scores[i]>.05]
   inf['body_hit_bounds_m']=[xyz[verts].min(0).tolist(),xyz[verts].max(0).tolist()]
report=dict(method='All skinned triangles of the imported character from its 50 native joint transforms after each physics tick of real touch-input play. Held five of each material. Triangle intersections with the rendered solid cargo and visible frame parts only; nearest attachment contact is interpreted separately. Broad-phase triangle AABBs followed by exact triangle BVH intersection tests.', body=bi,duplicates={k:v for k,v in hashes.values() if len(v)>1},stages=r)
(out/'Body-and-pack.json').write_text(json.dumps(report,indent=2)+'\n')
print({name:{k:z['frames'] for k,z in d['overlapping_props'].items()} for name,d in r.items()})
