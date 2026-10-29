#!/usr/bin/env python3
"""T05 handmade source-traced saw module. INCOMPLETE COOKER / VISUAL CRITIC PENDING.
Run: blender -b -t 2 --python THIS.py -- ORIGINALS_DIR TRACE.json OUTPUT_DIR
All primary arch vertices come from the owner's original JPG trace; NO R28-R38
mesh or AI-derived mesh is imported. Every mechanical feature is a separate
editable 3D object. Export/test this part before building another component.
"""
import bpy,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
assert len(a)==3
src,trace_path,out=Path(a[0]),Path(a[1]),Path(a[2])
out.mkdir(parents=True,exist_ok=True)
spec=json.loads(trace_path.read_text())
sources={'32451.jpg':'70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4',
'32450.jpg':'5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719',
'32441.png':'0ff99199e1eb4bedeffe4d9953f5253a97e49366a2118d5976132c9137d93510'}
for fn,digest in sources.items():assert hashlib.sha256((src/fn).read_bytes()).hexdigest()==digest,fn
assert spec['sha256']==sources['32451.jpg']
outer,inner=spec['outer_steel_arch_pixels'],spec['inner_opening_pixels']
assert len(outer)==len(inner)==15
# Preserve the fifteen literal owner-traced anchors, then smoothly interpolate
# their curved forged perimeter for real geometry (not a 15-facet arch).
def soften_closed_source_trace(points,steps=4):
    result=[]
    for i in range(len(points)):
        p0=points[(i-1)%len(points)]
        p1=points[i];p2=points[(i+1)%len(points)];p3=points[(i+2)%len(points)]
        for j in range(steps):
            t=j/steps
            xy=[]
            for d in (0,1):
                # Keep sharp joined bottom/side corners literal: cubic overshoot
                # would self-intersect the actual traced window near its sill.
                if i in (0,13,14):
                    v=p1[d]*(1-t)+p2[d]*t
                else:
                    v=.5*((2*p1[d])+(-p0[d]+p2[d])*t+
                      (2*p0[d]-5*p1[d]+4*p2[d]-p3[d])*t*t+
                      (-p0[d]+3*p1[d]-3*p2[d]+p3[d])*t*t*t)
                xy.append(v)
            result.append(tuple(xy))
    return result
outer=soften_closed_source_trace(outer)
inner=soften_closed_source_trace(inner)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE' if bpy.app.version<(4,2,0) else 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x=960;scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('T05 winter studio')
scene.world.color=(.015,.017,.026)
reference=bpy.data.collections.new('OWNER_3_PACKED_IMAGES_AND_REFERENCE_CAMERAS')
scene.collection.children.link(reference)
parts=bpy.data.collections.new('SAW_PHYSICAL_SEPARATE_PARTS_WIP')
scene.collection.children.link(parts)
source_images={}
for fn in sources:
    path=src/fn
    if fn=='32441.png' and path.read_bytes()[:2]==b'\xff\xd8':
        path=out/'REAR_OWNER_EXACT_BYTES_JPEG_ALIAS.jpg'
        path.write_bytes((src/fn).read_bytes())
    im=bpy.data.images.load(str(path),check_existing=False)
    im.name='OWNER_SOURCE_'+fn;im.pack();source_images[fn]=im
o_x,o_z=spec['origin_px'];scale=float(spec['scale_px_per_model_unit'])
def pos(point,y=0.0):return ((point[0]-o_x)/scale,y,(o_z-point[1])/scale)
def material(name,rgb,metal=0.,rough=.65):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*rgb,1)
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    return m
metal=material('FORGED_METAL_PHYSICAL',(.38,.45,.55),.65,.43)
bright=material('BRUSHED_STEEL_PHYSICAL',(.59,.66,.74),.67,.28)
dark=material('DEEP_DARK_CHAMBER',(.017,.026,.050),.05,.90)
blade_mat=material('SEPARATE_JAGGED_STEEL_BLADE',(.33,.39,.47),.70,.42)
orange=material('ORANGE_HARD_PAINTED_STEEL',(.82,.26,.035),.2,.47)
rust=material('ORANGE_DARK_SEAMS',(.40,.13,.04),.25,.55)
photo=bpy.data.materials.new('ACTUAL_OWNER_32451_BORDER_PIXELS')
photo.use_nodes=True;nd=photo.node_tree.nodes;nd.clear()
tex=nd.new('ShaderNodeTexImage');tex.image=source_images['32451.jpg']
pbr=nd.new('ShaderNodeBsdfPrincipled')
pbr.inputs['Metallic'].default_value=.03;pbr.inputs['Roughness'].default_value=.93
output=nd.new('ShaderNodeOutputMaterial')
photo.node_tree.links.new(tex.outputs['Color'],pbr.inputs['Base Color'])
photo.node_tree.links.new(pbr.outputs['BSDF'],output.inputs['Surface'])
def mesh(name,vertices,faces,mat,uv=False):
    data=bpy.data.meshes.new(name+'_mesh');data.from_pydata(vertices,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);parts.objects.link(obj);obj.data.materials.append(mat)
    if uv:
        uvmap=data.uv_layers.new(name='OWNER_FULL_REFERENCE_PIXELS')
        for face in data.polygons:
            for li in face.loop_indices:
                v=data.vertices[data.loops[li].vertex_index].co
                uvmap.data[li].uv=((v.x*scale+o_x)/1536.,(1536.-o_z+v.z*scale)/1536.)
    obj['T05_ROLE']=name;obj['T05_REVIEW']='UNAPPROVED'
    return obj
