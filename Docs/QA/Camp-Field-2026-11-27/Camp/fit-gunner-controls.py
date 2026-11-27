"""Fit the original Meshy tower to Havenline's footing and articulate its existing mesh islands."""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

parser = argparse.ArgumentParser()
parser.add_argument("donor", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
source = args.donor.read_bytes()
size = struct.unpack_from("<I", source, 12)[0]
doc = json.loads(source[20:20 + size])
raw = source[28 + size:]
primitive = doc["meshes"][0]["primitives"][0]


def accessor(index):
    a = doc["accessors"][index]
    v = doc["bufferViews"][a["bufferView"]]
    address = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    width = {"VEC2": 2, "VEC3": 3, "SCALAR": 1}[a["type"]]
    dtype = {5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]]
    return np.frombuffer(raw, dtype, count=a["count"] * width, offset=address).reshape(-1, width)


pos = accessor(primitive["attributes"]["POSITION"])
normals = accessor(primitive["attributes"]["NORMAL"])
uvs = accessor(primitive["attributes"]["TEXCOORD_0"])
faces = accessor(primitive["indices"]).reshape(-1, 3)
verts, weld = np.unique(np.round(pos, 5), axis=0, return_inverse=True)
welded = weld[faces]
edges = coo_matrix((np.ones(welded.size), (welded.flatten(), np.roll(welded, -1, axis=1).flatten())), shape=(len(verts),)*2)
_, islands = connected_components(edges, directed=False)
labels = islands[welded[:, 0]]
pieces = {k: [] for k in ["Footings", "Cabin", "EmplacementDeck", "Turntable", "BowStock", "LoadedQuarrel"]}
for i in np.unique(labels):
    tri = faces[labels == i]
    points = pos[tri].reshape(-1,3)
    lower, upper = points.min(0), points.max(0)
    # Work on complete disconnected pieces so the remaining surface retains its painted UVs.
    if lower[2] > .192 and lower[1] > .32:
        part = "LoadedQuarrel"
    elif lower[1] > .275:
        part = "BowStock"
    elif upper[1] > .21:
        part = "Turntable"
    elif (lower[1] + upper[1]) * .5 > .052:
        part = "EmplacementDeck"
    elif upper[1] < -.22:
        part = "Footings"
    else:
        part = "Cabin"
    pieces[part].append(tri)
assert sum(len(tri) for group in pieces.values() for tri in group) == len(faces)
root = np.array([0.,pos[:,1].min(),-.105])
deck = np.array([0.,.172,-.105])
hinge = np.array([0.,.336,-.104])
bolt = np.array([0.,.387,.333])
body_scale = 2.60
mount_scale = 2.23

buffer = bytearray()
views, arrays, meshes, nodes = [], [], [], []


def view(payload):
    buffer.extend(b'\0' * (-len(buffer) % 4))
    views.append({"buffer":0, "byteOffset":len(buffer), "byteLength":len(payload)})
    buffer.extend(payload)
    return len(views)-1


def add_array(data, kind, component):
    a = np.asarray(data, dtype="<u2" if component == 5123 else "<f4")
    row = {"type":kind, "componentType":component, "count":len(a), "bufferView":view(a.tobytes())}
    if kind == "VEC3":
        row.update(min=a.min(0).tolist(), max=a.max(0).tolist())
    arrays.append(row)
    return len(arrays)-1


for name, group in pieces.items():
    tri = np.concatenate(group)
    indices, compact = np.unique(tri, return_inverse=True)
    if name == "LoadedQuarrel":
        anchor, factor = bolt, mount_scale
    elif name == "BowStock":
        anchor, factor = hinge, mount_scale
    elif name == "Turntable":
        anchor, factor = deck, mount_scale
    else:
        anchor, factor = root, body_scale
    points = (pos[indices]-anchor)*factor
    prim = {"attributes":{"POSITION":add_array(points, "VEC3", 5126),
                           "NORMAL":add_array(normals[indices], "VEC3", 5126),
                           "TEXCOORD_0":add_array(uvs[indices], "VEC2", 5126)},
            "indices":add_array(compact.ravel(), "SCALAR", 5123), "material":0}
    meshes.append({"name":name, "primitives":[prim]})
    node = {"name":name, "mesh":len(meshes)-1}
    if name == "Turntable":
        node["translation"] = ((deck-root)*body_scale).tolist()
    elif name == "BowStock":
        node["translation"] = ((hinge-deck)*mount_scale).tolist()
    elif name == "LoadedQuarrel":
        node["translation"] = ((bolt-hinge)*mount_scale).tolist()
    nodes.append(node)
nodes[3]["children"]=[4]
nodes[4]["children"]=[5]

