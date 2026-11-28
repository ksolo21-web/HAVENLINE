import argparse, hashlib, json, math, re, struct
from pathlib import Path
import numpy as np

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(p, h):
    manifest = p / "SHA256SUMS"
    assert sha(manifest) == h, p
    for line in manifest.read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        assert sha(p / name) == expected, name

def decode(path):
    raw=path.read_bytes()
    assert sha(path)=="31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554"
    assert struct.unpack_from("<4sII", raw)==(b"glTF",2,len(raw))
    a, kind=struct.unpack_from("<II",raw,12); assert kind==0x4E4F534A
    doc=json.loads(raw[20:20+a])
    size, kind=struct.unpack_from("<II",raw,a+20); assert kind==0x004E4942
    binary=raw[a+28:a+28+size]
    def accessor(index):
        item=doc["accessors"][index]; view=doc["bufferViews"][item["bufferView"]]
        dt={5126:"<f4",5123:"<u2",5125:"<u4",5121:"u1"}[item["componentType"]]
        k={"SCALAR":1,"VEC3":3}[item["type"]]
        off=view.get("byteOffset",0)+item.get("byteOffset",0)
        stride=np.dtype(dt).itemsize
        assert view.get("buffer",0)==0
        assert not item.get("sparse") and not item.get("normalized")
        return np.ndarray((item["count"],k),dtype=dt,buffer=binary,offset=off,
                          strides=(view.get("byteStride",k*stride),stride))
    i=next(i for i,n in enumerate(doc["nodes"]) if n.get("name")=="Pickup LOD - Crown log")
    node=doc["nodes"][i]
    assert i in doc["scenes"][doc["scene"]]["nodes"]
    assert all(k not in node for k in ("matrix","translation","scale","rotation","skin"))
    groups=[]
    for prim in doc["meshes"][node["mesh"]]["primitives"]:
        assert prim.get("mode",4)==4 and "COLOR_0" in prim["attributes"]
        p=accessor(prim["attributes"]["POSITION"]).astype(float)
        indices=accessor(prim["indices"]).reshape(-1,3)
        groups.append(p[indices])
    return np.concatenate(groups), [len(g) for g in groups]

# A proper surface crossing must straddle both planes and have positive
# overlap along their line. Coplanarity, edge-on-plane and point contact
# are deliberately excluded; the count is a strict lower bound.
def plane_section(t,d,tol):
    if min(d)>=-tol or max(d)<=tol or min(abs(d))<=tol:
        return None
    pts=[t[i]+(t[j]-t[i])*d[i]/(d[i]-d[j])
         for i,j in ((0,1),(1,2),(2,0)) if d[i]*d[j]<0]
    assert len(pts)==2
    return np.asarray(pts)

def crossings(t, delta):
    eps=1e-9; q=t+delta
    n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]); norm=np.linalg.norm(n,axis=1)
    np.divide(n,norm[:,None],out=n,where=norm[:,None]>1e-15)
    lo,hi=q.min(axis=1),q.max(axis=1)
    spans=[]; witness=None
    for i,x in enumerate(t):
        js=np.flatnonzero(np.all(lo<=x.max(axis=0)+eps,axis=1)&np.all(hi>=x.min(axis=0)-eps,axis=1)&(norm>1e-15))
        if norm[i]<=1e-15: continue
        d=(q[js]-x[0])@n[i]
        for j,dj in zip(js,d):
            s=plane_section(q[j],dj,eps)
            if s is None: continue
            u=plane_section(x,(x-q[j,0])@n[j],eps)
            if u is None: continue
            line=np.cross(n[i],n[j]); k=np.linalg.norm(line)
            if k<=1e-9: continue
            line/=k
            a,b=sorted(s@line); c,e=sorted(u@line)
            overlap=min(b,e)-max(a,c)
            if overlap>eps:
                spans.append(float(overlap))
                if witness is None or overlap>witness["overlap_m"]:
                    witness={"triangle_a":i,"triangle_b":int(j),"overlap_m":float(overlap)}
    return {"strict_crossing_pair_count_lower_bound":len(spans),"strongest_witness":witness}

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    for field in ("glb","art","lip","fixture"): cli.add_argument(field,type=Path)
    args=cli.parse_args()
    verify(args.art,"0ff600cff503855db0edeba2037fe243e231ee1ccd51c79ed297579be100c9f5")
    verify(args.lip,"7bd474cebcd6a0c4779b80b6476675ca92df65b9c4d5fbee86c3d3760da55d7d")
    verify(args.fixture,"1217b23b7f17a386f1f7a0b81b3772b8d5c025ee2974defb017b668637e0fb34")
    t, groups=decode(args.glb); low=t.min(axis=(0,1)); high=t.max(axis=(0,1)); ext=high-low
    assert len(t)==1300
    data=json.loads((args.art/"evidence.json").read_text()); e=data["existing_mounts_bind_geometry_derived_not_a_native_pose"]
    step=data["isolated_52_endpoint_role"]["step_m"]; assert step==0.035
    assert any(re.search(r"(?<![\d.])(?:0)?\.035(?!\d)",p.read_text()) for p in args.fixture.glob("*.gd"))
    checks={axis:crossings(t,np.eye(3)[i]*step) for i,axis in enumerate("XYZ")}
    assert all(r["strict_crossing_pair_count_lower_bound"]>0 for r in checks.values())
    assert all(crossings(t,np.eye(3)[i]*(ext[i]+.001))["strict_crossing_pair_count_lower_bound"]==0 for i in range(3))
    # Carry representative box is only an envelope, not an actual free area.
    bound=np.asarray(e["carry_representative_effective_extents_m"])
    lip=json.loads((args.lip/"summary.json").read_text())["sides"]
    spacing=ext+.001  # chosen test margin, not minimum separation
    def cells(counts):
        counts=np.array(counts); return list(ext+spacing*(counts-1))
    print(json.dumps({
       "axes":"unchanged glTF X length, Y up, Z depth; metres",
       "source_sha256":sha(args.glb),"crown_primitive_triangle_counts":groups,
       "crown_aabb_extents_m":list(ext),"naive_pitch_m":step,
       "strict_at_pitch":checks,
       "disjoint_box_axis_spacings_m_with_1mm_margin":list(spacing),
       "constructive_packing_cases_xyz":{str(c):cells(c) for c in [(1,1,2),(1,2,1),(1,2,2),(1,1,26),(1,2,26),(1,4,13)]},
       "technical_carry_comparison":{"box_m":list(bound),"same_axis_separated_cell_count":list(np.floor((bound+.001)/spacing).astype(int).tolist()),
          "exact_role":e["ledger_link"],"bind_center_m":e["carry_representative_center_actor_local_m"]},
       "unbound_lip_comparison":{"tested_support_xz_m":[.05,.05],"aligned_crown_envelope_xz_m":list(ext[[0,2]]),
          "aligned_crown_envelope_area_vs_small_test_square_ratio":float(ext[0]*ext[2]/.05**2),
          "roles":{k:v["allowed_role"] for k,v in lip.items()}},
       "scope":"Unchanged glTF mesh offline. Parallel aligned crown copies only. No minimum separation, actor/receiver fit, capacity, support, motion, or gameplay approval."
    },indent=2))

# Tests use SHA-pinned assets and independently assert constructive box separation.
if __name__=="__main__": main()
