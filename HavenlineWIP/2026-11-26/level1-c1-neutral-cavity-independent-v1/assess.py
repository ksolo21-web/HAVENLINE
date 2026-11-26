"""Independently reduce exact same-look rejected neutral trial; all inputs private read-only."""
from collections import Counter
from hashlib import sha256
import json,struct,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
TRIAL_SEAL="beb9ac5c30794ae10f22c313633e57d2a73e067d5bc46f31675b29e838a734b7"
STOCK_SHA="95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099"

def sha(data):
    return sha256(data).hexdigest()

def geometry(path):
    raw=path.read_bytes()
    assert sha(raw)==STOCK_SHA
    n=int(struct.unpack_from("<I",raw,12)[0])
    meta=json.loads(raw[20:20+n])
    p=meta["meshes"][0]["primitives"][0]
    def read(i):
        a=meta["accessors"][i]; v=meta["bufferViews"][a["bufferView"]]
        assert not v.get("byteStride")
        k={"SCALAR":1,"VEC2":2,"VEC3":3}[a["type"]]
        typ={5126:"<f4",5125:"<u4",5123:"<u2"}[a["componentType"]]
        off=n+28+v.get("byteOffset",0)+a.get("byteOffset",0)
        return np.frombuffer(raw,dtype=typ,count=a["count"]*k,offset=off).reshape(-1,k)
    return [read(p["attributes"][x]).astype(float) for x in ("POSITION","TEXCOORD_0","NORMAL")]+[read(p["indices"]).reshape(-1,3)]

def section(a,b,eps=1e-12):
    n=np.cross(b[1]-b[0],b[2]-b[0]);mag=np.linalg.norm(n)
    if mag<1e-15:
        return None
    n/=mag
    d=(a-b[0])@n
    if not (min(d)<-eps and max(d)>eps):
        return None
    values=[a[i] for i in range(3) if abs(d[i])<=eps]
    values.extend(a[i]+(a[j]-a[i])*(-d[i]/(d[j]-d[i])) for i,j in ((0,1),(1,2),(2,0)) if d[i]*d[j]<-eps**2)
    if len(values)<2:
        return None
    return n,values

def proper_span(a,b):
    sa,sb=section(a,b),section(b,a)
    if sa is None or sb is None:
        return None
    axis=np.cross(sa[0],sb[0]);size=np.linalg.norm(axis)
    if size<1e-10:
        return None
    axis/=size
    pools=[(np.array(s[1])-a[0])@axis for s in (sa,sb)]
    span=min(map(max,pools))-max(map(min,pools))
    return float(span) if span>1e-9 else None

def both_visible_projection(verts,faces,source_tri,orig,visible,n0):
    unchanged=np.flatnonzero(~np.any(faces[:n0]!=source_tri,axis=1))
    assert len(unchanged)==95468
    changed=np.flatnonzero(np.any(faces[:n0]!=source_tri,axis=1))
    fmeta=np.column_stack((verts[0],verts[1]))
    # Visible shells are either exact copies or an exactly area-partitioned same source triangle.
    groups={}
    for i in np.flatnonzero(visible & ((np.arange(len(faces))>=n0)|(~np.isin(np.arange(len(faces)),unchanged)))):
        groups.setdefault(int(orig[i]),[]).append(int(i))
    count_exact=0
    uv_max=0.
    for parent,cells in groups.items():
        src=source_tri[parent];v=verts[0][src];uv=verts[1][src]
        area=np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))/2
        total=0.
        for idx in cells:
            v1=verts[0][faces[idx]];uv1=verts[1][faces[idx]]
            if len(cells)==1:
                assert np.array_equal(v,v1) and np.array_equal(uv,uv1)
                count_exact+=1;break
            weights=np.linalg.lstsq(np.c_[v,np.ones(3)].T, np.c_[v1,np.ones(3)].T,rcond=None)[0].T
            assert np.min(weights)>-2e-8
            assert np.max(np.abs(weights@v-v1))<1e-11
            uv_max=max(uv_max,np.max(np.abs(weights@uv-uv1)))
            assert uv_max<1e-7
            total+=np.linalg.norm(np.cross(v1[1]-v1[0],v1[2]-v1[0]))/2
        if len(cells)>1:
            assert len(cells)==3 and abs(total-area)<1e-11
    assert len(groups)==len(changed)
    return len(unchanged),count_exact,len(changed)-count_exact,float(uv_max)

def cross2(a,b):
    return a[0]*b[1]-a[1]*b[0]

