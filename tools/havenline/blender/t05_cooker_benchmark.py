#!/usr/bin/env python3
"""HAVENLINE T05 Blender authoring benchmark — cooker, source model only.

Keep the canonical T05 Python-generated GLBs and their approved/tested pipeline
UNCHANGED. This produces an editable .blend, a separate candidate .glb and
four reference-comparison camera renders; it never overwrites the game cooker.
Primary object reference: owner-supplied 18567.png (not redistributable).
"""
import bpy, math, random, sys, json, pathlib
from mathutils import Vector, Matrix

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
out=pathlib.Path(args[args.index("--out")+1] if "--out" in args else "/tmp/havenline-blender-cooker").resolve()
out.mkdir(parents=True,exist_ok=True)
random.seed(18567)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.collections):
    if block.name!="Collection" and block.users==0: bpy.data.collections.remove(block)

art=bpy.data.collections.new("T05_Cooker_EDITABLE_Source")
bpy.context.scene.collection.children.link(art)
stage=bpy.data.collections.new("RENDER_ONLY_not_in_GLb")
bpy.context.scene.collection.children.link(stage)
made=[]; palette={}
def move(obj,collection):
    for old in list(obj.users_collection):old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj
def mat(key,color,rough=.74,metal=0):
    m=bpy.data.materials.new("HL_"+key)
    m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    palette[key]=m
    return m
mat("blue",(.16,.34,.53),.40,.32)
mat("dark",(.075,.12,.17),.53,.48)
mat("metal",(.64,.70,.75),.41,.38)
mat("wood",(.34,.17,.085),.78)
mat("wood_light",(.59,.32,.14),.74)
mat("snow",(.85,.91,.95),.88)
mat("cream",(.96,.73,.52),.74)
mat("orange",(.94,.30,.045),.43,.22)
mat("yellow",(.86,.60,.15),.54,.20)
mat("red",(.72,.14,.10),.64,.04)
# Game-ready 256x256 base color tiles, *not* unsupported procedural BSDF
# graphs. Wood has subtle longitudinal grain; metal brushed linework.
def tile(key,kind):
    img=bpy.data.images.new("T05_"+key+"_basecolor",width=256,height=256,alpha=True)
    base=palette[key].diffuse_color
    random_seed=random.Random(500+sum(ord(x) for x in key))
    pixels=[]
    for y in range(256):
        yy=y/256.
        for x in range(256):
            xx=x/256.
            wave=math.sin((xx*5.6+yy*.12)*math.tau)*.034
            streak=math.sin((yy*3.7+xx*.036)*math.tau)*.02 if kind=="metal" else wave
            grain=(random_seed.random()-.5)*(.042 if kind=="wood" else .02)
            var=1+streak+grain
            pixels.extend((min(1,base[0]*var),min(1,base[1]*var),min(1,base[2]*var),1))
    img.pixels.foreach_set(pixels)
    img.filepath_raw=str(out/("T05_"+key+"_basecolor.png"))
    img.file_format="PNG";img.save()
    bs=palette[key].node_tree.nodes["Principled BSDF"]
    node=palette[key].node_tree.nodes.new("ShaderNodeTexImage")
    node.image=img
    palette[key].node_tree.links.new(node.outputs["Color"],bs.inputs["Base Color"])
for key,kind in (("wood","wood"),("wood_light","wood"),("metal","metal"),("blue","metal")):
    tile(key,kind)

def register(obj,name,key):
    obj.name=name
    move(obj,art)
    obj.data.materials.clear();obj.data.materials.append(palette[key])
    made.append(obj)
    return obj
