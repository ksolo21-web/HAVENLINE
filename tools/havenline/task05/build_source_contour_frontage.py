#!/usr/bin/env python3
"""T05 source-traced front-module diagnostic; NOT a finished cooker.

Source-pixel scale is 1536/1280 = 1.2. The 1280-coordinate preview and the
1536-pixel actual owner image were previously confused. This tool traces the
blue and timber frontal outlines as separate 3D meshes, adds them to the
UNALTERED original Artisan Saw GLB, and maps clean material-only source crops.
It must NOT be promoted without owner visual critic approval. The invisible
left/rear surfaces and reference cameras are not reconstructed here.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh
from trimesh.visual.texture import TextureVisuals
from trimesh.visual.material import PBRMaterial
from shapely.geometry import Polygon
from shapely.ops import triangulate
from source_carved_eave import build_carved_eave
from source_rear_service_five_slots import add_rear_panel

SHA="70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4"
FRONT_SCALE=1536/1280
MATERIAL_REGIONS={"blue":(640,565,775,675),
                  "wood_horizontal":(555,490,777,517),
                  "wood_vertical":(493,560,525,664)}
PROFILES={
"BLUE_SHOULDER_VOLUMETRIC_WIP":([(477,640),(457,600),(449,555),(459,484),(484,431),(521,410),(573,390),(646,376),(744,372),(824,378),(899,397),(954,414),(994,451),(1015,493),(1020,575),(1014,656),(1001,703),(969,732),(927,744),(858,745),(748,738),(639,722),(548,697),(498,664)],-.38,-1.55,"blue"),
"BLUE_SERVICE_DOOR_LEFT":([(483,448),(629,447),(685,451),(706,471),(706,585),(693,614),(662,632),(582,629),(509,626),(480,602),(469,561),(471,498)],.13,-.18,"blue"),
"BLUE_SERVICE_DOOR_RIGHT":([(696,448),(740,451),(759,465),(760,589),(748,617),(704,616)],.18,-.16,"blue"),
"TIMBER_EAVE_REAL_CONTOUR":([(361,394),(372,379),(390,376),(412,382),(434,378),(471,375),(517,371),(573,372),(618,371),(668,377),(715,381),(756,375),(801,377),(835,392),(845,425),(839,445),(820,450),(781,448),(738,448),(691,450),(641,451),(596,452),(546,451),(505,454),(463,452),(425,456),(387,451),(365,443)],.62,-.20,"wood_horizontal"),
"LEFT_CARVED_TIMBER_UPRIGHT":([(400,446),(460,448),(459,512),(459,581),(450,609),(395,607),(389,575),(396,518)],.46,-.16,"wood_vertical"),
"RIGHT_CARVED_TIMBER_UPRIGHT":([(741,451),(808,451),(817,487),(814,574),(812,616),(752,620),(747,569),(745,512)],.44,-.18,"wood_vertical"),
"LEFT_STEEL_CLAMP":([(389,523),(473,519),(477,577),(460,585),(397,585),(388,574)],.78,.36,"blue"),
"RIGHT_STEEL_CLAMP":([(749,540),(833,535),(840,591),(826,606),(753,600)],.79,.39,"blue"),
"DOOR_SILVER_SEAM_LEFT":([(671,459),(681,462),(683,613),(675,616)],.23,.15,"blue"),
"DOOR_SILVER_SEAM_RIGHT":([(699,459),(705,462),(706,609),(701,612)],.23,.15,"blue")}
FASTENERS=[
 ("SERVICE_LEFT",487,486,.065,.38),("SERVICE_RIGHT",692,490,.07,.38),
 ("CLAMP_LEFT",414,550,.077,.88),("CLAMP_RIGHT",790,568,.080,.88)]
def pixel_to_3d(x,y):
    return ((x*FRONT_SCALE-1128)/150,1.818-(y*FRONT_SCALE-519)/150)
def layer(scene,name,profile,front,back,material):
    p=Polygon([pixel_to_3d(*xy) for xy in profile])
    assert p.is_valid and p.area>0.01,name
    xy=list(p.exterior.coords)[:-1];n=len(xy)
    verts=np.asarray([(x,y,z) for z in (front,back) for x,y in xy],dtype=float)
    vals=np.asarray(xy)
    u=(vals[:,0]-vals[:,0].min())/max(np.ptp(vals[:,0]),1.e-6)
    v=(vals[:,1]-vals[:,1].min())/max(np.ptp(vals[:,1]),1.e-6)
    uv=np.tile(np.column_stack([u,v]),(2,1))
    lookup={tuple(np.round(point,7)):i for i,point in enumerate(xy)}
    faces=[]
    for tri in triangulate(p):
        if not p.covers(tri.representative_point()):continue
        ids=[lookup[tuple(np.round(pt,7))] for pt in list(tri.exterior.coords)[:-1]]
        faces.extend([ids,[i+n for i in ids[::-1]]])
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,j+n),(i,j+n,i+n)])
    mesh=trimesh.Trimesh(vertices=verts,faces=faces,process=False,
         visual=TextureVisuals(uv=uv,material=material))
    mesh.fix_normals()
    assert mesh.is_winding_consistent
    scene.add_geometry(mesh,geom_name=name,node_name=name)
    return len(mesh.faces)
def build(source,saw,rear,out):
    source,saw,out=Path(source),Path(saw),Path(out)
    out.mkdir(parents=True,exist_ok=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==SHA
    im=Image.open(source).convert("RGB")
    assert im.size==(1536,1536)
    original=saw.read_bytes()
    original_sha=hashlib.sha256(original).hexdigest()
    scene=trimesh.load(saw,force="scene")
    saw_faces=sum(len(m.faces) for m in scene.geometry.values())
    assert saw_faces==7088,"Different saw model; preserve approved-looking source"
    materials={}
    for name,box in MATERIAL_REGIONS.items():
        cropped=im.crop(box)
        cropped.save(out/("original_"+name+"_sample.png"))
        materials[name]=PBRMaterial(name="32451_ORIGINAL_"+name,
           baseColorTexture=cropped,metallicFactor=.05 if name=="blue" else 0,
           roughnessFactor=.78 if name=="blue" else .9,doubleSided=True)
    added=0
    for name,(outline,front,back,kind) in PROFILES.items():
        if name=="TIMBER_EAVE_REAL_CONTOUR":
            # Detailed continuous watertight eave, NOT a faceted slab.
            carved=build_carved_eave(materials["wood_horizontal"],pixel_to_3d)
            scene.add_geometry(carved,geom_name="SOURCE_SCULPTED_TIMBER_EAVE",
                               node_name="SOURCE_SCULPTED_TIMBER_EAVE")
            added+=len(carved.faces)
        else:
            added+=layer(scene,name,outline,front,back,materials[kind])
    rear_audit=add_rear_panel(scene,rear,out)
    assert rear_audit["real_through_holes"]==5
    for name,x,y,r,z in FASTENERS:
        pt=pixel_to_3d(x,y)
        mesh=trimesh.creation.icosphere(subdivisions=2,radius=r)
        mesh.apply_translation([pt[0],pt[1],z])
        mesh.visual.vertex_colors=np.tile([155,173,185,255],(len(mesh.vertices),1))
        scene.add_geometry(mesh,geom_name=name,node_name=name)
        added+=len(mesh.faces)
    destination=out/"T05_SOURCE_CONTOUR_FRONTAGE_ONLY_UNAPPROVED.glb"
    destination.write_bytes(scene.export(file_type="glb"))
    final=trimesh.load(destination,force="scene")
    result={
      "status":"REAL_SOURCE_CONTOUR_GLTF_BUILT__INTERNAL_ART_CRITIC_FAIL",
      "reference_sha256":SHA,"saw_original_sha256":original_sha,
      "original_saw_face_count":saw_faces,"saw_mesh_source_not_rescaled":True,
      "new_frontage_triangles":added,
      "rear_service_panel":rear_audit,
      "overall_triangles":sum(len(m.faces) for m in final.geometry.values()),
      "material_samples_are_separated_blue_wood":True,
      "display_to_source_coordinate_ratio":FRONT_SCALE,
      "no_all_image_projected_on_shell":True,
      "occluded_meat_or_snow_texture_projection_rejected":True,
      "first_person_3D":True,"valid_complete_cooker":False,
      "owner_approved":False,"art_critic_pass":False,
      "shipping_asset_changed":False,
      "known_defects":["Blue shoulder and vertical framing still too coarse; eave sculpt is only a subpart",
       "Absent snow/food/roof/chimney/rear/pressure",
       "Reference camera not metrically calibrated",
       "Steel shoulder lacks source sculpted volume",
       "Artisan timber carving still shallow"],
      "SHA256_GLb":hashlib.sha256(destination.read_bytes()).hexdigest()}
    (out/"STATUS.json").write_text(json.dumps(result,indent=2)+"\n")
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--reference",required=True)
    p.add_argument("--saw",required=True)
    p.add_argument("--rear",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    print(json.dumps(build(args.reference,args.saw,args.rear,args.out),indent=2))
