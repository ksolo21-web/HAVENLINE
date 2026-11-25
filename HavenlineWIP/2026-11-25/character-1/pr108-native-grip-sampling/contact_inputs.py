"""Summarize exact native socket-to-tool triangles; not hand skin contact."""
import hashlib,json,pathlib,struct,sys
import numpy as np

model_root=pathlib.Path(sys.argv[1])
path=pathlib.Path(sys.argv[2])
pins={'axe':'9d7ab5e3cbb42f64b3ce0451e6e5171954dc172e','pickaxe':'f6e12004a1bcc261df842f3dc758fdabd4cd269f'}
def glb(tool):
 b=(model_root/'assets'/'tools'/f'{tool}.glb').read_bytes()
 assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==pins[tool]
 n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);q=b[28+n:]
 assert len(j['nodes'])==1 and set(j['nodes'][0])=={'mesh','name'}
 p=j['meshes'][0]['primitives'][0]
 def acc(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
  dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']]); k={'SCALAR':1,'VEC3':3}[a['type']]
  return np.ndarray((a['count'],k),dtype=dt,buffer=q,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',k*dt.itemsize),dt.itemsize)).copy()
 v=acc(p['attributes']['POSITION']).astype(float)
 return v[acc(p['indices']).reshape(-1,3)]
def transform(mat):
 return np.array(mat['origin']),np.stack([mat[k] for k in 'xyz'],axis=1)

def distance(point,tri):
 a,b,c=np.transpose(tri,(1,0,2))
 e=b-a;f=c-a
 ee=np.einsum('ij,ij->i',e,e);ff=np.einsum('ij,ij->i',f,f);ef=np.einsum('ij,ij->i',e,f)
 lhs=point-a;de=np.einsum('ij,ij->i',e,lhs);df=np.einsum('ij,ij->i',f,lhs)
 den=ee*ff-ef**2
 u=np.divide(ff*de-ef*df,den,out=np.zeros_like(den),where=den>1e-20)
 v=np.divide(ee*df-ef*de,den,out=np.zeros_like(den),where=den>1e-20)
 q=a+u[:,None]*e+v[:,None]*f
 good=(den>1e-20)&(u>=0)&(v>=0)&(u+v<=1)
 options=[np.where(good,np.linalg.norm(q-point,axis=1),np.inf)]
 for x,y in ((a,b),(b,c),(c,a)):
  d=y-x;sq=np.einsum('ij,ij->i',d,d)
  t=np.clip(np.divide(np.einsum('ij,ij->i',point-x,d),sq,out=np.zeros_like(sq),where=sq>1e-20),0,1)
  options.append(np.linalg.norm(x+t[:,None]*d-point,axis=1))
 return float(np.min(options))
rows=[];header=verdict=None
for line in path.read_text().splitlines():
 if line.startswith('GRIP_HEADER '):header=json.loads(line.split(' ',1)[1])
 if line.startswith('GRIP_SAMPLE '):rows.append(json.loads(line.split(' ',1)[1]))
 if line.startswith('GRIP_VERDICT '):verdict=json.loads(line.split(' ',1)[1])
assert verdict and verdict['samples']==36 and not verdict['failures'] and len(rows)==36
triangles={k:glb(k) for k in pins}
out={}
for a in ('carry','chop','mine'):
 samples=[]
 for r in [t for t in rows if t['action']==a]:
  assert len(r['tool_visuals'])==1
  tool_o,tool_b=transform(r['tool_visuals'][0]['world'])
  tri=triangles[r['tool']]
  w=tri@tool_b.T+tool_o
  # Restrict to polygons having all vertices in the lower, clearly head-free asset region.
  # Full exact mesh result separately avoids misstating this subset as the entire handle.
  bare=tri[:,:,1].max(axis=1)<=-.029
  assert np.count_nonzero(bare)>10
  palms={k:np.array(r['anatomical_'+k]['origin']) for k in 'LR'}
  row={'ratio':r['ratio'],'position_s':r['position_s'],'lower':r['observed_low_label'],'palm_span_mm':float(np.linalg.norm(palms['L']-palms['R'])*1e3)}
  row['palms']={}
  for label,p in palms.items():
   loc=np.linalg.solve(tool_b,p-tool_o)
   nominal_idx=0 if r['observed_low_label']==label else 1
   y=r['band_local_y'][nominal_idx]
   # World local scale length along Y may differ from nominal presentation scaling in the import.
   row['palms'][label]=dict(tool_local_m=loc.tolist(),full_tool_triangle_unsigned_mm=distance(p,w)*1e3,lower_haft_subset_unsigned_mm=distance(p,w[bare])*1e3,
    axial_from_sorted_band_signed_mm=float((loc[1]-y)*np.linalg.norm(tool_b[:,1])*1e3))
  samples.append(row)
 summary={'sample_count':len(samples),'lower_hand_counts':{k:sum(t['lower']==k for t in samples) for k in 'LR'}}
 summary['span_mm']=[min(r['palm_span_mm'] for r in samples),max(r['palm_span_mm'] for r in samples)]
 for k in ('full_tool_triangle_unsigned_mm','lower_haft_subset_unsigned_mm','axial_from_sorted_band_signed_mm'):
  summary[k]={hand:[min(t['palms'][hand][k] for t in samples),max(t['palms'][hand][k] for t in samples)] for hand in 'LR'}
 out[a]={'summary':summary,'samples':samples}
print(json.dumps({'scope':'Native imported socket points to exact physical tool triangles, unsigned point distance only, not closed hand surface contact or integrated grip','attached_hero_scale':header['hero_factor'],'pins':pins,'actions':out},sort_keys=True,indent=2))
