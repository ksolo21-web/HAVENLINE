import json
import struct
from pathlib import Path

def collect(path):
    contents=path.read_bytes()
    extent,_,chunk_length=struct.unpack_from("<III",contents,4)
    document=json.loads(contents[20:20+chunk_length])
    meshes=document["meshes"]
    nodes=document["nodes"]
    accessors=document["accessors"]
    assert all("matrix" not in n and n.get("scale",(1,1,1))==[1,1,1] or "scale" not in n for n in nodes)
    bounds={}
    envelope=([[float("inf")]*3,[float("-inf")]*3])
    triangles=0
    def descend(n, head):
        nonlocal triangles
        node=nodes[n]
        point=[head[i]+node.get("translation",[0,0,0])[i] for i in range(3)]
        if "mesh" in node:
            for primitive in meshes[node["mesh"]]["primitives"]:
                triangles+=accessors[primitive["indices"]]["count"]//3
                entry=accessors[primitive["attributes"]["POSITION"]]
                for i in range(3):
                    envelope[0][i]=min(envelope[0][i],point[i]+entry["min"][i])
                    envelope[1][i]=max(envelope[1][i],point[i]+entry["max"][i])
        bounds[node["name"]]=point
        for child in node.get("children",[]):
            descend(child,point)
    for i in document["scenes"][document["scene"]]["nodes"]:
        descend(i,[0,0,0])
    return envelope,triangles,{k:[round(v,4) for v in bounds[k]] for k in bounds if k.startswith(("Blade","Wheel","Slat","Roof")) and "Geometry" not in k}
if __name__=="__main__":
    for f in Path('/dev/shm/hl14game/assets/snow_truck').glob('*.glb'):
        b,t,p=collect(f)
        print(f.name,b,t,p)