def box(name,pos,size,key,bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=bpy.context.object
    o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    register(o,name,key)
    if bevel>0:
        mod=o.modifiers.new("Hand-finished edge bevel","BEVEL")
        mod.width=min(bevel,min(size)*.22);mod.segments=2
        if hasattr(mod,"affect"): mod.affect="EDGES"
        if hasattr(o.data,"use_auto_smooth"): o.data.use_auto_smooth=True
        o.modifiers.new("Weighted corner normals","WEIGHTED_NORMAL")
    return o
def cylinder(name,pos,radius,depth,key,axis="Z",verts=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=pos)
    o=bpy.context.object
    if axis=="Y":o.rotation_euler[0]=math.pi/2
    if axis=="X":o.rotation_euler[1]=math.pi/2
    return register(o,name,key)
def ball(name,pos,size,key,segments=12,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    o=bpy.context.object;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return register(o,name,key)
def tube(name,points,material,width=.035,res=2):
    curve=bpy.data.curves.new(name,"CURVE");curve.dimensions="3D"
    curve.resolution_u=8;curve.bevel_depth=width;curve.bevel_resolution=res
    spline=curve.splines.new("POLY");spline.points.add(len(points)-1)
    for p,loc in zip(spline.points,points):
        p.co=(*loc,1)
    o=bpy.data.objects.new(name,curve);art.objects.link(o)
    o.data.materials.append(palette[material]);made.append(o)
    return o
def arch(name,cx,cy,z,rx,ry,key,width=.028):
    pts=[(cx-rx,cy-.24,z),(cx-rx,cy,z)]
    for i in range(21):
        angle=math.pi-i*math.pi/20
        pts.append((cx+rx*math.cos(angle),cy+ry*math.sin(angle),z))
    pts.extend(((cx+rx,cy-.24,z),))
    return tube(name,pts,key,width)
# Compact footprint 2.45 X 2.30 Z, sockets maintained by canonical catalog.
# Heavy timber table and metal feet.
for x in (-1.01,1.01):
    for z in (-.53,.53):
        box("Timber corner post", (x,.34,z),(.17,.67,.18),"wood",.035)
        box("Bolted iron boot",(x,.13,z),(.20,.22,.22),"dark",.024)
for z in (-.57,.57):
    box("Long carved load rail",(0,.61,z),(2.25,.19,.20),"wood_light",.044)
    box("Blue protective rail",(0,.50,z),(2.17,.075,.20),"blue",.018)
# Frozen footprint allows stronger ironwork and a readable low-front chassis.
box("Steel front load beam",(0,.30,-.575),(2.14,.18,.12),"blue",.025)
for x in (-.96,.96):
    box("Bolted knee bracket",(x,.51,-.63),(.155,.25,.09),"metal",.022)
    cylinder("Iron corner rivet",(x,.53,-.683),.038,.018,"dark","Y",10)
for x in (-.72,-.26,.20,.68):
    box("Joined plank work surface",(x,.73,0),(.43,.13,1.32),"wood",.034)
# Main stove architecture; -Z is its actual operator/front side.
box("Enamel blue forged firebox",(0,1.23,-.11),(.99,.84,.79),"blue",.115)
box("Raised upper fascia",(0,1.67,-.11),(1.13,.19,.94),"blue",.052)
box("Outer metal door bezel",(0,1.26,-.545),(.80,.59,.12),"metal",.070)
box("Recessed black window",(0,1.26,-.62),(.68,.47,.035),"dark",.020)
arch("Inset window polished top arch",0,1.38,-.656,.35,.15,"metal",.032)
tube("Window bottom metal rim",[(-.34,1.015,-.656),(.34,1.015,-.656)],"metal",.039)
for x in (-.37,.37):
    tube("Window rounded vertical edge",[(x,1.02,-.654),(x,1.39,-.654)],"metal",.027)
# Reference-style visible machined metal hardware and inset steel rivets.
for x in (-.40,.40):
    for y in (1.055,1.48):
        cylinder("Bezel corner rivet",(x,y,-.67),.034,.020,"metal","Y",12)
# A forged saw disc with actual toothed thickness and machined sidewalls:
# the previous perfectly flat gear looked like a silhouette decal in Godot.
tooth_steps=48
front_z=-.695
back_z=-.661
ring=[]
for i in range(tooth_steps):
    a=math.tau*i/tooth_steps
    r=(.215 if i%4==0 else .187 if i%4==1 else .179 if i%4==2 else .207)
    ring.append((r*math.cos(a),1.265+r*math.sin(a)))
front=[(x,y,front_z) for x,y in ring]
rear=[(x,y,back_z) for x,y in ring]
verts=[(0,1.265,front_z)]+front+[(0,1.265,back_z)]+rear
rear_center=tooth_steps+1
faces=[]
for i in range(tooth_steps):
    j=(i+1)%tooth_steps
    faces.extend((
        (0,1+j,1+i),
        (rear_center,rear_center+1+i,rear_center+1+j),
        (1+i,1+j,rear_center+1+j),
        (1+i,rear_center+1+j,rear_center+1+i)
    ))
mesh=bpy.data.meshes.new("Forged steel saw with thick toothed wall")
mesh.from_pydata(verts,[],faces);mesh.update()
wheel=bpy.data.objects.new("Visible forged saw thickness",mesh)
art.objects.link(wheel);made.append(wheel)
wheel.data.materials.append(palette["metal"])
cylinder("Saw beveled central steel bearing",(0,1.265,-.703),.098,.032,"metal","Y",18)
cylinder("Saw axle",(0,1.265,-.709),.060,.060,"dark","Y",16)
cylinder("Copper axle fastener",(0,1.265,-.752),.040,.034,"orange","Y",12)
tube("Safety orange handgrip",[(-.27,.90,-.752),(.27,.90,-.752)],"orange",.057,3)
for x in (-.23,.23):
    tube("Handle steel mount",[(x,.91,-.636),(x,.91,-.76)],"metal",.027)
# Timber bins and meat cuts: raw left, finished steel tray right.
box("Raw input bin bottom",(-.85,.94,.15),(.63,.09,.80),"wood",.034)
for x in (-1.145,-.555):
    box("Raw bin carved sidewall",(x,1.07,.15),(.08,.29,.83),"wood_light",.03)
for z in (-.22,.52):
    box("Raw bin front back board",(-.85,1.07,z),(.66,.29,.09),"wood_light",.03)
for i,(x,z,rx,rz) in enumerate(((-1.06,-.04,.15,.13),(-.83,-.06,.17,.13),(-.64,.1,.14,.14),(-1.00,.28,.18,.13),(-.72,.36,.17,.13))):
    ball("Individually sculptable raw meat cut",(x,1.20+i%2*.036,z),(rx,.095,rz),"red",12,8)
    ball("Fat marbling",(x-.037,1.28+i%2*.037,z+.027),(rx*.57,.025,rz*.70),"cream",10,6)
box("Prepared meat steel tray",(.85,.95,.15),(.66,.12,.85),"metal",.038)
box("Prepared tray dark inner bed",(.85,1.018,.15),(.56,.04,.72),"dark",.018)
for x in (.54,1.16): box("Folded steel side tray wall",(x,1.13,.15),(.065,.20,.86),"metal",.016)
for z in (-.245,.545): box("Steel tray lip",(.85,1.13,z),(.70,.20,.064),"metal",.017)
for i,(x,z) in enumerate(((.68,-.07),(.96,-.07),(.69,.22),(.96,.23))):
    o=box("Cooked meat wrapped cut",(x,1.20,z),(.23,.17,.26),"red",.055)
    o.rotation_euler[2]=(-1)**i*.13
    box("Fat cap",(x,1.29,z),(.17,.025,.22),"cream",.009)
    box("Orange securing band",(x,1.304,z),(.045,.041,.28),"orange",.009)
# Exterior mechanical cylinder, side pipe, gauge (functional hierarchy).
cylinder("Side pressure vessel",(.59,1.30,.47),.17,.46,"dark","Z",16)
cylinder("Hose collar",(.59,1.58,.47),.15,.070,"metal","Z",16)
tube("Pressure feed hose",[(.59,1.47,.47),(.75,1.46,.34),(.81,1.36,.22)],"metal",.038)
cylinder("Gauge outside",(.87,1.61,.40),.11,.045,"metal","Y",16)
cylinder("Gauge face",(.87,1.61,.37),.075,.047,"cream","Y",14)
tube("Gauge needle",[(.84,1.57,.336),(.89,1.66,.336)],"dark",.009)
# Rear-top integrated chimney; open dark throat on top.
cylinder("Chimney neck",(.20,1.95,.06),.135,.37,"dark","Z",16)
cylinder("Chimney steel collar",(.20,2.18,.06),.175,.13,"metal","Z",18)
cylinder("Chimney upper cap",(.20,2.34,.06),.19,.10,"dark","Z",18)
cylinder("Hollow looking black exhaust",(.20,2.398,.06),.113,.012,"dark","Z",18)
# One hand-shaped continuous snowy overhang over the complete iron roof.
# Unlike overlapping primitive snow spheres this forms a continuous hood with
# localized drips and thickness, a core defining feature of owner art 18567.
x_steps,z_steps=20,16
top=[];bottom=[];surface_faces=[]
for zi in range(z_steps+1):
    uz=zi/z_steps;zz=-.63+1.21*uz
    for xi in range(x_steps+1):
        ux=xi/x_steps;xx=-.68+1.36*ux
        dome=max(0.,1.-.69*((xx/.68)**2)-.59*((zz/.63)**2))
        # Three asymmetric, physically connected leading-edge snow tongues.
        # Their drop is strongest at the front, tapering smoothly into the roof.
        scallop=(.024*math.sin(xx*9.3+.3)+.015*math.sin(zz*13.1+xx*2.7)
                 +.009*math.sin(xx*21.0-zz*7.4))
        front_strength=max(0.,1.-uz/.26)**2
        front_tongues=sum(amplitude*math.exp(-((xx-center)/spread)**2)
                          for center,amplitude,spread in
                          ((-.49,.096,.16),(-.14,.062,.12),(.22,.105,.15),(.50,.079,.14)))
        edge_drape=(.035*(abs(2*uz-1)**7)+.034*(abs(2*ux-1)**8)
                    +front_strength*front_tongues)
        y=1.805+.150*dome+scallop-edge_drape
        top.append((xx,y,zz))
        bottom.append((xx,min(1.67,y-.12),zz))
stride=x_steps+1
num=len(top)
for zi in range(z_steps):
    for xi in range(x_steps):
        q=zi*stride+xi
        # Positive game Y must be the visible upper-face normal: X/Z order is
        # inverted compared to Blender's default XY plane.
        surface_faces.append((q,q+stride,q+stride+1,q+1))
        surface_faces.append((q+num,q+num+1,q+num+stride+1,q+num+stride))
# Rounded perimeter drop-face drapes, stitched as one closed mesh.
edges=[]
for xi in range(x_steps):edges.append((xi,xi+1))
for zi in range(z_steps):edges.append((zi*stride+x_steps,(zi+1)*stride+x_steps))
for xi in range(x_steps,0,-1):edges.append((z_steps*stride+xi,z_steps*stride+xi-1))
for zi in range(z_steps,0,-1):edges.append((zi*stride,(zi-1)*stride))
for aidx,bidx in edges:
    surface_faces.append((aidx,bidx,bidx+num,aidx+num))
roof_mesh=bpy.data.meshes.new("Sculpted_Continuous_Snow_Hood")
roof_mesh.from_pydata(top+bottom,[],surface_faces);roof_mesh.update()
roof=bpy.data.objects.new("Continuous thick snow roof, owner reference 18567",roof_mesh)
art.objects.link(roof);made.append(roof);roof.data.materials.append(palette["snow"])
for face in roof_mesh.polygons:face.use_smooth=True
snow_edge=roof.modifiers.new("Snow overhang soft rounded edge","BEVEL")
snow_edge.width=.026
snow_edge.segments=2
snow_edge.limit_method="ANGLE"
snow_normal=roof.modifiers.new("Sculpted snow weighted normals","WEIGHTED_NORMAL")
# Connected leading snow forms overlap the continuous roof perimeter, rather
# than the isolated bead-like globules rejected by native pixel inspection.
for x,y,z,rx in ((-.48,1.655,-.585,.134),(-.15,1.680,-.592,.112),(.23,1.651,-.586,.140),(.50,1.667,-.575,.121)):
    ball("Integrated scalloped snow lip",(x,y,z),(rx,.103,.131),"snow",12,8)
for x,z in ((-1.09,-.20),(-.61,.54),(1.02,.61)):
    ball("Accumulated snow on tray edges",(x,1.22,z),(.10,.054,.083),"snow",12,7)
# Blender is Z-up while Godot and glTF are Y-up: rotate the authored
# Godot-space model into Blender-space before editing, viewing and export.
# Blender glTF export_yup rotates it back to the original game coordinates.
coordinate_rotation=Matrix.Rotation(math.pi/2,4,"X")
# Align the actual front-facing food workflow to the owner's image: raw wood
# on visual left, finished steel on visual right, gauge right. Model-space X
# reflection does not move the frozen origin, socket markers, or Z-facing door.
reference_layout_reflection=Matrix.Diagonal((-1.0,1.0,1.0,1.0))
for object in made:
    object.matrix_world=coordinate_rotation @ reference_layout_reflection @ object.matrix_world
# Exporting does NOT use the black-background studio, only the actual model.
bpy.ops.object.select_all(action="DESELECT")
for o in made:o.select_set(True)
bpy.context.view_layer.objects.active=made[0]
# Preview backdrop is a separate labeled studio collection, not exported.
def staging_box(n,pos,size,color):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=bpy.context.object;o.name=n;o.scale=size
    move(o,stage);o.data.materials.append(color)
floor=mat("preview_floor",(.032,.055,.085),1)
staging_box("Studio ground only",(0,0,-.17),(7,7,.1),floor)
world=bpy.context.scene.world
if world is None:world=bpy.data.worlds.new("Night stage");bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs[0].default_value=(.06,.09,.14,1)
world.node_tree.nodes["Background"].inputs[1].default_value=.65
def area_light(name,pos,energy,size):
    light=bpy.data.lights.new(name,"AREA");light.energy=energy;light.shape="DISK";light.size=size
    o=bpy.data.objects.new(name,light);stage.objects.link(o)
    o.location=(pos[0],-pos[2],pos[1])
    direction=Vector((0,0,1.2))-o.location;o.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
for name,pos,energy,size in (("Key",(3,-2,-4),900,4),("Fill",(-4,2,-1),650,5),("Rim",(-2,4,3),600,4)):
    area_light(name,pos,energy,size)
camera_data=bpy.data.cameras.new("Review Camera");cam=bpy.data.objects.new("Review Camera",camera_data)
stage.objects.link(cam);bpy.context.scene.camera=cam
cam.data.type="ORTHO";cam.data.ortho_scale=3.35
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=12
scene.cycles.use_denoising=False # Ubuntu Free Blender 4.0.2 build omits OIDN
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
shots={"front":(0,2.7,-5.2),"three-quarter":(4.0,3.1,-4.7),"right":(5.4,2.9,.0),"rear":(0,3.0,5.2)}
for key,loc in shots.items():
    cam.location=(loc[0],-loc[2],loc[1]);d=Vector((0,0,1.22))-cam.location;cam.rotation_euler=d.to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str(out/("T05_cooker_"+key+".png"))
    bpy.ops.render.render(write_still=True)
# Save editable source with preview studio cameras AND packed authored images.
# This happens before any join operations used solely for GLB optimization.
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out/"T05_cooker_EDITABLE.blend"))
# Join by material ONLY in the exported GLB, not in editable .blend.
# Avoid exporting the studio; protect low draw-call model in Godot.
bpy.ops.object.select_all(action="DESELECT")
for obj in made:
    if obj.type=="CURVE":
        bpy.context.view_layer.objects.active=obj
        obj.select_set(True)
        bpy.ops.object.convert(target="MESH")
        bpy.context.view_layer.objects.active.select_set(False)
