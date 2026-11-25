"""Read exact source with git; no project edits, engine or proprietary asset export."""
import argparse, hashlib, json, math, re, struct, subprocess

p=argparse.ArgumentParser()
p.add_argument("repo")
a=p.parse_args()
pin="11c14a1c41971067c7dc97db69375f720a408f68"
def git(*args): return subprocess.check_output(["git","-C",a.repo,*args])
keys=("project.godot","previews/integrated_opening.gd","pad_v5_view.gd","purchase_pad_visual.gd","assets/studio/purchase_pad_v5.glb")
raw={key:git("show",pin+":HavenlineLevel1/"+key) for key in keys}
blobs={k:git("rev-parse",pin+":HavenlineLevel1/"+k).decode().strip() for k in keys}
for k,v in raw.items(): assert hashlib.sha1(f"blob {len(v)}\0".encode()+v).hexdigest()==blobs[k]
project, opening,view, bridge=[raw[key].decode() for key in keys[:4]]
assert 'run/main_scene="res://opening.tscn"' in project
assert 'window/stretch/mode="canvas_items"' in project
assert "camera.projection = Camera3D.PROJECTION_ORTHOGONAL" in opening and "camera.keep_aspect" not in opening
assert 'purchase_pad_view.name = "ExactStudioV5_PresentationOnly"' in opening and "purchase_pad_view.install_exact()" in opening
assert 'commit_confirmed' in view and '"BUILD", "3 WOOD"' in bridge
assert "label.rotate_x(-PI / 2.0)" in view and "label.font_size = 30" in view
assert "label.position.y = deck_roof + SEAT_LABEL_GAP / factor" in bridge
sw,sh=[int(re.search(r"window/size/viewport_"+d+r"=(\d+)",project)[1]) for d in ("width","height")]
camera=tuple(map(float,re.search(r"camera.position = actor.position \+ Vector3\(([^)]+)\)",opening)[1].split(",")))
assert "camera.look_at(actor.position)" in opening
span=float(re.search(r"camera\.size = (\d+(?:\.\d+)?)",opening)[1])
def const(name): return float(re.search(name+r" := ([0-9.]+)",bridge)[1])
asset=raw[keys[-1]]
magic,ver,tot,n,kind=struct.unpack_from("<4sIIII",asset)
assert (magic,ver,tot,kind)==(b"glTF",2,len(asset),0x4e4f534a)
d=json.loads(asset[20:20+n]); roots=d["scenes"][d.get("scene",0)]["nodes"]
assert set(roots)==set(range(6))
bounds={}
for i in roots:
    node=d["nodes"][i]
    assert set(node)=={"mesh","name"} # exact scan supports flat identity transforms only
    mesh=d["meshes"][node["mesh"]]
    assert len(mesh["primitives"])==1
    b=d["accessors"][mesh["primitives"][0]["attributes"]["POSITION"]]
    bounds[node["name"]]=(b["min"],b["max"])
assert set(bounds)=={"Mesh_0","PurchaseDeck_Surface",*(("PurchaseCorner_"+k) for k in ("SW","SE","NE","NW"))}
lo=[min(b[0][j] for b in bounds.values()) for j in range(3)]
hi=[max(b[1][j] for b in bounds.values()) for j in range(3)]
s=const("FOOTPRINT_CAP")/max(hi[j]-lo[j] for j in (0,2))
z0=-(lo[2]+hi[2])*s/2
deck_h=const("SEAT_Y")+s*(bounds["PurchaseDeck_Surface"][1][1]-lo[1])
rx=(camera[2]/math.hypot(camera[0],camera[2]),0,-camera[0]/math.hypot(camera[0],camera[2]))
n=tuple(v/math.sqrt(sum(v*v for v in camera)) for v in camera)
ry=(n[1]*rx[2]-n[2]*rx[1],n[2]*rx[0]-n[0]*rx[2],n[0]*rx[1]-n[1]*rx[0])
def project_vec(dx,dz,hh):
    # Godot Camera3D default keep-aspect KEEP_HEIGHT, in nominal logical viewport.
    return [(dx*axis[0]+dz*axis[2])*hh/span for axis in (rx,ry)]
def label(z,pixel,hh):
    x,zv=project_vec(pixel*s,0,hh),project_vec(0,pixel*s,hh)
    return {"authored_local_z_m":z, "label_parent_z_m":z0+s*z,
            "world_per_font_pixel_m":s*pixel,"one_font_px_x_to_screen_xy":x,
            "one_font_px_line_vertical_to_screen_xy":zv,
            "30_font_px_vertical_screen_axis_length":30*math.hypot(*zv),
            "30_font_px_vertical_screen_y_only":30*abs(zv[1])}
labels={key:label(*map(float,re.search(r'_new_label\("'+key+r'", ([\-0-9.]+), ([\-0-9.]+)\)',view).groups()),sh) for key in ("Action","Cost")}
result={"pin":pin,"git_blobs":blobs,"asset_sha256":hashlib.sha256(asset).hexdigest(),
        "scope":"Opt-in replacement preview V5, source-derived label-plane projection at authored 1280x720 only. A 30-font-pixel direction is an illustrative scale, not measured glyph box, readability, phone or occlusion proof.",
        "source_inputs":{"viewport":[sw,sh],"camera_vector":camera,"camera_height_span":span,"asset_scale":s,"fitted_dims_m":[s*(hi[j]-lo[j]) for j in range(3)],"deck_roof_m_above_anchor":deck_h,"label_y_m_above_anchor":deck_h+const("SEAT_LABEL_GAP")},
        "labels":labels}
# Positive camera sanity: vertical in world spans exactly 720 logical px * up.y at 13m.
# Orthographic height doubling moves projected deltas by exactly half. Pixel-size doubling doubles both deltas.
for key, r in labels.items():
    vv=r["one_font_px_line_vertical_to_screen_xy"]
    assert math.isclose(math.hypot(*vv),sh/span*r["world_per_font_pixel_m"]*math.sqrt(1-n[2]**2),rel_tol=1e-12)
assert labels["Cost"]["30_font_px_vertical_screen_y_only"]<labels["Action"]["30_font_px_vertical_screen_y_only"]
print(json.dumps(result,indent=2,sort_keys=True))
