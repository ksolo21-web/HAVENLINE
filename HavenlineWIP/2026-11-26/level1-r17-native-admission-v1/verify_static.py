from pathlib import Path
import json, sys, subprocess, hashlib, re
p=Path(sys.argv[1]).resolve()
here=Path(__file__).resolve().parent
q=p/'previews'/'r17_fence'
pins={'boundary_v2.mtl':'c9fdad18392bf29a4122ba33203779b5bf52a40b',
      'fence_panel.obj':'2d6d52190f27df276624ef1dfb00898d3a708041',
      'gate_post.obj':'dc678ac587151aae882dc728523b18545734723d',
      't03_boundary_v2.gdshader':'0d0498d041b5bfeed8665ce8558ea550a2effd07'}
def blob(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
for name,digest in pins.items():
    assert blob((q/'assets'/name).read_bytes())==digest
    assert (q/'assets'/name).read_bytes()==(here/'assets'/name).read_bytes()
for name in ('r17_fence_view.gd','r17_fence_view.tscn'):
    assert (q/name).read_bytes()==(here/name).read_bytes()
with (p.parent/'final.sha256').open() as manifest:
    subprocess.run(['sha256sum','-c','--status','-'],stdin=manifest,cwd=p,check=True)
def obj(name):
    l=(q/'assets'/name).read_text().splitlines()
    verts=[tuple(map(float,x.split()[1:])) for x in l if x.startswith('v ')]
    faces=[x for x in l if x.startswith('f ')]
    assert all(len(x.split())==4 for x in faces)
    assert [x for x in l if x.startswith('mtllib ')] == ['mtllib boundary_v2.mtl']
    return [min(a) for a in zip(*verts)], [max(a) for a in zip(*verts)], len(faces), sorted({s.split()[1] for s in l if s.startswith('usemtl ')})
pmin,pmax,pt,pm=obj('fence_panel.obj')
smin,smax,st,sm=obj('gate_post.obj')
assert (pt,st,pm,sm)==(640,176,['snow','timber'],['orange','snow','timber'])
assert pmin==[-1.47045,0.0,-.0806] and pmax==[1.47045,1.465,.0706]
assert smin==[-.168,0.0,-.1724] and smax==[.168,1.605,.168]
walls=json.loads((p/'layout.json').read_text())['walls_xz']
widths = [max(*row[2:]) for row in walls]
counts = [2,2,1,1,3,3]
assert widths==[3.9,3.9,2.8,2.8,10,8]
lens=[[w/n + .006*((j>0)+(j+1<n)) for j in range(n)] for w,n in zip(widths,counts)]
assert all(1.95<=x<=3.55 for row in lens for x in row)
assert (pmax[2]-pmin[2])*1.95 < .30
assert .19616-smax[0]*1.12>.00799
assert 'main_scene="res://opening.tscn"' in (p/'project.godot').read_text() or 'run/main_scene="res://opening.tscn"' in (p/'project.godot').read_text()
print(json.dumps({'candidate':'assets and authored footprints only; no engine','baseline_files_verified':130,
 'draw_triangles':sum(counts)*pt+4*st,'panel_count':sum(counts),'post_count':4,
 'batches':2,'expected_material_surfaces':5,'panel_breadth_m':(pmax[2]-pmin[2])*1.95,
 'panel_lengths_m':lens,'post_clear_span_m':2*(1.2+.19616-.168*1.12),
 'stock_visual_gate_leaves':True,'gate_leaf_swing_visual_check':'pending native',
 'grounding':'uses exact Terrain.sample; pending draw and run','source_git_blobs':pins},indent=2))
