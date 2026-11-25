import contextlib, hashlib, io, json, runpy
from pathlib import Path
import numpy as np
before=hashlib.sha256(Path('reauthored-review-LOCAL.npz').read_bytes()).hexdigest()
with contextlib.redirect_stdout(io.StringIO()):
    g=runpy.run_path('uv_repair.py')
U,V,F,T,drop,I=(g[k] for k in ('U','trial','F','Tn','drop','I'))
cand=g['report']
assert json.loads(Path('../hvn-c1-owner-right-palm-uv-v1/result.json').read_text())==cand
assert hashlib.sha256(Path('reauthored-review-LOCAL.npz').read_bytes()).hexdigest()==before
def det(a,b): return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def area(t):
    return det(t[:,1]-t[:,0],t[:,2]-t[:,0])
def overlap(a,b):
    # Independent convex-triangle separating-axis test using normals of both triangles.
    # Positive overlap requires a positive interval on all six axes.
    edges=np.concatenate([np.roll(t,-1,axis=-2)-t for t in (a,b)],axis=-2)
    n=np.stack([-edges[:,1],edges[:,0]],axis=1)
    n/=np.linalg.norm(n,axis=1)[:,None]
    aa=(a-a[0])@n.T; bb=(b-a[0])@n.T
    return (np.minimum(aa.max(0),bb.max(0))-np.maximum(aa.min(0),bb.min(0))).min()>1e-13
def broad(A,B,same=False):
    amin,amax=A.min(1),A.max(1); bmin,bmax=B.min(1),B.max(1)
    total=0; hits=[]
    for i,a in enumerate(A):
        mask=((bmax>amin[i])&(bmin<amax[i])).all(1)
        if same: mask[:i+1]=False
        for j in np.flatnonzero(mask):
            total+=1
            if overlap(a,B[j]):hits.append((i,int(j)))
    return total,hits
def info(X):
    current=X[T]; sta=area(current)
    ix=np.flatnonzero(sta>=0)
    return {'nonnegative_faces':ix.tolist(),'min_abs_twice_area':float(abs(sta).min()),'sum_signed_twice_area':float(sta.sum()),'min_twice_area_texels_squared':float(abs(sta).min()*np.prod(I.shape[:2]))}
retained=np.ones(len(F),bool); retained[drop]=False
lo=V[T].min((0,1)); hi=V[T].max((0,1))
C=V[F[retained]]; C=C[((C.max(1)>lo)&(C.min(1)<hi)).all(1)]
ni,i=broad(V[T],V[T],True); ne,e=broad(V[T],C)
assert not i and not e
assert not overlap(np.array([[0.,0.],[1.,0.],[0.,1.]]),np.array([[1.,0.],[1.,1.],[0.,1.]]))
assert overlap(V[T][0],V[T][0])
old=info(U); new=info(V); f32=info(V.astype('float32').astype('float64'))
assert len(old['nonnegative_faces'])==14 and not new['nonnegative_faces']
f32X=V.astype("float32").astype("float64"); _, f32overlap=broad(f32X[T],f32X[T],True)
edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1)
ee,ct=np.unique(edges,axis=0,return_counts=True); seam=np.unique(ee[ct==1])
assert np.array_equal(U[seam],V[seam]) and np.array_equal(U[:g['N']],V[:g['N']])
uvdiff=np.linalg.norm((V-U)*I.shape[1::-1],axis=1)
res={'baseline':old,'candidate':new,'float32_storage_diagnostic':f32,'shape_texels':I.shape[1::-1],'preserved_seam_vertex_count':len(seam),'atlas_retained_count':len(C),'patch_pairs_tested':ni,'retained_pairs_tested':ne,'patch_positive_overlap_pairs':i,'retained_positive_overlap_pairs':e,'negative_duplicate_chart_triangle_overlap_detected':True,'negative_shared_edge_not_flagged':True,'changed_rows':int((uvdiff>0).sum()),'max_texels':float(uvdiff.max()),'identical_material_source_only':cand['source_inputs'][0],'candidate_uv_sha':cand['candidate_uv_array_SHA256'],'unchanged_geometry_hashes':cand['unchanged_geometry_arrays_SHA256']}
res["float32_internal_positive_overlap_pairs"]=f32overlap
print(json.dumps(res,indent=2,sort_keys=True))
