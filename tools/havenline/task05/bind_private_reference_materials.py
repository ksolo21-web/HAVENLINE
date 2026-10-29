#!/usr/bin/env python3
"""PRIVATE T05 reference-sourced GLB material binding.

Never commit the owner image or generated image maps to the public repository.
Does not change vertex/triangle/indices data or promote game assets.
This is a geometry-independent UV tiling trial, NOT matched-camera projection
and NOT the final reference-fidelity or PBR relighting approval.
"""
import argparse, hashlib, io, json, pathlib, struct
import numpy as np
from PIL import Image

LOCKED_SHA="729393f7980d8bd70906a7e4de04c3c6b21de5dfe4deb3d98ca7005b54d61635"
REGIONS={
    "HL_wood":(961,1080,1112,1111),
    "HL_wood_light":(190,815,295,837),
    "HL_blue":(549,574,664,616),
    "HL_metal":(711,339,806,377),
    "HL_red":(207,724,269,756),
    "HL_snow":(491,456,609,491),
    "HL_orange":(1172,771,1186,798),
    "HL_cream":(1228,765,1255,784),
    "HL_dark":(577,904,620,920),
}
def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_glb(data):
    assert data[:4]==b"glTF" and struct.unpack_from("<I",data,4)[0]==2
    assert struct.unpack_from("<I",data,8)[0]==len(data)
    length,kind=struct.unpack_from("<I4s",data,12)
    assert kind==b"JSON"
    doc=json.loads(data[20:20+length])
    start=20+length
    bin_len,bin_kind=struct.unpack_from("<I4s",data,start)
    assert bin_kind==b"BIN\x00" and start+8+bin_len==len(data)
    return doc,bytearray(data[start+8:])

def pack_glb(doc,buffer):
    doc["buffers"][0]["byteLength"]=len(buffer)
    header=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode("utf8")
    header+=b" "*((-len(header))%4)
    buffer+=b"\x00"*((-len(buffer))%4)
    total=28+len(header)+len(buffer)
    return (struct.pack("<4sII",b"glTF",2,total)+
            struct.pack("<I4s",len(header),b"JSON")+header+
            struct.pack("<I4s",len(buffer),b"BIN\x00")+buffer)

def mirrored_source_pixels(im,box):
    patch=np.asarray(im.crop(box).convert("RGB"))
    h,w=patch.shape[:2]
    assert h>=12 and w>=14
    assert (np.max(patch,axis=2)<24).mean()<0.05, "black background contaminated material crop"
    assert max(patch.std(axis=(0,1)))>3, "uninformative crop"
    y=np.arange(256)%(2*h)
    x=np.arange(256)%(2*w)
    y=np.minimum(y,2*h-1-y)
    x=np.minimum(x,2*w-1-x)
    result=patch[y[:,None],x[None,:]]
    return Image.fromarray(result,"RGB")

def build(reference,candidate,destination):
    source_bytes=pathlib.Path(reference).read_bytes()
    assert digest(source_bytes)==LOCKED_SHA, "wrong original reference bytes"
    image=Image.open(io.BytesIO(source_bytes)).convert("RGB")
    assert image.size==(1536,1536)
    original=pathlib.Path(candidate).read_bytes()
    doc,buffer=read_glb(original)
    assert set(m["name"] for m in doc["materials"])==set(REGIONS)
    assert len(doc["materials"])==9 and len(doc["meshes"])==9
    frozen=json.dumps(doc["meshes"],sort_keys=True)
    out=pathlib.Path(destination)
    out.mkdir(parents=True,exist_ok=True)
    folder=out/"source-map-pixels"
    folder.mkdir(exist_ok=True)
    checked=[]
    for material in doc["materials"]:
        name=material["name"]
        map_img=mirrored_source_pixels(image,REGIONS[name])
        path=folder/(name+".png")
        map_img.save(path)
        blob=path.read_bytes()
        while len(buffer)%4: buffer.append(0)
        view=len(doc["bufferViews"])
        doc["bufferViews"].append({"buffer":0,"byteOffset":len(buffer),"byteLength":len(blob)})
        buffer.extend(blob)
        img_idx=len(doc["images"])
        doc["images"].append({"name":"PRIVATE_SOURCE_"+name,"mimeType":"image/png","bufferView":view})
        tex_idx=len(doc["textures"])
        doc["textures"].append({"source":img_idx,"sampler":0})
        pbr=material["pbrMetallicRoughness"]
        pbr["baseColorTexture"]={"index":tex_idx,"texCoord":0}
        pbr["baseColorFactor"]=[1,1,1,1]
        checked.append({"material":name,"source_box":REGIONS[name],"embedded_png_sha256":digest(blob)})
    assert json.dumps(doc["meshes"],sort_keys=True)==frozen
    doc["asset"].setdefault("extras",{})["t05_r29"]={
        "status":"PRIVATE_SOURCE_UV_TRIAL_NOT_APPROVED",
        "reference_sha256":LOCKED_SHA,
        "source_candidate_sha256":digest(original),
        "source_materials":9,
        "warning":"No native render, source-camera projection or owner approval"}
    glb=out/"T05_cooker_PRIVATE_SOURCE_UV_TRIAL.glb"
    glb.write_bytes(pack_glb(doc,buffer))
    verify,bin_bytes=read_glb(glb.read_bytes())
    assert json.dumps(verify["meshes"],sort_keys=True)==frozen
    for check in checked:
        material=next(m for m in verify["materials"] if m["name"]==check["material"])
        index=material["pbrMetallicRoughness"]["baseColorTexture"]["index"]
        view=verify["bufferViews"][verify["images"][verify["textures"][index]["source"]]["bufferView"]]
        blob=bytes(bin_bytes[view["byteOffset"]:view["byteOffset"]+view["byteLength"]])
        assert digest(blob)==check["embedded_png_sha256"]
    receipt={
        "status":"PRIVATE_REFERENCE_PIXEL_BINDING_TECHNICAL_PASS_NO_VISUAL_APPROVAL",
        "original_source_sha256":LOCKED_SHA,
        "candidate_source_sha256":digest(original),
        "private_glb_sha256":digest(glb.read_bytes()),
        "source_texture_slots_verified":9,
        "frozen_geometry_unchanged":True,
        "native_godot_match_verified":False,
        "camera_projection_verified":False,
        "material_style_approved":False,
        "owner_approved":False,
        "shipping_asset_modified":False,
        "limitations":["Photographic/render pixels contain lighting","UVs repeat; not full perspective projection","R28 geometry remains visibly inaccurate"],
        "materials":checked}
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",required=True)
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    print(json.dumps(build(args.reference,args.candidate,args.out),indent=2))
