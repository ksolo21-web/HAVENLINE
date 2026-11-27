"""Measure the unobstructed opening in the fitted GLB, in metres.
Usage: python check-clearance.py <connected_storehouse.glb>. Requires NumPy.
"""
import json
import struct
import sys
from pathlib import Path
import numpy as np
b=Path(sys.argv[1]).read_bytes()
size=struct.unpack_from('<I',b,12)[0]
j=json.loads(b[20:20+size])
buf=b[28+size:]
def access(idx):
    a=j['accessors'][idx]
    v=j['bufferViews'][a['bufferView']]
    i=v.get('byteOffset',0)
    dtype={5126:'<f4',5123:'<u2'}[a['componentType']]
    return np.frombuffer(buf[i:i+v['byteLength']],dtype).reshape(a['count'],-1)
res={}
for node in j['nodes']:
    if node['name'] not in ('UtilityDockFrame','FoodDockFrame'):
        continue
    mesh=j['meshes'][node['mesh']]['primitives'][0]
    v=access(mesh['attributes']['POSITION'])
    faces=v[access(mesh['indices']).reshape(-1,3)]
    # Goods travel longitudinally along local Z. The widest live raw resource
    # measures 0.354 m across after the ordinary transit normalization.
    overlap=(faces[:,:,0].max(1)>-.18)&(faces[:,:,0].min(1)<.18)
    ceiling=float(faces[overlap,:,1].min())
    assert ceiling >= .35,node['name']
    res[node['name']]={'least_height_over_central_.36m':ceiling,
        'width_m':float(np.ptp(v[:,0])),'depth_m':float(np.ptp(v[:,2]))}
assert len(res)==2
print(json.dumps(res,indent=2))
