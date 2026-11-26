"""Expose the actual saw and axle on the original Git T05 station.

python build_lakeshore_cooker.py /path/to/cooker_processor.glb cooker_workshop.glb
The earlier V18 preview is unidentified. The input is the R18 station from
5abfc29f1c3c51bef99247641cf1131581899942, verified by its exact byte hash.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
raw = args.source.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '985041e9e28eed01fa73366ff30870ac4071fba8a89520a2744c86439673d56d'
n = int.from_bytes(raw[12:16], 'little')
doc = json.loads(raw[20:20+n]); data = bytearray(raw[28+n:])

def values(index, fields):
    a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
    code = {5123:'H',5125:'I',5126:'f'}[a['componentType']]
    return list(struct.Struct('<'+code*fields).iter_unpack(data[view.get('byteOffset',0):view.get('byteOffset',0)+a['count']*fields*struct.calcsize(code)]))

def subset(original, indices):
    data.extend(b'\0'*(-len(data)%4)); start=len(data)
    data.extend(struct.pack('<'+'H'*len(indices),*indices))
    a=len(doc['accessors']); v=len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':2*len(indices),'target':34963})
    doc['accessors'].append({'bufferView':v,'componentType':5123,'count':len(indices),'type':'SCALAR','min':[min(indices)],'max':[max(indices)]})
    return {**original,'indices':a}

fixed=[]; moving=[]; moving_triangles=0
for p in doc['meshes'][0]['primitives']:
    mat=doc['materials'][p['material']]['name']
    verts=values(p['attributes']['POSITION'],3)
    indices=[x[0] for x in values(p['indices'],1)]
    stationary=[]; drive=[]
    for i in range(0,len(indices),3):
        triangle=indices[i:i+3]; xyz=[verts[q] for q in triangle]
        # Keep the original forged arch and chamber. The circular blade, twelve
        # teeth and axle cap occupy concentric planes in front of that chamber.
        x,y,z=[sum(q[a] for q in xyz)/3 for a in range(3)]
        radius=((x-.03)**2+(y-1.27)**2)**.5
        moving_face=(mat=='HL_metal' and radius<.26 and
                     ((all(-.688<=q[2]<=-.650 for q in xyz) and all((q[0]-.03)**2+(q[1]-1.27)**2<.207**2 for q in xyz)) or all(abs(q[2]+.694)<.0015 for q in xyz))) or (mat in ['HL_dark','HL_orange'] and radius<.077 and z<-.685)
        (drive if moving_face else stationary).extend(triangle)
    if stationary:fixed.append(subset(p,stationary))
    if drive:moving.append(subset(p,drive));moving_triangles+=len(drive)//3
assert moving_triangles==164,moving_triangles
doc['meshes']=[{'name':'CookerWorkshop','primitives':fixed},{'name':'OriginalSaw','primitives':moving}]
pivot=[.03,1.27,-.669]
doc['nodes']=[{'name':'CookerWorkshop','mesh':0,'children':[1]},{'name':'SawAxle','translation':pivot,'children':[2]},{'name':'OriginalSaw','mesh':1,'translation':[-x for x in pivot]}]
doc['buffers'][0]['byteLength']=len(data)
head=json.dumps(doc,separators=(',',':')).encode();head+=b' '*(-len(head)%4);data+=b'\0'*(-len(data)%4)
args.output.write_bytes(struct.pack('<4sIII4s',b'glTF',2,len(data)+len(head)+28,len(head),b'JSON')+head+struct.pack('<I4s',len(data),b'BIN\0')+data)
