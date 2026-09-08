#!/usr/bin/env python3
"""T01 R8: authored asymmetric folded snow mantles from actual reference pixels.
Three closed meshes, unchanged material count, placement, gameplay and originals.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np
import bake_reference_forest as base
import finish_reference_tree as prior
import polish_reference_forest as polish

def conifer(variant):
    m=base.kit.Model(f'pine_{variant}')
    h=[3.30,3.08,3.52][variant-1];width=[1.,.94,1.04][variant-1]
    m.lathe([(0,-.18),(.21,-.18),(.21,-.07),(.19,.065),(.132,.28),(.12,.72),(.045,h*.78),(0,h*.80)],'trunk',sides=18)
    for layer,(bottom,span,radius) in enumerate([(.43,1.26,1.14),(1.11,1.18,.88),(1.91,1.15,.60)]):
        bottom*=h/3.3;span*=h/3.3;radius*=width
        phase=layer*.63+variant*.24;lobes=[10,9,8][layer]
        tip=np.array([-.16*span,.0,.055*span])*(1 if variant==1 else (-.65 if variant==2 else .85))
        def underlying(u,t):
            a=u*math.tau
            shape=1.+(.065*math.sin(a*3+phase)+.022*math.sin(a*5-phase))*t*t
            lobe=1.+.038*math.cos(a*lobes+phase)*t**3
            r=radius*t**.83*(1.+.030*math.sin(math.pi*t))*shape*lobe
            offset=tip*(1-t)**1.35
            y=bottom+span*(1-t)+.040*span*math.sin(math.pi*t)+.024*span*math.sin(a*3+phase)*t**3
            return np.array([r*math.sin(a)+offset[0],y,r*math.cos(a)+offset[2]])
        def edge(u):
            a=u*math.tau;cycle=(a*lobes+phase)/math.tau;index=math.floor(cycle);sector=cycle%1
            depth=.25+.055*math.sin(index*2.31+layer*.7+variant*.4)
            halfwidth=.065+.013*math.sin(index*1.79+layer+variant)
            notch=max(0.,1-abs(sector-.5)/halfwidth)**.90
            return 1-depth*notch
        def crown(u,v):return underlying(u,v*edge(u))
        base.surface(m,crown,120,11,'crown',layer)
        verts,faces,normals,uv=m.parts['crown'][-1];result=[]
        for j in range(12):
            for i in range(121):
                u=i/120;t=(j/11)*edge(u)
                if t<1e-6:result.append([0,1,0]);continue
                e=1e-4
                da=underlying(u+e,t)-underlying(u-e,t)
                dt=underlying(u,min(t+e,1))-underlying(u,max(t-e,0))
                normal=np.cross(dt,da);normal/=max(np.linalg.norm(normal),1e-12)
                result.append(normal)
        m.parts['crown'][-1]=(verts,faces,np.array(result,dtype=np.float32),uv)
        def underside(u,v):
            outer=crown(u,1.)
            return outer*(1-v)+np.array([0,bottom-.082,0])*v-np.array([0,.018*math.sin(math.pi*v),0])
        base.surface(m,lambda u,v:underside(1-u,v),120,3,'lip')
    m.features=['asymmetric leaning apex and broad folded snow branch mantles','irregular narrow deep V incisions matching source trees','smooth normals of the actual curved mantle surface','closed underside joins and seated trunk','three surfaces; original forest, resources and other models untouched','R8 candidate; no independent approval assigned']
    return m

def main():
    prior.materials();records=[]
    for i in (1,2,3):
        r=conifer(i).export();p=base.OUT/(r['name']+'.glb');polish.remove_density_occlusion(p)
        r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();records.append(r)
        assert r['triangles']==9576 and r['surfaces']==3
    manifest={'task':'T01','revision':8,'source':'tools/havenline/sculpt_reference_tree.py','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_assets_modified':False,'independent_visual_approval':False,'physical_4k60_verified':False,'assets':records}
    (base.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'revision':8,'triangles':sum(r['triangles'] for r in records),'approved':False}))
if __name__=='__main__':main()