def clip(poly, polygon):
    out=np.asarray(poly)
    sign=np.sign(cross2(polygon[1]-polygon[0],polygon[2]-polygon[0]))
    if not sign:
        return np.zeros((0,2))
    for p,q in zip(polygon,np.roll(polygon,-1,axis=0)):
        entry=[]
        for a,b in zip(out,np.roll(out,-1,axis=0)):
            sa=sign*cross2(q-p,a-p);sb=sign*cross2(q-p,b-p)
            if sa>=-1e-18: entry.append(a)
            if sa*sb<0 and abs(sa-sb)>1e-20:entry.append(a+(b-a)*(sa/(sa-sb)))
        out=np.asarray(entry).reshape(-1,2)
    return out

def area(poly):
    if len(poly)<3:return 0.
    return abs(sum(cross2(a,b) for a,b in zip(poly,np.roll(poly,-1,axis=0))))/2

def profile(roof,floor,eps=1e-10):
    count=0; ext=[];total=0.; sign_cells=Counter()
    for a in roof:
        for b in floor:
            p=clip(a[:,:2],b[:,:2]);ground=area(p)
            if ground<eps:
                continue
            A=np.c_[a[:,:2],np.ones(3)]
            B=np.c_[b[:,:2],np.ones(3)]
            diff=np.c_[p,np.ones(len(p))]@(np.linalg.solve(A,a[:,2])-np.linalg.solve(B,b[:,2]))
            sign_cells['negative']+=int(np.min(diff)<-1e-8)
            sign_cells['positive']+=int(np.max(diff)>1e-8)
            count+=1;total+=ground;ext.extend(diff.tolist())
    return {"projected_triangle_overlap_pair_sum_mm2":total*1e6,"overlap_cells":count,
        "signed_roof_minus_cloth_extrema_art_mm":[min(ext)*1000,max(ext)*1000] if ext else [],
        "cells_with_signed_gap_below_zero":sign_cells['negative'],"cells_with_signed_gap_above_zero":sign_cells['positive']}

