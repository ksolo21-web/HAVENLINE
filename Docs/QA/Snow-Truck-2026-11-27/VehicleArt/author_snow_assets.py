"""Build the two selected Havenline snow-vehicle turnarounds as animated GLB parts."""
from collections import defaultdict
from math import cos, sin, pi
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

OUTPUT = Path('/dev/shm/hl14game/assets/snow_truck')
TAU = 2 * pi

def blender(point):
    x, y, z = point
    return Vector((x, -z, y))

def srgb(u):
    return u / 12.92 if u < 0.04045 else ((u + 0.055) / 1.055) ** 2.4

def material(name, tint, metal=0, rough=.48, emit=0):
    rgba = tuple(srgb(int(tint[i:i+2], 16)/255) for i in (0, 2, 4)) + (1.,)
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = rgba
        bsdf.inputs["Emission Strength"].default_value = emit
    return m

M = {
    "blue": material("Cobalt enamel", "194CB1", .16, .33),
    "blue_light": material("Raised cobalt enamel", "3567CD", .12, .36),
    "blue_dark": material("Recessed navy", "152D6B", .12, .42),
    "bed": material("Navy cargo bed", "303A61", .12, .41),
    "bed_rib": material("Cargo rib edge", "47537A", .12, .40),
    "orange": material("Warm orange enamel", "EF812E", .08, .39),
    "orange_l": material("Orange enamel edge", "FFAB54", .08, .40),
    "orange_d": material("Orange enamel recess", "A84C20", .05, .48),
    "iron": material("Graphite hardware", "444753", .33, .40),
    "metal": material("Machined gunmetal", "777F90", .55, .37),
    "silver": material("Machined steel edging", "C5CFDA", .55, .34),
    "black": material("Deep rubber recess", "171B26", 0, .80),
    "rubber": material("Snow tire", "2B303D", 0, .82),
    "rubber_t": material("Snow tire treads", "414857", 0, .77),
    "snow": material("Packed snow", "EBF3FF", 0, .70),
    "snow_d": material("Cold snow", "CFDEF7", 0, .74),
    "glass": material("Cyan cab glass", "2DB6D8", .20, .24),
    "glass_l": material("Cab glass soft reflection", "56C8E1", .12, .30),
    "glass_d": material("Glass edge", "1A7394", .15, .30),
    "headlight": material("Warm driving lights", "FFE2A5", .04, .30, 1.25),
    "orange_light": material("Amber lamp lens", "FFAB39", .03, .29, .95),
    "tail": material("Rear hazard red", "FF432C", .06, .31, .7),
    "char": material("Impact scorch", "24252D", .04, .83),
    "floor": material("Garage slate floor", "595354", .05, .78),
    "floor_l": material("Garage slate seam", "69605C", .04, .81),
    "floor_d": material("Garage slate edge", "382F32", .06, .74),
    "stone": material("Glacier foundation", "858DA1", .02, .80),
    "stone_l": material("Glacier foundation light", "A1A9BE", 0, .80),
    "stone_d": material("Glacier foundation dark", "626D85", .03, .79),
    "wood1": material("Timber warm vertical grain", "A95936", 0, .77),
    "wood2": material("Timber amber vertical grain", "B8643D", 0, .74),
    "wood3": material("Timber shaded vertical grain", "94472D", 0, .78),
    "post": material("Orange structural timber", "DE783D", 0, .64),
    "post_l": material("Chamfered timber edge", "F5944E", 0, .62),
    "wood_g": material("Timber fine groove", "743522", 0, .79),
    "crate": material("Stained crate", "8E5737", 0, .75),
    "badge": material("Service sign ivory", "F9CA9C", .02, .58),
}
parts = defaultdict(list)
parents = {}

def new_art():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    parts.clear()
    parents.clear()

def pivot(name, center=(0,0,0), parent=None):
    node = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(node)
    node.empty_display_size = .07
    if parent:
        node.parent = parents[parent]
    node.location = blender(center)
    parents[name] = node
    return node

