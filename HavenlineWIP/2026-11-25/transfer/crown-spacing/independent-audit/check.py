"""Independent projected-line clipping on the exact transfer crown source."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
glb,packet,fixture,art,lip=map(Path,sys.argv[1:6])
for folder,h in [
    (packet,"c47d55f4674f1eed9feda0573c01f765363d9fcb3fa55ad28faa363ff9bce04a"),
    (fixture,"1217b23b7f17a386f1f7a0b81b3772b8d5c025ee2974defb017b668637e0fb34"),
    (art,"0ff600cff503855db0edeba2037fe243e231ee1ccd51c79ed297579be100c9f5"),
    (lip,"7bd474cebcd6a0c4779b80b6476675ca92df65b9c4d5fbee86c3d3760da55d7d")]:
    manifest=folder/"SHA256SUMS"
    assert sha(manifest)==h
    for row in manifest.read_text().splitlines():
        digest,name=row.split(maxsplit=1)
        assert sha(folder/name)==digest
source=glb.read_bytes()
assert sha(glb)=="31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554"
n,ty=struct.unpack_from("<I4s",source,12); assert ty==b'JSON'
g=json.loads(source[20:20+n]); payload=memoryview(source)[28+n:]
j,node=next((i,v) for i,v in enumerate(g['nodes']) if v['name']=="Pickup LOD - Crown log")
assert j in g["scenes"][g["scene"]]["nodes"] and not ({"matrix","rotation","translation","scale","skin"}&node.keys())
def acc(i):
    a=g["accessors"][i]; b=g["bufferViews"][a["bufferView"]]
    fmt={5121:"B",5123:"H",5125:"I",5126:"f"}[a["componentType"]]
    k={"SCALAR":1,"VEC3":3}[a["type"]]
    rec=struct.Struct("<"+fmt*k)
    start=b.get("byteOffset",0)+a.get("byteOffset",0)
    return np.array([rec.unpack_from(payload,start+q*b.get("byteStride",rec.size)) for q in range(a["count"])])
groups=[]
for p in g["meshes"][node["mesh"]]["primitives"]:
    assert p.get("mode",4)==4 and "COLOR_0" in p["attributes"]
    groups.append(acc(p["attributes"]["POSITION"])[acc(p["indices"]).reshape(-1,3)])
T=np.concatenate(groups); assert len(T)==1300
sizes=np.ptp(T,axis=(0,1))
N=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
NL=np.linalg.norm(N,axis=1); safe=NL>1e-15
N[safe]/=NL[safe,None]
# Compute the *intersection line of the two planes*, then clip it against
# oriented halfspaces spanned by the three edges of each triangle.
def cross(V):
    Q=T+V; out=[]; e=1e-9
    for i,P in enumerate(T):
        if not safe[i]:continue
        j=np.where(safe & np.all(Q.max(axis=1)>=P.min(axis=0)-e,axis=1) & np.all(Q.min(axis=1)<=P.max(axis=0)+e,axis=1))[0]
        if not len(j):continue
        P2=Q[j]; N2=N[j]
        b=np.einsum('mki,mi->mk',P[None,:,:]-P2[:,:1,:],N2); a=(P2-P[0])@N[i]
        def strict(d): return (d.min(axis=1)<-e)&(d.max(axis=1)>e)&(np.abs(d).min(axis=1)>e)
        direction=np.cross(N[i],N2)
        L=np.linalg.norm(direction,axis=1)
        ok=strict(a)&strict(b)&(L>e)
        j=j[ok];P2=P2[ok];N2=N2[ok];direction=direction[ok]/L[ok,None]
        if not len(j):continue
        M=np.stack([np.repeat(N[i][None,:],len(j),axis=0),N2,direction],axis=1)
        R=np.stack([np.full(len(j),P[0]@N[i]),np.einsum('mi,mi->m',P2[:,0],N2),np.zeros(len(j))],axis=1)
        orig=np.linalg.solve(M,R[:,:,None])[:,:,0]
        lower=np.full(len(j),-np.inf); upper=np.full(len(j),np.inf); valid=np.ones(len(j),bool)
        for tri,normal in ((np.broadcast_to(P,P2.shape),np.broadcast_to(N[i],N2.shape)),(P2,N2)):
            for k in range(3):
                s=np.cross(normal,tri[:,(k+1)%3]-tri[:,k])
                u=np.einsum('mi,mi->m',s,direction); v=np.einsum('mi,mi->m',s,orig-tri[:,k])
                a=np.divide(-v,u,out=np.zeros_like(v),where=np.abs(u)>1e-15)
                lower=np.where(u>1e-15,np.maximum(lower,a),lower)
                upper=np.where(u<-1e-15,np.minimum(upper,a),upper)
                valid&=(np.abs(u)>1e-15)|(v>=-1e-15)
        span=upper-lower
        out.extend((i,int(j[k]),float(span[k])) for k in np.where(valid&(span>e))[0])
    return {"count":len(out),"strongest":max(out,key=lambda a:a[2]) if out else None}
observed=[cross(u*.035) for u in np.eye(3)]
pitch=sizes+.001
safe_pitch=[cross(np.eye(3)[i]*p) for i,p in enumerate(pitch)]
result=json.loads((packet/"result.json").read_text())
assert np.allclose(sizes,result["crown_aabb_extents_m"],atol=1e-12,rtol=0)
for k,got in zip("XYZ",observed):
    exp=result["strict_at_pitch"][k]
    assert got["count"]==exp["strict_crossing_pair_count_lower_bound"]
    w=exp["strongest_witness"]
    assert got["strongest"][:2]==(w["triangle_a"],w["triangle_b"]) and abs(got["strongest"][2]-w["overlap_m"])<1e-10
assert not any(x["count"] for x in safe_pitch)
assert "k%8)*.035, (k/8)*.035, 0.0" in (fixture/"test.gd").read_text()
bounds=np.array(json.loads((art/"evidence.json").read_text())["existing_mounts_bind_geometry_derived_not_a_native_pose"]["carry_representative_effective_extents_m"])
area=sizes[0]*sizes[2]/.05**2
print(json.dumps(dict(dimensions_m=list(sizes),axis_order="glTF and Godot 3D: X right Y up Z depth; imported Blender mesh losslessly rotates +Y=>+Z and +Z=>-Y",point_grid_axes=["X","Y"],strict_crossings_xyz=observed,separated_pitch_m=list(pitch),strict_at_safe_pitch=safe_pitch,carry_box_axis_family_counts=(np.floor((bounds+.001)/pitch).astype(int)).tolist(),four_box_m=(sizes+pitch*[0,1,1]).tolist(),depth_26_disjoint_no_margin_m=sizes[2]*26,depth_26_at_1mm_m=sizes[2]*26+.025,lip_aligned_envelope_area_ratio=area),indent=2))
