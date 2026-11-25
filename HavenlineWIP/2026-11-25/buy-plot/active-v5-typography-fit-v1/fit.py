"""Offline conservative painted-deck footprint model for the exact active V5 asset."""
import hashlib, json, math, re, struct, subprocess, sys
from pathlib import Path
repo, witness = sys.argv[1:3]
w = Path(witness)
assert hashlib.sha256((w / "SHA256SUMS").read_bytes()).hexdigest() == "f62ddaddca3699c7c455650a00bb977808c8ce41221cb59a8cd609abb1f6ae43"
for row in (w / "SHA256SUMS").read_text().splitlines():
    digest, filepath = row.split("  ",1)
    assert hashlib.sha256((w / filepath).read_bytes()).hexdigest() == digest
source = json.loads((w / "result.json").read_text())
native = json.loads((w / "native.json").read_text())
def git(*argv):
    return subprocess.check_output(["git","-C",repo,*argv])
pin=source["pin"]
files={k:git("show",pin+":HavenlineLevel1/"+k) for k in source["git_blobs"]}
for k,d in files.items():
    assert hashlib.sha1(f"blob {len(d)}\0".encode()+d).hexdigest()==source["git_blobs"][k]
view=files["pad_v5_view.gd"].decode()
asset=files["assets/studio/purchase_pad_v5.glb"]
assert hashlib.sha256(asset).hexdigest()==source["asset_sha256"]
magic,ver,total,n,what=struct.unpack_from("<4sIIII",asset)
assert (magic,ver,total,what)==(b"glTF",2,len(asset),0x4e4f534a)
glb=json.loads(asset[20:20+n]); data=asset[28+n:]
def accessor(i):
    a=glb["accessors"][i]; b=glb["bufferViews"][a["bufferView"]]
    d={"VEC3":3,"SCALAR":1}[a["type"]]; f={5126:"f",5123:"H"}[a["componentType"]]
    fmt="<"+f*d
    return [struct.unpack_from(fmt,data,b["byteOffset"]+a.get("byteOffset",0)+b.get("byteStride",struct.calcsize(fmt))*k) for k in range(a["count"])]
nodes={e["name"]:e for e in glb["nodes"]}
def triangles(name):
    node=nodes[name]; assert set(node)=={"name","mesh"}
    mm=glb["meshes"][node["mesh"]]["primitives"]; assert len(mm)==1
    v=accessor(mm[0]["attributes"]["POSITION"]); idx=accessor(mm[0]["indices"])
    return [[v[c[0]] for c in idx[k:k+3]] for k in range(0,len(idx),3)]
deck=triangles("PurchaseDeck_Surface")
roof=max(v[1] for t in deck for v in t)
top=[[(v[0],v[2]) for v in t] for t in deck if all(abs(v[1]-roof)<1e-7 for v in t)]
assert len(top)==256
def area(poly):
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))*.5
def clip(poly, axis, side, bound):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        v1=(a[axis]-bound)*side; v2=(b[axis]-bound)*side
        if v1>=0: out.append(a)
        if (v1>=0)!=(v2>=0):
            alpha=v1/(v1-v2)
            out.append(tuple(x+(y-x)*alpha for x,y in zip(a,b)))
    return out
def covered(rect, soup):
    x0,z0,x1,z1=rect
    return sum(area(clip(clip(clip(clip(p,0,1,x0),0,-1,x1),1,1,z0),1,-1,z1)) for p in soup)
def rectangle_intersection(a,b):
    return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
rawz={}
baseline={}
for role in ("Action","Cost"):
    rawz[role],baseline[role]=map(float,re.search(r'_new_label\("'+role+r'", ([\-0-9.]+), ([\-0-9.]+)\)',view).groups())
chosen={"Action":.0047,"Cost":.0050}
world_factor=source["source_inputs"]["asset_scale"]
inlays=[]
for k in sorted(nodes):
    if not k.startswith("PurchaseCorner_"): continue
    coords=[v for t in triangles(k) for v in t]
    inlays.append((min(v[0] for v in coords),min(v[2] for v in coords),max(v[0] for v in coords),max(v[2] for v in coords)))
def examine(scales):
    out={}
    for role,px in scales.items():
        g=native["label"][role]; assert g["font_size"]==30
        width,line=g["string_metrics"]
        # Outline default 12, then a separate 2-font-pixel modeling margin
        # on each side beyond native advance/full line and documented outline.
        # Not a claim about exact glyph placement or textured/filtered pixels.
        budget=14.
        hw,hh=(width/2+budget)*px,(line/2+budget)*px
        z=rawz[role]; rect=(-hw,z-hh,hw,z+hh)
        real=area([(rect[0],rect[1]),(rect[2],rect[1]),(rect[2],rect[3]),(rect[0],rect[3])])
        actual=covered(rect,top)
        f=px/baseline[role]
        va=math.hypot(*g["px_axis_y_for_30"])/30
        ha=math.hypot(*g["px_axis_x_for_30"])/30
        out[role]={"pixel_size":px,"budget_rect_asset_local_m":rect,"budget_rect_covered_fraction_on_flat_top":actual/real,"inlay_aabb_intersects":any(rectangle_intersection(rect,a)>1e-10 for a in inlays),"advance_nominal_logical_px":width*ha*f,"first_atlas_box_line_axis_logical_px":g["glyph_texture_metrics"][0]["size"][1]*va*f}
    a=out["Action"]["budget_rect_asset_local_m"]; c=out["Cost"]["budget_rect_asset_local_m"]
    return {"labels":out,"budget_between_rows_world_m":(c[1]-a[3])*world_factor,"row_budget_overlap_asset_local_m2":rectangle_intersection(a,c)}
report={"base":examine(baseline),"proposed":examine(chosen)}
report["both_doubled_reject"]=examine({k:v*2 for k,v in baseline.items()})
report["cost_overruns_reject"]=examine(dict(chosen,Cost=.018))
def fully_supported(x):
    return all(abs(g["budget_rect_covered_fraction_on_flat_top"]-1)<1e-8 and not g["inlay_aabb_intersects"] for g in x["labels"].values()) and x["budget_between_rows_world_m"]>0
assert fully_supported(report["base"]) and fully_supported(report["proposed"])
assert report["base"]["labels"]["Cost"]["first_atlas_box_line_axis_logical_px"] < 2.
for role, milestone in {"Action":2.0,"Cost":2.1}.items():
    previous=examine(dict(chosen,**{role:chosen[role]-0.0001}))
    assert previous["labels"][role]["first_atlas_box_line_axis_logical_px"] < milestone
    assert report["proposed"]["labels"][role]["first_atlas_box_line_axis_logical_px"] >= milestone
assert report["both_doubled_reject"]["row_budget_overlap_asset_local_m2"]>0
assert report["cost_overruns_reject"]["labels"]["Cost"]["budget_rect_covered_fraction_on_flat_top"]<.95
print(json.dumps({"source_pin":pin,"top_triangles":len(top),"model":"default outline12+2 font-px safety allowance per side, outset around full line/advance; no raster or occlusion",**report},sort_keys=True,indent=2))