def extrude(name,poly,front,back,mat):
    n=len(poly);vertices=[pos(pt,y) for y in (front,back) for pt in poly]
    faces=[]
    for i in range(1,n-1):faces.extend([[0,i,i+1],[n,n+i+1,n+i]])
    for i in range(n):faces.append([i,(i+1)%n,n+(i+1)%n,n+i])
    return mesh(name,vertices,faces,mat)
def thin_line(name,pts,depth,rad,mat):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D'
    spl=cu.splines.new('POLY');spl.points.add(len(pts)-1)
    for item,pt in zip(spl.points,pts):item.co=(*pos(pt,depth),1.)
    spl.use_cyclic_u=True;cu.bevel_depth=rad;cu.bevel_resolution=3
    ob=bpy.data.objects.new(name,cu);parts.objects.link(ob);cu.materials.append(mat)
def cylinder(name,loc,radius,depth,mat,rotation=(math.pi/2,0,0),segments=56):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=radius,depth=depth,
                                        location=loc,rotation=rotation)
    obj=bpy.context.object
    for collection in list(obj.users_collection):collection.objects.unlink(obj)
    parts.objects.link(obj);obj.name=name;obj.data.materials.append(mat)
    for polygon in obj.data.polygons:polygon.use_smooth=True
    mod=obj.modifiers.new('Softened real machined edge','BEVEL');mod.width=.013;mod.segments=3
    return obj
# Real front ring, 3D sidewall and recessed inner wall; NEVER a 2D billboard.
n=len(outer)
verts=[pos(pt,y) for y,shape in [(-.29,outer),(-.29,inner),(.04,outer),(.04,inner)]
       for pt in shape]
front=[];walls=[]
for i in range(n):
    j=(i+1)%n
    front.append([i,j,n+j,n+i])
    walls.extend([[i,j,2*n+j,2*n+i],[n+i,n+j,3*n+j,3*n+i],
                  [2*n+i,2*n+j,3*n+j,3*n+i]])
front_lip=mesh('01_SOURCE_TRACED_FRONT_FORGED_ARCH',verts,front,photo,True)
front_lip.data.materials.append(bright)
for i in range(14*4,15*4):front_lip.data.polygons[i].material_index=1  # prevent duplicate baked orange at steel sill
mesh('02_EXTRUDED_FRAME_SIDEWALLS',verts,walls,metal)
thin_line('03_INNER_RUBBER_STEEL_GASKET',inner,-.31,.017,bright)
thin_line('04_OUTER_FORGED_EDGE',outer,-.32,.011,metal)
extrude('05_DEEP_INTERIOR_SAW_CHAMBER_BACK',inner,.30,.34,dark)
thin_line('06_RECESSED_REAR_WINDOW_TRIM',inner,.17,.014,metal)
# Actual 19-tooth radial saw, separately movable/correctable from its axle.
sx,sy=spec['saw']['wheel_center_px'];teeth=int(spec['saw']['teeth'])
blade=[]
for i in range(teeth):
    for phase,rad in [(0,.79),(.18,1.05),(.51,1.11),(.80,.83)]:
        theta=2*math.pi*(i+phase)/teeth
        blade.append((sx+spec['saw']['outer_radius_px']*rad*math.cos(theta),
                      sy+spec['saw']['outer_radius_px']*rad*math.sin(theta)))
# The wheel teeth must stop BEHIND the frame sill. Crop true 2D star
# geometry before extrusion; never let a loose saw protrude below the oven.
def clip_halfplane(poly,axis,limit,keep_less):
    result=[]
    for idx,finish in enumerate(poly):
        start=poly[idx-1]
        a=(start[axis]<=limit) if keep_less else (start[axis]>=limit)
        b=(finish[axis]<=limit) if keep_less else (finish[axis]>=limit)
        if a!=b:
            t=(limit-start[axis])/(finish[axis]-start[axis])
            result.append((start[0]+t*(finish[0]-start[0]),start[1]+t*(finish[1]-start[1])))
        if b:result.append(finish)
    return result
