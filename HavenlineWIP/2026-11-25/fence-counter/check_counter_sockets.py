import hashlib,json,struct,subprocess
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description="Inspect exact archived service-counter Git objects")
parser.add_argument("repo",type=Path,help="HAVENLINE checkout with the referenced art history fetched")
repo=parser.parse_args().repo
def git(sha):
    raw=subprocess.check_output(["git","-C",repo,"cat-file","blob",sha])
    assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==sha
    return raw
catalog=json.loads(git("69027ee239cd6abd0f9a761aeab87c40ece36550"))
def walk(j):
    if isinstance(j,dict):
        if j.get("id")=="service_counter": yield j
        for x in j.values(): yield from walk(x)
    if isinstance(j,list):
        for x in j: yield from walk(x)
row=next(x for x in walk(catalog) if "sockets" in x)
selected=next(walk(json.loads(git("6c7be79a4d4c5d16abff3dfbd2514a1bcde73691"))))
assert selected["score"]==9.4 and selected["git_blob_sha"]=="7427702548e15af1f3395e33ee3301df27f72117"
print("selected reference",selected["score"],selected["git_blob_sha"],"catalog sockets",row["sockets"])
raw=git("8654977d664202724b7089984bf7fb876ffbd331")
assert hashlib.sha256(raw).hexdigest()==row["sha256"]
n=struct.unpack_from("<I",raw,12)[0]; model=json.loads(raw[20:20+n]); data=raw[28+n:]
assert model["nodes"]==[{"mesh":0,"name":"service_counter"}]
def read(i):
    a=model["accessors"][i]; v=model["bufferViews"][a["bufferView"]]
    f={5126:"f",5125:"I",5123:"H",5121:"B"}[a["componentType"]]*{"SCALAR":1,"VEC3":3}[a["type"]]
    size=struct.calcsize("<"+f); off=v.get("byteOffset",0)+a.get("byteOffset",0)
    return [struct.unpack_from("<"+f,data,off+k*v.get("byteStride",size)) for k in range(a["count"])]
def vertical(x,z,tri):
    (a,y,b),(c,v,d),(e,w,f)=tri
    det=(c-a)*(f-b)-(d-b)*(e-a)
    if abs(det)<1e-10:return None
    u=((x-a)*(f-b)-(z-b)*(e-a))/det
    l=((z-b)*(c-a)-(x-a)*(d-b))/det
    return y+(v-y)*u+(w-y)*l if min(u,l,1-u-l)>=-1e-8 else None
sides={k:[] for k in row["sockets"]}
total=0
for pr in model["meshes"][0]["primitives"]:
    v=read(pr["attributes"]["POSITION"]); ix=[i[0] for i in read(pr["indices"])]
    assert len(ix)%3==0
    total+=len(ix)//3
    mat=model["materials"][pr["material"]]["name"]
    for i in range(0,len(ix),3):
        tri=[v[a] for a in ix[i:i+3]]
        for k,(x,_,z) in row["sockets"].items():
            h=vertical(x,z,tri)
            if h is not None:sides[k].append((round(h,5),mat))
assert total==row["triangles"]==13624
print("donor triangles",total,"materials",len(model["materials"]),"images",len(model.get("images",[])),"one identity node; no authored node sockets or colliders")
for k,hits in sides.items(): print(k,"vertical mesh contacts",sorted(set(hits)))
