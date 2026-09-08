#!/usr/bin/env python3
"""T01 candidate: authored notched snow-conifers. Original GLBs untouched.
The bake cannot award art, gameplay or physical-device performance approval.
"""
from __future__ import annotations
import hashlib,io,json,math
from pathlib import Path
import numpy as np
from PIL import Image
import bake_environment as kit
OUT=kit.ROOT/'HavenlineGodot/assets/reference_forest'
OUT.mkdir(parents=True,exist_ok=True);kit.OUT=OUT
for name,rgb in [('crown','b8dbef'),('lip','71aacb'),('trunk','99553f')]:
    kit.MATS[name]=('snow',rgb,.92,0.,None)
    color=tuple(int(rgb[i:i+2],16) for i in (0,2,4))
    a=io.BytesIO();Image.new('RGB',(8,8),color).save(a,format='PNG')
    b=io.BytesIO();Image.new('RGB',(8,8),(128,128,255)).save(b,format='PNG')
    kit.TEX[name]=(a.getvalue(),b.getvalue())
def conifer(variant:int):
    m=kit.Model(f'pine_{variant}');h=[3.3,3.0,3.55][variant-1]
    m.tube([(0,0,0),(.015,.27,0),(0,h*.8,.01)],[.16,.13,.028],'trunk',12)
    for j in range(4):
        a=j*math.tau/4+.3
        m.tube([(.04*math.sin(a),.12,.04*math.cos(a)),(.24*math.sin(a),.025,.24*math.cos(a))],[.085,.025],'trunk',8)
    levels=[(.43,1.26,1.14),(1.11,1.18,.88),(1.91,1.15,.60)]
    for layer,(base,span,radius) in enumerate(levels):
        base*=h/3.3;span*=h/3.3;phase=layer*.43+variant*.17;lobes=9+layer
        def crown(u,v):
            a=u*math.tau
            sector=(a*lobes+phase)/math.tau % 1.0
            notch=max(0.0,1.0-abs(sector-.5)/.16)
            r=radius*(v**.98)*(1-.045*notch*v**5)
            lip_lift=.26*span*notch*v**6
            y=base+span*(1-v)+.018*span*math.sin(math.pi*v)+lip_lift
            bend=.035*math.sin(a*2+phase)*v*(1-v)
            return (r*math.sin(a)+bend,y,r*math.cos(a))
        m.patch(crown,72,15,'crown')
        def underside(u,v):
            a=u*math.tau;outer=np.array(crown(u,1.0));r=math.hypot(outer[0],outer[2])
            rr=r*(1-v)
            y=(1-v)*outer[1]+v*(base-.09)-.045*math.sin(math.pi*v)
            return (rr*math.sin(a),y,rr*math.cos(a))
        m.patch(lambda u,v:underside(1-u,v),72,5,'lip')
    m.features=['three overlapping authored V-notched snow crowns','fully closed blue undersides','warm tapered trunk and noncoincident roots','clean blue-white reference palette','no primitive mesh nodes or leaf cards','T01 revision 2 candidate; no visual approval']
    return m
def main():
    records=[conifer(i).export() for i in (1,2,3)]
    manifest={'task':'T01','revision':2,'source':str(Path(__file__).relative_to(kit.ROOT)),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_assets_modified':False,'independent_visual_approval':False,'physical_4k60_verified':False,'assets':records}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'task':'T01','revision':2,'assets':len(records),'triangles':sum(a['triangles'] for a in records),'bytes':sum(a['bytes'] for a in records),'approved':False}))
if __name__=='__main__':main()
