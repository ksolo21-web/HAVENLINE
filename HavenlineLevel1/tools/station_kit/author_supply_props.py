"""Build the painted shoreline catch, timber cargo chest, and red fuel can."""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PAINT = "Paint"
IRON = "#50545c"
DARK = "#332b29"
COPPER = "#b86324"
WHITE = "#fff5df"


def linear(value):
    value /= 255
    return value / 12.92 if value < .04045 else ((value + .055) / 1.055) ** 2.4


def color(hex_rgb):
    return tuple(linear(int(hex_rgb[i:i + 2], 16)) for i in (1, 3, 5)) + (1.,)


def paint_object(obj, tint, variation=.025):
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials["Havenline Supply Paint"])
    attribute = obj.data.color_attributes.new(name=PAINT, type="FLOAT_COLOR", domain="CORNER")
    rgb = color(tint)
    for loop in obj.data.loops:
        vertex = obj.data.vertices[loop.vertex_index].co
        shade = 1. + variation * math.sin(vertex.x*17.8 + vertex.y*9.1 + vertex.z*41.)
        attribute.data[loop.index].color = tuple(min(1., x * shade) for x in rgb[:3]) + (1.,)
    obj.data.color_attributes.active_color = attribute
    return obj


def beveled(obj, radius, segments=3):
    modifier = obj.modifiers.new("Rounded edges", "BEVEL")
    modifier.width = radius
    modifier.segments = segments
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    modifier = obj.modifiers.new("Broad face normals", "WEIGHTED_NORMAL")
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def board(name, center, size, tint, radius=.023, angle=0.):
    bpy.ops.mesh.primitive_cube_add(size=1., location=center)
    obj = bpy.context.object
    obj.name = name
    for vertex in obj.data.vertices:
        vertex.co.x *= size[0]
        vertex.co.y *= size[1]
        vertex.co.z *= size[2]
    beveled(obj, radius)
    obj.rotation_euler.y = angle
    return paint_object(obj, tint, .05)


def rod(name, begin, end, radius, tint, segments=12):
    a, b = Vector(begin), Vector(end)
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=radius, depth=(b-a).length,
                                      location=(a+b)*.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b-a).to_track_quat("Z", "Y").to_euler()
    beveled(obj, radius*.18, 2)
    return paint_object(obj, tint)


