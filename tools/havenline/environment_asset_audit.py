"""Audit actual generated GLB bytes. Geometry checks are NOT a visual critic."""
from pathlib import Path
import argparse,hashlib,json,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def inspect():
 manifest=json.loads((ROOT/'HavenlineGodot/assets/environment_v2/manifest.json').read_text())
 output=[]
 for asset in manifest['assets']:
  path=ROOT/asset['path'];raw=path.read_bytes()
  assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,8)[0]==len(raw)
  size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
  def read(i):
   a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
   dtype={5126:'<f4',5125:'<u4'}[a['componentType']]
   return np.frombuffer(binary,dtype=dtype,count=a['count']*count,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,count)
  faces=0
  for primitive in doc['meshes'][0]['primitives']:
   a=primitive['attributes'];v=read(a['POSITION']);n=read(a['NORMAL']);t=read(a['TANGENT']);c=read(a['COLOR_0']);f=read(primitive['indices']).reshape(-1,3)
   assert np.isfinite(v).all() and np.isfinite(n).all() and np.isfinite(t).all()
   assert f.max()<len(v) and len(f)>0
   assert np.allclose(np.linalg.norm(n,axis=1),1,atol=1e-4)
   assert np.allclose(np.linalg.norm(t[:,:3],axis=1),1,atol=1e-4)
   assert np.max(np.abs((n*t[:,:3]).sum(axis=1)))<1e-4
   assert np.isfinite(c).all() and c.min()>=0 and c.max()<=1
   assert (np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)>1e-10).all()
   faces+=len(f)
  assert faces==asset['triangles']
  assert hashlib.sha256(raw).hexdigest()==asset['sha256']
  output.append({'name':asset['name'],'triangles':faces,'sha256':asset['sha256'],'passed':True})
 assert len(output)==14
 return {'assets':output,'passed':True,'visual_quality_score':None,'independent_critic':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();result=inspect();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
