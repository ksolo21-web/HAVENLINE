"""Prepare the owner's Skybound Sentinel (spread) and Frostwing Pathfinder (folded) for Level 1.

python tools/art/build_authored_owl.py spread.glb folded.glb pet_owl_01.png assets/settlement_people/expedition_owl_authored.glb
The inputs are the textured Meshy task downloads recorded below. No generation is needed.
"""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

from build_owl_strike import normal_delta, ramp


FLIGHT = ("01a07c8a-74a3-727b-b05b-df02ee8c031c", "ef4c6ac544c166e7436620887c13355074df6f696a0a2cda77ed023ebcbd8000")
PERCH = ("01a07c5f-9e76-7539-85b4-db496cf86e65", "bdaa0aa9f84e6089b536da505461948ca9e8a3863fb4f5c282d89c8fb544c687")
HEIGHT = .675


def read_donor(path, identity):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != identity[1]:
        raise ValueError(f"Unexpected model for Meshy task {identity[0]}")
    length = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20+length]), data[28+length:]


def array(donor, index):
    doc, data = donor
    acc = doc["accessors"][index]
    view = doc["bufferViews"][acc["bufferView"]]
    dims = {"SCALAR":1, "VEC2":2, "VEC3":3, "VEC4":4}[acc["type"]]
    dtype = {5126:"<f4",5125:"<u4",5123:"<u2"}[acc["componentType"]]
    return np.frombuffer(data, dtype, acc["count"]*dims,
                         view.get("byteOffset", 0)+acc.get("byteOffset", 0)).reshape(-1, dims).copy()


def atomic(path, data):
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_bytes(data)
    temp.replace(path)