for obj in made:
    if obj.name in bpy.data.objects:pass
src=[obj for obj in art.objects if obj.type=="MESH"]
for o in src:
    bpy.context.view_layer.objects.active=o
    for m in list(o.modifiers):
        o.select_set(True)
        try:bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError:pass
        o.select_set(False)
groups={}
for o in list(src):
    name=o.data.materials[0].name
    groups.setdefault(name,[]).append(o)
for key,objs in groups.items():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objs:obj.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    if len(objs)>1:bpy.ops.object.join()
    bpy.context.view_layer.objects.active.name="Export_"+key
bpy.ops.object.select_all(action="DESELECT")
for obj in art.objects:
    if obj.type=="MESH":obj.select_set(True)
if not list(x for x in bpy.context.selected_objects if x.type=="MESH"):raise RuntimeError("no candidate meshes")
bpy.context.view_layer.objects.active=list(bpy.context.selected_objects)[0]
bpy.ops.export_scene.gltf(filepath=str(out/"T05_cooker_BLENDER_CANDIDATE.glb"),
                          export_format="GLB",use_selection=True,export_apply=True,export_yup=True)
report={"status":"CANDIDATE_NOT_VISUALLY_APPROVED","source_image":"18567.png",
        "reference_is_user_authority":True,
        "object":"cooker_processor","app":"Blender","candidate_only":True,
        "does_not_replace_game_asset":True,
        "footprint_m":[2.45,2.30],"materials":[m for m in groups],
        "preview_cameras":list(shots),
        "output_blend":"T05_cooker_EDITABLE.blend",
        "output_glb":"T05_cooker_BLENDER_CANDIDATE.glb",
        "warning":"Preview images are BLENDER STUDIO images, NOT in-game Godot evidence."}
(out/"benchmark.json").write_text(json.dumps(report,indent=2)+"\n")
print("HAVENLINE_T05_BLENDER_BENCHMARK "+json.dumps(report))
