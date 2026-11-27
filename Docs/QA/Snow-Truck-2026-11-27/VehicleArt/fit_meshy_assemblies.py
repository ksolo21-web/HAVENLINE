"""Fit generated, textured vehicle shell meshes around tested interactive pivots."""
from math import cos, radians, sin
from pathlib import Path
import bpy
import bmesh
import json
import os
import sys
import numpy as np
from mathutils import Matrix, Vector

WORKSPACE = Path(os.environ.get("HAVENLINE_SNOW_TRUCK_ART", "/tmp/hl14/art"))
REFERENCE = Path('/dev/shm/hl14game/assets/snow_truck')

def game_coords(point):
    x, y, z = point
    return np.array((x, z, -y), dtype=np.float64)

def blender_coords(point):
    x, y, z = point
    return x, -z, y

def load(path):
    previous = set(bpy.context.scene.objects)
    result = bpy.ops.import_scene.gltf(filepath=str(path))
    if 'FINISHED' not in result:
        raise RuntimeError("Could not load " + str(path))
    new_objects = [ob for ob in bpy.context.scene.objects if ob not in previous]
    bpy.context.view_layer.update()
    return new_objects

def required(objects, name):
    for ob in objects:
        if ob.name == name:
            return ob
    raise RuntimeError(f"{name} was not found ({[ob.name for ob in objects]})")

def bounds(objects):
    parts = []
    for ob in objects:
        if ob.type != "MESH" or not ob.data.vertices:
            continue
        parts.append(np.array([game_coords(ob.matrix_world @ v.co) for v in ob.data.vertices]))
    points = np.vstack(parts)
    return np.array((points.min(axis=0), points.max(axis=0)))

def donor_fit(objects, pose):
    """Move real imported vertices and preserve all original corner UVs and material slots."""
    meshes = [ob for ob in objects if ob.type == 'MESH']
    donors = np.vstack([np.array([game_coords(ob.matrix_world @ v.co) for v in ob.data.vertices]) for ob in meshes])
    yaw = radians(float(pose["yaw_degrees"]))
    rotation = np.array(((cos(yaw), 0, sin(yaw)), (0, 1, 0), (-sin(yaw), 0, cos(yaw))))
    rotated = donors @ rotation.T
    minimum = np.min(rotated, axis=0)
    maximum = np.max(rotated, axis=0)
    # Optional source landmarks replace bbox-based fit on individual axes.
    for i, axis in enumerate("xyz"):
        if axis in pose.get("source_axis_limits", {}):
            minimum[i], maximum[i] = pose["source_axis_limits"][axis]
    to_min, to_max = np.array(pose["target"], dtype=np.float64)
    scale = (to_max - to_min) / (maximum-minimum)
    shift = to_min - minimum * scale
    for ob in meshes:
        matrix = ob.matrix_world.copy()
        for vertex in ob.data.vertices:
            point = game_coords(matrix @ vertex.co) @ rotation.T
            fitted = point * scale + shift
            for i, axis in enumerate("xyz"):
                calibration = pose.get("piecewise", {}).get(axis)
                if calibration:
                    source, target = zip(*calibration)
                    fitted[i] = np.interp(point[i], source, target)
            vertex.co = blender_coords(fitted)
        ob.parent = None
        ob.matrix_world = Matrix.Identity(4)
        ob.data.update()
    for ob in objects:
        if ob.type != 'MESH':
            bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in meshes:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.object
    mesh.name = "MeshySource"
    bpy.context.view_layer.update()
    print(json.dumps({"source_rotated_bounds":[minimum.tolist(),maximum.tolist()],
                      "fit_scale":scale.tolist(), "fit_translation":shift.tolist()}))
    return mesh