def rest_head(positions, normals, tangents, faces):
    """Square the donor's 43-degree head turn for the forward-looking perch."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components, dijkstra

    points, weld = np.unique(positions.round(7), axis=0, return_inverse=True)
    triangles = weld[faces].reshape(-1,3)
    edges = np.sort(np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]),axis=1)
    edges = np.unique(edges,axis=0)
    lengths = np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)
    def graph(mask):
        a,b=edges[mask].T
        return coo_matrix((lengths[mask],(a,b)),shape=(len(points),len(points))).tocsr()
    # Above the collar the donor's head and bedroll are separate surface islands.
    top=(points[:,1]>.475)
    _,labels=connected_components(graph(top[edges].all(1)),directed=False)
    head=labels==labels[np.argmax(points[:,1])]
    pack=top & ~head
    paths=graph(np.ones(len(edges),dtype=bool))
    distance_head=dijkstra(paths,directed=False,indices=np.flatnonzero(head),min_only=True)
    distance_pack=dijkstra(paths,directed=False,indices=np.flatnonzero(pack),min_only=True)
    near_head=np.nan_to_num(distance_pack-distance_head,nan=-1)
    weight=ramp(-.032,.030,near_head[weld])*ramp(.416,.493,positions[:,1])
    angle=-np.deg2rad(43.)*weight
    pivot=np.array([-.020,0,.173])
    def twist(v):
        x,z=v[:,0].copy(),v[:,2].copy()
        v[:,0]=x*np.cos(angle)+z*np.sin(angle)
        v[:,2]=z*np.cos(angle)-x*np.sin(angle)
    positions-=pivot
    twist(positions)
    positions+=pivot
    positions[:,0]+=.018*weight
    twist(normals)
    twist(tangents)


def rear_feather_bands(original, reference, positions, normals, uv, faces):
    """Transfer the rear-view feather bars within the folded wing/tail silhouette.

    The donor's mesh, UV islands and remaining albedo as well as both PBR maps
    stay intact. Preserve the sculpt's fine variation under the documented bars.
    """
    source=np.asarray(reference.convert("RGB"))
    previous=np.asarray(original.convert("RGB"))
    result=previous.copy()
    h,w=previous.shape[:2]
    coords=uv*np.array([w,h])-.5
    for face in faces:
        xyz=positions[face]
        if xyz[:,1].max()<.033 or xyz[:,1].min()>.415 or xyz[:,2].min()>.015: continue
        a,b,c=coords[face]
        low=np.maximum(0,np.floor(np.min([a,b,c],axis=0)).astype(int))
        high=np.minimum([w-1,h-1],np.ceil(np.max([a,b,c],axis=0)).astype(int))
        if np.any(high<low) or np.prod(high-low+1)>60000: continue
        yy,xx=np.mgrid[low[1]:high[1]+1,low[0]:high[0]+1]
        edge=b-a;cross=c-a;det=edge[0]*cross[1]-edge[1]*cross[0]
        if abs(det)<.01:continue
        u=((xx-a[0])*cross[1]-(yy-a[1])*cross[0])/det
        v=(edge[0]*(yy-a[1])-edge[1]*(xx-a[0]))/det
        inside=(u>=0)&(v>=0)&(u+v<=1)
        if not inside.any(): continue
        ix,iy=xx[inside],yy[inside]
        u,v=u[inside],v[inside]
        bary=np.column_stack([1-u-v,u,v])
        x,y,z=(bary@xyz).T
        nz=(bary@normals[face])[:,2]
        # Register the back image to the top of the folded wings under the pack,
        # the three tail tips, and the center of each row as it falls toward the feet.
        sx=np.clip(np.rint(191-(x-(.045+.035*(1-y/.40)))*526),80,302).astype(int)
        sy=np.clip(np.rint(869-y*527),657,856).astype(int)
        sample=source[sy,sx].astype(float)
        base=previous[iy,ix].astype(float)
        alpha=ramp(.035,.083,y)*(1-ramp(.341,.406,y))*(1-ramp(-.040,.018,z))
        alpha*=ramp(-.08,.32,-nz)*ramp(43,72,sample[:,0])
        # Retain feather grooves, microcontrast and weathering from the Meshy atlas.
        texture=(base-base.mean(axis=1,keepdims=True))*.18
        color=sample*1.05+texture
        alpha*=.84
        result[iy,ix]=np.clip(base*(1-alpha[:,None])+color*alpha[:,None],0,255).astype(np.uint8)
    return Image.fromarray(result)


class OwlModel:
    def __init__(self, reference):
        self.reference=reference
        self.doc = dict(asset={"version":"2.0","generator":"Havenline authored expedition owl rig"}, scene=0,
                        scenes=[{"nodes":[0]}], nodes=[{"name":"ExpeditionOwl","children":[]}], skins=[],
                        meshes=[], images=[], materials=[], textures=[], buffers=[], bufferViews=[], accessors=[])
        self.data = bytearray()

    def accessor(self, data, kind, target=None):
        data = np.ascontiguousarray(data, dtype="<f4" if data.dtype.kind == "f" else "<u2")
        self.data.extend(bytes(-len(self.data)%4))
        views = self.doc["bufferViews"]
        view = dict(buffer=0, byteOffset=len(self.data), byteLength=data.nbytes)
        if target:
            view["target"] = target
        views.append(view)
        self.data.extend(data.tobytes())
        acc = dict(bufferView=len(views)-1, count=len(data), type=kind,
                   componentType=5126 if data.dtype.kind == "f" else 5123)
        if kind == "VEC3":
            acc.update(min=data.min(0).tolist(), max=data.max(0).tolist())
        self.doc["accessors"].append(acc)
        return len(self.doc["accessors"])-1

    def node(self, name, parent=0, **kw):
        index = len(self.doc["nodes"])
        self.doc["nodes"].append(dict(name=name, **kw))
        self.doc["nodes"][parent].setdefault("children", []).append(index)
        return index

    def material(self, donor, tag, out, positions, normals, uv, faces):
        doc, raw = donor
        start = len(self.doc["textures"])
        for image, label, size in zip(doc["images"], ["Albedo","RoughnessMetallic","Normal"], [2048,512,1024]):
            view = doc["bufferViews"][image["bufferView"]]
            offset = view.get("byteOffset",0)
            original = Image.open(io.BytesIO(raw[offset:offset+view["byteLength"]])).convert("RGB")
            if tag=="Perched" and label=="Albedo":
                original=rear_feather_bands(original,self.reference,positions,normals,uv,faces)
            if original.width != size:
                original = original.resize((size,size),Image.Resampling.LANCZOS)
            leaf = f"owl_{tag.lower()}_{label.lower()}.jpg"
            blob = io.BytesIO()
            original.save(blob,format="JPEG",quality=94,subsampling=0,optimize=True)
            atomic(out/leaf,blob.getvalue())
            index = len(self.doc["images"])
            self.doc["images"].append(dict(uri=leaf))
            self.doc["textures"].append(dict(source=index))
        index = len(self.doc["materials"])
        self.doc["materials"].append(dict(name=tag+"Plumage", doubleSided=True,
            pbrMetallicRoughness=dict(baseColorTexture={"index":start},metallicRoughnessTexture={"index":start+1}),
            normalTexture={"index":start+2}))
        return index

    def add_donor(self, donor, folded, out):
        src = donor[0]["meshes"][0]["primitives"][0]
        attrs = src["attributes"]
        verts = array(donor, attrs["POSITION"])
        normals = array(donor,attrs["NORMAL"])
        tangents = array(donor,attrs["TANGENT"])
        faces = array(donor,src["indices"]).reshape(-1,3)
        tag = "Perched" if folded else "Flight"
        scale = HEIGHT / np.ptp(verts[:,1])
        # +Z faces the player. Pathfinder's source three-quarter pose faces -43 degrees.
        yaw = np.deg2rad(43 if folded else 0)
        co, si = np.cos(yaw), np.sin(yaw)
        rot = np.array([[co,0,si],[0,1,0],[-si,0,co]])
        verts = (verts @ rot.T) * scale
        verts[:,1] -= verts[:,1].min()
        toes = verts[verts[:,1] < .039]
        center = (np.percentile(toes[:,[0,2]],5,axis=0)+np.percentile(toes[:,[0,2]],95,axis=0))*.5
        verts[:,[0,2]] -= center
        normals = normals@rot.T
        tangents[:,:3] = tangents[:,:3]@rot.T
        uv=array(donor,attrs["TEXCOORD_0"])
        if folded:
            rest_head(verts,normals,tangents,faces)
        prim = dict(attributes={"POSITION":self.accessor(verts, "VEC3",34962),
                                "NORMAL":self.accessor(normals,"VEC3",34962),
                                "TANGENT":self.accessor(tangents,"VEC4",34962),
                                "TEXCOORD_0":self.accessor(uv,"VEC2",34962)},
                    indices=self.accessor(faces.reshape(-1,1),"SCALAR",34963), material=self.material(donor,tag,out,verts,normals,uv,faces))
        mesh = {"name":tag+"Owlet","primitives":[prim]}
        index = len(self.doc["meshes"])
        self.doc["meshes"].append(mesh)
        if folded:
            self.node("FrostwingPathfinder",mesh=index)
            return
        self.node("SkyboundSentinel",mesh=index,skin=0)
        self.add_wing_skin(prim,verts,center,scale)
        self.add_talons(prim,mesh,verts,normals,faces)

    def add_wing_skin(self, prim, verts, center, scale):
        # Animate the actual owner's mantle, secondaries and primary feathers with three
        # smooth segments per side. Exclude the nearby pack, pouches, feet and face by depth.
        pos = verts.copy()
        pos[:,[0,2]] += center
        pos /= scale
        pos[:,1] -= .318359
        x,y,z = pos.T
        distance = np.abs(x)
        wing = ramp(.123,.202,distance)*ramp(-.178,-.13,y)
        near_sheet = (1-ramp(.05,.102,np.abs(z-.063)))
        wing *= np.maximum(near_sheet,ramp(.193,.222,distance))
        elbow = ramp(.238,.317,distance)
        wrist = ramp(.337,.412,distance)
        weights = np.column_stack([1-wing,wing*(1-elbow),wing*(elbow-wrist),wing*wrist])
        bone_ids = np.tile([0,1,2,3],(len(verts),1))
        bone_ids[x>0,1:] += 3
        prim["attributes"]["JOINTS_0"] = self.accessor(bone_ids.astype("<u2"),"VEC4",34962)
        prim["attributes"]["WEIGHTS_0"] = self.accessor(weights,"VEC4",34962)
        root = self.node("OwlRoot")
        nodes=[root]
        points=[np.zeros(3)]
        for side, sign in [("L",-1),("R",1)]:
            parent=root
            prev=np.zeros(3)
            for label, raw in [("Shoulder",[.142,.082,.062]),("Elbow",[.278,.079,.062]),("Wrist",[.375,.107,.062])]:
                v=np.array([sign*raw[0],raw[1]+.318359,raw[2]])*scale
                v[[0,2]]-=center
                parent=self.node(label+side,parent,translation=(v-prev).tolist())
                prev=v
                nodes.append(parent)
                points.append(v)
        inverse=[]
        for pivot in points:
            m=np.eye(4);m[:3,3]=-pivot
            inverse.append(m.T.flatten())
        self.doc["skins"].append(dict(name="ExpeditionFlightRig",skeleton=root,joints=nodes,
                                     inverseBindMatrices=self.accessor(np.array(inverse),"MAT4")))

    def add_talons(self,prim,mesh,verts,normals,faces):
        x,y,z=verts.T
        shank=(1-ramp(.058,.235,y))*ramp(-.155,-.077,z)
        toe=(1-ramp(.042,.085,y))*shank
        sign=np.sign(x)
        radix=x-sign*.088
        tuck=np.column_stack((-.012*sign*shank,shank*(.103+.02*z),-shank*.124))
        reach=np.column_stack((sign*.019*shank+.30*radix*toe,-.076*shank-.022*toe,
                               .152*shank+.043*toe+.23*z*toe))
        grip=np.column_stack((sign*.008*shank-.45*radix*toe,-.084*shank-.034*toe,
                              .072*shank+.016*toe-.32*z*toe))
        prim["targets"]=[]
        morphs=[tuck,reach,grip]
        for motion in morphs:
            prim["targets"].append(dict(POSITION=self.accessor(motion,"VEC3",34962),
                                        NORMAL=self.accessor(normal_delta(verts,normals,motion,faces),"VEC3",34962)))
        mesh.update(weights=[0,0,0],extras={"targetNames":["FlightTalons","StrikeReach","GripAndRake"]})
        for sign,side in [(-1,"Left"),(1,"Right")]:
            for i,offset in enumerate([.046,.094,.154]):
                candidates=np.flatnonzero((np.abs(x*sign-offset)<.024)&(y<.052)&(z>-.006))
                vertex=candidates[np.argmax(z[candidates]-.75*y[candidates])]
                base=self.node(f"Claw{side}{i}",translation=verts[vertex].tolist())
                for name,delta in zip(["Tuck","Reach","Grip"],morphs):
                    self.node(name,base,translation=delta[vertex].tolist())

    def write(self,path):
        self.data.extend(bytes(-len(self.data)%4))
        self.doc["buffers"]=[{"byteLength":len(self.data)}]
        head=json.dumps(self.doc,separators=(",",":")).encode()
        head+=b" "*(-len(head)%4)
        atomic(path,struct.pack("<4sIII4s",b"glTF",2,28+len(head)+len(self.data),len(head),b"JSON")
               +head+struct.pack("<I4s",len(self.data),b"BIN\0")+self.data)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ["spread","folded","reference","output"]: p.add_argument(arg,type=Path)
    args=p.parse_args()
    if hashlib.sha256(args.reference.read_bytes()).hexdigest()!="0ae787ef27d7961ad3c8f760275c514457326b0a0aac9a371dd1470085529cd8":
        raise ValueError("Expected selected GitHub owl sheet db465610eb61d155a7ae0876b624fa625361a19f")
    owl=OwlModel(Image.open(args.reference))
    owl.add_donor(read_donor(args.spread,FLIGHT),False,args.output.parent)
    owl.add_donor(read_donor(args.folded,PERCH),True,args.output.parent)
    owl.write(args.output)
