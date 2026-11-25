"""Editable orthographic section diagram from exact fixture geometry; not a Blender render."""
import numpy as np
from pathlib import Path
p=Path(__file__).parent
a=np.load(p/'editable_seam_bearing_landmarks.npz')
text=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="760" viewBox="0 0 1080 760">','<rect width="1080" height="760" fill="#162334"/>','<text x="26" y="36" fill="#fff" font-family="sans-serif" font-size="23">Character 1 | exact compact contact-seam layout (diagnostic)</text>']
pal=['#f8c173','#9ecaff','#ffa8b2']
def poly(pts,stroke,fill='none',width=1.6,closed=True):
 xy=' '.join(f'{u:.3f},{v:.3f}' for u,v in pts)
 return f'<{"polygon" if closed else "polyline"} points="{xy}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
for y,side in enumerate('RL'):
 shaft=a[f'{side}_compatible_shaft_face']; c=shaft.mean(0);q=a[f'{side}_guide_vertices'];qedges=a[f'{side}_guide_edges'];loops=a[f'{side}_loop_vertices']; off=a[f'{side}_loop_offsets'];patch=a[f'{side}_bearing_patch'][:3]
 u=shaft[1]-shaft[0];u/=np.linalg.norm(u);n=np.cross(u,shaft[2]-shaft[0]);n/=np.linalg.norm(n);v=np.cross(n,u)
 for x,(label,axes) in enumerate((('Palm-in / shaft plane',(u,v)),('Side / bearing normal',(u,n)))):
  ox=28+x*526; oy=62+y*337
  text.extend([f'<rect x="{ox}" y="{oy}" width="506" height="310" rx="12" fill="#22354a"/>',f'<text x="{ox+15}" y="{oy+26}" fill="#fefefe" font-family="sans-serif" font-size="16">{side} · {label}</text>'])
  project=lambda X:(X-c)@np.asarray(axes).T*np.array([1,-1])*1050+np.array([ox+278,oy+168])
  text.append(poly(project(shaft),'#6785a5','#2b4963'))
  for k in range(len(off)-1):text.append(poly(project(loops[off[k]:off[k+1]]),pal[k],width=1.1))
  for j in qedges:text.append(poly(project(q[j]),'#d4dcdf',width=1.5,closed=False))
  text.append(poly(project(patch),'#86edc5','#256d63',width=2.1))
text += ['<text x="28" y="735" fill="#dbe4ee" font-family="sans-serif" font-size="15">Pure geometry: traced source loops and proposed crease guides. Green = finite ideal shaft-face contact patch, not a glove mesh.</text>','</svg>']
(p/'palm-in-and-side-layout.svg').write_text('\n'.join(text)+'\n')