def audit(path,asset,rigpath):
    assert sha((path/"SHA256SUMS").read_bytes())==TRIAL_SEAL
    for row in (path/"SHA256SUMS").read_text().splitlines():
        digest,f=row.split()
        assert sha((path/f).read_bytes())==digest
    build=json.loads((path/"build.json").read_text())
    native=path/"candidate.LOCAL.npz"
    assert sha(native.read_bytes())==build["candidate_private_sha256"]
    q=np.load(native,allow_pickle=False)
    r=np.load(rigpath/"skin.LOCAL.npz",allow_pickle=False)
    assert sha((rigpath/"skin.LOCAL.npz").read_bytes())=="b22a32e9d0ebb28b626c757364c34a4bd00b326a5aac435c0f96ba8aae388220"
    rigraw=(rigpath/"rig.LOCAL.json").read_bytes()
    assert sha(rigraw)=="ce9551d2f34a90c9f5b1dd08c7854ecf471e8ba5965f3be99a41dfd6bb15943c"
    slots=json.loads(rigraw)["weighted_slots"]
    old,olduv,oldnorm,oldf=geometry(asset)
    V,F,uv,norm,W,orig,ls,vis=[q[k] for k in ("positions","faces","uv","normals","weights","source_face_map","layer","visible_surface_mask")]
    oldsize=len(old);n0=len(oldf)
    assert np.array_equal(V[:oldsize],old) and np.array_equal(uv[:oldsize],olduv) and np.array_equal(norm[:oldsize],oldnorm)
    dense=np.zeros((oldsize,len(slots)));np.add.at(dense,(np.arange(oldsize)[:,None],r["joints"]),r["weights"])
    assert np.array_equal(dense,W[:oldsize]) and np.array_equal(orig[:n0],np.arange(n0)) and vis[:n0].all()
    unchanged,copy,split,uv_dev=both_visible_projection((V,uv),F,oldf,orig,vis,n0)
    assert (unchanged,copy,split)==(95468,262,271)
    changed=np.flatnonzero(np.any(F[:n0]!=oldf,axis=1))
    assert V[F[changed],1].max()<=.330
    assert not (np.max(dense[oldf[changed]][:,:,[i for i,s in enumerate(slots) if s.endswith(("Heel","Ball"))]],axis=2)>.9999).any()
    _,weld=np.unique(np.round(V,6),axis=0,return_inverse=True)
    touched=np.flatnonzero((~vis)|(F>=oldsize).any(1))
    assert len(touched)==1243
    T=V[F];lo=T.min(1);hi=T.max(1);cent=(lo+hi)*.5;rad=np.linalg.norm(hi-cent,axis=1)
    broad=cKDTree(cent);rmax=rad.max();seen=set();hits={}
    for i in touched:
        sel=np.asarray(broad.query_ball_point(cent[i],rmax+rad[i]+1e-12),dtype=int)
        sel=sel[((lo[sel]<=hi[i]+1e-12)&(hi[sel]>=lo[i]-1e-12)).all(1)]
        sel=sel[~((ls[sel]==ls[i])&np.isin(weld[F[sel]],weld[F[i]]).any(1))]
        for j in sel:
            a,b=sorted((int(i),int(j)))
            if a==b or (a,b) in seen:continue
            seen.add((a,b))
            span=proper_span(T[a],T[b])
            if span is not None:hits[(a,b)]=span
    pairs=[{"faces":[a,b],"visible":[bool(vis[a]),bool(vis[b])],"layer":[int(ls[a]),int(ls[b])],
            "proper_span_art_mm":hits[a,b]*1000} for a,b in sorted(hits)]
    # Seat span includes only this actual #05 six-edge authored rim (not an arbitrary horizontal cut).
    a,b=49721,96066
    center=V[F[b,2]]
    rim_faces=F[(~vis)&(F[:,2]==F[b,2])]
    assert len(rim_faces)==6 and (rim_faces[:,:2]<oldsize).all()
    rim_idx=np.unique(rim_faces[:,:2])
    assert len(rim_idx)==6
    rim=V[rim_idx]
    avg=(rim.mean(0)-center); norm1=np.linalg.norm(avg); axis=avg/norm1
    assert abs(norm1-.00095)<1e-10
    d=V[rim_faces[0,1]]-V[rim_faces[0,0]];d-=axis*(d@axis)
    e=d/np.linalg.norm(d);basis=np.stack((e,np.cross(axis,e),axis),axis=1)
    seam=rim.mean(0)
    trans=lambda P:(P-seam)@basis
    trim=T[(ls==4)&vis]
    assert len(trim)==4 and (a,b) in hits
    identified=sorted({j["face"] for j in build["seat_source"]["Rigid_HemFastener_05"][0]})
    assert len(identified)==6
    source_fabric=old[oldf[identified]]
    signed=profile(trans(trim),trans(source_fabric))
    seat=T[(F[:,2]==F[b,2])&(~vis)]
    local_roof=trans(trim);local_seat=trans(seat)
    cover=profile(local_roof,local_seat)
    # One fixed check of all other authentic source faces in the same submitted
    # cap's measured support slab. This does not search alternative depths.
    existing=trans(old[oldf]); l=existing.min(1);h=existing.max(1)
    measured_bbox=np.concatenate((local_roof,local_seat)).reshape(-1,3)
    a,b=measured_bbox.min(0),measured_bbox.max(0)
    elig=((l<=b+1e-12)&(h>=a-1e-12)).all(1)
    native_trim_ids=orig[(ls==4)&vis]
    elig[native_trim_ids]=False
    local_check=profile(local_roof,existing[elig])
    local_check["candidate_original_nontrim_faces_in_measured_slab_bbox"]=int(elig.sum())
    local_check["actual_submitted_trim_seat_axial_interval_art_mm"]=[float(a[2]*1000),float(b[2]*1000)]
    
    # Extrema after cutting computed from actual local planar polygons, not AABBs.
    return {"seal":TRIAL_SEAL,"unchanged_exterior_faces":unchanged,"exact_exterior_rigid_face_copies":copy,
     "source_exterior_triangles_split_coplanar_visible":split,"new_centroid_interpolated_uv_max_error":uv_dev,"unchanged_all_original_position_normal_uv_and_weights_rows":oldsize,
     "protected_pure_heel_ball_or_upper_rows_unchanged":True,"changed_scope_faces":len(touched),"proper_neutral_pairs":pairs,
     "hem05":{"actual_trim_faces":4,"rim_vertex_count":6,"actual_adjacent_cloth_faces":identified,
       "cavity_signed_actual_immutable_surface_overlap":signed,
       "all_unedited_nontrim_faces_in_exact_submitted_slab":local_check,
       "existing_hidden_seat_signed_vs_immutable_roof_on_overlap":cover},
     "engine_or_render_or_geometry_edit":False}
if __name__=="__main__":
    print(json.dumps(audit(*map(Path,sys.argv[1:])),indent=2))
