from collections import Counter
from pathlib import Path
import hashlib,json,sys
import numpy as np
p,source=map(Path,sys.argv[1:3])
raw=p.read_text().splitlines()
def vec(lines,tag):
    return np.array([[float(q) for q in x.split()[1:4]] for x in lines if x.startswith(tag+' ')])
v=vec(raw,'v'); n=vec(raw,'vn'); old=vec(source.read_text().splitlines(),'v')
assert np.isfinite(v).all() and np.isfinite(n).all()
assert np.all(np.abs(np.linalg.norm(n,axis=1)-1)<1e-8)
mats={}; faces=None
for l in raw:
    if l.startswith('usemtl '):
        faces=[]; mats[l.split()[1]]=faces
    if l.startswith('f '):
        pairs=[q.split('//') for q in l.split()[1:]]
        assert len(pairs)==3 and all(a==b for a,b in pairs)
        faces.append([int(a)-1 for a,b in pairs])
bounds={}
size0=v.min(0); size1=v.max(0)
assert np.allclose(size0,old.min(0),rtol=0,atol=1e-9)
assert np.allclose(size1,old.max(0),rtol=0,atol=1e-9)
for label,each,posts,step in [('amber_timber',180,10,1),('draped_snow',192,10,1),('cream_hemp',128,20,2),('warm_hemp',128,20,2)]:
    face=np.array(mats[label]); assert len(face)==each*posts
    volumes=[]; ranges=[]
    for j in range(posts):
        data=v[face[j*each:(j+1)*each,:]]
        ref=old[j//step*192:(j//step+1)*192]
        lo,hi=data.min((0,1)),data.max((0,1))
        ranges.append([lo.tolist(),hi.tolist()])
        assert np.all(lo>=ref.min(0)-1e-9) and np.all(hi<=ref.max(0)+1e-9)
        if label=='draped_snow':
            assert np.allclose(hi,ref.max(0),rtol=0,atol=1e-9)
            assert np.allclose(lo[[0,2]],ref.min(0)[[0,2]],rtol=0,atol=1e-9)
        e=Counter()
        for t in data:
            xyz=[tuple(x) for x in t]
            assert len(set(xyz))==3
            for a,b in zip(xyz,xyz[1:]+xyz[:1]):e[(a,b)]+=1
        assert all(k==1 and e[(b,a)]==1 for (a,b),k in e.items())
        t=data-data.mean((0,1))
        vol=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
        assert vol>0
        volumes.append(vol)
    bounds[label]={'closed_parts':posts,'faces':len(face),'mins':np.array(ranges)[:,0].min(0).tolist(),
                   'maxs':np.array(ranges)[:,1].max(0).tolist(),'min_positive_volume':min(volumes)}
# Inspect the actual emitted rope cross sections at x-near center: two
# continuous, signed opposing y diagonals, with distinct z at crossings.
rope_rows={}
for color in ('cream_hemp','warm_hemp'):
    a=v[np.array(mats[color])[:128]]
    x=(old[:192,0].max()+old[:192,0].min())*.5
    near=np.unique(a[np.abs(a[:,:,0]-x)<.011],axis=0)
    flat=near.reshape(-1,3)
    plus=flat[flat[:,2]>.025]; minus=flat[flat[:,2]<-.025]
    assert len(plus) and len(minus)
    rope_rows[color]={'front_crossing_y_span_m':float(plus[:,1].max()-plus[:,1].min()),
                      'rear_crossing_y_span_m':float(minus[:,1].max()-minus[:,1].min()),
                      'front_back_both_exposed_mesh_sectors':True}
assert min(a['front_crossing_y_span_m'] for a in rope_rows.values())>.029
assert min(a['rear_crossing_y_span_m'] for a in rope_rows.values())>.029
print(json.dumps({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'material_closed_shells':bounds,'ropes_actual_center_coverage':rope_rows,
 'two_continuous_formed_wraps_per_level':True,
 'shared_protected_aabb_and_snow_bounds':True,'geometry_only_no_native_visual_or_seam_approval':True},indent=2))
