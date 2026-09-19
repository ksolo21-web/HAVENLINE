#!/usr/bin/env python3
"""T01 reference conifers: closed notched crowns, layered snow atlas and seated trunks.

Only assets/reference_forest is written. Original GLBs remain unchanged. Model
construction does not grant visual, task, gameplay or physical-device approval.
"""
from __future__ import annotations
import hashlib, io, json, math
from pathlib import Path
import numpy as np
from PIL import Image
import bake_environment as kit

OUT = kit.ROOT / 'HavenlineGodot/assets/reference_forest'
OUT.mkdir(parents=True, exist_ok=True)
kit.OUT = OUT
REVISION = 3

def png(rgb: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(buffer, format='PNG')
    return buffer.getvalue()

def materials() -> None:
    # One atlas/material for all crown layers: no extra draw calls. Designed
    # broad shade separation follows the reference rather than gritty noise.
    size = 192
    snow = np.zeros((size, 32, 3), dtype=np.float64)
    palettes = [('679acb','83b4df'), ('88b7dd','a4ceee'), ('a9d6f2','c0e6fc')]
    for layer, (low, high) in enumerate(palettes):
        a, b = kit.color(high)*255, kit.color(low)*255
        t = np.linspace(0, 1, 64)[:, None, None]
        snow[layer*64:(layer+1)*64] = a[None,None,:]*(1-t)+b[None,None,:]*t
    lip = np.zeros((64, 32, 3))
    for row in range(64):
        # Blue underside with rounded rim, not an open cone or opaque flat cap.
        t = row/63
        lip[row] = (kit.color('5e87b5')*(1-t)+kit.color('739ec4')*t)*255
    trunk = np.zeros((64,32,3))
    for row in range(64):
        trunk[row] = (kit.color('95473b')*(1-row/63)+kit.color('aa6350')*row/63)*255
    for name, image in [('crown',snow),('lip',lip),('trunk',trunk)]:
        kit.MATS[name] = ('authored_snow_atlas' if name!='trunk' else 'authored_trunk', 'ffffff', .90, 0., None)
        normal = np.empty_like(image);normal[:]=[128,128,255]
        kit.TEX[name] = (png(image),png(normal))

def surface(m, fn, nu, nv, mat, layer=None):
    vertices=[];uv=[];faces=[]
    for j in range(nv+1):
        for i in range(nu+1):
            u,v=i/nu,j/nv
            vertices.append(fn(u,v))
            # Sampling stays inside a palette band, avoiding mip-edge bleed.
            uv.append((u,(layer+(1+v*61)/64)/3 if layer is not None else v))
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i;b=a+1;c=a+nu+1;d=c+1
            faces.extend([(a,c,b),(b,c,d)])
    m.add(vertices,faces,mat,uv=uv)

def conifer(variant: int):
    m=kit.Model(f'pine_{variant}')
    h=[3.30,3.08,3.52][variant-1]
    # Continuous closed flared trunk. The seated base extends below the sampled
    # ground, so slope changes cannot turn small root ends into floating pegs.
    m.lathe([(0,-.18),(.225,-.18),(.225,-.07),(.19,.065),(.132,.28),(.12,.72),(.045,h*.78),(0,h*.80)],'trunk',sides=18)
    widths=[1.,.94,1.04]
    levels=[(.43,1.26,1.14),(1.11,1.18,.88),(1.91,1.15,.60)]
    for layer,(base,span,radius) in enumerate(levels):
        base*=h/3.3;span*=h/3.3;radius*=widths[variant-1]
        phase=layer*.41+variant*.19
        lobes=[10,9,8][layer]
        # Four angular samples per notch plus broad panels. More angular
        # resolution is used at silhouettes; no saw-toothed low-resolution lip.
        nu=120
        def crown(u,v):
            a=u*math.tau
            sector=((a*lobes+phase)/math.tau)%1.0
            notch=max(0.,1.-abs(sector-.5)/.105)
            notch=notch**.90
            # Cut a V out of the conical surface; do not lift the lip into a
            # fluted skirt. All radial samples stay on the same smooth profile.
            edge=1.0-(.115 if layer<2 else .16)*notch
            t=v*edge
            r=radius*t**.99
            y=base+span*(1-t)+.016*span*math.sin(math.pi*t)
            return (r*math.sin(a),y,r*math.cos(a))
        surface(m,crown,nu,11,'crown',layer)
        def underside(u,v):
            a=u*math.tau;outer=np.array(crown(u,1.0))
            rr=math.hypot(outer[0],outer[2])*(1-v)
            y=outer[1]*(1-v)+(base-.082)*v-.022*math.sin(math.pi*v)
            return (rr*math.sin(a),y,rr*math.cos(a))
        surface(m,lambda u,v:underside(1-u,v),nu,3,'lip')
    m.features=['three closed sculpted snow crowns with narrow reference V-notches',
                'authored cool snow gradient atlas with distinct layer shades',
                'thin closed blue undersides, outward surface normals',
                'continuous warm flared trunk seated below sampled ground',
                'three proportion/phase variants; three shared material surfaces',
                'T01 revision 3 candidate, not self-approved']
    return m

def main():
    materials()
    records=[conifer(i).export() for i in (1,2,3)]
    manifest={'task':'T01','revision':REVISION,'source':str(Path(__file__).relative_to(kit.ROOT)),
      'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'original_assets_modified':False,'independent_visual_approval':False,
      'physical_4k60_verified':False,'assets':records}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'task':'T01','revision':REVISION,'assets':len(records),
      'triangles':sum(a['triangles'] for a in records),'bytes':sum(a['bytes'] for a in records),'approved':False}))
if __name__=='__main__':main()
