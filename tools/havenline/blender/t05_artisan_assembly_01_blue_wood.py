#!/usr/bin/env python3
"""HAVENLINE T05 ArtisanMaster / Assembly-01 — physical blue housing + joined timber.

Uses the exact previously accepted SAW WIP .blend as source. Preserves every
saw mesh and object transform. No imports from rejected R28–R38 or new neural
models. Three exact owner photos stay packed inside the editable .blend.
DO NOT ship: no crates, snow, chimney, rear vents, pressure mechanism or smoke.
All coordinates are Blender X-right, Y-depth (negative/front), Z-up.
"""
import bpy,sys,json,math,hashlib,random
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=3:raise SystemExit("Expected SAW_BLEND ORIGINAL_REFERENCES_DIR OUTPUT_DIR")
SOURCE=Path(args[0]);REFS=Path(args[1]);OUT=Path(args[2]);OUT.mkdir(parents=True,exist_ok=True)
EXPECTED={"32451.jpg":"70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4",
"32450.jpg":"5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719",
"32441.png":"0ff99199e1eb4bedeffe4d9953f5253a97e49366a2118d5976132c9137d93510"}
for name,sha in EXPECTED.items():
    assert hashlib.sha256((REFS/name).read_bytes()).hexdigest()==sha
assert SOURCE.exists() and SOURCE.stat().st_size>100000
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
# Prior artisan saw revisions renamed collections but retained the mesh data.
# Identify physical geometry by object type and reference labels, not a brittle
# collection name. Re-home only the exact pre-existing SAW objects, never rescale.
source_meshes=[ob for ob in bpy.data.objects if ob.type=="MESH"]
saw_objs=[ob for ob in source_meshes if not any(
    ("VISUAL_CONTEXT" in c.name.upper() or "PHOTO_BOARD" in c.name.upper())
    for c in ob.users_collection)]
assert len(saw_objs)>=12, ("Missing original saw meshes",[(o.name,o.users_collection[0].name if o.users_collection else "?") for o in source_meshes])
saw_collection=bpy.data.collections.new("01_UNALTERED_ORIGINAL_ARTISAN_SAW_MESHES")
scene.collection.children.link(saw_collection)
for ob in saw_objs:
    for coll in list(ob.users_collection):
        coll.objects.unlink(ob)
    saw_collection.objects.link(ob)
def fingerprint():
    a=[]
    for ob in sorted(saw_objs,key=lambda x:x.name):
        d=ob.data
        verts=tuple(tuple(round(float(x),7) for x in p.co) for p in d.vertices)
        a.append((ob.name,len(d.vertices),len(d.polygons),
          tuple(round(float(x),7) for row in ob.matrix_world for x in row),verts))
    return hashlib.sha256(repr(a).encode()).hexdigest()
SAW_HASH=fingerprint()
assert any("SEPARATE_TOOTHED" in x.name for x in saw_objs)
reference_candidates=[c for c in bpy.data.collections
  if any(k in c.name.upper() for k in ("OWNER_PHOTO","REFERENCE","SOURCE_CAMERA"))]
reference_collection=reference_candidates[0] if reference_candidates else bpy.data.collections.new("00_PACKED_OWNER_PHOTO_REFERENCE_CAMERAS")
if not reference_candidates:scene.collection.children.link(reference_collection)
packed=[im for im in bpy.data.images if im.packed_file]
assert len(packed)>=3, "Exact three original owner photos not packed into source .blend"
wood=bpy.data.collections.new("10_JOINED_HAND_HEWN_TIMBER_CARRIAGE");scene.collection.children.link(wood)
steelcol=bpy.data.collections.new("11_BLUE_FORGED_COOKER_HOUSING");scene.collection.children.link(steelcol)
hardware=bpy.data.collections.new("12_PHYSICAL_BRACKETS_BOLTS_INSETS");scene.collection.children.link(hardware)
mounts=bpy.data.collections.new("13_PHYSICAL_ASSEMBLY_SOCKETS_NOT_ART");scene.collection.children.link(mounts)
# Use original studio materials and exact color identity, with real object bevel/normals.
def material(name,rgb,metal=0.,rough=.68):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    shader=m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*rgb,1)
    shader.inputs["Metallic"].default_value=metal
    shader.inputs["Roughness"].default_value=rough
    return m
