from pathlib import Path
import numpy as np,json,sys,hashlib,struct
p=Path('/tmp/havenline-critic95-post/geom')
rack=np.fromfile(p/'rack-v',np.float32).reshape(-1,3)
from scipy.spatial import cKDTree
rr=np.fromfile(p/'rack-f',np.int32).reshape(-1,3)
# Vertical rays through underside candidate vertices, using barycentric x,z within a frame triangle.
def support(vs):
 low=vs[:,1].min()
 pts=vs[vs[:,1]<low+.055]; mind=100.;maxg=0;minpt=None
 for x,y,z in pts:
  a,b,c=rack[rr].transpose(1,0,2);u=b-a;v=c-a
  den=u[:,0]*v[:,2]-v[:,0]*u[:,2]; valid=np.abs(den)>1e-8
  den=np.where(valid,den,1);s=((x-a[:,0])*v[:,2]-v[:,0]*(z-a[:,2]))/den;t=(u[:,0]*(z-a[:,2])-(x-a[:,0])*u[:,2])/den
  ok=valid&(s>=0)&(t>=0)&(s+t<=1);h=a[:,1]+s*u[:,1]+t*v[:,1];h=h[ok&(h<=y+.04)]
  if len(h):
   d=np.min(np.abs(y-h))
   if d<mind:mind=d;minpt=(x,y,z)
   maxg+=1
 return dict(underside_samples=len(pts),rays_over_rack=maxg,min_vertical_surface_distance_m=None if minpt is None else round(float(mind),5))
result={'rack_bounds_m':[rack.min(0).tolist(),rack.max(0).tolist()],'support':{k:support(np.fromfile(p/(k+'0-v'),np.float32).reshape(-1,3)) for k in ['wood','stone','meat','coal','slate','metal']}}
print(result)
r=Path('/workspace/shared/downloads/Havenline/critic-95/Rig/Post-repair');(r/'Rack-support.json').write_text(json.dumps(result,indent=2,default=int))
def access(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];return np.frombuffer(b,dtype={5126:'<f4',5123:'<u2',5121:'u1',5125:'<u4'}[a['componentType']],count=a['count']*{'VEC4':4,'VEC3':3,'VEC2':2,'SCALAR':1,'MAT4':16}[a['type']],offset=v.get('byteOffset',0)+a.get('byteOffset',0))
def glb(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
base=Path('/dev/shm/havenline-world/Game/assets/characters/Character1Fresh.glb')
g,b=glb(base); attrs=g['meshes'][0]['primitives'][0]['attributes'];p0=access(g,b,attrs['POSITION']).reshape(-1,3);q={};orig=Path('/dev/shm/havenline-field/qa/rig-critic/refresh12/eval')
for label,dir in [('v2',Path('/dev/shm/hvn-rig95-hem')),('v3',Path('/workspace/scratch/hem95-v3'))]:
 gg,bb=glb(dir/'candidate.glb'); changed=[i for i in range(len(g['accessors'])) if not np.array_equal(access(g,b,i),access(gg,bb,i))];j=access(g,b,attrs['JOINTS_0']).reshape(-1,4);jj=access(gg,bb,attrs['JOINTS_0']).reshape(-1,4);w=access(g,b,attrs['WEIGHTS_0']).reshape(-1,4);ww=access(gg,bb,attrs['WEIGHTS_0']).reshape(-1,4);vchg=(j!=jj).any(1)|(w!=ww).any(1);rows={}
 f=np.load(dir/'eval/faces.npy');edges=np.unique(np.sort(f[:,[0,1,1,2,2,0]].reshape(-1,2),axis=1),axis=0);a0,a1=edges.T;length=np.linalg.norm(p0[a0]-p0[a1],axis=1);mask=length>0.005
 for c in ['Idle','Walk','Run']:
  file=np.load(dir/('eval/'+c+'.npy'),mmap_mode='r');old=np.load(orig/(c+'.npy'),mmap_mode='r');peak=(0,);target=(0,);motion=0
  for i,(xyz,prev) in enumerate(zip(file,old)):
   strain=np.linalg.norm(xyz[a0]-xyz[a1],axis=1)/np.maximum(length,1e-8);strain[~mask]=0;k=np.argmax(strain);v=float(strain[k]);peak=max(peak,(v,i,int(a0[k]),int(a1[k])));target=max(target,(float(np.linalg.norm(xyz[3566]-xyz[3568])/np.linalg.norm(p0[3566]-p0[3568])),i));motion=max(motion,float(np.max(np.linalg.norm(xyz[~vchg]-prev[~vchg],axis=1))))
  rows[c]={'worst_edge_gt5mm':[round(peak[0],4),*peak[1:]],'original_bad_edge_max':list(target),'maximum_unchanged_vertex_pose_difference_m':motion}
 q[label]={'sha256':hashlib.sha256((dir/'candidate.glb').read_bytes()).hexdigest(),'glb_json_unchanged':g==gg,'changed_accessors':changed,'expected_skin_accessors':[attrs['JOINTS_0'],attrs['WEIGHTS_0']],'affected_skin_vertices':int(vchg.sum()),'changed_rest_y_range':p0[vchg,1].min().item(),'metrics':rows}
print(q);(r/'Candidates.json').write_text(json.dumps(q,indent=2))
