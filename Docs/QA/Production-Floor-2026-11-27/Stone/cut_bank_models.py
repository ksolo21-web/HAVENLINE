"""Bake four fitted fracture pieces from each shipping quarry mesh using Blender."""
import bpy
import bmesh
import sys
from pathlib import Path
from mathutils import Vector
root = Path(sys.argv[sys.argv.index("--")+1])
sources = {"stone":"reference_forest/mine-stone.glb","metal":"field/metal.glb","coal":"field/coal.glb","slate":"field/slate.glb"}
for kind, donor in sources.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(root / "assets" / donor), merge_vertices=True)
    src=next(obj for obj in bpy.context.scene.objects if obj.type=="MESH")
    source=src.data.copy()
    source.transform(src.matrix_world)
    surfaces=len(source.materials)
    surface_indices=[poly.material_index for poly in source.polygons]
    source.materials.clear()
    for i in range(surfaces):
        source.materials.append(bpy.data.materials.new("bank_surface_%d" % i))
    source.materials.append(bpy.data.materials.new("fracture_interior"))
    for poly,slot in zip(source.polygons,surface_indices): poly.material_index=slot
    verts=[v.co for v in source.vertices]
    lo=Vector([min(v[i] for v in verts) for i in range(3)])
    hi=Vector([max(v[i] for v in verts) for i in range(3)])
    center=(lo+hi)*.5
    width=max(hi-lo)
    # Export maps Blender (x,-z,y) to the Godot bank's (x,y,z).
    planes=[(Vector((1.,-.19,.24)),.065),(Vector((-.34,-1.,-.14)),-.035)]
    for idx in range(4):
        bm=bmesh.new()
        bm.from_mesh(source)
        bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-5)
        for j,(n,k) in enumerate(planes):
            normal=n.normalized()
            cut=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],dist=1.e-6,plane_co=center+n*k*width/n.length_squared,plane_no=normal,clear_outer=not(idx>>j & 1),clear_inner=bool(idx>>j & 1))
            edges=[e for e in cut["geom_cut"] if isinstance(e,bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
            caps=bmesh.ops.holes_fill(bm,edges=edges,sides=0)["faces"] if edges else []
            for face in caps:
                face.material_index=surfaces
                face.smooth=False
        bmesh.ops.triangulate(bm,faces=bm.faces[:])
        mesh=bpy.data.meshes.new(f"BankPiece_{idx}")
        for mat in source.materials: mesh.materials.append(mat)
        bm.to_mesh(mesh); bm.free()
        obj=bpy.data.objects.new(f"BankPiece_{idx}",mesh)
        bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("BankPiece_"): obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(root/"assets/mining_fracture"/(kind+".glb")),use_selection=True,export_format="GLB",export_yup=True,export_materials="EXPORT",export_vertex_color="MATERIAL",export_cameras=False,export_lights=False)
