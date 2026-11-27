"""Paint a continuous cobalt and snow boundary on the fitted Meshy garage UVs."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import hashlib
import json
import struct
import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def glb_contents(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and length == len(data)
    json_size, json_type = struct.unpack_from("<I4s", data, 12)
    assert json_type == b"JSON"
    binary_size, binary_type = struct.unpack_from("<I4s", data, 20+json_size)
    assert binary_type == b"BIN\0"
    return json.loads(data[20:20+json_size]), data[28+json_size:28+json_size+binary_size]


def get_view(document, binary, index):
    view = document["bufferViews"][index]
    off = view.get("byteOffset",0)
    return binary[off:off+view["byteLength"]]


def read_accessor(document, binary, index):
    declaration = document["accessors"][index]
    view = document["bufferViews"][declaration["bufferView"]]
    dimensions = {"SCALAR":1,"VEC2":2,"VEC3":3}[declaration["type"]]
    dtype = np.dtype({5123:"<u2",5125:"<u4",5126:"<f4"}[declaration["componentType"]])
    byte_offset = view.get("byteOffset",0)+declaration.get("byteOffset",0)
    byte_stride = view.get("byteStride",dimensions*dtype.itemsize)
    return np.ndarray(shape=(declaration["count"],dimensions),dtype=dtype,buffer=binary,
                      offset=byte_offset,strides=(byte_stride,dtype.itemsize))


def transition(lower,upper,value):
    fraction=np.clip((value-lower)/(upper-lower),0.,1.)
    return fraction*fraction*(3.-2.*fraction)


def roof_pixel(column, normal_up, original):
    x,y,z=column.T
    width=np.abs(x)
    # Natural drip edges travel continuously over the generated snow surface.
    # Blue reveals on both roof pitches, between the retained ridge and eaves.
    ridge = .50 + .085*np.sin(2.1*z+.17) + .055*np.sin(5.2*z+.67)
    eave = 1.78 + .115*np.sin(2.25*z+.78) + .075*np.sin(4.15*z+.48)
    front = .21+.10*np.cos(2.1*width)+.09*np.sin(4.7*width+.14)
    rear = 5.17+.08*np.cos(2.8*width+.32)
    edge_dist=np.minimum.reduce([width-ridge,eave-width,z-front,rear-z])
    slope = transition(0.12,.44,normal_up)
    roof_elevation=transition(-.20,-.08,y-(3.81-.62*width))
    alpha=transition(-.041,.053,edge_dist)*slope*roof_elevation

    # Slightly raised continuous metal seams follow the fall of each roof
    # panel. Paired highlights and shadows read at gameplay scale.
    tile=.375
    seam = (z-.047)%tile
    nearest = np.minimum(seam,tile-seam)
    shadow = np.exp(-((nearest-.008)/.013)**2)
    highlight = np.exp(-((seam-.035)/.019)**2)
    panel = 1. + .024*np.sin(np.floor((z-.047)/tile)*4.8)
    original_luma=original @ np.array([.215,.709,.076],dtype=np.float32)
    patina=.76+.25*np.clip(original_luma/247.,.0,1.10)
    blue_appearance = np.array([32.,86.,184.]) * (patina*panel*(1.0-.27*shadow+.13*highlight))[:,None]
    blue_appearance += np.array([7.0,12.0,22.0]) * ((width-.5)/1.30)[:,None]
    return alpha,blue_appearance


def timber_pixel(column, normal_up, original):
    x,y,z=column.T
    r,g,b=original.T
    warmer=transition(8.,16.,r-g)*transition(6.,14.,g-b)
    exterior=(transition(1.42,1.56,np.abs(x))*transition(.33,.46,y)
            *(1.-transition(2.32,2.43,y))*transition(.12,.45,z)
            *(1.-transition(5.,5.32,z))*(1.-transition(.31,.72,np.abs(normal_up))))
    wood=warmer*exterior*.86
    lift=original*np.array([1.20,1.36,1.30]) + np.array([11.5,8.,5.])
    return wood,lift


def paint(document, binary, skin):
    height,width,_=skin.shape
    strength=np.zeros((height,width),dtype=np.float32)
    coverage=np.zeros((height,width),dtype=bool)
    painted=skin.copy()
    names={"MeshyGarageRoofAndGables":roof_pixel,"MeshyGarageWallsAndFootings":timber_pixel}
    primitive_table=[]
    for node in document["nodes"]:
        surface=names.get(node.get("name",""))
        if surface is None:
            continue
        assert not any(k in node for k in ("translation","rotation","scale","matrix"))
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            primitive_table.append(primitive)
            attributes=primitive["attributes"]
            coords=read_accessor(document,binary,attributes["POSITION"])
            normals=read_accessor(document,binary,attributes["NORMAL"])[:,1]
            uv=read_accessor(document,binary,attributes["TEXCOORD_0"])
            px=uv*np.array([width,height])-0.5
            faces=read_accessor(document,binary,primitive["indices"]).reshape(-1,3)
            for f in faces:
                points=px[f]
                minx,miny=np.maximum(np.floor(points.min(axis=0)),0).astype(int)
                maxx,maxy=np.minimum(np.ceil(points.max(axis=0)),(width-1,height-1)).astype(int)
                if minx>maxx or miny>maxy:
                    continue
                pu,pv=points[1]-points[0],points[2]-points[0]
                signed=pu[0]*pv[1]-pu[1]*pv[0]
                if abs(signed)<1e-8:
                    continue
                uvs=np.mgrid[miny:maxy+1,minx:maxx+1]
                y=uvs[0].ravel()
                x=uvs[1].ravel()
                dx,dy=x-points[0,0],y-points[0,1]
                u=(dx*pv[1]-dy*pv[0])/signed
                v=(dy*pu[0]-dx*pu[1])/signed
                coverage_mask=(u>=-.001)&(v>=-.001)&(u+v<=1.001)
                if not coverage_mask.any():
                    continue
                y,x=y[coverage_mask],x[coverage_mask]
                blend=np.stack((1-u[coverage_mask]-v[coverage_mask],u[coverage_mask],v[coverage_mask]),axis=1)
                coverage[y,x]=True
                src=skin[y,x].astype(np.float32)
                alpha,color=surface(blend @ coords[f],blend @ normals[f],src)
                write=alpha>strength[y,x]
                if write.any():
                    yw,xw=y[write],x[write]
                    strength[yw,xw]=alpha[write]
                    result=src[write]+alpha[write,None]*(color[write]-src[write])
                    painted[yw,xw]=np.clip(result,0,255).astype(np.uint8)
    # Keep clean color under texture filtering at the padded UV island edge.
    distance, nearest=ndimage.distance_transform_edt(~coverage,return_indices=True)
    padding=(distance>0)&(distance<=3.1)&(strength[nearest[0],nearest[1]]>.05)
    painted[padding]=painted[nearest[0][padding],nearest[1][padding]]
    return painted,primitive_table,int(np.count_nonzero(strength>.05))


def main(source, destination):
    document,binary=glb_contents(source)
    original=get_view(document,binary,document["images"][0]["bufferView"])
    skin=np.array(Image.open(BytesIO(original)).convert("RGB"))
    fixed,primitives,pixels=paint(document,binary,skin)
    assert len(primitives)==3 and pixels>120000, (len(primitives),pixels)
    new_image=BytesIO()
    Image.fromarray(fixed).save(new_image,format="JPEG",quality=93,optimize=True)
    texture=new_image.getvalue()
    index_view=len(document["bufferViews"])
    index_image=len(document["images"])
    index_texture=len(document["textures"])
    index_material=len(document["materials"])
    document["bufferViews"].append({"buffer":0,"byteOffset":len(binary),"byteLength":len(texture)})
    document["images"].append({"name":"FittedGarageRoof","mimeType":"image/jpeg","bufferView":index_view})
    document["textures"].append({"source":index_image,"sampler":0})
    surface=deepcopy(document["materials"][0])
    surface["name"]="Fitted Meshy garage · etched cobalt panels"
    surface["pbrMetallicRoughness"]["baseColorTexture"]["index"]=index_texture
    # A low diffuse lift maintains the orange timber in the native camp shade.
    surface["emissiveTexture"]={"index":index_texture}
    surface["emissiveFactor"]=[.065,.065,.065]
    document["materials"].append(surface)
    for primitive in primitives:
        primitive["material"]=index_material
    original_binary=binary
    binary+=texture
    binary+=b"\0"*((-len(binary))%4)
    assert binary[:len(original_binary)]==original_binary
    document["buffers"][0]["byteLength"]=len(binary)
    metadata=json.dumps(document,separators=(",",":"),ensure_ascii=False).encode("utf8")
    metadata+=b" "*((-len(metadata))%4)
    total=28+len(metadata)+len(binary)
    destination.write_bytes(struct.pack("<4sIII4s",b"glTF",2,total,len(metadata),b"JSON")+metadata
                            +struct.pack("<I4s",len(binary),b"BIN\0")+binary)
    print(json.dumps({"source":str(source),"candidate":str(destination),"painted_texels":pixels,
                      "original_binary_bytes":len(original_binary),
                      "original_buffer_sha256":hashlib.sha256(original_binary).hexdigest(),
                      "original_meshy_texture_sha256":hashlib.sha256(original).hexdigest(),
                      "new_roof_and_timber_texture_sha256":hashlib.sha256(texture).hexdigest(),
                      "surface_primitives_reassigned":len(primitives)}))


if __name__=="__main__":
    main(*(Path(arg) for arg in sys.argv[1:]))
