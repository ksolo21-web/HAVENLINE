#!/usr/bin/env python3
"""Global Blender DETAIL_MASTER -> GAME_LOD0 PBR bake + export.

Input .blend must contain collections DETAIL_MASTER (high-poly source) and
GAME_LOD0 (artist-retopologized game mesh), each with exactly one joined mesh.
Artist-authored base_color/roughness/metallic PNGs must exist; no flat or
procedural surrogate is manufactured to fake reference quality.

Use: blender -b --factory-startup --python blender_build.py -- \
 --source asset.blend --maps source_textures --out build --asset-id asset_name
"""
import argparse,json,pathlib,hashlib,shutil,sys
import bpy
def parse_args():
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    for k in ("source","maps","out","asset-id"):p.add_argument("--"+k,required=True)
    p.add_argument("--size",type=int,default=512)
    p.add_argument("--triangles-max",type=int,default=20000)
    return p.parse_args(a)
def coll(name):
    c=bpy.data.collections.get(name)
    if c is None:raise RuntimeError("Missing editable asset collection "+name)
    o=[v for v in c.all_objects if v.type=="MESH"]
    if len(o)!=1:raise RuntimeError(name+" requires one joined mesh; got "+str(len(o)))
    return o[0]
def set_active(objs,active):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=active
def texture_node(mat,img):
    if not mat.use_nodes:mat.use_nodes=True
    nodes=mat.node_tree.nodes
    prev=nodes.get("HAVENLINE_BAKE_TARGET")
    if prev:nodes.remove(prev)
    node=nodes.new("ShaderNodeTexImage")
    node.name="HAVENLINE_BAKE_TARGET"
    node.image=img
    # Cycles writes only to the active AND selected Image Texture node.
    for existing in nodes: existing.select=False
    node.select=True
    nodes.active=node
    return node
def material_for_low(low):
    if len(low.data.materials)!=1:raise RuntimeError("GAME_LOD0 must use one atlased PBR material for this v1 baker")
    mat=low.data.materials[0]
    if mat is None:raise RuntimeError("GAME_LOD0 material slot empty")
    mat.use_nodes=True
    return mat
def save_image(image,path):
    image.filepath_raw=str(path)
    image.file_format="PNG"
    image.save()
def load_png(path):
    if not path.is_file() or not path.stat().st_size:raise RuntimeError("Required author texture missing: "+str(path))
    return bpy.data.images.load(str(path),check_existing=False)