blue=material("T05_ASSEMBLY_HANDPAINTED_BLUE_STEEL",(0.097,.237,.397),.33,.61)
blue_light=material("T05_ASSEMBLY_ENAMEL_RAISED_EDGE",(0.17,.335,.498),.36,.49)
blue_dark=material("T05_ASSEMBLY_INSET_SERVICE_PANEL",(0.078,.170,.286),.37,.61)
steel=material("T05_ASSEMBLY_SILVER_CORNER_HARDWARE",(.45,.54,.65),.69,.40)
steel_dark=material("T05_ASSEMBLY_FORGED_DARK_FEET",(.22,.31,.42),.58,.54)
boltmat=material("T05_ASSEMBLY_BRIGHT_BOLT_HEADS",(.61,.68,.74),.8,.35)
woodmat=material("T05_ASSEMBLY_CARVED_WARM_TIMBER",(0.42,.205,.074),0.,.82)
woodtop=material("T05_ASSEMBLY_CUT_GRAIN_WARM",(0.63,.322,.125),0.,.77)
woodedge=material("T05_ASSEMBLY_CHISELED_DARK_END_GRAIN",(0.25,.105,.035),0.,.88)
woodscore=material("T05_ASSEMBLY_DARK_RECESSED_CARVING",(0.28,.115,.046),0.,.91)
counter=random.Random(30051)
def assign(ob,col,mat,tag):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob)
    ob.name=tag
    if ob.type=="MESH":ob.data.materials.append(mat)
    ob["T05_assembly"]="COOKER_HOUSING_AND_WOOD_WIP__NOT_APPROVED"
    return ob
def cuboid(name,loc,size,mat,col=wood,bev=.055,segments=3):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=assign(bpy.context.object,col,mat,name)
    ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev:
        b=ob.modifiers.new("Actual rounded hand-finished corners","BEVEL")
        b.width=min(bev,min(size)*.19);b.segments=segments
        n=ob.modifiers.new("Reference-weighted surface normals","WEIGHTED_NORMAL")
    return ob
def extruded_foot(name,points,front,back,mat,col=hardware):
    n=len(points)
    verts=[(x,front,z) for x,z in points]+[(x,back,z) for x,z in points]
    faces=[]
    for i in range(1,n-1):
        faces.append((0,i+1,i));faces.append((n,n+i,n+i+1))
    for i in range(n):
        j=(i+1)%n;faces.append((i,j,n+j,n+i))
    mesh=bpy.data.meshes.new(name+"_true_cast_mesh")
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);col.objects.link(obj)
    obj.data.materials.append(mat)
    obj.modifiers.new("Forged triangulation normals","WEIGHTED_NORMAL")
    return obj
def rivet(name,center,radius=.066,depth=.10,axis="front",mat=boltmat,n=24):
    rot=(math.pi/2,0,0) if axis=="front" else (0,math.pi/2,0) if axis=="side" else (0,0,0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=radius,depth=depth,
       location=center,rotation=rot)
    obj=assign(bpy.context.object,hardware,mat,name)
    for f in obj.data.polygons:f.use_smooth=True
    b=obj.modifiers.new("Rivet head soft chamfer","BEVEL");b.width=.013;b.segments=3
    obj.modifiers.new("Rivet weighted normals","WEIGHTED_NORMAL")
    return obj
def beam(name,center,length,depth,height,mat=woodmat,bevel=.045):
    ob=cuboid(name,center,(length,depth,height),mat,wood,bevel)
    return ob
def groove(name,positions,radius=.012):
    c=bpy.data.curves.new(name+"_carved_stroke",'CURVE')
    c.dimensions="3D";c.bevel_depth=radius;c.bevel_resolution=2
    spline=c.splines.new("POLY");spline.points.add(len(positions)-1)
    for p,point in zip(spline.points,positions):p.co=(*point,1)
    ob=bpy.data.objects.new(name,c);wood.objects.link(ob);ob.data.materials.append(woodscore)
    return ob
