"""T05 actual 3D right-side pressure mechanism from owner's original 32450.jpg.

One physical component, including lathed forged bell, seal collars, piston
shaft, crank and separate orange operating fasteners. This is NOT a traced
metric camera reconstruction or a complete cooker.
"""
from pathlib import Path
import hashlib,math
import numpy as np
from PIL import Image
import trimesh
from trimesh.visual.texture import TextureVisuals
from trimesh.visual.material import PBRMaterial

SIDE_SHA="5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719"
def lathe(x,z,profile,material,sections=48):
    vertices=[];uv=[]
    for j,(r,y) in enumerate(profile):
        for i in range(sections):
            a=i*math.tau/sections
            vertices.append((x+r*math.cos(a),y,z+r*math.sin(a)))
            uv.append((i/(sections-1),j/(len(profile)-1)))
    faces=[]
    for j in range(len(profile)-1):
        for i in range(sections):
            a=j*sections+i
            b=j*sections+(i+1)%sections
            c=(j+1)*sections+(i+1)%sections
            d=(j+1)*sections+i
            faces.extend(((a,b,c),(a,c,d)))
    left=len(vertices)
    right=left+1
    vertices.extend(((x,profile[0][1],z),(x,profile[-1][1],z)))
    uv.extend(((.5,0),(.5,1)))
    for i in range(sections):
        faces.append((left,(i+1)%sections,i))
        a=(len(profile)-1)*sections+i
        b=(len(profile)-1)*sections+(i+1)%sections
        faces.append((right,a,b))
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False,
         visual=TextureVisuals(uv=uv,material=material))
    mesh.fix_normals()
    assert mesh.is_watertight
    return mesh
def rod(start,end,r,material,sections=24):
    a=np.asarray(start,dtype=float)
    b=np.asarray(end,dtype=float)
    direction=b-a
    length=float(np.linalg.norm(direction))
    assert length>0
    mesh=trimesh.creation.cylinder(radius=r,height=length,sections=sections)
    mesh.apply_transform(trimesh.geometry.align_vectors([0,0,1],direction/length))
    mesh.apply_translation((a+b)*.5)
    mesh.visual=TextureVisuals(
        uv=np.tile([[.5,.5]],(len(mesh.vertices),1)),material=material)
    return mesh
def add_side_pressure(scene,reference,out):
    reference=Path(reference)
    assert hashlib.sha256(reference.read_bytes()).hexdigest()==SIDE_SHA
    source=Image.open(reference).convert("RGB")
    assert source.size==(1536,1147)
    pigment=source.crop((828,476,912,529))
    pigment.save(Path(out)/"owner32450_pressure_metal_sample.png")
    steel=PBRMaterial(name="OWNER_32450_STYLIZED_FORGED_SILVER",
           baseColorTexture=pigment,metallicFactor=.7,roughnessFactor=.44,
           doubleSided=True)
    dark=PBRMaterial(name="PRESSURE_REAL_FORGED_SEALS",
           baseColorFactor=[.17,.23,.32,1.0],metallicFactor=.6,
           roughnessFactor=.52,doubleSided=True)
    orange=PBRMaterial(name="PRESSURE_OPERATING_ORANGE",
           baseColorFactor=[.72,.29,.08,1.0],metallicFactor=.3,
           roughnessFactor=.4,doubleSided=True)
    x,z=1.10,-.43
    main=[(.23,.11),(.29,.13),(.33,.19),(.33,.30),(.29,.34),
          (.29,.44),(.29,.68),(.27,.77),(.19,.89),(.12,.95),
          (.12,1.00),(.10,1.06),(.08,1.09),(.08,1.24),(.07,1.27)]
    assemblies=[
      ("PHYSICAL_PRESSURE_VESSEL",main,steel),
      ("PRESSURE_CAST_SEAL_RING",[(.33,.28),(.37,.32),(.37,.42),(.32,.44)],dark),
      ("PRESSURE_TOP_BEARING",[(.15,.99),(.20,1.02),(.20,1.10),(.11,1.15)],steel),
      ("PRESSURE_BUTTON",[(.08,1.19),(.12,1.23),(.12,1.31),(.07,1.34)],steel)]
    for name,profile,material in assemblies:
        scene.add_geometry(lathe(x,z,profile,material),geom_name=name)
    shafts=[
      ("PRESSURE_PISTON_ROD",(1.18,.70,+.90),(1.18,.70,-.20),.090,steel),
      ("SIDE_CRANK_AXLE",(1.13,.59,-.70),(1.13,.59,-1.22),.085,steel),
      ("SIDE_CRANK_LEVER",(1.18,.61,-1.20),(1.18,.15,-1.20),.082,dark),
      ("SIDE_CRANK_HANDGRIP",(1.18,.15,-1.20),(1.18,.15,-1.55),.073,steel)]
    for name,start,end,r,material in shafts:
        scene.add_geometry(rod(start,end,r,material),geom_name=name)
    for name,center,r,material in [
      ("PRESERVED_ORANGE_SIDEPIVOT",(1.18,.70,.89),.16,orange),
      ("PRESERVED_SILVER_CRANK_KNOB",(1.18,.70,-1.25),.13,steel)]:
        mesh=trimesh.creation.icosphere(subdivisions=2,radius=r)
        mesh.apply_translation(center)
        mesh.visual=TextureVisuals(uv=np.tile([[.5,.5]],(len(mesh.vertices),1)),material=material)
        scene.add_geometry(mesh,geom_name=name)
    return {"source_sha256":SIDE_SHA,"separate_lathed_housing":True,
            "physical_rods":4,"side_crank_independent":True,
            "source_camera_calibrated":False,"critic_passed":False}