# Reuse intact painted components from this exact donor to build a fixed rear
# winding station on the turning bearing. The lever, supports and tread keep the
# artist's UVs, grain, iron finish and fastener shapes.
def fitted_island(island, center, size):
    tri=faces[labels==island]
    indices, inverse = np.unique(tri,return_inverse=True)
    points=pos[indices]
    lo,hi=points.min(0),points.max(0)
    fit=np.asarray(size)/(hi-lo)
    normal=normals[indices]/fit
    normal/=np.linalg.norm(normal,axis=1)[:,None]
    return { "attributes":{"POSITION":add_array((points-(lo+hi)*.5)*fit+np.asarray(center),"VEC3",5126),
             "NORMAL":add_array(normal,"VEC3",5126),"TEXCOORD_0":add_array(uvs[indices],"VEC2",5126)},
             "indices":add_array(inverse.ravel(),"SCALAR",5123),"material":0}
def equipment(name,center,primitives,parent):
    index=len(nodes)
    meshes.append({"name":name,"primitives":primitives})
    nodes.append({"name":name,"mesh":len(meshes)-1,"translation":list(center)})
    nodes[parent].setdefault("children",[]).append(index)
    return index

equipment("GunnerTread",(0.,0.,0.),[
    fitted_island(62,(0.,-.002,-.78),(.81,.058,.69)),
    fitted_island(77,(-.173,-.09,-.49),(.16,.13,.64)),
    fitted_island(145,(.173,-.09,-.49),(.16,.13,.64)),
    fitted_island(77,(-.139,.22,-.32),(.093,.51,.49)),
    fitted_island(145,(.139,.22,-.32),(.093,.51,.49))
],3)
for name,side,wheel in [("RightWindlass",-1.,95),("LeftBreechControl",1.,143)]:
    x=side*.160
    drive=equipment(name,(x,.52,-.45),[fitted_island(wheel,(0.,0.,0.),(.123,.21,.21))],3)
    equipment(name+"Handle",(side*.088,.075,-.070),[fitted_island(167,(0.,0.,0.),(.117,.060,.062))],drive)
v=doc["bufferViews"][doc["images"][0]["bufferView"]]
im=Image.open(io.BytesIO(raw[v["byteOffset"]:v["byteOffset"]+v["byteLength"]])).convert("RGB")
# The matched B43 shot has steel-blue bow arms. Keep the donor's wear and bronze
# ferrules while tempering the outer sprung arms, where they silhouette against timber.
finish = Image.new("L", im.size, 0)
brush = ImageDraw.Draw(finish)
for triangle in faces[np.isin(labels,[6,8,152,164])]:
    extent = abs(pos[triangle,0].mean())
    weight = np.clip((extent-.12)/.16,0.,1.)
    polygon = [tuple(pt) for pt in (uvs[triangle]*im.size).round().astype(int)]
    brush.polygon(polygon, fill=round(float(weight)*235))
mask = np.asarray(finish.filter(ImageFilter.MaxFilter(3)), dtype=float)[:,:,None]/255.
paint = np.asarray(im, dtype=float)
light = .34*paint[:,:,0]+.51*paint[:,:,1]+.15*paint[:,:,2]
steel = np.clip(light[:,:,None]*np.array([.63,1.10,1.39])+np.array([6,12,18]),0,255)
im = Image.fromarray(np.rint(paint*(1.-mask)+steel*mask).astype("uint8"),"RGB")
picture=io.BytesIO()
im.save(picture, format="JPEG", quality=93, subsampling=0)
image_view=view(picture.getvalue())
out={"asset":{"version":"2.0"}, "scene":0, "scenes":[{"nodes":[0,1,2,3]}], "nodes":nodes, "meshes":meshes,
     "materials":[{"name":"Ballista timber, iron, slate, snow and warm windows",
        "doubleSided":True, "pbrMetallicRoughness":{"baseColorTexture":{"index":0},"metallicFactor":0,"roughnessFactor":.8}}],
     "images":[{"bufferView":image_view,"mimeType":"image/jpeg"}], "textures":[{"source":0}],
     "buffers":[{"byteLength":len(buffer)}], "bufferViews":views,"accessors":arrays}
encoded=json.dumps(out,separators=(",",":")).encode()
encoded+=b" "*(-len(encoded)%4)
buffer.extend(b"\0"*(-len(buffer)%4))
args.output.write_bytes(struct.pack("<4sIII4s",b"glTF",2,28+len(encoded)+len(buffer),len(encoded),b"JSON")+encoded+struct.pack("<I4s",len(buffer),b"BIN\0")+buffer)
print("source",hashlib.sha256(source).hexdigest(),"output",hashlib.sha256(args.output.read_bytes()).hexdigest())
print({k:sum(len(t) for t in groups) for k,groups in pieces.items()})