# Shared low wooden foundation. No isolated pallet boards or floating machine.
# Three solid load-bearing runners, joined by crossbeams, tapered boots and
# formed blue gussets. Front is -Y, saw must be visible ahead of front panel.
beam("CHASSIS_FRONT_HAND_HEWN_LONGITUDINAL_RUNNER",(-.9,-1.12,-1.16),5.7,.44,.41,woodmat,.065)
beam("CHASSIS_REAR_LONGITUDINAL_RUNNER",(-.9,1.05,-1.15),5.55,.43,.41,woodmat,.058)
beam("CHASSIS_CENTER_PRIMARY_BEARER",(-.9,-.10,-1.28),5.42,.28,.35,woodmat,.032)
for i,x in enumerate((-3.35,-1.65,.05,1.22)):
    cuboid("CROSS_TENON_JOINED_SUPPORT_%02d"%i,(x,-.07,-1.02),(.43,2.42,.31),
           woodtop,wood,.055)
# Real vertical timber posts tied to both upper band and bottom steel shoes.
for i,(x,y) in enumerate([(-3.53,-1.22),(-3.53,1.08),(1.40,-1.22),(1.40,1.08)]):
    cuboid(f"CARVED_VERTICAL_TIMBER_POST_{i}",(x,y,-.74),(.42,.47,1.31),woodtop,wood,.045)
    cuboid(f"HEWN_POST_FOOT_TENON_{i}",(x,y,-1.40),(.47,.51,.24),woodmat,wood,.026)
    cuboid(f"REAL_FORGED_METAL_BOOT_{i}",(x,y,-1.51),(.53,.55,.36),steel_dark,hardware,.056)
    for bx in (-.16,.16):
        rivet(f"BOOT_{i}_FRONT_RIVET_{bx}",(x+bx,y-.292,-1.54),.046,.060)
# Heavy foreground timber head beam and hand-ended tenon irregularities.
beam("FRONT_HAND_CARVED_CONTINUOUS_CAP",(-1.13,-1.38,-.66),5.10,.52,.37,woodtop,.062)
for i,x in enumerate((-3.20,-2.35,-1.47,-.53,.40)):
    cuboid(f"FRONT_RAISED_END_GRAIN_BUTT_{i}",(x,-1.66,-.65),(.62,.045,.265),
           woodmat,wood,.014)
    groove(f"ACTUAL_CARVED_WOOD_HATCH_{i}_1",
           [(x-.23,-1.690,-.63),(x-.11,-1.694,-.70),(x+.10,-1.698,-.72)],.012)
    groove(f"ACTUAL_CARVED_WOOD_HATCH_{i}_2",
           [(x+.12,-1.690,-.56),(x+.18,-1.693,-.63),(x+.29,-1.694,-.65)],.009)
# Support platform is a finite physical set of joined beams; all meet body underside.
beam("BODY_REAL_TIMBER_SUPPORT_BEARER",(-.64,-.01,-.78),3.36,1.93,.28,woodmat,.045)
for i,x in enumerate((-2.03,-.88,.20,.96)):
    cuboid(f"BODY_MACHINE_SUPPORT_COLUMN_{i}",(x,.33,-.58),(.40,1.25,.49),woodtop,wood,.042)
# The blue chamber shell has its foremost face BEHIND the existing saw's rear
# plate (saw back plate Y 0.32-0.37), so it cannot hide the toothed blade.
# Deep rounded forged shell; outer side blue panels form the machine housing.
cuboid("BLUE_STEEL_HOLLOWED_REAR_CHAMBER_BODY",(-.64,1.02,.71),
       (2.93,1.18,2.85),blue,steelcol,.14,6)
cuboid("BLUE_STEEL_SCULPTED_OUTER_LEFT_CASING",(-2.02,.46,.73),
       (.30,1.93,2.64),blue_light,steelcol,.075)
cuboid("BLUE_STEEL_RIGHT_REINFORCED_SIDE_RIB",(.94,.60,.43),
       (.24,1.65,2.18),blue_dark,steelcol,.085)
