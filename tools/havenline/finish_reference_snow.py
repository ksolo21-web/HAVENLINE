#!/usr/bin/env python3
"""T01 revision5: snow volume/finish correction, not unchanged-image rescoring.
Keep existing silhouettes/notches, three materials, triangle count, placement,
player visibility and all original GLBs. Fresh renderer/critic evidence required.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np
import bake_reference_forest as base
import polish_reference_forest as prior

BULGE=.065
EXTRA_RISE=.029

def materials():
    base.materials()
    rows,cols=192,128
    u=np.linspace(0,1,cols)[None,:]
    v=(np.arange(rows)%64)[:,None]/63.0
    nx=.065*np.sin(2*math.pi*3*u+.65*np.cos(math.pi*v))*np.sin(math.pi*v)
    ny=.030*np.sin(2*math.pi*2*v+.4*np.sin(2*math.pi*u))*np.sin(math.pi*v)
    nz=np.sqrt(1-nx*nx-ny*ny)
    normal=np.stack([nx,ny,nz],axis=-1)
    assert np.isfinite(normal).all() and np.max(np.abs(np.linalg.norm(normal,axis=-1)-1))<1e-8
    assert np.ptp(normal[:,:,0])>.10 and np.ptp(normal[:,:,1])>.04
    albedo,_=base.kit.TEX['crown']
    base.kit.TEX['crown']=(albedo,base.png((normal+1)*127.5))
    value=list(base.kit.MATS['crown']);value[2]=.82;base.kit.MATS['crown']=tuple(value)

def conifer(variant):
    model=base.conifer(variant)
    height=[3.30,3.08,3.52][variant-1];width=[1.,.94,1.04][variant-1]
    for material in ('crown','lip'):
        parts=[]
        for layer,(v,f,n,uv) in enumerate(model.parts[material]):
            radius=[1.14,.88,.60][layer]*width;span=[1.26,1.18,1.15][layer]*height/3.3
            rho=np.linalg.norm(v[:,[0,2]],axis=1);t=np.clip((rho/radius)**(1/.99),0,1)
            vv=v.copy();vv[:,[0,2]]*=1+BULGE*np.sin(math.pi*t)[:,None]
            vv[:,1]+=EXTRA_RISE*span*np.sin(math.pi*t)
            if material=='crown':
                tt=np.maximum(t,1e-5)
                dr=radius*(.99*tt**(-.01)*(1+BULGE*np.sin(math.pi*tt))+tt**.99*BULGE*math.pi*np.cos(math.pi*tt))
                rise=span-(.016+EXTRA_RISE)*span*math.pi*np.cos(math.pi*tt)
                nn=np.stack([rise*v[:,0]/np.maximum(rho,1e-7),dr,rise*v[:,2]/np.maximum(rho,1e-7)],axis=1)
                nn[rho<1e-7]=[0,1,0];nn/=np.linalg.norm(nn,axis=1)[:,None]
                parts.append((vv,f,nn.astype(np.float32),uv))
            else:
                tmp=base.kit.Model('normal_builder');tmp.add(vv,f,material,uv=uv);parts+=tmp.parts[material]
        model.parts[material]=parts
    model.features += ['revision5 softly convex snow volume rather than planar cone flanks','authored continuous low-amplitude snow relief normal atlas','snow roughness 0.82 with existing nonmetallic shading','original notch rims and closed underside joins preserved','no random surface noise, leaf cards, new draw surfaces or extra triangles']
    return model

def main():
    materials();records=[]
    for variant in (1,2,3):
        model=conifer(variant);record=model.export();path=base.OUT/(record['name']+'.glb')
        prior.remove_density_occlusion(path)
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();records.append(record)
        assert record['triangles']==9576 and record['surfaces']==3
    manifest={'task':'T01','revision':5,'source':'tools/havenline/finish_reference_snow.py','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base_geometry_sha256':hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest(),'original_assets_modified':False,'independent_visual_approval':False,'physical_4k60_verified':False,'assets':records,'material_repair_checks':{'unit_continuous_normal_map':True,'nonflat_authored_normal_map':True,'three_materials_and_triangle_budget_preserved':True}}
    (base.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'task':'T01','revision':5,'assets':3,'triangles':sum(r['triangles'] for r in records),'approved':False}))
if __name__=='__main__':main()
