"""Exact source-mesh feasibility only, no engine and no rendered images."""
from pathlib import Path
from itertools import combinations
from hashlib import sha256
import sys, struct, json, re
import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path(sys.argv[1])
def check_source():
    for line in Path(__file__).with_name("SOURCE-SHA256SUMS").read_text().splitlines():
        h, p=line.split(maxsplit=1)
        assert sha256((ROOT/p).read_bytes()).hexdigest()==h, p
    p=(ROOT/"project.godot").read_text()
    size=tuple(int(re.search(r"window/size/viewport_"+ax+r"=(\d+)",p)[1]) for ax in ("width","height"))
    g=(ROOT/"previews/integrated_opening.gd").read_text()
    assert "camera.projection = Camera3D.PROJECTION_ORTHOGONAL" in g
    assert "camera.look_at(actor.position)" in g
    eye=[float(x) for x in re.search(r"camera.position = actor.position \+ Vector3\(([^\)]+)",g)[1].split(",")]
    ortho=float(re.search(r"camera.size = ([0-9.]+)",g)[1])
    return eye,ortho,size,json.loads((ROOT/"layout.json").read_text())["actor_height"]

class GLB:
    def __init__(self,path):
        b=path.read_bytes()
        assert struct.unpack_from("<4sII",b)==(b"glTF",2,len(b))
        n,typ=struct.unpack_from("<II",b,12)
        assert typ==0x4e4f534a
        self.j=json.loads(b[20:20+n])
        a,typ=struct.unpack_from("<II",b,20+n)
        assert typ==0x004e4942
        self.buf=b[28+n:28+n+a]
        self.transforms={}
        def visit(i,ancestor):
            n=self.j["nodes"][i]
            if "matrix" in n:
                x=np.array(n["matrix"]).reshape(4,4).T
            else:
                x=np.eye(4)
                x[:3,:3]=Rotation.from_quat(n.get("rotation",[0,0,0,1])).as_matrix()@np.diag(n.get("scale",[1,1,1]))
                x[:3,3]=n.get("translation",[0,0,0])
            self.transforms[i]=ancestor@x
            for child in n.get("children",[]): visit(child,self.transforms[i])
        for i in self.j["scenes"][self.j["scene"]]["nodes"]: visit(i,np.eye(4))
    def read(self,i):
        a=self.j["accessors"][i]; v=self.j["bufferViews"][a["bufferView"]]
        assert v.get("buffer",0)==0 and "sparse" not in a and not a.get("normalized",False)
        d=np.dtype({5126:"<f4",5125:"<u4",5123:"<u2",5121:"u1"}[a["componentType"]])
        k={"SCALAR":1,"VEC3":3,"VEC4":4,"MAT4":16}[a["type"]]
        return np.ndarray((a["count"],k),dtype=d,buffer=self.buf,offset=v.get("byteOffset",0)+a.get("byteOffset",0),strides=(v.get("byteStride",d.itemsize*k),d.itemsize))
    def triangles(self,name=None,skin=False):
        output=[]; delta=[]
        for i,m in self.transforms.items():
            n=self.j["nodes"][i]
            if "mesh" not in n or (name is not None and n.get("name")!=name): continue
            for primitive in self.j["meshes"][n["mesh"]]["primitives"]:
                assert primitive.get("mode",4)==4
                a=primitive["attributes"]; rest=self.read(a["POSITION"]).astype(float)
                raw=np.c_[rest,np.ones(len(rest))]
                x=(raw@m.T)[:,:3]
                if skin:
                    s=self.j["skins"][n["skin"]]
                    b=self.read(s["inverseBindMatrices"]).reshape(-1,4,4).transpose(0,2,1)
                    f=np.array([self.transforms[i] for i in s["joints"]])@b
                    k=self.read(a["JOINTS_0"]); w=self.read(a["WEIGHTS_0"]).astype(float)
                    assert abs(w.sum(axis=1)-1).max()<1e-6
                    cpu=(np.einsum("nklm,nm->nkl",f[k],raw)*w[:,:,None]).sum(axis=1)[:,:3]
                    delta.append(float(np.linalg.norm(cpu-x,axis=1).max()))
                    x=cpu
                index=self.read(primitive["indices"]).reshape(-1,3)
                output.append(x[index])
        assert output
        return np.concatenate(output),max(delta,default=0)