blade=clip_halfplane(blade,1,750,True)
blade=clip_halfplane(blade,0,1073,False)
blade=clip_halfplane(blade,0,1207,True)
assert len(blade)>=12,'Clipped steel teeth must remain present'
extrude('07_SEPARATE_REAL_SAW_TOOTH_BLADE',blade,.10,.16,blade_mat)
cylinder('08_INNER_SAW_WHEEL',pos((sx,sy),.085),.32,.09,metal)
cylinder('09_OUTER_MACHINED_HUB',pos((sx,sy),-.04),.21,.14,bright)
cylinder('10_PROTRUDING_AXLE',pos((sx,sy),-.16),.102,.18,metal)
cylinder('11_COPPER_HUB_PIN',pos((sx+4,sy),-.25),.058,.07,rust)
# Accurate orange visible roller is a shaft along X with independent orange
# boss faces and separate silver/copper fasteners, not a painted strip.
left,right=spec['handle']['left_end_px'],spec['handle']['right_end_px']
px,rx=pos(left)[0],pos(right)[0]
z=(pos(left)[2]+pos(right)[2])/2
cylinder('12_ORANGE_SOLID_CROSSBAR',((px+rx)/2,-.61,z),.105,abs(rx-px)+.035,
         orange,(0,math.pi/2,0))
for label,pt in [('LEFT',left),('RIGHT',right)]:
    x,_,height=pos(pt)
    cylinder('13_ORANGE_'+label+'_BOSS',(x,-.68,height),.221,.15,orange)
    cylinder('14_DARK_'+label+'_GASKET',(x,-.78,height),.160,.016,rust)
    cylinder('15_STEEL_'+label+'_CAP',(x,-.81,height),.115,.045,bright)
cylinder('16_REAR_INTERNAL_BEARING',pos((sx,sy),.46),.265,.16,metal)
# All THREE exact original images embedded into the Blender scene.
for key,loc,fn in [('FRONT_TRACE',(0,-5,.45),'32451.jpg'),
                   ('RIGHT_HYPOTHESIS',(5,-.5,.45),'32450.jpg'),
                   ('REAR_HYPOTHESIS',(0,5,.45),'32441.png'),
                   ('ORBIT_CRITIQUE',(-4,-4,1),'32451.jpg')]:
    ca=bpy.data.cameras.new(key);ob=bpy.data.objects.new('VIEW_'+key,ca)
    reference.objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector((0,0,.75))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    ca.type='ORTHO';ca.ortho_scale=3.1 if key=='FRONT_TRACE' else 3.5
    ca.show_background_images=True
    bg=ca.background_images.new();bg.image=source_images[fn];bg.alpha=.35
    ob['SOURCE_CAMERA']='front hand trace; other reference camera poses NOT calibrated'
def light(name,loc,power):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=4.
    ob=bpy.data.objects.new(name,d);reference.objects.link(ob);ob.location=loc
    ob.rotation_euler=(-Vector(loc)).to_track_quat('-Z','Y').to_euler()
light('White winter studio key',(-3,-4,5),610)
light('Steel rim fill',(2,2.5,4),750)
scene.camera=bpy.data.objects['VIEW_FRONT_TRACE']
scene['T05_ARTIST_MASTER_STATUS']='SAW_SUBASSEMBLY_ONLY__NOT_WHOLE_COOKER'
scene['T05_REQUIRES_OWNER_AND_INDEPENDENT_CRITIC_APPROVAL']=True
scene['T05_REJECTED_MESHES_IMPORTED']=False
bpy.ops.wm.save_as_mainfile(filepath=str(out/'T05_SAW_ARTISAN_MASTER.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in parts.objects:
    if obj.type in {'MESH','CURVE'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'T05_SAW_ARTISAN_MODULE.glb'),
        export_format='GLB',use_selection=True,export_yup=True,export_normals=True,
        export_texcoords=True,export_materials='EXPORT',export_extras=True)
for view in ['FRONT_TRACE','RIGHT_HYPOTHESIS','REAR_HYPOTHESIS','ORBIT_CRITIQUE']:
    scene.camera=bpy.data.objects['VIEW_'+view]
    scene.render.filepath=str(out/('T05_SAW_'+view+'.png'))
    bpy.ops.render.render(write_still=True)
result={'status':'PHYSICAL_SOURCE_TRACED_SAW_SUBASSEMBLY_EXPORTED_NOT_COOKER_APPROVED',
    'original_sources_verified':3,'arch_outer_source_points':15,
    'arch_inner_source_points':15,'physical_saw_teeth':teeth,
    'separate_mesh_objects':sum(x.type=='MESH' for x in parts.objects),
    'actual_owner_front_pixels_on_steel':True,'borrowed_R38_geometry':False,
    'four_Blender_views_attempted':True,'whole_cooker_complete':False,
    'visual_critic_pass':False,'owner_approved':False,
    'shipping_asset_modified':False,'phone_fps_verified':False}
(out/'STATUS.json').write_text(json.dumps(result,indent=2)+'\n')
print('T05_SOURCE_TRACED_PHYSICAL_SAW_EXPORT_PASS',json.dumps(result),flush=True)
