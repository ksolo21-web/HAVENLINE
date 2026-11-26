"""Exact source upper seam and reserved-area evidence; drawing only."""
from pathlib import Path
from xml.sax.saxutils import escape
from collections import defaultdict
import hashlib,json,sys
import numpy as np
P=Path(__file__).resolve().parent.parent
S=P/'hvn-l1-c1-stock66-co-design-boundary-v1'
A=P/'hvn-pad-mount-admission/isolated-source/HavenlineLevel1/assets/characters/Character1.glb'
sh=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sh(S/'SHA256SUMS')=='77b6f55115cbe83652340b6300f71766cd2a0db074bf58206bf5706f93f1f0de'
for l in (S/'SHA256SUMS').read_text().splitlines():
 h,n=l.split('  ',1);assert sh(S/n)==h
obj=json.loads((S/'result.json').read_bytes()); k=obj['custody']['both_sides']
src=P/'hvn-c1-fastener-mounts/inspect_source.py'
sys.path.insert(0,str(src.parent))
from inspect_source import load,weld
d,V,N,UV,J,W,F=load(A)
rep,idx=weld(V)
X=V[rep].astype(float)*1000
art=V.astype(float)*1000
results={}
out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1060 942" role="img" aria-label="Character 1 stock lower-garment ring engineering drawing, no artwork or design approval">','<rect width="1060" height="942" fill="#101d2e"/>']
def txt(x,y,label,size=15,c='#d9e4f0',w=400):
 out.append(f'<text x="{x}" y="{y}" fill="{c}" font-family="system-ui,sans-serif" font-size="{size}" font-weight="{w}">{escape(label)}</text>')
