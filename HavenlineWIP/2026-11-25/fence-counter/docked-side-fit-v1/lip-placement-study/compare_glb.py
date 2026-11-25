"""Independently decode and check exact position triangle content of the unchanged donor."""
import numpy as np, json,struct,hashlib
from pathlib import Path
from itertools import permutations
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

GLB_SHA='a62f900f8587008fc0349782b4aa7da3d1a8ebcaa9847569d2b9fa67a47dd25c'
NATIVE_SHA='7825ba134e6b13ce6539e3cbab16899f64a2cd83de0e085a50e6443fc08d36b4'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bdata(p, n):
    assert digest(p)==GLB_SHA and digest(n)==NATIVE_SHA
    data=Path(p).read_bytes()
    assert data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2
    ts,tag=struct.unpack_from('<I4s',data,12);assert tag==b'JSON'
    meta=json.loads(data[20:20+ts])
    size,tag=struct.unpack_from('<I4s',data,20+ts);assert tag==b'BIN\x00'
    blob=memoryview(data)[28+ts:28+ts+size]
    assert meta['nodes']==[{'mesh':0,'name':'service_counter'}]
    def acc(idx):
        a=meta['accessors'][idx];v=meta['bufferViews'][a['bufferView']]
        dt={5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']]
        width={'VEC3':3,'SCALAR':1}[a['type']]
        assert 'sparse' not in a and 'byteStride' not in v
        return np.frombuffer(blob,dtype=dt,offset=v.get('byteOffset',0)+a.get('byteOffset',0),
                             count=width*a['count']).reshape(-1,width)
    def match(a,b):
        # Native import preserves positions but may apply float-matrix
        # roundoff to ties. Centroid query followed by exact vertex permutations
        # avoids accidental global lexical tie mismatches. Use bijection to
        # preserve duplicate-facet multiplicities when they exist.
        near=cKDTree(b.astype(np.float64).mean(1)).query_ball_point(a.astype(np.float64).mean(1),.0002)
        rows=[];cols=[];errors={}
        for i,opts in enumerate(near):
            for j in opts:
                err=min(float(np.max(np.abs(a[i]-b[j,list(pp)]))) for pp in permutations(range(3)))
                if err<=.0002:
                    rows.append(i);cols.append(j);errors[i,j]=err
        graph=csr_matrix((np.ones(len(rows),dtype=bool),(rows,cols)),shape=(len(a),len(b)))
        chosen=maximum_bipartite_matching(graph,perm_type='column')
        if not np.all(chosen>=0):
            print('unmatched',np.sum(chosen<0),'of',len(chosen),'no-centroid',sum(len(x)==0 for x in near), 'native/glb', a[np.flatnonzero(chosen<0)[0]], 'nearest', cKDTree(b.reshape(-1,3)).query(a[np.flatnonzero(chosen<0)[0]])[0], file=__import__('sys').stderr)
        assert np.all(chosen>=0)
        return max(errors[i,j] for i,j in enumerate(chosen)),chosen.tolist()
    native=json.loads(Path(n).read_text()); mats={}; report=[]
    for x,q in enumerate(meta['meshes'][0]['primitives']):
        glb=acc(q['attributes']['POSITION'])[acc(q['indices']).reshape(-1,3)]
        m=native[x];g=np.asarray(m['positions'],dtype=np.float32)[np.array(m['triangles']).reshape(-1,3)]
        assert glb.shape==g.shape,(x,glb.shape,g.shape)
        error,mapping=match(g,glb)
        assert error<=.0002,(x,error)
        material=meta['materials'][q['material']]['name'];mats[x]=(material,mapping)
        report.append(dict(native_surface=x,position_triangle_count=len(glb),
                            material=material,max_abs_component_error_m=error))
    return report,mats

if __name__=='__main__':
 import sys
 print(json.dumps(bdata(*sys.argv[1:])[0],indent=2))
