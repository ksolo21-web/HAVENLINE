#!/usr/bin/env python3
"""T01 revision7: narrow irregular notches, blue rims and warm trunk finish.
Only writes the three reference-forest GLBs and manifest. Previous failed reviews
and all original models remain preserved. Fresh independent review is required.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np
import bake_reference_forest as base
import polish_reference_forest as polish

def materials():
    base.materials()
    image=np.zeros((192,128,3),float)
    palettes=[('81bde9','9dcef0'),('9fd8f3','b7e7fa'),('b5e8fa','d2f4fc')]
    for layer,(bottom,top) in enumerate(palettes):
        for row in range(64):
            t=row/63;color=base.kit.color(top)*(1-t)+base.kit.color(bottom)*t
            edge=np.clip((row-60)/2,0,1)
            image[layer*64+row]=255*(color*(1-edge*.70)+base.kit.color('285886')*edge*.70)
    base.kit.TEX['crown']=(base.png(image),base.kit.TEX['crown'][1])
    for name,lo,hi in [('lip','315b8a','527dac'),('trunk','b66a59','c58067')]:
        rows=np.linspace(0,1,64)[:,None,None]
        arr=(base.kit.color(hi)[None,None,:]*(1-rows)+base.kit.color(lo)[None,None,:]*rows)*255
        base.kit.TEX[name]=(base.png(np.repeat(arr,32,axis=1)),base.kit.TEX[name][1])
    for name in ('crown','lip','trunk'):
        value=list(base.kit.MATS[name]);value[2]=.90;base.kit.MATS[name]=tuple(value)

def conifer(variant):
    m=base.kit.Model(f'pine_{variant}')
    h=[3.30,3.08,3.52][variant-1];width=[1.,.94,1.04][variant-1]
    m.lathe([(0,-.18),(.225,-.18),(.225,-.07),(.19,.065),(.132,.28),(.12,.72),(.045,h*.78),(0,h*.80)],'trunk',sides=18)
    for layer,(bottom,span,radius) in enumerate([(.43,1.26,1.14),(1.11,1.18,.88),(1.91,1.15,.60)]):
        bottom*=h/3.3;span*=h/3.3;radius*=width
        phase=layer*.41+variant*.19;lobes=[10,9,8][layer]
        def crown(u,v):
            a=u*math.tau;cycle=(a*lobes+phase)/math.tau;index=math.floor(cycle);sector=cycle%1
            depth=.205+.052*math.sin(index*2.31+layer*.7+variant*.4)
            halfwidth=.090+.012*math.sin(index*1.79+layer+variant)
            notch=max(0.,1-abs(sector-.5)/halfwidth)**.95
            t=v*(1-depth*notch)
            irregular=1+.024*math.sin(a*3+layer*.7+variant*.33)*t*t
            r=radius*t**.99*(1+.03*math.sin(math.pi*t))*irregular
            y=bottom+span*(1-t)+.028*span*math.sin(math.pi*t)
            return r*math.sin(a),y,r*math.cos(a)
        base.surface(m,crown,120,11,'crown',layer)
        vv,ff,nn,uv=m.parts['crown'][-1];rho=np.linalg.norm(vv[:,[0,2]],axis=1)
        t=np.clip((rho/radius)**(1/.99),1e-5,1)
        dr=radius*(.99*t**(-.01)*(1+.03*np.sin(math.pi*t))+t**.99*.03*math.pi*np.cos(math.pi*t))
        rise=span-.028*span*math.pi*np.cos(math.pi*t)
        norm=np.stack([rise*vv[:,0]/np.maximum(rho,1e-7),dr,rise*vv[:,2]/np.maximum(rho,1e-7)],axis=1)
        norm[rho<1e-7]=[0,1,0];norm/=np.linalg.norm(norm,axis=1)[:,None]
        m.parts['crown'][-1]=(vv,ff,norm.astype(np.float32),uv)
        def underside(u,v):
            a=u*math.tau;outer=np.array(crown(u,1.0));rr=math.hypot(outer[0],outer[2])*(1-v)
            y=outer[1]*(1-v)+(bottom-.082)*v-.022*math.sin(math.pi*v)
            return rr*math.sin(a),y,rr*math.cos(a)
        base.surface(m,lambda u,v:underside(1-u,v),120,3,'lip')
    m.features=['three closed snow mantles with longer narrow irregular V-notches','blue-white three-band snow atlas with thin blue boundary','warm reddish trunk without density-derived blackening','continuous snow geometry and seated closed trunk','same three materials, 9576 triangles and original forest placement','revision7 candidate; no automatic art approval']
    return m

def main():
    materials();records=[]
    for variant in (1,2,3):
        model=conifer(variant);r=model.export();p=base.OUT/(r['name']+'.glb');polish.remove_density_occlusion(p)
        r['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();records.append(r)
        assert r['surfaces']==3 and r['triangles']==9576
    m={'task':'T01','revision':7,'source':'tools/havenline/finish_reference_tree.py','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_assets_modified':False,'independent_visual_approval':False,'physical_4k60_verified':False,'assets':records}
    (base.OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'revision':7,'triangles':sum(r['triangles'] for r in records),'approved':False}))
if __name__=='__main__':main()
