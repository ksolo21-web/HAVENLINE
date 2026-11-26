"""Independently reconstruct exact measured rays from four disclosed distances."""
from pathlib import Path
import json, struct, sys, re
from collections import Counter
import hashlib
import numpy as np
from scipy.spatial import cKDTree

root=Path(sys.argv[1])
r=Path(sys.argv[2])
e=root/"compact-reach-v1/evidence"
donor=root/"donor"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(d,h):
    m=d/"SHA256SUMS"
    assert sha(m)==h
    for row in m.read_text().splitlines():
        want,name=row.split(maxsplit=1)
        assert sha(d/name)==want,name
verify(e,"b80a0f93e8b4d75dfa6f376bc35341555981565dc3e6b1ad2815276c537b21fd")
verify(donor,"46f4c8450016c69d21330ba6aaea138ed8ab1fa6360c0c1bf80ca7c6cd81f2d6")
for name, h in (
    ("verification/test_docked.gd","055641f98fb83e24072c69b7f7aa2b3d57ffdf195960b5e040ebf1e3c4f8f3cd"),
    ("render-observer-centerline/observe.gd","e050fbb6281310fa8b35ad68e3d9447ea365b9ad835ab4bbd69eff963d73fa97"),
    ("cpu-surface-audit/audit.gd","4e7ec30240ce0f42cc9e9c1789a15bea7691ed6265e8b358b1d4e28b2cb124a7"),
    ("center-stop-guard/stop_guard.gd","b9fea462a80189c24b04fa85181f5a277226de9d3ea29670412ab3e26ff6c24a")):
    assert sha(root/name)==h,name
proof=json.loads((e/"result.json").read_text())
assert sha(r/"route.log")==proof["route_sha256"]
for name, h in (
    ("counter.json","7825ba134e6b13ce6539e3cbab16899f64a2cd83de0e085a50e6443fc08d36b4"),
    ("center-inboard-stance.json","f1dd275392a775f92ce6837dbd279382a7f283a2e5de35ff8e91d8cb233555b5"),
    ("center-outboard-stance.json","c8c1e84d2b1b50eb8f9dfff3381b5bb0fac0654f40ae7408f8a196c9136fbdce"),
    ("import.log","8c374c91af8b8af47a043aa59851acb5bb0107305dcacdfb8669d81f35dd1a14"),
    ("materialized.before","9af17f3f11528ea57e88cc78b8d5de1d89aa34a8693030453a80c20b153484eb")):
    assert sha(r/name)==h,name
annot=re.compile("^WARNING: OBJ: Ambient light for material '([a-z_]+)' is ignored in PBR$")
diag=[l for l in r.joinpath("import.log").read_text().splitlines() if re.search("ERROR:|WARNING:",l,re.I)]
names="beam board board_soft board_warm brace_back metal rope rope_dark snow".split()
assert len(diag)==18 and all(annot.fullmatch(l) for l in diag)
assert Counter(annot.fullmatch(l)[1] for l in diag)==Counter({x:2 for x in names})
assert r.joinpath("godot-status.txt").read_text().strip()=="0"
for empty in ("import.errors","save-artifacts.txt","materialized.after"):
    assert r.joinpath(empty).stat().st_size==0
assert r.joinpath("donor.before").read_bytes()==r.joinpath("donor.after").read_bytes()
before=r.joinpath("materialized.before").read_text().splitlines()
assert len(before)==136 and len({row.split(maxsplit=1)[1] for row in before})==136
for d in (root/"compact-reach-v1/reach_probe.gd",e/"reach_probe.gd"):
    assert f"{sha(d)}  reach_probe.gd" in r.joinpath("provenance.txt").read_text()
assert r.joinpath("provenance.txt").read_text().splitlines()[:2]==[proof["pinned_source"],proof["pinned_tree"]]
lines=r.joinpath("route.log").read_text().splitlines()
assert len([l for l in lines if l.startswith("PASS ")])==153
assert not any(re.match(r"FAIL |ERROR:|WARNING:|SCRIPT ERROR:",l) for l in lines)
assert lines.count("DOCKED_CENTER_ROUTE_RESULT checks=153 failures=0 no_image_stages=24")==1
assert sum(l.startswith("ROUTE_ONLY_NO_IMAGE ") for l in lines)==12
assert sum(l.startswith("PASS compact reach lawful axial apron by ordinary input") for l in lines)==2
assert sum(l.startswith("PASS compact reach unchanged stance by ordinary input") for l in lines)==2
for gate in ("South","East"):
    for desc in ("real approach","seated-range binding","opens once actor is clear","physical outward traversal","physical return traversal"):
        assert any(l.startswith(f"PASS {gate} unchanged gate {desc} tick=") for l in lines)