def shell(name, rings, tint, smooth=False):
    width = len(rings[0])
    faces = [tuple(reversed(range(width)))]
    for i in range(len(rings)-1):
        for j in range(width):
            k = (j+1) % width
            faces.append((i*width+j, i*width+k, (i+1)*width+k, (i+1)*width+j))
    last = (len(rings)-1)*width
    faces.append(tuple(last+i for i in range(width)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([point for ring in rings for point in ring], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    return paint_object(obj, tint)


def panel(name, profile, middle, thickness, tint):
    back = [(x,middle-thickness*.5,z) for x,z in profile]
    front = [(x,middle+thickness*.5,z) for x,z in profile]
    return shell(name, [back, front], tint)


def fuel():
    body = board("Pressed steel reservoir", (0,0,.282), (.47,.223,.553), "#be451c", .063)
    body.scale.z = .976
    for face in (-1, 1):
        side = .113 * face
        inset = board("Pressing field", (0,side,.272), (.357,.015,.402), "#a73018", .044)
        for angle in (-.62,.62):
            board("Raised reinforcing rib", (0,side+face*.011,.272), (.027,.017,.405),
                  "#e05922", .009, angle)
        board("Welded bottom plate", (0,side*.95,.058), (.399,.020,.022), "#7d3021", .009)
        board("Grade plate", (.096,side+face*.018,.121), (.091,.011,.058), "#efc899", .010)
        rod("Plate rivet", (.096,side,.122), (.096,side+face*.022,.122), .011, "#3a332d")
    for x in (-.18,.055):
        board("Grip root", (x,0,.555), (.087,.115,.125), "#d04b1e", .022)
    board("Rounded open handgrip", (-.063,0,.624), (.317,.110,.063), "#e85d22", .026)
    rod("Gray threaded neck", (.159,0,.511), (.169,0,.592), .056, IRON)
    rod("Ribbed safety cap", (.169,0,.579), (.176,0,.623), .059, "#333941", 14)
    rod("Cap seal", (.169,0,.608), (.175,0,.624), .052, "#838891")


def crate(style):
    for column in (-1, 1):
        board("Sled runner", (.356*column,0,.034), (.12,.67,.069), DARK, .022)
    board("Timber base", (0,0,.091), (.87,.595,.096), "#7b441f", .028)
    for tier, (z, tint) in enumerate(((.164,"#a8612e"),(.256,"#bb7236"),(.348,"#a76432"))):
        for side in (-1,1):
            board(f"Long stave {tier}", (0,.289*side,z), (.912,.060,.097), tint)
            board(f"Short stave {tier}", (.426*side,0,z), (.061,.547,.097), tint)
    for sx in (-1,1):
        for sy in (-1,1):
            board("Corner upright", (.416*sx,.274*sy,.234), (.099,.097,.300), "#94552d")
            for z in (.112,.358):
                board("Iron corner glove", (.432*sx,.292*sy,z), (.091,.080,.067), IRON, .015)
                rod("Iron pin", (.432*sx,.322*sy,z), (.432*sx,.339*sy,z), .013, "#aab0b4")
    if style != "cargo":
        for side in (-1,1):
            board("Blue reinforced rim", (0,.29*side,.407), (.912,.081,.075), "#285e8f")
            board("Blue reinforced rim", (.427*side,0,.407), (.089,.585,.075), "#285e8f")
        board("Chilled catch bed", (0,0,.196), (.785,.506,.10), "#b9d8e6", .043)
        if style == "stocked":
            for y, x, angle in ((-.151,-.025,.1),(.015,.035,3.03),(.167,-.052,.06)):
                with_pose(fish, (x, y, .236), angle, .92)
    else:
        for strip in range(4):
            board("Canvas-covered lid stave", (0,(strip-1.5)*.151,.427), (.908,.149,.080), "#666245", .02)
        for x in (-.267,.267):
            board("Saddle strap", (x,0,.476), (.082,.631,.023), "#8a602d", .01)
            for side in (-1,1):
                board("Saddle strap", (x,.325*side,.416), (.082,.020,.122), "#996b36", .009)
                board("Buckle", (x,.339*side,.369), (.106,.026,.064), "#d29647", .014)
        for side in (-1,1):
            board("Diagonal brace", (0,.325*side,.235), (.644,.045,.064), "#855029", .013, .28*side)


def fish():
    heights = [(-.287,.012,.018),(-.222,.046,.066),(-.142,.079,.091),(-.036,.080,.095),
               (.073,.067,.073),(.161,.043,.047),(.211,.022,.026)]
    # The flank crosses from a blue back to pearl around the rounded belly.
    paint = [color(t) for t in ("#3a6482", "#7595a3", "#d8d9cd", "#5e7e95")]
    rings = []
    for x, width, height in heights:
        rings.append([(x,width*math.cos(j*math.tau/20),.110+height*math.sin(j*math.tau/20))
                      for j in range(20)])
    body = shell("Silver flank and blue back", rings, "#779ba6", True)
    a = body.data.color_attributes.active_color
    for loop in body.data.loops:
        co = body.data.vertices[loop.vertex_index].co
        mix = min(2.99,max(0.,(co.z-.026)*17.5))
        left = int(mix)
        factor = mix-left
        palette = (paint[2],paint[1],paint[3],paint[0])
        scale = 1.+.055*math.sin(co.x*97.+co.z*78.)
        a.data[loop.index].color = tuple(min(1., (palette[left][i]*(1-factor)+palette[left+1][i]*factor)*scale)
                                         for i in range(3))+(1.,)
    panel("Forked orange tail", [(.185,.087),(.257,.028),(.298,.026),(.285,.104),
                                 (.309,.186),(.271,.19),(.184,.134)],0,.021,"#c97943")
    panel("Dorsal fin", [(-.114,.180),(-.038,.239),(.048,.223),(.117,.175)],0,.013,"#c7794e")
    panel("Ventral fin", [(-.039,.053),(.062,.015),(.104,.064)],0,.017,"#c7824b")
    for side in (-1,1):
        panel("Pectoral fin",[(-.110,.112),(-.018,.066),(.004,.091),(-.045,.121)],
              .066*side,.017,"#d89967")
        rod("Eye rim",(-.218,.039*side,.136),(-.218,.050*side,.137),.018,"#e1dbb2")
        rod("Pupil",(-.223,.050*side,.138),(-.223,.053*side,.138),.011,"#273741")
        rod("Eye catchlight",(-.228,.053*side,.141),(-.228,.055*side,.141),.004,WHITE)


def with_pose(make, center, yaw, scale):
    before = set(bpy.context.scene.objects)
    make()
    from mathutils import Matrix
    adjustment = Matrix.Translation(center) @ Matrix.Rotation(yaw,4,"Z") @ Matrix.Scale(scale,4)
    for obj in set(bpy.context.scene.objects) - before:
        obj.matrix_world = adjustment @ obj.matrix_world


def export(name, build, target):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    build()
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = sorted(bpy.context.scene.objects, key=lambda o: o.name)[0]
    bpy.ops.object.join()
    item = bpy.context.object
    item.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.export_scene.gltf(filepath=str(target/f"{name}.glb"), export_format="GLB",
                             export_texcoords=False, export_materials="EXPORT")


def main():
    material = bpy.data.materials.new("Havenline Supply Paint")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = .71
    vertex = material.node_tree.nodes.new("ShaderNodeVertexColor")
    vertex.layer_name = PAINT
    material.node_tree.links.new(vertex.outputs["Color"],shader.inputs["Base Color"])
    output = Path(sys.argv[sys.argv.index("--")+1])
    for name, make in (("fish",fish),("fish_crate",lambda:crate("stocked")),
                       ("fish_crate_empty",lambda:crate("empty")),("cargo_crate",lambda:crate("cargo")),
                       ("fuel_canister",fuel)):
        export(name, make, output)


if __name__ == "__main__":
    main()
