"""T05 rear reference 32441.png: real 3D five-through-slot service cover.

Authoritative original has 1536x903 dimensions and JPEG-encoded bytes under
the .png name. This generator creates a watertight forged service panel with
five physical holes, an inner dark chamber and source-blue material sampling.
The housing and full cooker are NOT artistically approved.
"""
from pathlib import Path
import hashlib,math
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import triangulate
from PIL import Image
import trimesh
from trimesh.visual.texture import TextureVisuals
from trimesh.visual.material import PBRMaterial

REAR_SHA="0ff99199e1eb4bedeffe4d9953f5253a97e49366a2118d5976132c9137d93510"
def add_rear_panel(scene,source,out):
    source=Path(source);out=Path(out)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==REAR_SHA
    original=Image.open(source).convert("RGB")
    assert original.size==(1536,903)
    pigment=original.crop((679,528,856,591))
    pigment.save(out/"owner32441_rear_steel_sample.png")
    blue=PBRMaterial(name="32441_AUTHENTIC_REAR_BLUE",baseColorTexture=pigment,
           metallicFactor=.25,roughnessFactor=.64,doubleSided=True)
    shadow=PBRMaterial(name="T05_REAR_REAL_RECESSED_CAVITY",
           baseColorFactor=[.045,.075,.12,1.0],
           metallicFactor=.09,roughnessFactor=.92,doubleSided=True)
    outer=[(614,392),(645,363),(878,363),(913,391),(916,591),
           (888,619),(638,620),(614,598)]
    def to_3d(x,y):
        return ((x-760)/140-1.65,1.80-(y-360)/130)
    def slot(x):
        r=9;top=408;bottom=477
        upper=[(x+r*math.cos(math.pi*i/12),
                top-r*math.sin(math.pi*i/12)) for i in range(13)]
        lower=[(x+r*math.cos(math.pi+math.pi*i/12),
                bottom-r*math.sin(math.pi+math.pi*i/12)) for i in range(13)]
        return upper+lower
    raw_holes=[slot(x) for x in (694,728,764,800,836)]
    poly=Polygon([to_3d(*p) for p in outer],
       holes=[[to_3d(*pt) for pt in hole] for hole in raw_holes])
    assert poly.is_valid and poly.area>.8
    rims=[list(poly.exterior.coords)[:-1]]+[
        list(ring.coords)[:-1] for ring in poly.interiors]
    xy=[p for ring in rims for p in ring]
    n=len(xy)
    lookup={tuple(np.round(p,7)):i for i,p in enumerate(xy)}
    verts=np.asarray([(x,y,z) for z in (-1.71,-1.46) for x,y in xy])
    uv_base=np.asarray([((x+3)/4.2,(y+.5)/2.8) for x,y in xy])
    uv=np.tile(uv_base,(2,1))
    faces=[]
    for tri in triangulate(poly):
        if not poly.covers(tri.representative_point()):continue
        ids=[lookup[tuple(np.round(pt,7))]
             for pt in list(tri.exterior.coords)[:-1]]
        faces.extend([ids,[i+n for i in ids[::-1]]])
    for ring in rims:
        for i,p in enumerate(ring):
            next_p=ring[(i+1)%len(ring)]
            a=lookup[tuple(np.round(p,7))]
            b=lookup[tuple(np.round(next_p,7))]
            faces.extend([(a,b,b+n),(a,b+n,a+n)])
    mesh=trimesh.Trimesh(vertices=verts,faces=faces,process=False,
        visual=TextureVisuals(uv=uv,material=blue))
    mesh.fix_normals()
    assert mesh.is_watertight and mesh.is_winding_consistent
    scene.add_geometry(mesh,geom_name="FORGED_REAR_SERVICE_PANEL_FIVE_REAL_THROUGH_SLOTS")
    # The cavity is a separate interior part behind the physical holes.
    wall=trimesh.creation.box(extents=(2.3,1.70,.04))
    wall.apply_translation((-1.65,.58,-1.60))
    wall.visual=TextureVisuals(
        uv=np.zeros((len(wall.vertices),2)),material=shadow)
    scene.add_geometry(wall,geom_name="DARK_INNER_REAR_SERVICE_CHAMBER")
    return {"real_through_holes":5,"panel_triangles":len(mesh.faces),
            "watertight_service_panel":True,"owner_rear_sha256":REAR_SHA}