aux={}
for tag, n in (("CPU_STANCE",10),("CPU_SURFACE",2),("STOP_GUARD",6),("SHOULDER_ROUTE",4)):
    aux[tag]=[json.loads(l.split(" ",1)[1]) for l in lines if l.startswith(tag+" ")]
    assert len(aux[tag])==n

# Decode original GLB independently of the builder's Godot triangle routine.
raw=(donor/"service_counter.glb").read_bytes()
assert struct.unpack_from("<4sII",raw)==(b"glTF",2,len(raw))
j,k=struct.unpack_from("<II",raw,12); assert k==0x4e4f534a
a=json.loads(raw[20:20+j])
l,k=struct.unpack_from("<II",raw,20+j); assert k==0x004e4942
buf=raw[28+j:28+j+l]
assert a["scenes"]==[{"nodes":[0]}] and a["nodes"]==[{"mesh":0,"name":"service_counter"}]
def read(i):
    x=a["accessors"][i]; v=a["bufferViews"][x["bufferView"]]
    assert "sparse" not in x and not x.get("normalized") and v["buffer"]==0
    dt=np.dtype({5126:"<f4",5123:"<u2",5125:"<u4",5121:"u1"}[x["componentType"]])
    cols={"SCALAR":1,"VEC3":3}[x["type"]]
    return np.ndarray((x["count"],cols),dtype=dt,buffer=buf,offset=v.get("byteOffset",0)+x.get("byteOffset",0),strides=(v.get("byteStride",dt.itemsize*cols),dt.itemsize)).astype(float)
surfaces=[]; import_quantization=0.0
native=json.loads((r/"counter.json").read_text())
for i,p in enumerate(a["meshes"][0]["primitives"]):
    assert p.get("mode",4)==4
    P=read(p["attributes"]["POSITION"])
    I=read(p["indices"]).astype(int).reshape(-1,3)
    B=np.array(native[i]["positions"]); K=np.array(native[i]["triangles"]).reshape(-1,3)
    assert native[i]["name"]=="service_counter" and native[i]["surface"]==i and native[i]["matrixes"]==0
    # Import may reverse winding. Compare vertex identity on each indexed face
    # rather than demand a particular orientation from the unordered segment test.
    assert P.shape==B.shape
    C, ix=np.unique(P,axis=0,return_inverse=True)
    ds, idx=cKDTree(C).query(B)
    assert ds.max()<.0001
    pp=np.sort(ix[I],axis=1)
    bb=np.sort(idx[K],axis=1)
    assert Counter(map(tuple,pp))==Counter(map(tuple,bb))
    import_quantization=max(import_quantization,float(ds.max()))
    surfaces.append(B[K])
tri=np.concatenate(surfaces)
assert len(tri)==13624
S=(donor/"north_counter_donor.tscn").read_text()
def mark(name):
    l=re.search(r'^\[node name="'+name+r'" type="Marker3D" parent="Markers_NotBindings"\]\nposition = Vector3\(([^)]+)\)',S,re.M)
    return np.array([l for l in l[1].split(",")],dtype=np.float32).astype(float)
marker_names=["StockHandling","PaymentHandling","StockRestWitness","PaymentRestWitness"]
M=np.array([mark(name) for name in marker_names])
assert np.all(M[:,2]==0)
A=-2*(M[1:,:2]-M[0,:2])
B=np.sum(M[1:]**2-M[0]**2,axis=-1)

def infer(d, sign):
    # For coplanar endpoints: recover x,y from independent squared distance
    # differences, then choose z reflecting the actual actor mesh's only side.
    xy=np.linalg.lstsq(A,d[1:]**2-d[0]**2-B,rcond=None)[0]
    z2=d*d - ((xy-M[:,:2])**2).sum(axis=1)
    assert min(z2)>0 and np.ptp(z2)<1e-5
    xyz=np.r_[xy,sign*np.sqrt(z2.mean())]
    return xyz,abs(np.linalg.norm(xyz-M,axis=1)-d).max()

