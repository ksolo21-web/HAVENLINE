"""Read-only independent triangle plane/segment reduction of the sealed existing V3 pose."""
from hashlib import sha256
from collections import Counter
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial import cKDTree

def sealed_parent(root):
    p=root/'hvn-l1-clean-character-grounded-v3'
    def sha(f):return sha256(f.read_bytes()).hexdigest()
    seal=sha(p/'SHA256SUMS')
    if not seal.startswith("35481eb6"):
        raise RuntimeError(f"V3 manifest seal mismatch: {seal}")
    for line in (p/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split()
        assert sha(p/name)==digest
    return p,seal

def published_sample(root,path):
    # Load only the verified original sealed articulation, never its intersection detector.
    sys.path.insert(0,str(path))
    source=(path/'evaluate.py').read_text().split('\nedges=stock.edges\n',1)[0]
    env=dict(__file__=str(path/'evaluate.py'))
    exec(compile(source,str(path/'evaluate.py'),'exec'),env)
    return env

def cut(face, other, eps=1e-11):
    """Crossing interval through the plane of 'other'. No tangent/coplanar contact."""
    normal=np.cross(other[1]-other[0],other[2]-other[0])
    n=np.linalg.norm(normal)
    if n<=1e-14:
        return None
    dist=(face-other[0])@(normal/n)
    if not min(dist)<-eps or not max(dist)>eps or min(abs(dist))<eps:
        return None
    out=[]
    for i,j in ((0,1),(1,2),(2,0)):
        if dist[i]*dist[j]<0:
            out.append(face[i]+(face[j]-face[i])*(-dist[i]/(dist[j]-dist[i])))
    return normal/n,np.asarray(out)

def finite(a,b):
    # If both planes strictly cut, overlap of noncoplanar intervals is a proper interior crossing.
    sa,sb=cut(a,b),cut(b,a)
    if sa is None or sb is None:
        return None
    t=np.cross(sa[0],sb[0])
    if np.linalg.norm(t)<1e-12:
        return None
    t/=np.linalg.norm(t)
    orig=a[0]
    u=sorted((sa[1]-orig)@t)
    v=sorted((sb[1]-orig)@t)
    span=min(u[1],v[1])-max(u[0],v[0])
    return float(span) if span>1e-10 else None

def classify(vertices,indices,wts,slots,tri,world_scale):
    w = Counter()
    for row in tri:
        for j,f in zip(indices[row],wts[row]):
            w[slots[j]]+=float(f/len(tri))
    hist=w.most_common()
    top=hist[0][0]
    z=vertices[tri].mean(axis=0)
    return {
        "source_triangle_rows":list(map(int,tri)),
        "dominant_averaged_regions":[(name,v) for name,v in hist if v>.01],
        "source_side": "R" if z[0]<-.044 else "L" if z[0]>.072 else "midline",
        "source_height_art_mm":float(z[1]*1000),
        "source_lateral_art_mm":float(z[0]*1000),
        "source_front_art_mm":float(z[2]*1000),
        "aggregate_per_row_weight_ranges":{
            name:[float(min((wts[tri]*(indices[tri]==slots.index(name))).sum(1))),
                  float(max((wts[tri]*(indices[tri]==slots.index(name))).sum(1)))]
            for name,v in hist if v>.01},
    }
def audit():
    root=Path(__file__).resolve().parents[1]
    path,seal=sealed_parent(root)
    E=published_sample(root,path)
    V,R,P,TR,I,W,S,Weld,scale=(E[k] for k in ('V','rest','Y','TR','indices','weights','slots','Weld','S'))
    source=json.loads((path/'result.json').read_text())
    first=source['first_new_strict_pair']; fault=source['parts']['R']['worst_failed_raw_rows']
    assert not set(Weld[TR[first[0]]]).intersection(Weld[TR[first[1]]])
    exact_rest=finite(*R[TR[first]])
    exact_grounded=finite(*P[TR[first]])
    assert exact_rest is None and exact_grounded is not None
    edge=lambda A:float(np.linalg.norm(A[fault[0]]-A[fault[1]]))
    sidefaces=np.flatnonzero(np.isin(TR,fault).sum(1)==2)
    ratio=edge(P)/edge(R)
    assert abs(ratio-source['parts']['R']['guard_min_max_ratio'][0])<1e-10
    # Broad coverage separately reconstructed with a sweep on X bounds and Y/Z box filtering.
    # Only actual input faces containing at least one source row below .32m; original V3 scope.
    scope=np.flatnonzero((V[:,1]<.32)[TR].any(1))
    results={'v3_seal':seal,'same_pose_and_proof_source':True,
      'first_pair':{'triangle_ids':first,'rest_intersection':False,
        'posed_finite_crossing_length_mm':exact_grounded*1000,
        'regions':[classify(V,I,W,S,TR[j],scale) for j in first]},
      'right_compressed_edge':{'raw_rows':fault,'faces':list(map(int,sidefaces)),
         'rest_mm':edge(R)*1000,'posed_mm':edge(P)*1000,'ratio':ratio,
         'region':classify(V,I,W,S,np.array(fault),scale)},
      'native_or_render_validation':False}
    def full(Q):
        # Sweep without old KD pair search; simple sparse candidate generation in X then exact Y/Z AABB.
        all_xyz=Q[TR]
        lo=np.min(all_xyz,axis=1); hi=np.max(all_xyz,axis=1)
        # Stable X sweep; broadphase unchanged by input face indexing.
        order=np.argsort(lo[:,0],kind='stable')
        sorted_x=lo[order,0]
        seen=set(); hits={}
        for i in scope:
            stop=np.searchsorted(sorted_x,hi[i,0]+1e-10,side='right')
            keep=order[:stop]
            sel=keep[(hi[keep,0]>=lo[i,0]-1e-10)]
            sel=sel[((hi[sel,1:]>=lo[i,1:]-1e-10)&(lo[sel,1:]<=hi[i,1:]+1e-10)).all(1)]
            sel=sel[~np.isin(Weld[TR[sel]],Weld[TR[i]]).any(1)]
            for j in sel:
                a,b=sorted((int(i),int(j)))
                if (a,b) in seen:
                    continue
                seen.add((a,b))
                span=finite(all_xyz[a],all_xyz[b])
                if span is not None:
                    hits[(a,b)]=span
        return hits
    if E.get('_do_full_scope',False):
        pass
    if __import__('os').environ.get("HVN_INDEPENDENT_FULL")=="1":
        before,after=full(R),full(P)
        persistent=set(before)&set(after)
        new=sorted(set(after)-set(before))
        def region(j):
            face=classify(V,I,W,S,TR[j],scale)
            tag=face["dominant_averaged_regions"][0][0]
            if "BootFastener" in tag:
                return "boot fastener carrier"
            if tag.endswith(("CollarFlex","Heel","Ball")):
                return "mixed/heel/toe collar"
            if tag.endswith(("Shin","Hip")):
                return "shin or thigh"
            return "proximal/hardware or other"
        groups=Counter(" | ".join(sorted((region(i),region(j)))) for i,j in new)
        results["independent_lower_mesh"]={"active_scope_faces":len(scope),"strict_rest_pairs":len(before),
            "strict_pose_pairs":len(after),"persistent":len(persistent),"new_pairs":len(new),
            "new_pair_regions":dict(groups),"max_strict_interval_mm":max(after[p] for p in new)*1000 if new else 0}
    return results

if __name__=="__main__":
    print(json.dumps(audit(),indent=2))