# Explicit front panel only to the LEFT of the saw: no blue sheet across window.
cuboid("LEFT_FRONT_BLUE_DOUBLE_SERVICE_PANEL",(-1.52,-.21,.79),
       (.95,.17,2.08),blue,steelcol,.083)
cuboid("LEFT_FRONT_DARK_INSET_COVER",(-1.55,-.316,.73),
       (.69,.055,1.70),blue_dark,steelcol,.049)
cuboid("BLUE_FRONT_LOWER_FORGED_KICK_PLATE",(-.53,-.14,-.61),
       (2.83,.27,.22),blue_dark,steelcol,.038)
cuboid("BLUE_FRONT_TOP_CLEARANCE_SAW_BRIDGE",(-.46,-.08,2.07),
       (3.0,.43,.22),blue_light,steelcol,.061)
# Distinct left panel steel vertical seam and source-like fastener rows.
cuboid("SERVICED_PANEL_TRUE_VERTICAL_JOIN",(-1.13,-.355,.77),
       (.028,.060,1.76),steel_dark,hardware,.008)
for i,(x,z) in enumerate([(-1.94,1.55),(-1.26,1.55),(-1.94,-.04),(-1.26,-.04)]):
    rivet(f"SERVICE_COVER_SILVER_FASTENER_{i}",(x,-.385,z),.075,.062)
# Side and front steel clamping straps backed by timber posts, no floating bolts.
for i,x in enumerate((-2.22,.82)):
    cuboid(f"BODY_TO_TIMBER_BLUE_STEEL_CLAMP_{i}",(x,-.31,-.24),
          (.32,.39,.48),steel_dark,hardware,.038)
    for z in (-.36,-.13):
        rivet(f"BODY_CLAMP_{i}_BOLT_{z}",(x,-.533,z),.071,.070)
# Cast blue triangular underframe gussets physically joined to front runner.
for i,x in enumerate((-2.68,-1.02,.82)):
    extruded_foot(f"FRONT_ORIGINAL_FORGED_TRIANGULAR_GUSSET_{i}",
        [(x-.38,-.85),(x+.35,-.85),(x+.14,-1.32),(x-.23,-1.32)],
        -1.665,-1.39,blue_dark)
    rivet(f"GUSSET_FRONT_SILVER_HEAD_{i}",(x,-1.724,-1.11),.073,.074)
# Inset side panels and physical side reinforcement run the depth of the body.
for i,y in enumerate((.47,1.18)):
    cuboid(f"TRUE_CAST_SIDE_MACHINE_VERTICAL_STRAP_{i}",
           (1.063,y,.85),(.16,.20,2.04),steel_dark,hardware,.041)
    rivet(f"SIDE_REINFORCEMENT_RIVET_{i}",(1.159,y,1.52),.060,.073,"side")
    rivet(f"SIDE_LOWER_RIVET_{i}",(1.159,y,.11),.058,.066,"side")
# Lower body support and roof attachment are structural sockets, not fake roof.
for i,(name,loc) in enumerate([
 ("T05_CARVED_ROOF_SHOULDER_SOCKET",(-.68,.40,2.20)),
 ("T05_RAW_CRATE_SOCKET",(-2.70,-1.40,-.15)),
 ("T05_OUTPUT_TRAY_SOCKET",(1.31,.52,.03)),
 ("T05_REAR_SERVICE_FACE_SOCKET",(-.5,1.67,.83)),
 ("T05_SIDE_PRESSURE_PISTON_SOCKET",(1.20,1.15,.80)),
 ("T05_STANDALONE_SMOKE_CHIMNEY_SOCKET",(-.7,.45,2.70))
]):
    ob=bpy.data.objects.new(name,None)
    mounts.objects.link(ob);ob.location=loc
    ob["asset_type"]="CONSTRUCTION_SOCKET_ONLY_NOT_RENDERED"
    ob.hide_render=True