def bounds(x): return np.array([x.min(axis=(0,1)),x.max(axis=(0,1))])

def section(t,d,eps=1e-9):
    if d.min()>=-eps or d.max()<=eps or abs(d).min()<=eps:return None
    return np.array([t[i]+(t[j]-t[i])*d[i]/(d[i]-d[j]) for i,j in ((0,1),(1,2),(2,0)) if d[i]*d[j]<0])

def crossing(a,b):
    eps=1e-9; low=b.min(axis=1); high=b.max(axis=1)
    def normals(t):
        n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]); v=np.linalg.norm(n,axis=1)
        return np.divide(n,v[:,None],out=np.zeros_like(n),where=v[:,None]>1e-15),v
    n,v=normals(a); k,q=normals(b)
    count=0; longest=0.0
    for i,t in enumerate(a):
        if v[i] <=1e-15:continue
        lt,ht=t.min(axis=0)-eps,t.max(axis=0)+eps
        indexes=np.flatnonzero((q>1e-15)&np.all(low<=ht,axis=1)&np.all(high>=lt,axis=1))
        if not len(indexes):continue
        for j,d in zip(indexes,(b[indexes]-t[0])@n[i]):
            s=section(b[j],d)
            if s is None:continue
            u=section(t,(t-b[j,0])@k[j])
            if u is None:continue
            cross=np.cross(n[i],k[j]); z=np.linalg.norm(cross)
            if z<=eps:continue
            cross/=z
            x,y=np.sort(s@cross); p,r=np.sort(u@cross)
            span=min(y,r)-max(x,p)
            if span>eps:
                count+=1; longest=max(longest,float(span))
    return {"strict_crossings_lower_bound":count,"longest_plane_intersection_m":longest}

def sampled_depth(tri, eye, ortho, size):
    # Orthographic opaque-ray witness at screen-pixel centers; no raster,
    # engine, textures or lighting and no saved images. Camera center is actor.
    z=np.array(eye,dtype=float); z/=np.linalg.norm(z)
    x=np.cross([0,1,0],z);x/=np.linalg.norm(x)
    y=np.cross(z,x)
    px_per_m=size[1]/ortho
    p=tri@np.array([x,y,z]).T
    p[:,:,:2]*=px_per_m; p[:,:,:2]+=np.array(size)/2
    m=np.full((size[1],size[0]),-np.inf)
    for q in p:
        x0,y0=np.maximum(0,np.floor(q[:,:2].min(axis=0)).astype(int))
        x1,y1=np.minimum(size,np.ceil(q[:,:2].max(axis=0)).astype(int))
        if x1<=x0 or y1<=y0:continue
        e=q[1,:2]-q[0,:2];f=q[2,:2]-q[0,:2]
        d=e[0]*f[1]-f[0]*e[1]
        if abs(d)<1e-10:continue
        X,Y=np.meshgrid(np.arange(x0,x1)+.5-q[0,0],np.arange(y0,y1)+.5-q[0,1])
        a=(X*f[1]-Y*f[0])/d;b=(e[0]*Y-e[1]*X)/d
        good=(a>=-1e-10)&(b>=-1e-10)&(a+b<=1+1e-10)
        s=q[0,2]+a*(q[1,2]-q[0,2])+b*(q[2,2]-q[0,2])
        m[y0:y1,x0:x1]=np.maximum(m[y0:y1,x0:x1],np.where(good,s,-np.inf))
    return m

def one_camera(actor,logs,eye,ortho,size):
    hero=sampled_depth(actor,eye,ortho,size)
    parts=[sampled_depth(g,eye,ortho,size) for g in logs]
    a=np.stack([hero,*parts]); front=np.argmax(a,axis=0)
    return [{"solo_geometric_pixel_centres":int(np.isfinite(p).sum()),
             "visible_against_hero_only":int((p>hero).sum()),
             "visible_against_hero_and_other_logs":int((front==i+1).sum())}
            for i,p in enumerate(parts)]

