#!/usr/bin/env python3
"""HAVENLINE T05 R22 reference-first trial, derived from protected R07 author source.

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
def extruded_arch_panel(name, cx, bottom, shoulder, crown, z, width, thickness, key):
    """Forged semi-circular door housing with real raised thickness, -Z front."""
    profile=[(cx-width,bottom),(cx+width,bottom),(cx+width,shoulder)]
    for step in range(1,15):
        angle=math.pi*step/14
        profile.append((cx+width*math.cos(angle),shoulder+crown*math.sin(angle)))
    verts=[(x,y,z-thickness*.5) for x,y in profile]
    verts += [(x,y,z+thickness*.5) for x,y in profile]
    n=len(profile)
    faces=[]
    for i in range(1,n-1):
        faces.append((0,i+1,i))
        faces.append((n,n+i,n+i+1))
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    mesh=bpy.data.meshes.new(name+"_geometry")
    mesh.from_pydata(verts,[],faces)
    mesh.validate(clean_customdata=False)
    mesh.update(calc_edges=True)
    o=bpy.data.objects.new(name,mesh)
    art.objects.link(o);made.append(o)
    mesh.materials.append(palette[key])
    bevel=o.modifiers.new("Sculpted cast edge bevel","BEVEL")
    bevel.width=.018
    bevel.segments=2
    o.modifiers.new("Weighted forged normals","WEIGHTED_NORMAL")
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
# Integrated wide timber-and-steel carriage (not an open four-leg table).
# R22 reference-first: continuous load-bearing wooden lower skirts remove the
# unsupported daylight gaps that make R07 resemble an open cafeteria table.
box("R22 continuous heavy front lower carriage apron",(0,.325,-.615),(2.09,.255,.15),"wood_light",.036)
box("R22 continuous heavy rear lower carriage apron",(0,.325,.615),(2.09,.238,.15),"wood",.030)
box("R22 continuous side lower timber skirt L",(-.967,.337,0),(.135,.23,1.17),"wood",.023)
box("R22 continuous side lower timber skirt R",(.967,.337,0),(.135,.23,1.17),"wood",.023)

# Additional front/base dress belongs to existing material groups and budget.
for front_z in (-.568,.565):
    box("Continuous timber carriage apron",(0,.467,front_z),(2.10,.186,.126),"wood_light",.027)
for x in (-.98,-.50,.49,.98):
    box("Forged blue carriage gusset",(x,.398,-.650),(.129,.266,.102),"blue",.024)
    cylinder("Carriage front steel rivet",(x,.395,-.710),.028,.016,"metal","Y",10)
for x in (-.94,.94):
    box("Corner wood frame overlay",(x,.675,-.553),(.174,.165,.144),"wood",.020)
    box("Corner bent steel cuff",(x,.559,-.611),(.182,.084,.143),"metal",.025)
# Main stove architecture; -Z is its actual operator/front side.
box("Enamel blue forged firebox",(0,1.23,-.11),(.99,.84,.79),"blue",.115)
box("Raised upper fascia",(0,1.67,-.11),(1.13,.19,.94),"blue",.052)
# Actual deep cast-iron arch, not the former stacked flat rectangles.
# R22 reference-first stainless oven bezel: real hollow extruded arch, not
# an opaque extruded rectangle masking the actual moving saw in its recess.
# Exact visual target: owner reference 18567.png, SHA-256 729393f7980d...
def _door_profile(width,bottom,shoulder,rise,steps=24):
    path=[(-width,bottom),(-width,shoulder)]
    for i in range(1,steps):
        ang=math.pi*(1-i/steps)
        path.append((width*math.cos(ang),shoulder+rise*math.sin(ang)))
    path.extend(((width,shoulder),(width,bottom)))
    return path
outer=_door_profile(.478,1.010,1.343,.169)
inner=_door_profile(.354,1.102,1.342,.100)
middle=[(p[0]*.65+q[0]*.35,p[1]*.65+q[1]*.35)
        for p,q in zip(outer,inner)]
n=len(outer)
rings=[(outer,-.693),(middle,-.750),(inner,-.723),
       (outer,-.614),(inner,-.617)]
door_vertices=[(x,y,z) for contour,z in rings for x,y in contour]
door_faces=[]
for i in range(n-1):
    for a,b in ((0,1),(1,2),(3,0),(2,4)):
        door_faces.append((a*n+i,a*n+i+1,b*n+i+1,b*n+i))
bezel_mesh=bpy.data.meshes.new("R22_Deep_stamped_silver_arch_actual_hole")
bezel_mesh.from_pydata(door_vertices,[],door_faces)
bezel_mesh.validate(clean_customdata=False);bezel_mesh.update(calc_edges=True)
bezel=bpy.data.objects.new("Reference 18567 deep curved metal window housing",bezel_mesh)
art.objects.link(bezel);made.append(bezel)
bezel_mesh.materials.append(palette["metal"])
# Dark chamber backing is behind the steel saw geometry, which remains visible.
glass_vertices=[(x,y,-.633) for x,y in inner]
glass_vertices.append((0.,1.277,-.633))
glass_faces=[(n,i,i+1) for i in range(n-1)]
glass_mesh=bpy.data.meshes.new("R22_Charcoal_recessed_window")
glass_mesh.from_pydata(glass_vertices,[],glass_faces)
glass_mesh.update(calc_edges=True)
glass=bpy.data.objects.new("Reference 18567 recessed dark inspection surface",glass_mesh)
art.objects.link(glass);made.append(glass)
glass_mesh.materials.append(palette["dark"])
# Keep already-authored actual toothed saw, metal rivets and orange control.
for x in (-.40,.40):
    for y in (1.055,1.48):
        cylinder("Bezel corner rivet",(x,y,-.751),.034,.023,"metal","Y",12)
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
# R22: reference-matched puffy roof silhouette with real scalloped edge.
# A watertight, continuous mesh, not a set of overlapping sphere primitives.
radial_steps=12
around_steps=64
snow_vertices=[(0.0,2.075,-.045)]
snow_faces=[]
def _snow_lobe(x,z,cx,cz,sx,sz):
    return math.exp(-((x-cx)/sx)**2-((z-cz)/sz)**2)
for ring_index in range(1,radial_steps+1):
    r=ring_index/radial_steps
    for j in range(around_steps):
        a=math.tau*j/around_steps
        flare=1+.033*math.sin(5*a+1.17*r)+.025*math.cos(9*a-1.6*r)
        x=.765*r*math.cos(a)*flare
        z=-.035+.695*r*math.sin(a)*flare
        dome=.175*(1-r**2.2)
        pillows=(.063*_snow_lobe(x,z,-.37,-.16,.31,.26)
                 +.077*_snow_lobe(x,z,.29,-.12,.30,.30)
                 +.063*_snow_lobe(x,z,-.28,.30,.33,.29)
                 +.077*_snow_lobe(x,z,.34,.29,.30,.30)
                 +.046*_snow_lobe(x,z,.02,-.46,.39,.18))
        micro=(.012*math.sin(a*7.2+r*7.6)+.009*math.sin(a*13.1-r*5.1))*r**1.6
        front=max(0.,(-z-.34)/.36)
        y=1.835+dome+pillows+micro-.026*front*r**6
        snow_vertices.append((x,y,z))
for j in range(around_steps):
    nj=(j+1)%around_steps
    snow_faces.append((0,1+nj,1+j))
for ring_index in range(radial_steps-1):
    inner_index=1+ring_index*around_steps
    outer_index=inner_index+around_steps
    for j in range(around_steps):
        nj=(j+1)%around_steps
        snow_faces.append((inner_index+j,inner_index+nj,outer_index+nj,outer_index+j))
lower_start=len(snow_vertices)
outer_start=1+(radial_steps-1)*around_steps
for j in range(around_steps):
    x,y,z=snow_vertices[outer_start+j]
    front=max(0.,(-z-.31)/.41)
    side=max(0.,(abs(x)-.35)/.44)
    scallops=(.075*_snow_lobe(x,z,-.53,-.56,.13,.24)
              +.115*_snow_lobe(x,z,-.13,-.65,.16,.20)
              +.092*_snow_lobe(x,z,.29,-.62,.18,.21)
              +.049*_snow_lobe(x,z,.62,.20,.17,.33))
    fall=.113+.034*front+.022*side+scallops
    snow_vertices.append((x,y-fall,z))
for j in range(around_steps):
    nj=(j+1)%around_steps
    snow_faces.append((outer_start+j,outer_start+nj,lower_start+nj,lower_start+j))
lower_center=len(snow_vertices)
snow_vertices.append((0.,1.73,-.035))
for j in range(around_steps):
    nj=(j+1)%around_steps
    snow_faces.append((lower_center,lower_start+j,lower_start+nj))
snow_mesh=bpy.data.meshes.new("R22_puffy_organic_snow_roof_high_detail_editable")
snow_mesh.from_pydata(snow_vertices,[],snow_faces)
snow_mesh.validate(clean_customdata=False);snow_mesh.update(calc_edges=True)
snow_object=bpy.data.objects.new("Reference 18567 continuous scalloped snow overhang",snow_mesh)
art.objects.link(snow_object)
snow_object.data.materials.append(palette["snow"])
for face in snow_object.data.polygons:face.use_smooth=True
made.append(snow_object)
# The underside and contours are part of one mesh, not overlapping spheres.
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
scene.cycles.samples=24
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
    if obj.type in ("CURVE","META"):
        # META conversion can drop the original material slot in Blender 4.0.
        # Snapshot it before conversion (which invalidates the old object RNA).
        source_material=(obj.data.materials[0] if len(obj.data.materials) else None)
        source_kind=obj.type
        bpy.context.view_layer.objects.active=obj
        obj.select_set(True)
        bpy.ops.object.convert(target="MESH")
        converted=bpy.context.view_layer.objects.active
        assert converted is not None and converted.type=="MESH"
        if not converted.data.materials:
            assert source_material is not None, "Unmaterialed Blender "+source_kind+" source"
            converted.data.materials.append(source_material)
        if source_kind=="META":
            snow_faces=len(converted.data.polygons)
            print("T05_METABALL_SNOW_SURFACE_POLYGONS",snow_faces,flush=True)
            assert snow_faces>=150, "Fused Blender snow has no usable exterior surface"
            # Editable .blend retains the detailed implicit-surface sculpt;
            # only the GLB export receives a mobile-targeted decimator.
            if snow_faces>2450:
                lod=converted.modifiers.new("Mobile snow silhouette decimator","DECIMATE")
                lod.ratio=min(1.,2450./snow_faces)
                print("T05_METABALL_SNOW_EXPORT_RATIO",lod.ratio,flush=True)
        converted.select_set(False)
# Blender replaces the Object RNA when META is converted into a mesh.
# Never dereference stale source-object handles after conversion; instead
# discover actual surviving editable/source meshes from the live collection.
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
    assert o.data.materials, "Candidate mesh has no PBR material after conversion: "+o.name
    name=o.data.materials[0].name
    assert name.startswith("HL_"), "Non-HAVENLINE material leaked into GLB: "+name
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
report={"status":"R22_GEOMETRY_CANDIDATE_NOT_VISUALLY_APPROVED","source_image":"18567.png",
        "reference_is_user_authority":True,
        "reference_sha256":"729393f7980d8bd70906a7e4de04c3c6b21de5dfe4deb3d98ca7005b54d61635",
        "corrected_geometry":["scalloped overhanging snow roof","genuinely hollow inset steel oven arch","integrated continuous supporting timber carriage"],
        "reference_pixel_comparison_in_ci":False,
        "independent_critic_approved":False,
        "source_smoke_vfx_included":False,
        "object":"cooker_processor","app":"Blender","candidate_only":True,
        "does_not_replace_game_asset":True,
        "footprint_m":[2.45,2.30],"materials":[m for m in groups],
        "preview_cameras":list(shots),
        "output_blend":"T05_cooker_EDITABLE.blend",
        "output_glb":"T05_cooker_BLENDER_CANDIDATE.glb",
        "warning":"Preview images are BLENDER STUDIO images, NOT in-game Godot evidence."}
(out/"benchmark.json").write_text(json.dumps(report,indent=2)+"\n")
print("HAVENLINE_T05_BLENDER_BENCHMARK "+json.dumps(report))
