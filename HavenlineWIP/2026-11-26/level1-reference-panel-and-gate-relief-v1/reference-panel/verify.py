"""Read the emitted mesh independently: exact per-module bounds and closed oriented shells."""
from collections import Counter
from pathlib import Path
import hashlib,json,sys
import numpy as np
root=Path(__file__).resolve().parent
file=Path(sys.argv[1])
original=Path(sys.argv[2])
def obj(p):
    verts=[]; norms=[]; face=[]; tags=[]; tag=''
    for l in p.read_text().splitlines():
        w=l.split()
        if not w: continue
        if w[0]=='v': verts.append(tuple(map(float,w[1:])))
        if w[0]=='vn': norms.append(tuple(map(float,w[1:])))
        if w[0]=='usemtl': tag=w[1]
        if w[0]=='f':
            face.append(tuple(int(el.split('/')[0])-1 for el in w[1:]))
            tags.append(tag)
    return np.array(verts), np.array(norms), np.array(face), np.array(tags)
src,*_=obj(original)
v,n,fn,tag=obj(file)
assert np.isfinite(v).all() and np.isfinite(n).all() and len(v)==len(n)==len(fn)*3
assert np.all(np.abs(np.linalg.norm(n,axis=1)-1)<1e-8)
assert np.allclose(v.min(0),src.min(0),rtol=0,atol=1e-9)
assert np.allclose(v.max(0),src.max(0),rtol=0,atol=1e-9)
res={}
for label,parts,each in [('timber',10,180),('snow',10,144),('rope',40,120)]:
    tf=v[fn[tag==label]]
    assert len(tf)==parts*each
    signed=[]
    for k in range(parts):
        a=tf[k*each:(k+1)*each]
        m=k//4 if label=='rope' else k
        ref=src[m*192:(m+1)*192]
        assert np.all(a.min((0,1))>=ref.min(0)-1e-9) and np.all(a.max((0,1))<=ref.max(0)+1e-9)
        if label=='snow':
            assert np.allclose(a.max((0,1)),ref.max(0),rtol=0,atol=1e-9)
            assert np.allclose(a.min((0,1))[[0,2]],ref.min(0)[[0,2]],rtol=0,atol=1e-9)
        all_edges=Counter()
        for tris in a:
            tri=[tuple(x) for x in tris]
            assert len(set(tri))==3
            for x,y in zip(tri,tri[1:]+tri[:1]): all_edges[(x,y)]+=1
        assert all(n==1 and all_edges[(y,x)]==1 for (x,y),n in all_edges.items())
        s=a-a.mean((0,1))
        vol=float(np.einsum('ij,ij->i',s[:,0],np.cross(s[:,1],s[:,2])).sum()/6)
        assert vol>0.0,(label,k,vol)
        signed.append(vol)
    res[label]={'outward_closed_parts':parts,'total_triangles':len(tf),'min_signed_volume_m3':min(signed)}
print(json.dumps({'emitted_mesh_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                  'all_modules_inside_exact_original_individual_world_axis_boxes_at_same_transform':True,
                  'stock_snow_outer_join_width_depth_and_apex_per_module_exact':True,
                  'area_proof_not_runtime_intersection_or_art_approval':True,
                  'mesh_checks':res},indent=2))
