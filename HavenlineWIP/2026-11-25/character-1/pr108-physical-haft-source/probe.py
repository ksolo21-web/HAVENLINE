import hashlib,json,pathlib,struct,sys
import numpy as np
from scipy.spatial.transform import Rotation,Slerp
root=pathlib.Path(sys.argv[1])
const=dict(axe='9d7ab5e3cbb42f64b3ce0451e6e5171954dc172e',pickaxe='f6e12004a1bcc261df842f3dc758fdabd4cd269f', hero='9d11c756195ffaac649b7f4c01d80f29d50dfec1', sockets='e075b7bb6cb824a853e3b81b4bdadd6fc9f886bb',layout='5bac3496d3cf1b952736e8ecafa70f9978ffdbf5')
def read(path,key):
 b=(root/path).read_bytes()
 h=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
 assert h==const[key],(key,h)
 return b
def glb(path,key):
 b=read(path,key)
 n=struct.unpack_from('<I',b,12)[0]
 return json.loads(b[20:20+n]),b[28+n:]
def decode(g,i):
 j,b=g
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
 d=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']])
 c={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
 return np.ndarray((a['count'],c),dtype=d,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',c*d.itemsize),d.itemsize)).copy().astype(float)
hero=glb('assets/characters/Character1.glb','hero')
src=json.loads(read('assets/characters/character1_sockets.json','sockets'))
layout=json.loads(read('layout.json','layout'))
nodes=hero[0]['nodes']; parents={c:i for i,n in enumerate(nodes) for c in n.get('children',[])}
indices={n['name']:i for i,n in enumerate(nodes) if 'name' in n}
meshnode=next(n for n in nodes if 'mesh' in n)
pv=np.concatenate([decode(hero,p['attributes']['POSITION']) for p in hero[0]['meshes'][meshnode['mesh']]['primitives']])
factor=layout['actor_height']/np.ptp(pv[:,1])
names=['L_Hand','R_Hand']
offset=[src['left_palm_local'],src['right_palm_local']]
def poses(action):
 a=next(a for a in hero[0]['animations'] if a['name'].endswith(':'+action))
 tracks={}
 for ch in a['channels']:
  s=a['samplers'][ch['sampler']]
  assert s.get('interpolation','LINEAR')=='LINEAR'
  ts=decode(hero,s['input']).ravel(); vs=decode(hero,s['output'])
  kind=ch['target']['path']
  tracks[ch['target']['node'],kind]=(ts, Slerp(ts,Rotation.from_quat(vs)) if kind=='rotation' and len(ts)>1 else vs)
 duration=max(ts[-1] for ts,v in tracks.values())
 for t in np.linspace(0,duration,61):
  memo={}
  def tf(i):
   if i in memo:return memo[i]
   n=nodes[i]
   assert 'matrix' not in n
   def get(k,default):
    if (i,k) not in tracks:return n.get(k,default)
    ts,v=tracks[i,k]; t1=np.clip(t,ts[0],ts[-1])
    if k=='rotation' and isinstance(v,Slerp): return v(t1).as_quat()
    return [np.interp(t1,ts,v[:,n]) for n in range(v.shape[1])]
   m=np.eye(4)
   m[:3,:3]=Rotation.from_quat(get('rotation',[0,0,0,1])).as_matrix()@np.diag(get('scale',[1,1,1]))
   m[:3,3]=get('translation',[0,0,0])
   if i in parents:m=tf(parents[i])@m
   memo[i]=m
   return m
  palms=np.array([(tf(indices[n])@np.r_[o,1])[:3] for n,o in zip(names,offset)])
  yield t,palms
scale=.95/.70
radial=.08/scale
rows={}
# Offline exact intersection of a line parallel to X in tool space with original triangle surfaces.
# Barycentric solve in YZ, so intersection can read actual cross-section envelope rather than guessed cylinder.
def slice_x(V,T,y,z=0):
 tri=V[T]; yz=tri[:,:,1:]; B=(yz[:,1:]-yz[:,:1]).transpose(0,2,1)
 ok=np.abs(np.linalg.det(B))>1e-12
 B=B[ok]; tri=tri[ok]; q=(np.array([y,z])-yz[ok,0])[:,:,None]
 b=np.linalg.solve(B,q)[:,:,0]
 q=(b[:,0]>=-1e-8)&(b[:,1]>=-1e-8)&(b.sum(axis=1)<=1+1e-8)
 return tri[q,0,0]+np.sum(b[q]*(tri[q,1:,0]-tri[q,:1,0]),axis=1)
for action, tool in [('chop','axe'),('mine','pickaxe'),('carry','axe')]:
 g=glb('assets/tools/'+tool+'.glb',tool);p=g[0]['meshes'][0]['primitives'][0]
 assert len(g[0]['nodes'])==1 and set(g[0]['nodes'][0])=={'mesh','name'}
 v=decode(g,p['attributes']['POSITION']);tri=decode(g,p['indices']).astype(int).reshape(-1,3)
 bands=np.array(src['axe_grip_y' if tool=='axe' else 'pick_grip_y'])
 section=[]
 for y in bands:
  cuts=slice_x(v,tri,y)
  section.append({'model_y_m':y,'x_min_m':min(cuts),'x_max_m':max(cuts),'world_negative_x_radius_mm':-min(cuts)*scale*1000,'marker_inside_beyond_negative_edge_mm':(-min(cuts)*scale-.08)*1000})
 seq=[]
 for t,palms in poses(action):
  for scenario,actor_factor in [('direct_pr_asset_host',1.),('game_source_height_fit',factor)]:
   d=np.linalg.norm(palms[0]-palms[1])*actor_factor; lower='L' if palms[0,1]<=palms[1,1] else 'R'
   y=bands.mean()+np.array([-d,d])/(2*scale)
   negatives=[]
   for yy in y:
    cuts=slice_x(v,tri,yy)
    negatives.append(round((-min(cuts)-radial)*scale*1000,6) if len(cuts) else None)
   seq.append(dict(t_s=float(t),scenario=scenario,lower=lower,palm_span_m=d,offset_from_each_requested_band_mm=abs(d-np.ptp(bands)*scale)*500,actual_local_y_m=y.tolist(),x_axis_margin_inside_mm=negatives))
 rows[action]={'tool':tool,'exact_band_sections':section,'fit':{}}
 for scenario in {k['scenario'] for k in seq}:
  subset=[s for s in seq if s['scenario']==scenario]
  rounded=lambda x:round(float(x),7)
  invals=[a for s in subset for a in s['x_axis_margin_inside_mm'] if a is not None]
  rows[action]['fit'][scenario]=dict(samples=len(subset),low_handedness_counts={k:sum(s['lower']==k for s in subset) for k in 'LR'},palm_span_m=[rounded(min(s['palm_span_m'] for s in subset)),rounded(max(s['palm_span_m'] for s in subset))],band_error_each_mm=[rounded(min(s['offset_from_each_requested_band_mm'] for s in subset)),rounded(max(s['offset_from_each_requested_band_mm'] for s in subset))],x_negative_outer_edge_margin_mm=[min(invals),max(invals)] if invals else None,sections_missing=sum(a is None for s in subset for a in s['x_axis_margin_inside_mm']),witness_samples=[subset[i] for i in [0,15,30,45,60]])
print(json.dumps({'pins':const,'assumptions':'Offline exact source glTF local TRS linear/shortest quaternion interpolation, portrait-neutral up axis and source height-fit; no Godot import/skin/hand surface proof. Margin only to negative X outer edge at actual modeled socket y and z=0, not full intersection or penetration. Actor height fit is source model estimate, not measured native runtime.', 'source_actor_height_factor':factor,'scale':scale,'actions':rows},indent=2,sort_keys=True))
