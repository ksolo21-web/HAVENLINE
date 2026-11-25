import hashlib,json,numpy as np
from pathlib import Path
p=Path('../hvn-l1-c1-rear-adjacent-panel-hold-v1')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(p/'SHA256SUMS')=='99ab5bcc2e41b7b16a1bb493a5840e378b82ef776203f34f60ed1c2c5e65dd38'
for x in (p/'SHA256SUMS').read_text().splitlines():
 h,n=x.split(maxsplit=1);assert sha(p/n)==h
q=np.load(p/'exact_panel_boundary_counterexample.npz')
idx=dict(zip(map(int,q['face_ids']),q['vertex_ids']))
out={}
for pose in ('neutral_m','held_0ms_m'):
    A=dict(zip(map(int,q['face_ids']),q[pose].astype(float)))
    def cross(r,s):
        X,Y=A[r],A[s]; normal=np.cross(Y[1]-Y[0],Y[2]-Y[0]);normal/=np.linalg.norm(normal)
        answer=[]
        for i,j in ((0,1),(1,2),(2,0)):
            d=X[j]-X[i]
            B=np.column_stack((d,Y[0]-Y[1],Y[0]-Y[2]))
            h=np.linalg.solve(B,Y[0]-X[i]); w=np.r_[1-h[1:].sum(),h[1:]]
            near=(0<=h[0]<=1 and min(w)>=-1e-8)
            if near:
                # No shared endpoints, grazing or touches in the test set.
                assert 1e-7<h[0]<1-1e-7 and min(w)>1e-7
                answer.append({'source_boundary_edge':idx[r][[i,j]].tolist(),'t':float(h[0]),'interior_target_barycentric':w.tolist(),'strict_point_m':(X[i]+d*h[0]).tolist(),'plane_endpoint_distances_mm':((X[[i,j]]-Y[0])@normal*1000).tolist()})
        return answer
    row={}
    for a,b in ((28093,28305),(28093,42401),(27920,42401)):
        h1,h2=cross(a,b),cross(b,a)
        assert len(h1)%2==len(h2)%2
        row[f'{a}:{b}']={'forward_piercings':h1,'reverse_piercings':h2,'odd_linking_parity_of_disjoint_fixed_triangle_boundary_loops':bool(len(h1)%2)}
    out[pose]=row
assert all(not x['forward_piercings'] and not x['reverse_piercings'] for x in out['neutral_m'].values())
assert [out['held_0ms_m'][k]['odd_linking_parity_of_disjoint_fixed_triangle_boundary_loops'] for k in ('28093:28305','28093:42401','27920:42401')]==[True,True,False]
print(json.dumps({'read_only':True,'scope':'exact two poses, no plotted/rendered silhouette, no proposed mesh; disjoint original triangle-boundary loops only','result':out},indent=2))
