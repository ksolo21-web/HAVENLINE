from pathlib import Path
import hashlib,json,numpy as np
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parent;P=R.parent; q=P/'hvn-l1-fence-33036-continuous-terminal-footprint-v1'
assert hashlib.sha256((q/'SHA256SUMS').read_bytes()).hexdigest()=='910141edea3f1e3dfd6b642f60b4ac55232bd90a793d6c492d5ff1e1f35c47db'
p=P/'hvn-l1-fence-33036-owner-sized-seam-admission-v1'
src=(p/'section.py').read_text();a={'__file__':str(p/'section.py')};exec(src[:src.index('results={}')],a)
O,A,spec,terrain,bound=[a[k] for k in ('O','A','spec','terrain','bound')]
g=json.loads((q/'result.json').read_text())['joins']
g0=json.loads((p/'result.json').read_text())['joins']
out={};meshes={}
for nb,(run,pname,rem,(aa,bb),ax,sign) in spec.items():
 shape=O[run+'/'+pname]; cap=O[run+'/'+pname+'_icing']
 axis=2 if ax==0 else 0; outward=1 if nb=='SW1' else -1;line=9.8 if nb=='SW1' else -8.25
 root=(shape.min((0,1))+shape.max((0,1)))*.5
 base=shape[:,:,1].min();top=cap[:,:,1].max()
 limit=.14742; az=min(.124, g[nb]['clear_axial_half_shell_between_unchanged_timbers_m']-.002)
 # Convex, broad asymmetric, bevelled twelve-sided mortise blank maximum contour.
 # No re-root: reference offsets from old footprint, its central planted bearing stays exact.
 bz=np.array([[-.70,-1.], [.70,-1.], [1.,-.68],[1.,.72],[.73,1.],[-.73,1.],[-1.,.72],[-1.,-.68]])
 def boundary(f,y):
  u,v=bz[:,0],bz[:,1]
  D=np.empty((len(bz),3));D[:,ax]=root[ax]+u*az*f;D[:,1]=y
  width=(.1468+.130)/2;center=(.1468-.130)/2
  D[:,axis]=line+(center+v*width*f)*outward
  return D
 polys=a['C']['N']['d']['polys']
 body=polys(np.array([boundary(f,y) for f,y in [(1.,base-.04),(1.,base-.002),(1.,base+.92),(.96,top-.18),(.62,top-.085)]]),True)
 # Snow cap independent crown width: do not mechanically apply the rejected 2% expansion.
 crown=polys(np.array([boundary(f,y) for f,y in [(.91,top-.26),(1.,top-.208),(.98,top-.14),(.78,top-.08),(.47,top-.035),(.045,top)]]),True)
 faces=np.r_[body,crown];meshes[nb+'_blank']=body;meshes[nb+'_cap']=crown
 U=ConvexHull(np.unique(body.reshape(-1,3),axis=0)).equations
 groups=O.copy()
 usable={}
 theta=np.arange(16)*np.pi/8
 for b,gg in enumerate(g0[nb]):
  c=np.array(gg['exact_owner_tip_plane_xyz_m']);c[ax]=root[ax]+.021*sign
  d=np.zeros((16,3));d[:,axis]=.05655*np.sin(theta);d[:,1]=.064*np.cos(theta)
  vv=c+d
  rail=float(-(vv@U[:,:3].T+U[:,3]).max())
  # Worst local rope outward, conservatively ask for one axial-centered anchored cap, not actual measured rope ring burial.
  rope= c.copy();rope[axis]=line+outward*g[nb]['terminal_hemp_transport_outer_m']
  rope_margin=float(-(rope@U[:,:3].T+U[:,3]).max())
  usable[str(b)]={'rail_outline_margin_to_blank_bestcase_convex_mm':rail*1000,'rope_outer_control_point_only_margin_mm':rope_margin*1000}
 adjacent={}
 for k,t in O.items():
  if k in (run+'/'+pname,run+'/'+pname+'_icing'):continue
  if not ('post' in k or 'icing' in k or k.startswith('shared_')):continue
  rr=bound(faces,t,[nb]*len(faces),[k]*len(t))
  if rr:adjacent.update(rr)
 y=A[nb][0]; rest=np.array([i for i in range(len(y)) if not any(lo<=i<=hi for lo,hi in rem)])
 stock=bound(faces,y[rest],[nb]*len(faces),['stock_protected']*len(rest))
 out[nb]={'tri_faces':len(faces),'actual_root_still_held_m':root.tolist(),'axial_half_shell_m':az,
  'actual_lane_positive_mm':float((outward*(faces[:,:,axis]-line)).max()*1000),
  'stock_visual_width_guard_mm':147.42,'solid_mortise_not_cut':True,
  'only_best_case_convex_and_control_point_receipt':usable,'protected_unrelated_crossings':adjacent,
  'trimmed_stock_protected_crossings':stock,
  'base_boundary_terrain_samples_m':[float(a['C']['ctx']['height'](v[[0,2]])) for v in boundary(1.,base)]}
(R/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out))
v=['# HOLD maximum asymmetric blank contour, not owner-approved socket, no material or gameplay.'];i=1
for k,t in meshes.items():
 v.append('o '+k)
 for f in t:
  for z in f:v.append('v '+' '.join(f'{n:.9f}' for n in z))
  v.append(f'f {i} {i+1} {i+2}');i+=3
(R/'AsymmetricMortiseBlank_HOLD.obj').write_text('\n'.join(v)+'\n')
