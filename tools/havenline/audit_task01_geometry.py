#!/usr/bin/env python3
"""Generated T01 mesh audit; geometry checks are not independent art approval."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
records=[]
for name in ('pine_1','pine_2','pine_3'):
    path=ROOT/'HavenlineGodot/assets/reference_forest'/f'{name}.glb'
    data=path.read_bytes();assert data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2
    jl,jt=struct.unpack_from('<II',data,12);assert jt==0x4e4f534a
    document=json.loads(data[20:20+jl]);off=20+jl
    bl,bt=struct.unpack_from('<II',data,off);assert bt==0x004e4942
    binary=data[off+8:off+8+bl]
    def array(index):
        a=document['accessors'][index];view=document['bufferViews'][a['bufferView']]
        dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
        width={'VEC3':3,'SCALAR':1,'VEC2':2,'VEC4':4}[a['type']]
        return np.frombuffer(binary,dtype,count=a['count']*width,offset=view.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
    vertices=[];faces=[];offset=0
    for primitive in document['meshes'][0]['primitives']:
        v=array(primitive['attributes']['POSITION']);f=array(primitive['indices']).reshape(-1,3)
        assert np.isfinite(v).all() and f.max()<len(v)
        vertices.append(v);faces.append(f+offset);offset+=len(v)
    v=np.concatenate(vertices);f=np.concatenate(faces)
    unique,inverse=np.unique(np.round(v,5),axis=0,return_inverse=True);f=inverse[f]
    f=f[(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,2]!=f[:,0])]
    edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
    _,counts=np.unique(edges,axis=0,return_counts=True)
    row={'asset':name,'sha256':hashlib.sha256(data).hexdigest(),'triangles':len(f),'boundary_edges':int(sum(counts==1)),'nonmanifold_edges':int(sum(counts>2)),'weld_tolerance':1e-5}
    row['checks']={'closed_edges':row['boundary_edges']==0,'manifold_edges':row['nonmanifold_edges']==0,'triangle_budget':row['triangles']<10000}
    records.append(row)
report={'task':'T01','geometry_checks':9,'assets':records,'passed':all(all(r['checks'].values()) for r in records),'art_approved':False,'physical_4k60_verified':False}
print(json.dumps(report,indent=2))
sys.exit(0 if report['passed'] else 1)