eye,ortho,size,height=check_source()
H=GLB(ROOT/"assets/characters/Character1.glb")
mesh,_=H.triangles(); skin,err=H.triangles(skin=True)
assert len(mesh)==len(skin)==96001 and err<0.0002
bound=bounds(mesh); extent=bound[1]-bound[0]
dh=bound.mean(axis=0); dh[1]=bound[0,1]
hero=(skin-dh)*(height/extent[1])
hero_bounds=bounds((mesh-dh)*(height/extent[1]))
root=ROOT/"assets/studio"
P,_=GLB(root/"wood_bundle_v3.glb").triangles()
fit=bounds(P);psize=fit[1]-fit[0]
factor=min(np.array([.40,.22,.24])/psize)
center=np.array([0,hero_bounds[0,1]+.68*(hero_bounds[1,1]-hero_bounds[0,1]),hero_bounds[0,2]-.025-psize[2]*factor/2])
legacy=(P-fit.mean(axis=0))*factor+center
old_box=bounds(legacy); old_extent=old_box[1]-old_box[0]
assert np.allclose(old_extent,[.302106,.199339,.240000],atol=1e-6)

C,_=GLB(root/"starter_ground_wood_lod.glb").triangles("Pickup LOD - Crown log")
assert len(C)==1300
cb=bounds(C)
C-=cb.mean(axis=0)
src=np.ptp(C.reshape(-1,3),axis=0)
# Historic stock-comparison art scale, not authorized revised equipment placement.
B=3.522754*C
bext=np.ptp(B.reshape(-1,3),axis=0)
max_pair_of_transverse_witness=np.linalg.norm(B.reshape(-1,3)[np.argmax(B.reshape(-1,3)[:,0])]-B.reshape(-1,3)[np.argmin(B.reshape(-1,3)[:,0])])
assert max_pair_of_transverse_witness > np.linalg.norm(old_extent)
# Diagnostic center insertion preserves old two centres; not a proposed mount.
def model(g):return [g+center+[0,0,z] for z in (-.0525,0,.0525)]
def eval_fit(logs):
    return {"pair_checks":[crossing(a,b) for a,b in combinations(logs,2)],
            "aggregate_rest_bounds_m":bounds(np.concatenate(logs)).tolist(),
            "one_conservative_body_z_gap_m":float(hero_bounds[0,2]-max(bounds(g)[1,2] for g in logs)),
            "geometric_stock_camera_rest_witness":one_camera(hero,logs,eye,ortho,size)}
new_large=model(B); new_small=model(C)
report={"source":"exact 11c14a1c unmodified Character 1 bind mesh and old drop art",
        "engine_run":False,
        "bind_asset_normalized_skinned_vs_unskinned_max_delta_m":err*(height/extent[1]),
        "hero_triangles":len(hero),"unchanged_stock_fit_bounds_m":old_box.tolist(),
        "old_mount_diagonal_m":float(np.linalg.norm(old_extent)),
        "same_full_size_log_vertex_pair_distance_m":float(max_pair_of_transverse_witness),
        "outside_unchanged_mount_at_any_rotation":bool(max_pair_of_transverse_witness>np.linalg.norm(old_extent)),
        "authored_original_crown_geometry_extents_m":src.tolist(),
        "full_size_B_geometry_extents_m":bext.tolist(),
        "aligned_depth_row_three_source_scale_sufficient_box_m_at_1mm_gaps":float(3*src[2]+.002),
        "aligned_depth_row_three_B_sufficient_box_m_at_1mm_gaps":float(3*bext[2]+.002),
        "camera":{"viewport":list(size),"orthographic_height_m":ortho,"look_offset_m":eye,"actor_facing":"original spawn +Z bind; no movement or lighting"},
        "legacy_bundle_camera_control":one_camera(hero,[legacy],eye,ortho,size),
        "three_reuse_original_scale_stock_anchor_diagnostic":eval_fit(new_small),
        "three_full_size_B_stock_anchor_diagnostic":eval_fit(new_large),
        "full_size_B_stock_anchor_against_full_hero":[crossing(g,hero) for g in new_large],
        "unscaled_original_two_outer_105mm_regression":crossing(new_small[0],new_small[2]),
        "disposition":"No feasible full-size mount inside unchanged envelope; intersecting center additions are rejected. This does not certify all larger volumes, orientations, stances, or new equipment designs.",
        "protected_row":"No exact second-row bound exists in the admitted starter scene. It has not been redefined, consumed, or claimed clear.",
        "limits":"strict triangle crossing lower bounds exclude touching/coplanar and do not measure penetration depth; sampled opaque geometry is not a render or readability grade."}
print(json.dumps(report,indent=2,sort_keys=True))