def planes(bm, values):
    """Split along factual clearance planes while retaining the donor's UV interpolation."""
    for axis, value in values:
        coordinate = np.zeros(3)
        coordinate[axis] = value
        normal = np.zeros(3)
        normal[axis] = 1.
        bmesh.ops.bisect_plane(
            bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces), dist=0.00001,
            plane_co=blender_coords(coordinate), plane_no=blender_coords(normal),
            clear_inner=False, clear_outer=False)
    return bm

def cropped(ob, name, test, cut=(), copy=True, parent=None):
    if copy:
        child = ob.copy()
        child.data = ob.data.copy()
        bpy.context.scene.collection.objects.link(child)
    else:
        child = ob
    bm = bmesh.new()
    bm.from_mesh(child.data)
    planes(bm, cut)
    material_names = [m.name if m else "" for m in child.data.materials]
    drop = []
    for face in bm.faces:
        centroid = game_coords(face.calc_center_median())
        area = face.calc_area()
        material = material_names[face.material_index] if face.material_index < len(material_names) else ""
        if area < 0.00000001 or not test(centroid, material):
            drop.append(face)
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.to_mesh(child.data)
    bm.free()
    if not child.data.polygons:
        raise RuntimeError(f"{name}: slicing removed all source polygons")
    child.name = name
    for poly in child.data.polygons:
        if name.startswith('Meshy'):
            poly.use_smooth = True
    child.data.update()
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_world = world
    print(json.dumps({"part":name,"triangles":len(child.data.polygons),"bounds":bounds([child]).tolist()}))
    return child

def assembly_prototype(kind):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    return load(WORKSPACE / f"prototype-{kind}.glb")

def export(kind):
    result = bpy.ops.export_scene.gltf(filepath=str(WORKSPACE / f"fitted-{kind}.glb"),
            export_format='GLB', export_yup=True, export_lights=False, export_normals=True,
            export_texcoords=True, export_apply=True, export_image_format='AUTO')
    if 'FINISHED' not in result:
        raise RuntimeError("Export failed")

def truck(params):
    proto = assembly_prototype('truck')
    root = required(proto,'Truck')
    body = required(proto,'TruckGeometry')
    donor = donor_fit(load(WORKSPACE/'meshy-truck.glb'), params)
    cab_y = float(params.get('cab_floor', .74))
    bed_z = float(params.get('bed_start', .30))
    bed_crop = float(params.get('bed_crop_y',1.58))
    nose_z = float(params.get('nose_limit',-1.48))
    def body_surface(p, _material):
        x, y, z = p
        if y < cab_y or z < nose_z:
            return False
        if z > bed_z and y > bed_crop:
            return False
        if z > bed_z + .015 and z < 1.302 and abs(x) < .748 and y > 1.157:
            return False
        # The donor was generated with its tires joined to its cab. Remove
        # dark upper tire faces inside each full-depth native wheel arch.
        return not (abs(x) >= .697 and y < .952
                    and min((z+.905)**2, (z-.878)**2)+(y-.484)**2 < .497**2)
    cropped(donor,'MeshyTruckCabAndBed',body_surface,
        [(1,cab_y),(2,bed_z),(1,bed_crop),(2,nose_z),(1,1.157),
         (2,1.302),(0,-.748),(0,.748),(0,-.697),(0,.697)],parent=root)
    bpy.data.objects.remove(donor,do_unlink=True)
    # Preserve only the common fitted lower chassis, resonant lights, and
    # blade carrier. Main cab, bonnet, glazing and cargo sides stay Meshy PBR.
    cropped(body,'RetainedTruckChassisAndMount',
        lambda p,m: p[1]<cab_y+.013 or p[2]<nose_z+.012 or (p[2]>bed_z+.035 and p[1]<1.17),
        [(1,cab_y+.013),(2,nose_z+.012),(2,bed_z+.035),(1,1.17)], copy=False,parent=root)
    export('truck')