def line(x,y,x2,y2,c,width=1.2,dash=''):
 out.append(f'<path d="M{x} {y}L{x2} {y2}" fill="none" stroke="{c}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def poly(points,c,width=1.4):
 out.append('<polyline points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in points)+f'" fill="none" stroke="{c}" stroke-width="{width}" stroke-linejoin="round"/>')
def frame(x,y,w,h):
 out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#172a3e" stroke="#36506b"/>')
txt(35,43,'Character 1 — protected lower-leg interface',29,'#f1f6ff',700)
txt(36,72,'Source survey • two exact outer ring loops • proposed internal requirements are NOT construction',15,'#a9bfd7')
for j,side in enumerate('LR'):
 p=obj['summary'][side]; item=k[side]; owned=set(item['owned_source_face_ids']); rim=item['cut_edge_face_and_directions']
 forward={}
 for a,b,*faces in rim:
  own,=[v for v in faces if v[0] in owned]
  other,=[v for v in faces if v[0] not in owned]
  assert own[1:]==other[1:][::-1]
  aa,bb=own[1:];assert aa not in forward;forward[aa]=bb
 start=min(forward);raw=[start]; v=start
 while (v:=forward[v])!=start:
  assert v not in raw
  raw.append(v)
 assert len(raw)==len(forward)==p['cut_rim_edges']
 loop=X[raw];closed=np.r_[loop,loop[:1]]
 owned_xyz=art[np.unique(F[list(owned)].ravel())]
 h=p['near_hem_and_source_ownership']['near_hem_band_art_y_mm']
 hardware={}
 for n,w in item['hardware'].items():
  face=np.array(w['core_face_ids']); coords=art[F[face]]
  center=coords.mean((0,1))
  hardware[n]={'survey_core_centroid_art_mm_NOT_anchor':center.tolist(),
     'scope_AABB_art_mm_NOT_attachment_envelope':np.stack([coords.min((0,1)),coords.max((0,1))]).tolist(),
     'exact_existing_core_faces':len(face),'exact_open_edge_perimeter':w['core_open_rim_edges']}
 results[side]=dict(ordered_weld_ring=raw,ring_xyz_original_art_mm=loop.tolist(),
   coordinate_bounds_ring_art_mm=np.stack([loop.min(0),loop.max(0)]).tolist(),
   exterior_owned_bounding_box_art_mm=np.stack([owned_xyz.min(0),owned_xyz.max(0)]).tolist(),
   exact_original_protected_neighbor_from_source_side_sha=p['protected_source_face_segment_bytes_sha256'],
   immutable_source_alias_rows=p['cut_source_alias_rows'], protected_neighbor_faces=p['protected_face_rings_both_sides'],
   reference_visual_hardware_areas_hypothetical_attachments_unlocated=hardware,
   authorization_or_new_topology=False)
 xx=36+j*510
 frame(xx,102,476,348)
 txt(xx+19,136,f'{"Left" if side=="L" else "Right"} • exact ring survey',22,'#f1f6ff',700)
 txt(xx+19,160,'Projection X–Z in source art coordinates (not a footprint)',13,'#a9bfd7')
 scale=1.3; qx,qz=loop.mean(0)[[0,2]]
 center=np.array([xx+237,277])
 coords=center+np.c_[closed[:,0]-qx,-(closed[:,2]-qz)]*scale
 poly(coords,'#64d8d2',2.15)
 line(xx+65,386,xx+123,386,'#8cb1cf',1.25);line(xx+65,386,xx+65,335,'#8cb1cf',1.25)
 txt(xx+128,391,'+X',11);txt(xx+54,329,'+Z',11)
 dx,dz=np.ptp(loop,axis=0)[[0,2]]
 txt(xx+18,423,f'{len(raw)} exactly mated edges  •  {dx:.2f} × {dz:.2f} art-mm span  •  protected faces: {p["protected_face_rings_both_sides"]}',13)
frame(36,475,986,218)
txt(60,508,'SECTION REQUIREMENTS — conceptual; NOT to scale or approved',19,'#ffd27d',700)
txt(60,538,'A   Keep the exact outer ring and the two neighboring face rings on both sides byte-for-byte.',15)
txt(60,568,'B   Preserve the continuous exterior outsole; any internal lining needs a measured usable thickness.',15)
txt(60,598,'C   Fastener underside and seat must be a physical pair, not a copied shell or guessed cap.',15)
txt(60,628,'D   Show clearance at rest and under one permitted contact load before animating a gait.',15)
txt(60,657,'No geometry, proposed anchoring point, contact pose or attachment has been created.',14,'#f2aa93',600)
frame(36,714,986,196)
txt(60,747,'Proposed interface logic — symbols only',19,'#ffd27d',700)
# Symbolic relationship only; deliberately no exact anchors or panel shape.
line(70,774,260,774,'#64d8d2',3)
line(70,774,70,858,'#64d8d2',3)
line(70,858,260,858,'#64d8d2',3)
line(112,801,228,801,'#ffd27d',2,'7 6')
line(112,841,228,841,'#ffd27d',2,'7 6')
line(228,801,228,841,'#ffd27d',2,'7 6')
out.append('<circle cx="170" cy="821" r="6" fill="#101d2e" stroke="#f2aa93" stroke-width="2"/>')
txt(289,779,'SOLID TEAL   existing visible exterior invariants',14,'#64d8d2',600)
txt(289,812,'DASHED GOLD   hypothetical independent liner / attachment backing',14,'#ffd27d',600)
txt(289,847,'OPEN SYMBOL   unknown anchor: no measured underside, thickness, or clearance',14,'#f2aa93',600)
txt(61,889,'Not an outline of the real boot; no dimensions, layer material, capture, or attachment position implied.',13,'#a9bfd7')
out.append('</svg>')
if sys.argv[1:]==['--svg']:print('\n'.join(out))
else:
 assert not sys.argv[1:]
 print(json.dumps(dict(source_tag='stock66 95e4fed3 original unchanged; art-mm not game length',source_outer_custody=results,
    no_character_edit=True,no_new_geometry=True,reference_partitions='77b6f551'),indent=2))