def make_mesh(coords, faces, tint, group, bevel=0, smooth=False):
    mesh = bpy.data.meshes.new("Surface")
    mesh.from_pydata([blender(q) for q in coords], [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new("Part", mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(M[tint])
    if smooth:
        for polygon in mesh.polygons:
            polygon.use_smooth = True
    if bevel:
        mod = ob.modifiers.new("Rounded edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.affect = 'EDGES'
        mod.harden_normals = True
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
        normals = ob.modifiers.new("Weighted panel normals", "WEIGHTED_NORMAL")
        normals.keep_sharp = True
        bpy.ops.object.modifier_apply(modifier=normals.name)
    parts[group].append(ob)
    return ob

def turn(point, angle, axis):
    x, y, z = point
    c, s = cos(angle), sin(angle)
    if axis == "x":
        return x, y*c-z*s, z*c+y*s
    if axis == "z":
        return x*c-y*s, y*c+x*s, z
    return x*c+z*s, y, z*c-x*s

def box(at, size, tint, group, bevel=.025, angle=0, axis="x"):
    sx, sy, sz = [b/2 for b in size]
    pts = [(x*sx,y*sy,z*sz) for x,y,z in (
        (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    if angle:
        pts = [turn(p,angle,axis) for p in pts]
    pts = [tuple(at[k]+p[k] for k in range(3)) for p in pts]
    return make_mesh(pts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)],tint,group,bevel)

def prism(face, offset, tint, group, bevel=.02):
    n = len(face)
    vertices = list(face) + [tuple(p[i]+offset[i] for i in range(3)) for p in face]
    faces = [list(range(n)),list(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return make_mesh(vertices, faces, tint, group, bevel)

def ring(center, profile, axis, tint, group, count=24, caps=True):
    coords = []
    for offset,r in profile:
        for j in range(count):
            t = j*TAU/count
            a,b = r*cos(t), r*sin(t)
            p = (offset,a,b) if axis=="x" else (a,offset,b) if axis=="y" else (a,b,offset)
            coords.append(tuple(p[i]+center[i] for i in range(3)))
    faces = []
    for j in range(len(profile)-1):
        for i in range(count):
            a,b = j*count+i, j*count+(i+1)%count
            faces.append((a,b,b+count,a+count))
    if caps:
        faces += [list(range(count)),list(range((len(profile)-1)*count,len(profile)*count))]
    return make_mesh(coords, faces, tint, group, smooth=True)

def cyl(at, radius, length, axis, tint, group, count=20, lip=.015):
    lip = min(lip,length*.29, radius*.16)
    return ring(at,[(-length/2,radius-lip),(-length/2+lip,radius),
                   (length/2-lip,radius),(length/2,radius-lip)],axis,tint,group,count)

def segment(a, b, w, d, tint, group, bevel=.03):
    start,end=blender(a),blender(b)
    # The member length follows local Blender Z, equivalent to gameplay Y.
    ob = box((0,0,0),(w,(end-start).length,d),tint,group,bevel)
    ob.rotation_euler = (end-start).to_track_quat('Z','Y').to_euler()
    ob.location = (start+end)*.5
    return ob

def snow(x, y, z, rx, rz, depth, group, seed=0, tint="snow"):
    n = 18
    coords = [(x,y+depth,z)]
    for frac,h in [(0.47,.89),(.77,.64),(.96,.31),(1.,.04),(.91,-.15)]:
        for i in range(n):
            t = TAU*i/n
            bump = 1.+.09*sin(5*t+seed)+.07*cos(3*t+.8*seed)
            dip = .10*sin(4*t+.8*seed)
            coords.append((x+rx*cos(t)*frac*bump,y+depth*(h+dip),z+rz*sin(t)*frac*bump))
    faces=[(0,1+i,1+(i+1)%n) for i in range(n)]
    for j in range(4):
        start=1+j*n
        for i in range(n):
            a,b=start+i,start+(i+1)%n
            faces.append((a,b,b+n,a+n))
    faces.append([1+4*n+i for i in range(n)])
    return make_mesh(coords,faces,tint,group,smooth=True)

def fasten(at, axis, group, rad=.027, tint="silver"):
    return cyl(at,rad,.018,axis,tint,group,8,.006)

def wheel(side, z, name):
    x=side*.867
    y=.506
    pivot(name,(x,y,z),"Truck")
    ring((0,0,0),[(-.25,.343),(-.242,.422),(-.185,.475),(-.09,.487),(.09,.487),(.185,.475),(.242,.422),(.25,.343)],"x","rubber",name,32)
    for i in range(18):
        a=TAU*i/18
        for lateral in (-1,1):
            center=(lateral*.119,.482*cos(a),.482*sin(a))
            box(center,(.216,.041,.107),"rubber_t",name,.018,angle=a,axis="x")
            edge=(lateral*.208,.446*cos(a+.07),.446*sin(a+.07))
            box(edge,(.073,.057,.096),"rubber",name,.012,angle=a+.07,axis="x")
    cyl((side*.249,0,0),.285,.049,"x","black",name,32)
    cyl((side*.257,0,0),.241,.047,"x","metal",name,30)
    cyl((side*.265,0,0),.199,.034,"x","silver",name,28)
    cyl((side*.274,0,0),.159,.036,"x","iron",name,26)
    cyl((side*.287,0,0),.098,.048,"x","silver",name,24)
    for i in range(8):
        a=i*TAU/8
        fasten((side*.274,.215*cos(a),.215*sin(a)),"x",name,.023)

def fender(s, z, group):
    profile=[(-.605,.394),(-.557,.597),(-.426,.837),(-.266,.966),
             (.266,.966),(.426,.837),(.557,.597),(.605,.394),
             (.492,.404),(.453,.540),(.341,.738),(.215,.848),
             (-.215,.848),(-.341,.738),(-.453,.540),(-.492,.404)]
    prism([(s*.875,y,z+off) for off,y in profile],(s*.294,0,0),"orange",group,.032)
    for off,y in [(-.535,.588),(.535,.588),(-.288,.944),(.288,.944)]:
        fasten((s*1.164,y,z+off),"x",group,.022)
    snow(s*1.012,.946,z+.037,.146,.306,.085,group,2.4+z)
    snow(s*1.01,.91,z-.265,.148,.117,.093,group,4.2-z)

def blade(x, name):
    pivot(name,(x,.21,-1.78),"Truck")
    coords=[]
    for y in [-.05,.02]:
        for i in range(64):
            a=TAU*i/64
            radius=.562 if i%4 in (1,2) else .476
            coords.append((radius*cos(a),y,radius*sin(a)))
    faces=[list(range(64)),list(range(64,128))]
    faces.extend([(i,(i+1)%64,(i+1)%64+64,i+64) for i in range(64)])
    make_mesh(coords,faces,"silver",name,.009)
    cyl((0,.034,0),.423,.034,"y","metal",name,40)
    cyl((0,.057,0),.317,.015,"y","iron",name,40,.006)
    cyl((0,.068,0),.291,.018,"y","metal",name,36)
    cyl((0,.091,0),.148,.058,"y","silver",name,25)
    cyl((0,.133,0),.107,.065,"y","metal",name,22)
    for i in range(8):
        a=TAU*i/8
        fasten((.381*cos(a),.060,.381*sin(a)),"y",name,.022)

def make_truck():
    new_art()
    pivot("Truck")
    group="Truck"
    box((0,.493,.05),(1.50,.30,2.53),"iron",group,.098)
    box((0,.536,-1.212),(1.80,.27,.23),"iron",group,.093)
    box((0,.555,1.322),(1.76,.28,.24),"iron",group,.069)
    box((0,.543,1.455),(.51,.19,.03),"black",group,.05)
    box((0,.739,.057),(1.47,.26,2.40),"blue_dark",group,.09)
    box((0,1.02,-1.012),(1.528,.48,.53),"blue",group,.14)
    box((0,1.20,-1.03),(1.44,.075,.45),"blue_light",group,.044)
    # The cab front rises against a real windshield rake, with solid blue rear bulkhead.
    cab=[(-.69,.86,-.76),(-.69,1.29,-.79),(-.69,1.90,-.54),(-.69,1.90,.228),(-.69,.90,.256)]
    prism(cab,(1.38,0,0),"blue",group,.09)
    box((0,1.905,-.157),(1.489,.135,.891),"blue_light",group,.073)
    for x in [-.58,-.30,0,.34,.62]:
        snow(x,1.958,-.17,.20,.425,.045,group,3+x*7)
    snow(-.43,1.22,-1.054,.259,.19,.079,group,3.1)
    snow(.43,1.22,-1.055,.252,.21,.073,group,1.3)
    # Recessed glazing and its reflection strips are independent surfaces.
    front=[(-.57,1.28,-.815),(.57,1.28,-.815),(.57,1.80,-.609),(-.57,1.80,-.609)]
    prism(front,(0,0,.052),"blue_dark",group,.041)
    glass=[(-.493,1.323,-.813),(.493,1.323,-.813),(.493,1.756,-.641),(-.493,1.756,-.641)]
    prism(glass,(0,0,-.016),"glass",group,.030)
    prism([(-.38,1.334,-.829),(-.27,1.334,-.829),(-.005,1.749,-.663),(-.146,1.749,-.663)],
          (0,0,-.007),"glass_l",group,.008)
    prism([(.017,1.334,-.831),(.063,1.334,-.831),(.312,1.747,-.664),(.247,1.747,-.664)],
          (0,0,-.006),"glass_l",group,.008)
    box((0,1.575,.263),(.83,.345,.055),"blue_dark",group,.066)
    box((0,1.575,.299),(.67,.227,.04),"glass_d",group,.040)
    for sign in (-1,1):
        outline=[(sign*.70,1.23,-.645),(sign*.70,1.78,-.468),(sign*.70,1.78,.120),(sign*.70,1.23,.120)]
        prism(outline,(sign*.037,0,0),"blue_dark",group,.037)
        pane=[(sign*.740,1.268,-.598),(sign*.740,1.736,-.445),(sign*.740,1.736,.059),(sign*.740,1.268,.059)]
        prism(pane,(sign*.019,0,0),"glass",group,.030)
        prism([(sign*.762,1.283,-.532),(sign*.762,1.283,-.451),(sign*.762,1.724,-.136),(sign*.762,1.724,-.228)],(sign*.004,0,0),"glass_l",group,.008)
        box((sign*.715,1.080,-.02),(.027,.048,.155),"iron",group,.014)
        segment((sign*.72,1.546,-.559),(sign*.929,1.546,-.692),.083,.075,"iron",group)
        box((sign*.964,1.58,-.706),(.155,.335,.191),"iron",group,.059)
        box((sign*.967,1.583,-.598),(.109,.241,.029),"metal",group,.020)
        box((sign*.602,1.836,-.558),(.161,.102,.102),"iron",group,.023)
        box((sign*.604,1.839,-.61),(.098,.063,.026),"orange_light",group,.014)
        box((sign*.61,.999,-1.289),(.375,.30,.079),"orange_d",group,.066)
        box((sign*.61,1.008,-1.332),(.299,.226,.047),"iron",group,.054)
        box((sign*.61,1.011,-1.358),(.237,.162,.023),"orange_light",group,.045)
        box((sign*.613,1.011,-1.372),(.187,.115,.025),"headlight",group,.033)
        box((sign*.56,.75,1.442),(.353,.213,.039),"iron",group,.05)
        box((sign*.56,.75,1.47),(.24,.134,.02),"tail",group,.034)
        box((sign*.744,.6,.12),(.22,.25,.475),"metal",group,.08)
        for step_height in [.39,.53]:
            box((sign*.842,step_height,.09),(.246,.055,.325),"metal",group,.014)
        for z in (-.90,.878):
            fender(sign,z,group)
        box((sign*.795,1.244,.855),(.135,.514,1.052),"bed",group,.04)
        box((sign*.792,1.527,.848),(.146,.112,1.141),"bed_rib",group,.035)
        for z in (.49,.68,1.02,1.22):
            box((sign*.878,1.258,z),(.059,.407,.088),"bed_rib",group,.012)
        for z in [.345,1.339]:
            for y in [1.084,1.451]:
                box((sign*.884,y,z),(.046,.117,.157),"orange",group,.022)
                fasten((sign*.916,y,z+.022),"x",group,.021)
        snow(sign*.8,1.574,.97,.077,.34,.036,group,1+sign)
        snow(sign*.81,1.574,.45,.087,.152,.038,group,-sign)
    box((0,1.102,.863),(1.564,.115,1.146),"bed",group,.034)
    box((0,1.27,1.374),(1.595,.494,.094),"bed",group,.045)
    box((0,1.532,1.377),(1.647,.094,.108),"bed_rib",group,.035)
    box((0,1.26,.32),(1.5,.43,.08),"blue_dark",group,.028)
    for x in [-.57,-.29,0,.29,.57]:
        box((x,1.285,1.434),(.091,.338,.039),"bed_rib",group,.010)
    snow(0,1.568,1.409,.646,.074,.034,group,2.9)
    # The bonnet grille is inset with four bars inside a rounded steel housing.
    box((0,.973,-1.294),(.668,.525,.105),"iron",group,.081)
    box((0,.980,-1.347),(.607,.468,.069),"silver",group,.075)
    box((0,.983,-1.383),(.429,.334,.023),"black",group,.042)
    for y in (.856,.947,1.034,1.115):
        box((0,y,-1.399),(.445,.045,.036),"metal",group,.014)
    for x in [-.526,.526]:
        segment((x,.731,-1.19),(x,.462,-1.735),.209,.176,"iron",group,.039)
        segment((x,.759,-1.25),(x,.499,-1.735),.117,.135,"metal",group,.027)
        cyl((x,.731,-1.23),.133,.258,"x","orange",group,20)
        cyl((x,.463,-1.728),.125,.287,"x","orange",group,20)
        fasten((x+(.155 if x>0 else -.155),.463,-1.725),"x",group,.063,"metal")
    box((0,.36,-1.61),(1.894,.143,.280),"orange",group,.053)
    for s in (-1,1):
        box((s*.966,.286,-1.770),(.379,.181,.310),"orange",group,.051,angle=s*.39,axis="y")
        box((s*1.059,.265,-1.902),(.207,.235,.196),"orange",group,.048,angle=s*.43,axis="y")
        for x,z in [(s*.874,-1.616),(s*1.032,-1.811),(s*.23,-1.502)]:
            fasten((x,.442 if abs(x)<.94 else .391,z),"y",group,.023)
        snow(s*.997,.386,-1.784,.141,.112,.034,group,4+s)
    box((0,.395,-1.609),(.320,.184,.360),"orange_l",group,.057)
    fasten((-.107,.492,-1.727),"y",group,.024)
    fasten((.107,.492,-1.727),"y",group,.024)
    # Author the beacon low enough for the full truck to clear the portal lintel.
    cyl((0,1.982,-.143),.136,.068,"y","iron",group,24)
    cyl((0,2.034,-.143),.110,.093,"y","orange_light",group,24,.021)
    cyl((0,2.071,-.143),.071,.018,"y","headlight",group,20,.007)
    for name,x,z in [
        ("WheelFrontLeft",-1,-.90),("WheelFrontRight",1,-.90),
        ("WheelRearLeft",-1,.878),("WheelRearRight",1,.878)]:
        wheel(x,z,name)
    blade(-.55,"BladeLeft")
    blade(.55,"BladeRight")
    pivot("Damage",parent="Truck")
    for i in range(3):
        box((.715+i*.044,1.225,-.931-i*.036),(.021,.014,.116),"char","Damage",.004,angle=-.3,axis="y")
        box((-.611-i*.031,.361,-1.744+i*.048),(.029,.015,.081),"char","Damage",.004,angle=.46,axis="y")
    export_asset("snow_truck.glb")

def wood_post(x,z,group):
    for i in range(2):
        box((x,.14+.245*i,z),(.435-i*.063,.274,.452-i*.045),["stone_d","stone_l"][i],group,.055,angle=.051*(-1)**i,axis="y")
    box((x,1.531,z),(.295,2.482,.293),"post",group,.040)
    for y in (.559,2.353):
        box((x,y,z),(.327,.182,.33),"iron",group,.025)
        for side in (-1,1):
            for xoff in (-.087,.087):
                fasten((x+xoff,y,z+side*.172),"z",group,.026)
    snow(x,.103,z+.125,.228,.247,.089,group,x+z)

def lamp(x,y,z,axis,group):
    box((x,y,z),(.177,.183,.128),"iron",group,.027)
    box((x,y,z-.067 if axis=="z" else z),(.126,.123,.095),"orange_light",group,.023)
    box((x,y,z-.113 if axis=="z" else z),(.089,.091,.047),"headlight",group,.017)
    if axis=="z":
        for off in (-.064,.064):
            box((x+off,y,z-.130),(.018,.140,.014),"iron",group,.004)

def make_garage():
    new_art()
    group="Garage"
    pivot(group)
    pivot("Roof",parent=group)
    pivot("RollupDoor",parent=group)
    # The first plane is the outer closed door. The entire camp-side rear remains open.
    box((0,.004,2.57),(3.253,.082,5.149),"floor_d",group,.035)
    for j in range(6):
        for i in range(3):
            box(((i-1)*.959,.037,.429+j*.842),(.951,.022,.828),
                ["floor","floor_l"][(j+i)%2],group,.007)
    # Gold outline marks the exact rectangular parking area and remains readable under the roof.
    for x in (-1.398,1.398):
        box((x,.055,2.620),(.048,.013,4.755),"orange_light",group,.004)
    for z in (.244,4.995):
        box((0,.055,z),(2.828,.013,.048),"orange_light",group,.004)
    for x in [-1.485,1.485]:
        box((x,.075,2.57),(.088,.11,5.05),"iron",group,.010)
        for k in range(18):
            box((x,.132,.148+k*.286),(.083,.010,.076),"metal",group,.004)
    for side in (-1,1):
        x=side*1.605
        wood_post(side*1.681,-.019,group)
        wood_post(side*1.681,5.124,group)
        for row in range(2):
            for i in range(14):
                z=.199+i*.359+(.104 if row else 0)
                width=.207+.038*cos(i*1.55+row)
                at=(side*1.603,.104+row*.19,z)
                box(at,(width,.206,.349),["stone","stone_l","stone_d"][(i+row)%3],group,.039,angle=.052*sin(i*2.3),axis="y")
        for i in range(18):
            z=.242+i*.278
            box((side*1.645,1.463,z),(.089,2.136,.272),["wood1","wood2","wood1","wood3"][i%4],group,.012)
            for j in range(2):
                length=(.45+.119*sin(i*215+j*319))
                b=.607+j*.929+.23*sin(i*.81+j)
                box((side*1.696,b,z-.075+.08*j),(.003,length,.008),"wood_g",group,.0015,angle=.07*sin(i+j),axis="x")
        for y in (.473,2.524):
            box((side*1.626,y,2.571),(.221,.164,5.274),"post",group,.029)
            box((side*1.731,y+.045,2.57),(.013,.045,5.233),"post_l",group,.007)
        for z in (.32,1.69,3.71,4.87):
            box((side*1.611,2.269,z),(.222,.104,.145),"iron",group,.020)
            box((side*1.493,2.283,z),(.028,.062,.104),"headlight",group,.009)
        for z in (.569,1.0,3.69,4.31):
            snow(side*1.714,.112,z,.167,.307,.093,group,z+side)
        snow(side*1.724,.407,2.2,.136,.318,.042,group,side)
        snow(side*1.722,.423,3.17,.128,.239,.038,group,side+4)
        lamp(side*1.599,1.908,-.185,"z",group)
    # Left four-pane amber window and the right low vent distinguish the elevations.
    for side in (-1,1):
        z=2.97
        cy=1.39 if side<0 else 1.10
        box((side*1.705,cy,z),(.136,.630,.818),"post",group,.051)
        box((side*1.781,cy,z),(.036,.464,.630),"wood_g" if side<0 else "iron",group,.035)
        if side<0:
            for y in (cy-.111,cy+.111):
                for u in (z-.139,z+.139):
                    box((side*1.804,y,u),(.031,.192,.246),"headlight",group,.022)
        else:
            for y in (cy-.161,cy-.071,cy+.019,cy+.109):
                box((side*1.811,y,z),(.066,.048,.566),"metal",group,.010,angle=.20,axis="z")
        for y in (cy-.246,cy+.246):
            for u in (z-.347,z+.347):
                fasten((side*1.789,y,u),"x",group,.025)
    for z in (.014,5.14):
        box((0,2.557,z),(3.392,.244,.253),"post",group,.029)
        box((0,2.645,z-.142),(3.238,.041,.031),"post_l",group,.010)
        for side in (-1,1):
            segment((side*1.485,2.198,z),(side*1.164,2.496,z),.212,.24,"post",group,.029)
    for z in (1.01,2.17,3.44,4.48):
        box((0,2.604,z),(3.158,.167,.151),"wood1","Roof",.026)
        if z in (1.01,4.48):
            box((0,2.488,z),(.283,.074,.192),"orange_light","Roof",.029)
    # Closed front decking sits between posts. Individual slats feed into the roller.
    for i in range(12):
        name=f"Slat{i+1:02d}"
        h=.143+i*.189
        pivot(name,(0,h,.031),"RollupDoor")
        box((0,0,0),(2.866,.183,.119),"blue" if i%4 else "blue_light",name,.018)
        box((0,.002,-.067),(2.819,.035,.014),"blue_light",name,.005)
        if i==0:
            box((0,-.071,-.076),(2.853,.027,.032),"iron",name,.005)
    cyl((0,2.42,.043),.109,2.872,"x","blue_dark",group,32,.018)
    cyl((0,2.439,.019),.072,2.932,"x","blue",group,30,.017)
    for s in (-1,1):
        box((s*1.493,1.268,.034),(.085,2.327,.16),"orange_d",group,.029)
        box((s*1.487,1.270,-.050),(.043,2.308,.043),"metal",group,.009)
    # Visible workshop shelves sit outside the clearance envelope.
    for s,z in [(-1,.999),(1,4.207)]:
        box((s*1.514,.281,z),(.176,.465,.817),"crate",group,.028)
        for y in (.276,.478):
            box((s*1.494,y,z),(.169,.071,.837),"post",group,.016)
    # Timber gable with a relief gear emblem, cobalt roof and deep continuous snow caps.
    for side in (-1,1):
        for j in range(16):
            z = -.236+j*.365
            face=[(0,3.796,z),(side*1.985,2.697,z),(side*1.985,2.592,z),(0,3.687,z)]
            prism(face,(0,0,.355),["blue","blue_light","blue"][j%3],"Roof",.017)
        segment((side*2.048,2.672,-.301),(side*2.048,2.672,5.429),.155,.177,"blue_dark","Roof",.024)
        for end in (-.292,5.39):
            segment((side*2.025,2.605,end),(0,3.752,end),.156,.21,"post_l","Roof",.037)
            segment((side*2.107,2.708,end-.028),(0,3.869,end-.028),.144,.214,"blue","Roof",.029)
        for j in range(12):
            z = -.208+j*.509
            snow(side*.128,3.804,z,.296,.337,.112+.021*cos(j*3*side),"Roof",j*.44+side)
        for j in range(5):
            x = (j+1)*.352
            y = 3.807-x*.553
            snow(side*x,y,-.270,.228,.205,.115+.017*cos(j*2),"Roof",j*4+side)
            snow(side*x,y,5.413,.222,.189,.106+.04*sin(j),"Roof",j*3+side)
        for z,x in [(1.1,1.66),(2.42,1.5),(4.396,1.77)]:
            snow(side*x,3.806-x*.551,z,.275,.465,.114,"Roof",z+side)
    prism([(-1.819,2.676,-.251),(1.819,2.676,-.251),(0,3.708,-.251)],(0,0,.112),"wood2","Roof",.026)
    for i in range(-8,9):
        x=i*.191
        height=1.013-abs(x)*.56
        if height>.08:
            box((x,2.671+height*.5,-.272),(.018,height,.013),"wood_g","Roof",.003)
    # Keep the rear open; the three timber trusses are visible from the camp.
    for z in (-.325,5.437):
        box((0,3.690,z),(.259,.244,.076),"iron","Roof",.035)
        fasten((0,3.704,z+(-.051 if z<0 else .051)),"z","Roof",.056)
    for side in (-1,1):
        segment((side*.21,2.694,5.144),(side*.442,3.303,5.144),.158,.194,"post","Roof",.020)
    box((0,3.141,5.132),(.156,.883,.179),"post","Roof",.028)
    face=[]
    for i in range(40):
        a=TAU*i/40
        rad=.333 if i%4 in (1,2) else .282
        face.append((rad*cos(a),3.055+rad*sin(a),-.371))
    prism(face,(0,0,.065),"silver","Roof",.011)
    cyl((0,3.055,-.378),.248,.055,"z","iron","Roof",32)
    # Simplified stamped truck silhouette at the center of the owner's gear sign.
    box((-.07,3.02,-.416),(.285,.119,.025),"badge","Roof",.016)
    box((.098,3.051,-.416),(.142,.185,.025),"badge","Roof",.021)
    box((.101,3.082,-.433),(.093,.073,.011),"iron","Roof",.016)
    for x in (-.129,.104):
        cyl((x,2.966,-.431),.058,.04,"z","badge","Roof",12,.007)
        cyl((x,2.966,-.458),.027,.014,"z","iron","Roof",12,.003)
    export_asset("snow_garage.glb")

def export_asset(filename):
    for name, objects in parts.items():
        if not objects:
            continue
        # Merge per animated pivot to bound scene nodes and draw calls. Mesh surface
        # materials remain distinct so imported PBR properties match the authoring file.
        bpy.ops.object.select_all(action="DESELECT")
        for ob in objects:
            ob.select_set(True)
        first=objects[0]
        bpy.context.view_layer.objects.active=first
        if len(objects)>1:
            bpy.ops.object.join()
        mesh=bpy.context.object
        mesh.name=f"{name}Geometry"
        mesh.parent=parents[name]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.export_scene.gltf(filepath=str((OUTPUT/".staging")/filename),export_format="GLB",
                              export_yup=True,export_lights=False,export_normals=True,
                              export_texcoords=True,export_apply=True)

if __name__=="__main__":
    (OUTPUT/".staging").mkdir(exist_ok=True)
    make_truck()
    make_garage()
    for name in ("snow_truck.glb", "snow_garage.glb"):
        ((OUTPUT/".staging")/name).replace(OUTPUT/name)
    (OUTPUT/".staging").rmdir()