def garage(params):
    proto = assembly_prototype('garage')
    root = required(proto,'Garage')
    roof = required(proto,'Roof')
    body = required(proto,'GarageGeometry')
    old_roof=required(proto,'RoofGeometry')
    donor = donor_fit(load(WORKSPACE/'meshy-garage.glb'),params)
    clearance=float(params.get('half_clearance',1.445))
    roof_y=float(params.get('roof_cut_y',2.61))
    sill_y=float(params.get('sill_height',.10))
    # Keep the original shell sides and roof, including generated snow and
    # masonry. Discard any inferred front/back curtain in the driving lane.
    cropped(donor,'MeshyGarageWallsAndFootings',
        lambda p,m: p[1]<roof_y and abs(p[0])>=clearance and p[1]>-.12,
        [(1,roof_y),(0,-clearance),(0,clearance),(1,-.12)],parent=root)
    shell_roof = cropped(donor,'MeshyGarageRoofAndGables',
        lambda p,m: p[1]>=roof_y,
        [(1,roof_y)],parent=roof)
    # The selected three-quarter and left elevations show cobalt panels
    # between retained ridge/eave snow. The donor inferred an almost entirely
    # white roof. Repaint the faces of that generated roof itself.
    blue = next((m for m in old_roof.data.materials if m and m.name.startswith("Cobalt enamel")), None)
    if blue is None:
        raise RuntimeError("Cobalt roof finish is unavailable")
    deck = len(shell_roof.data.materials)
    shell_roof.data.materials.append(blue)
    coated = 0
    for face in shell_roof.data.polygons:
        x,y,z = game_coords(face.center)
        ridge_edge = .40 + .11*sin(z*2.6) + .073*sin(z*5.63+.9)
        eave_edge = 1.79 + .12*sin(z*2.12+.9) + .087*sin(z*6.5)
        if (ridge_edge < abs(x) < eave_edge and .10 < z < 5.11
                and y > 3.80-.67*abs(x)-.14 and abs(face.normal.z) > .29):
            face.material_index=deck
            coated += 1
    print(json.dumps({"painted_meshy_roof_faces":coated}))
    bpy.data.objects.remove(donor,do_unlink=True)
    # The real working dock uses the validated single bay floor/marker and
    # self-occluding roll-up slats. Preserve original lamps and guide hardware,
    # a bounded inside face for the cutaway, and the clearance-safe shutter posts.
    cropped(body,'RetainedGarageServiceHardware',
        lambda p,m: (
            (.04<p[1]<sill_y and 'Garage slate' in m)
            or (p[1] <= .17 and abs(p[0])<=1.57 and 'Glacier foundation' not in m and 'snow' not in m.lower())
            or ('Amber lamp' in m or 'Warm driving' in m or 'Shutter' in m)
            or (abs(p[0])<=1.56 and ('Iron' in m or 'Graphite hardware' in m or 'Machined' in m) and 0.12 < p[1] < 2.43)
            or (0.18 < p[1] < 2.57 and abs(p[0])>=1.56 and abs(p[0])<1.64 and 0.17<p[2]<4.98 and 'Timber ' in m)
            or (abs(p[0])<=1.52 and 2.31<p[1]<2.55 and p[2]<.17 and ('navy' in m or 'enamel' in m))
        ),
        [(1,sill_y),(1,.17),(0,-1.64),(0,1.64),(0,-1.56),(0,1.56),(1,2.55)],
        copy=False,parent=root)
    # Remove the old exterior roof, leaving its category for the native cutaway.
    cropped(old_roof,'RetainedGearEmblem',
            lambda p,m: abs(p[0])<.36 and 2.71<p[1]<3.43 and p[2]<-.318
                and any(k in m for k in ('Service sign','Machined','Graphite')),
            [(0,-.36),(0,.36),(1,2.71),(1,3.43),(2,-.318)],copy=False,parent=roof)
    export('garage')

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]
    config = json.loads((WORKSPACE/'mesh-fit.json').read_text())
    for kind in args or ["truck","garage"]:
        (truck if kind=="truck" else garage)(config[kind])