def build(a):
    if a.size<64 or a.size>4096 or a.size&(a.size-1):raise RuntimeError("Bake map size must be power-of-two 64..4096")
    source=pathlib.Path(a.source).resolve()
    raw=pathlib.Path(a.maps).resolve()
    out=pathlib.Path(a.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    texout=out/"textures";texout.mkdir(exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    high=coll("DETAIL_MASTER")
    low=coll("GAME_LOD0")
    if high==low:raise RuntimeError("High and low mesh must be independently editable")
    if not low.data.uv_layers or not low.data.uv_layers.active:
        raise RuntimeError("Artist UVs required on GAME_LOD0: refusing automatic quality-lowering unwrap")
    triangles=sum(len(p.vertices)-2 for p in low.data.polygons)
    if triangles>a.triangles_max or triangles==0:raise RuntimeError("LOD triangle budget exceeded: "+str(triangles))
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=12
    scene.render.bake.margin=8
    scene.render.bake.use_selected_to_active=True
    scene.render.bake.cage_extrusion=.042
    # Only source authored images are copied; no made-up texture maps.
    originals={}
    for name in ("base_color","roughness","metallic"):
        path=raw/(name+".png")
        image=load_png(path)
        target=texout/(name+".png")
        shutil.copy2(path,target)
        originals[name]=image
    material=material_for_low(low)
    # Blender 4.0 headless Cycles can return FINISHED while leaving an
    # internally generated alpha image entirely transparent. The external
    # baking path directly writes raster output; never mark empty PNGs valid.
    scene.render.image_settings.file_format="PNG"
    def sample_pixels(image):
        # 8192 distributed positions rather than a single UV corner. This
        # catches Blender's misleading FINISHED with a completely blank map,
        # without allocating a second full-resolution 4K image buffer.
        pixels=image.pixels
        total=image.size[0]*image.size[1]
        probes=min(total,8192)
        return [(pixels[4*((i*104729)%total)],
                 pixels[4*((i*104729)%total)+1],
                 pixels[4*((i*104729)%total)+2],
                 pixels[4*((i*104729)%total)+3]) for i in range(probes)]
    def changed_count(before,after):
        return sum(any(abs(v-w)>.03 for v,w in zip(a[:3],b[:3]))
                   for a,b in zip(before,after))
    normal_path=texout/"normal.png"
    normal=bpy.data.images.new("HAVENLINE_NORMAL_BAKE_TARGET",width=a.size,height=a.size,alpha=False)
    # Non-transparent sentinel lets Blender 4.0 preserve opaque output when
    # use_clear=False. The RGB change check independently proves real painting.
    normal.generated_color=(.90,.10,.85,1.0)
    normal.update()
    normal.colorspace_settings.name="Non-Color"
    texture_node(material,normal)
    bpy.context.view_layer.update()
    pre_normal=sample_pixels(normal)
    print("HAVENLINE DEBUG low UV samples",len(low.data.uv_layers.active.data),
          [tuple(x.uv) for x in low.data.uv_layers.active.data[:3]])
    print("HAVENLINE DEBUG image node active",material.node_tree.nodes.active.name)
    set_active([high,low],low)
    # Blender 4.0 saves image-target bakes INTERNALLY even when an external
    # save_mode is requested. Explicitly save the actual populated image.
    result=bpy.ops.object.bake(type="NORMAL",target="IMAGE_TEXTURES",
                               save_mode="INTERNAL",use_clear=False,
                               use_selected_to_active=True,cage_extrusion=.042,
                               normal_space="TANGENT")
    # Do NOT call Image.update() here: it can invalidate the freshly baked
    # buffer on Blender's generated image backing. Inspect/snapshot first.
    post_normal=sample_pixels(normal)
    delta_normal=changed_count(pre_normal,post_normal)
    print("HAVENLINE NORMAL baked_pixel_before_after",pre_normal[0],post_normal[0])
    print("HAVENLINE NORMAL baked_sample_changes",delta_normal,"of",len(pre_normal))
    assert "FINISHED" in result and delta_normal>=max(8,len(pre_normal)//200), (
        "Cycles failed to paint meaningful high-to-low normal pixels")
    save_image(normal,normal_path)
    assert normal_path.is_file() and normal_path.stat().st_size>128
    print("HAVENLINE NORMAL post-bake sampled opacity",sum(px[3]>.5 for px in post_normal),"/",len(post_normal))
    ao_path=texout/"ambient_occlusion.png"
    ao=bpy.data.images.new("HAVENLINE_AO_BAKE_TARGET",width=a.size,height=a.size,alpha=False)
    ao.colorspace_settings.name="Non-Color"
    # Even valid isolated objects can have an all-white AO map. Initialize the
    # target visibly magenta so a white bake must overwrite actual pixels.
    ao.generated_color=(.90,.10,.85,1.0)
    ao.update()
    texture_node(material,ao)
    bpy.context.view_layer.update()
    pre_ao=sample_pixels(ao)
    print("HAVENLINE AO target before bake",pre_ao[0],pre_ao[len(pre_ao)//2])
    set_active([low],low)
    result=bpy.ops.object.bake(type="AO",target="IMAGE_TEXTURES",save_mode="INTERNAL",
                               use_clear=False,use_selected_to_active=False)
    post_ao=sample_pixels(ao)
    delta_ao=changed_count(pre_ao,post_ao)
    print("HAVENLINE AO target after bake",post_ao[0],post_ao[len(post_ao)//2])
    print("HAVENLINE AO baked_sample_changes",delta_ao,"of",len(pre_ao))
    assert "FINISHED" in result and delta_ao>=max(8,len(pre_ao)//200), (
        "Cycles failed to paint meaningful ambient-occlusion pixels")
    save_image(ao,ao_path)
    assert ao_path.is_file() and ao_path.stat().st_size>128
    print("HAVENLINE AO post-bake sampled opacity",sum(px[3]>.5 for px in post_ao),"/",len(post_ao))
    shader=material.node_tree.nodes.get("Principled BSDF")
    if shader is None:raise RuntimeError("Principled BSDF material required")
    target=material.node_tree.nodes.get("HAVENLINE_BAKE_TARGET")
    if target:material.node_tree.nodes.remove(target)
    for name,input_name in (("base_color","Base Color"),("roughness","Roughness"),("metallic","Metallic")):
        img=originals[name]
        if name!="base_color":img.colorspace_settings.name="Non-Color"
        node=material.node_tree.nodes.new("ShaderNodeTexImage")
        node.name="HAVENLINE_"+name
        node.image=img
        material.node_tree.links.new(node.outputs["Color"],shader.inputs[input_name])
    node=material.node_tree.nodes.new("ShaderNodeTexImage")
    node.image=normal
    node.name="HAVENLINE_normal"
    node.image.colorspace_settings.name="Non-Color"
    norm=material.node_tree.nodes.new("ShaderNodeNormalMap")
    material.node_tree.links.new(node.outputs["Color"],norm.inputs["Color"])
    material.node_tree.links.new(norm.outputs["Normal"],shader.inputs["Normal"])
    # AO is saved as a separate authored map for Godot integration. Do not
    # silently multiply albedo or claim glTF occlusion is embedded.
    bpy.ops.file.pack_all()
    source_copy=out/(a.asset_id+"_MASTER_AND_LOD0.blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(source_copy))
    # Export GAME_LOD0 only; never include studio, high-detail meshes or cameras.
    set_active([low],low)
    output_glb=out/(a.asset_id+"_LOD0.glb")
    bpy.ops.export_scene.gltf(filepath=str(output_glb),export_format="GLB",
                              use_selection=True,export_yup=True,export_apply=True)
    if not output_glb.exists() or output_glb.stat().st_size<128:raise RuntimeError("GLB exporter produced no binary")
    report={
        "asset_id":a.asset_id,"state":"TECHNICAL_BAKE_CANDIDATE_ONLY",
        "blender_version":bpy.app.version_string,
        "low_triangles":triangles,
        "high_mesh_name":high.name,"low_mesh_name":low.name,
        "source_blend_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "glb_sha256":hashlib.sha256(output_glb.read_bytes()).hexdigest(),
        "normal_baked_from_high":True,"ao_baked_from_low":True,
        "normal_changed_sample_count":delta_normal,"ao_changed_sample_count":delta_ao,
        "base_color_roughness_metallic_are_artist_inputs":True,
        "glb_contains_ao_map":False,
        "native_godot_tested":False,"visual_approved":False,"owner_approved":False,
        "renderable_texture_maps":["base_color","normal","roughness","metallic","ambient_occlusion"]
    }
    (out/"bake_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":build(parse_args())
