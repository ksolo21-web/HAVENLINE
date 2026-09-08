#!/usr/bin/env python3
"""T01 revision 4. Smooth reference crowns without changing topology or other GLBs.
Analytic normals prevent notched tessellation from perturbing the conical surface.
Remove vertex-density-dependent crown occlusion; retain directional/contact shadows
and the authored three-band snow atlas. Same three surfaces and triangle budget.
"""
from __future__ import annotations
import hashlib,json,math,struct
from pathlib import Path
import numpy as np
import bake_reference_forest as base

def smooth_crowns(model,variant):
    h=[3.30,3.08,3.52][variant-1];width=[1.,.94,1.04][variant-1]
    spans=[1.26,1.18,1.15];radii=[1.14,.88,.60];parts=[]
    for layer,(v,f,n,uv) in enumerate(model.parts['crown']):
        rho=np.linalg.norm(v[:,[0,2]],axis=1)
        radius=radii[layer]*width;span=spans[layer]*h/3.3
        t=np.clip((rho/radius)**(1/.99),1e-5,1)
        dr=.99*radius*t**(-.01)
        rise=span-.016*span*math.pi*np.cos(math.pi*t)
        normal=np.stack([rise*v[:,0]/np.maximum(rho,1e-7),dr,rise*v[:,2]/np.maximum(rho,1e-7)],axis=1)
        normal[rho<1e-7]=[0,1,0];normal/=np.linalg.norm(normal,axis=1)[:,None]
        parts.append((v,f,normal.astype(np.float32),uv))
    model.parts['crown']=parts
    model.features+=['revision4 analytic crown normals independent of notch tessellation','uniform crown vertex tint: no point-density occlusion bands']

def remove_density_occlusion(path):
    data=bytearray(path.read_bytes());jl=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+jl]);binary_start=20+jl+8
    for primitive in doc['meshes'][0]['primitives']:
        if doc['materials'][primitive['material']]['name']!='crown':continue
        acc=doc['accessors'][primitive['attributes']['COLOR_0']];view=doc['bufferViews'][acc['bufferView']]
        assert acc['componentType']==5126 and acc['type']=='VEC4'
        start=binary_start+view.get('byteOffset',0)+acc.get('byteOffset',0)
        data[start:start+acc['count']*16]=np.ones((acc['count'],4),dtype='<f4').tobytes()
    path.write_bytes(data)

def main():
    base.materials();records=[]
    for variant in (1,2,3):
        model=base.conifer(variant);smooth_crowns(model,variant)
        record=model.export();path=base.OUT/(record['name']+'.glb');remove_density_occlusion(path)
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();records.append(record)
    manifest={'task':'T01','revision':4,'source':'tools/havenline/polish_reference_forest.py','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base_geometry_source_sha256':hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest(),'original_assets_modified':False,'independent_visual_approval':False,'physical_4k60_verified':False,'assets':records}
    (base.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'revision':4,'assets':len(records),'triangles':sum(r['triangles'] for r in records),'approved':False}))
if __name__=='__main__':main()