def first_hit(O,T):
    D=T-O; e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
    # Independent two-sided segment/triangle solver (not Godot API).
    P=np.cross(D,e2); det=np.einsum("ij,ij->i",e1,P)
    t=O-tri[:,0]; Q=np.cross(t,e1)
    keep=abs(det)>1e-11
    U=np.divide(np.einsum("ij,ij->i",t,P),det,out=np.ones(len(tri))*np.nan,where=keep)
    V=np.divide(Q@D,det,out=np.ones(len(tri))*np.nan,where=keep)
    H=np.divide(np.einsum("ij,ij->i",e2,Q),det,out=np.ones(len(tri))*np.nan,where=keep)
    ok=(U>=-1e-9)&(V>=-1e-9)&(U+V<=1+1e-9)&(H>0)&(H<1)
    return float(H[ok].min()*np.linalg.norm(D)) if ok.any() else None

got=[json.loads(l.split(" ",1)[1]) for l in lines if l.startswith("COMPACT_COUNTER_REACH ")]
assert got==proof["observed_original_marker_rows"]
summary={}; hand=total=0; match_max=fit_max=0.; margin_min=3.
for side, label, expected, sign in ((got[0],"inboard","WorkerInteriorStance",1),(got[1],"outboard","CustomerExteriorStance",-1)):
    measure=side["measurements"]
    assert len(measure)==12
    stance=next(x for x in aux["CPU_STANCE"] if x["id"]==f"center-{label}-stance")
    assert stance["foot"]==side["actor_foot"] and stance["floor"]
    assert "idle" in stance["animation"] and stance["actual_renderer"]=="headless"
    exact=mark(expected)
    assert np.max(abs(exact-side["unchanged_marker"]))<1e-6
    pos=np.asarray(stance["foot"]); stop=np.linalg.norm(pos[[0,2]]-exact[[0,2]])
    yaw_error=abs((stance["yaw"]-(np.pi if sign>0 else 0)+np.pi)%(2*np.pi)-np.pi)*180/np.pi
    assert stop < .05 and yaw_error<2 and abs(yaw_error-side["heading_error_deg"])<3e-5
    skin=json.loads((r/f"center-{label}-stance.json").read_text())[0]
    body=np.array(skin["positions"])
    assert skin["matrixes"]==66 and len(skin["triangles"])//3==96001 and np.min(sign*body[:,2])>0
    count=0; exceptions=[]
    for bone in ["Head","L_Hand","R_Hand"]:
        facts=[measure[bone+":"+k] for k in marker_names]
        lengths=np.array([x["straight_pivot_distance_m"] for x in facts])
        origin,fit=infer(lengths,sign)
        assert fit<2e-6 and sign*origin[2]>0
        fit_max=max(fit_max,float(fit))
        assert np.all(origin>=body.min(axis=0)-.035) and np.all(origin<=body.max(axis=0)+.035)
        for i,item in enumerate(facts):
            first=first_hit(origin,M[i]); old=item["first_donor_distance_m"]
            assert item["tested_triangles"]==len(tri)
            assert (first is None)==(old is None)
            if first is not None:
                match_max=max(match_max,abs(first-old))
                assert abs(first-old)<2e-5
            blocked=first is not None and first<lengths[i]-.010
            assert blocked==item["earlier_than_endpoint_by_1cm"]
            if blocked:
                count+=1; hand+=int(bone!="Head");margin_min=min(margin_min,float(lengths[i]-first))
            else:
                assert bone=="Head" and old is None
                exceptions.append(bone+":"+marker_names[i])
    summary[side["side"]]={"blocked":count,"exceptions":exceptions,"heading_error_deg":yaw_error,"axial_foot_error_m":stop}
    total+=count
assert hand==16 and total==22
assert summary["inside"]["blocked"]==12 and summary["outside"]["blocked"]==10
print(json.dumps({
    "scope":"no engine; independent replay of geometric line intersections from captured distances; not a reach envelope or animated service check",
    "checks_reported_and_counted":153,"image_stages_skipped":24,"explicit_image_skip_logs":12,
    "cpu_only_other_image_stages":12,"exact_import_annotations_only":18,
    "max_glb_to_native_quantization_m":import_quantization,
    "exact_GLTF_and_native_donor_triangles_matched":len(tri),
    "materials_or_physics_in_scope":False,
    "reconstructed_native_pivot_fit_max_m":fit_max,"first_hit_distance_max_disagreement_m":match_max,
    "minimum_actual_endpoint_minus_blocker_m":margin_min,
    "blocked_all":total,"paths_all":24,"blocked_hands":hand,"hand_paths":16,"stances":summary,
    "evidence_limit":"Pivots inferred from distances in same native run, not separate native bone sampling. No arm span, hand surface, trajectory, customer service or device proof.",
    "route_sha256":proof["route_sha256"],"frozen_builder_seal":sha(e/"SHA256SUMS"),
},indent=2,sort_keys=True))