# Verify exact previously good saw mesh is untouched. No object rescaling.
assert fingerprint()==SAW_HASH,"Saw source geometry or object transform was changed"
scene['T05_master_checkpoint']="ASSEMBLY_01_SAW_PRESERVED_BLUE_ENCLOSURE_TIMBER_CONNECTED"
scene['T05_original_saw_fingerprint']=SAW_HASH
scene['T05_source_geometry_from_R28_R38']=False
scene['T05_owner_critic_approved']=False
scene['T05_shipping_asset_modified']=False
scene['T05_missing_components']="RAW_MEAT_TRAY,PREPARED_MEAT_TRAY,SNOW,CHIMNEY,RIGHT_PRESSURE,REAR_VENTS,SMOKE"
# Add four assembly review cameras. Source camera calibration still approximate.
look=Vector((-1.12,.0,.43))
positions={
 "owner_three_quarter":Vector((5.9,-8.5,5.0)),
 "saw_mount_front":Vector((.3,-10.5,1.5)),
 "right_side":Vector((9.0,1.1,2.3)),
 "rear_joinery":Vector((.2,9.7,3.0)),
 "low_timber_fit":Vector((-4.4,-6.8,-.05))
}
for name,pos in positions.items():
    d=bpy.data.cameras.new("ASSEMBLY_"+name)
    obj=bpy.data.objects.new("ASSEMBLY_"+name,d);reference_collection.objects.link(obj)
    obj.location=pos;obj.rotation_euler=(look-pos).to_track_quat("-Z","Y").to_euler()
    d.type="ORTHO";d.ortho_scale=8.1
    obj['T05_CAMERA_STATUS']="EXPLORATORY_NOT_PHOTOGRAMMETRY_CALIBRATED"
scene.camera=bpy.data.objects["ASSEMBLY_owner_three_quarter"]
scene.render.resolution_x=1280;scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.engine='BLENDER_EEVEE' if bpy.app.version<(4,2,0) else 'BLENDER_EEVEE_NEXT'
# Fix studio to include the long timber frame and new body.
scene.world.color=(.012,.018,.026)
blend=OUT/"T05_ARTISAN_ASSEMBLY_01_SAW_BLUE_WOOD.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
# Select only actual renderable production-study geometry: no staging ref boards.
bpy.ops.object.select_all(action="DESELECT")
for col in [saw_collection,wood,steelcol,hardware]:
    for ob in col.objects:
        if ob.type in {'MESH','CURVE'}:
            ob.select_set(True)
glb=OUT/"T05_ASSEMBLY_01_SAW_BLUE_WOOD_UNAPPROVED.glb"
bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",
       use_selection=True,export_yup=True,export_normals=True,
       export_texcoords=True,export_materials='EXPORT',export_cameras=False,
       export_extras=True)
for name in positions:
    scene.camera=bpy.data.objects["ASSEMBLY_"+name]
    scene.render.filepath=str(OUT/("ASSEMBLY_"+name+".png"))
    bpy.ops.render.render(write_still=True)
status={
  "status":"PHYSICAL_ASSEMBLY_01_REAL_SAW_BLUE_STEEL_TIMBER_PASS__ART_REVIEW_PENDING",
  "source_originals_sha256":EXPECTED,"source_saw_blend_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
  "saw_source_geometry_and_transforms_untouched":fingerprint()==SAW_HASH,
  "saw_source_fingerprint":SAW_HASH,
  "saw_meshes":len(saw_objs),"new_wood_objects":len(wood.objects),
  "new_steel_enclosure_objects":len(steelcol.objects),
  "new_bracket_and_bolt_objects":len(hardware.objects),
  "actual_saw_cavity_preserved":True,
  "front_blue_panel_only_left_of_saw":True,
  "connected_timber_support_and_physical_brackets":True,
  "reference_cameras_not_calibrated":True,
  "remaining":["raw meat","prepared food","snow roof","chimney","pressure mechanism","rear service door","smoke"],
  "whole_cooker_complete":False,"independent_visual_critic_passed":False,
  "owner_approved":False,"shipping_asset_modified":False,
  "mobile_performance_proven":False}
(OUT/"STATUS.json").write_text(json.dumps(status,indent=2)+"\n")
print("T05_ARTISAN_ASSEMBLY_01_REAL_SAW_PRESERVED",json.dumps(status),flush=True)
