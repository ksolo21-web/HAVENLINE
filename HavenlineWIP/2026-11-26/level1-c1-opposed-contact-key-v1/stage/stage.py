"""Author one new source-bound opposed-contact diagnostic key; never an animation."""
import json
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import root
from scipy.spatial import ConvexHull
from source_inputs import sources,ground,FRESH,STOCK,sha,HASHES
from pathlib import Path
import os,sys
support_source=Path(os.environ['HAVENLINE_ARCHIVED_GROUND_SUPPORT']).resolve()
assert sha(support_source) == 'c835f8b27cf2e49cbc0f41efdeadb280a678d3f378e72bde2fcabbdff7385973'
sys.path.append(str(support_source.parent))
from support import connected

origin,base,S,cam,basis,V,F=sources()
tags=np.unique(np.round(V,6),axis=0,return_inverse=True)[1]
R=json.loads((FRESH/'rig.LOCAL.json').read_text()); N=R['new_bones']; slots=R['weighted_slots']
G={k:np.asarray(v['global_bind']) for k,v in N.items()}
inv=np.stack([np.linalg.inv(G[k]) for k in slots])
def at(k):return G[k][:3,3]
SK=np.load(FRESH/'skin.LOCAL.npz'); J=SK['joints']; W=SK['weights'].astype(float)
X=np.column_stack((V,np.ones(len(V))))
def weight(k):return np.where(J==slots.index(k),W,0).sum(1)
def homogeneous(R,a,b):
 M=np.eye(4);M[:3,:3]=R;M[:3,3]=b-R@a;return M
def swing(a,b):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
 c=np.cross(a,b)
 return Rotation.from_rotvec(c/np.linalg.norm(c)*np.arctan2(np.linalg.norm(c),a@b)).as_matrix()
def radians(a):return Rotation.from_euler('x',a,degrees=True).as_matrix()
roles={'L':'Heel','R':'Ball'}
# Single new starting design: shallow visible heel/forefoot emphasis, equal
# 43mm opposed physical footprint centers (not old ankle offsets).
angles={'L':[-1.3,0.0],'R':[1.8,-.8]}
offsets={'L':.043,'R':-.043}
bounds={}
for s,k in roles.items():
 sg=1 if s=='L' else -1
 leg=(sg*(V[:,0]-.014)>.038)&(V[:,1]<at(s+'Shin')[1]-.048)
 minY=V[leg,1].min()
 physical=(V[:,1]<minY+.023)&leg&(weight(s+k)>.96)
 faces=F[physical[F].all(1)]
 assert len(faces)>20
 low=physical & (V[:,1]<minY+.001)
 # A real original vertex nearest the signed physical contact core median.
 ids=np.flatnonzero(low);med=np.median(V[ids],axis=0); idx=int(ids[np.linalg.norm(V[ids]-med,axis=1).argmin()])
 target=np.array([base[0]+V[idx,0]*S,0.,origin[2]+offsets[s]])
 target[1]=ground(*target[[0,2]])
 bounds[s]=dict(role=k,leg=leg,physical=physical,faces=faces,anchor=idx,target=target)
# Convert actual marker position from the contact-role differential to heel
# target; no visual pose or old C1 motion samples are used.
def ankle(s,drop):
 a=V[bounds[s]['anchor']].astype(float);heel=at(s+'Heel');ball=at(s+'Ball')
 hr=radians(angles[s][0]); br=radians(sum(angles[s]))
 marker=hr@(a-heel) if roles[s]=='Heel' else hr@(ball-heel)+br@(a-ball)
 return (bounds[s]['target']-base)/S-marker+np.array([0,drop/S,0])
# Measured closed hip-to-ankle reach, keep an 11mm straightening reserve
# at the harder side before any source skinning test. This is a control
# restraint, not a statement of ground-contact pass.
def pelvic(h):
 margins=[]
 for k,q in h.items():
  a,kn,he=(at(k+n) for n in ('Hip','Shin','Heel'))
  cap=np.linalg.norm(kn-a)+np.linalg.norm(he-kn)-.011/S
  h2=cap**2-(a[0]-q[0])**2-(a[2]-q[2])**2
  if h2<=0:raise ValueError('No feasible opposed anchors keep hip reach guard.')
  margins.append((q[1]-a[1]+np.sqrt(h2))*S)
 return min(margins)
def driver(drops):
 H={s:ankle(s,drop) for s,drop in zip('LR',drops)}
 pelvis=pelvic(H);off=np.array([0,pelvis/S,0])
 C={'Pelvis':homogeneous(np.eye(3),[0,0,0],off)@G['Pelvis']}
 margins={}
 for s,q in H.items():
  a,k,b,t=(at(s+n) for n in ('Hip','Shin','Heel','Ball'))
  A0=np.linalg.norm(k-a);B0=np.linalg.norm(b-k); d=np.linalg.norm(q-a-off); u=(q-a-off)/d
  assert abs(A0-B0)<d<A0+B0
  margins[s]=(A0+B0-d)*S
  z=np.array([0.,0.,1.]); z-=u*(u@z); z/=np.linalg.norm(z)
  px=(A0*A0-B0*B0+d*d)/(2*d)
  K=a+off+u*px+z*np.sqrt(A0*A0-px*px)
  R0=swing(k-a,K-a-off); R1=swing(b-k,q-K)
  hroll=radians(angles[s][0]); broll=radians(sum(angles[s]))
  collar=R1@Rotation.from_rotvec(Rotation.from_matrix(R1.T@hroll).as_rotvec()*.5).as_matrix()
  T=q+hroll@(t-b); n0=at(s+'CollarFlex')
  for n,R,bb,tt in [('Hip',R0,a,a+off),('Shin',R1,k,K),('Heel',hroll,b,q),
      ('CollarFlex',collar,n0,K+R1@(n0-k)),('Ball',broll,t,T)]:
   C[s+n]=homogeneous(R,bb,tt)@G[s+n]
 Ts={}
 for n,m in N.items():
  pa=m['parent']
  Ts[n]=C.get(n,G[n] if pa is None else Ts[pa]@np.asarray(m['local_bind']))
 assert np.array_equal(Ts['Root'],G['Root'])
 transform=np.stack([Ts[k] for k in slots])@inv
 Y=sum((transform[J[:,i]]@X[:,:,None])[:,:3,0]*W[:,i,None] for i in range(4))*S+base
 return Y,Ts,pelvis,margins
def distance(x,inds):
 return np.array([a[1]-ground(*a[[0,2]]) for a in x[inds]])
def f(d):
 p,*_=driver(d)
 return np.array([distance(p,np.flatnonzero(bounds[s]['leg'])).min()-.00015 for s in 'LR'])
optim=root(f,[.006,.003],tol=1e-9)
drops=optim.x
if np.max(np.abs(f(drops)))>1e-7 or np.max(np.abs(drops))>.015:raise ValueError('Cannot ground both complete boots under signed key limits.')
P,Xfit,pelvis,margins=driver(drops)
points=[];contact={}
for s in 'LR':
 b=bounds[s];p=P[b['anchor']]; leg=b['leg']; phys=b['physical']
 # Count physical coverage and connected source faces intersecting inclusive
 # -1/+2mm contact band, including non-vertex crossings.
 surf=P[:,[0,2,1]].copy()
 surf[leg,2]=distance(P,leg)
 k=connected(surf,b['faces'],tags)
 low=np.abs(surf[:,2]-.0005)<=.0015
 pts=P[phys&low][:,[0,2]]
 points.extend(pts.tolist())
 contact[s]=dict(role=b['role'],source_contact_row=b['anchor'],source_bound_snow_target=b['target'].tolist(),
                actual_marker_world=p.tolist(),mantained_marker_xz_residual_m=float(np.max(np.abs(p[[0,2]]-b['target'][[0,2]]))),
                actual_marker_ground_distance_m=float(p[1]-ground(*p[[0,2]])),
                whole_boot_floor_min_m=float(surf[leg,2].min()),support=k,
                measured_indexed_snow=ground(*b['target'][[0,2]],True)[1])
support=np.asarray(points); hull=ConvexHull(support)
center=(Xfit['Pelvis'][:3,3]*S+base)[[0,2]]
margin=float(-np.max(hull.equations@np.r_[center,1]))
camera=str(sha(STOCK/'previews/integrated_opening.gd'))
assert all(margins[s]>.01099999 for s in 'LR')
out=dict(source_commit='11c14a1c41971067c7dc97db69375f720a408f68',source_input_manifest_sha256=sha('SOURCE-SHA256SUMS'),
  current_art_and_clean_rig={'original_glb':sha(STOCK/'assets/characters/Character1.glb'),**HASHES},stock_scene_script_sha256=camera,
  stock_spawn_world=origin.tolist(),art_to_world_scale=S,rest_mesh_world_translation=base.tolist(),
  normal_view=dict(viewport=[1280,720],ortho_size=13.,camera_origin_world=cam.tolist(),camera_rows_right_up_back=basis.tolist()),
  key_parameters=dict(foot_roll_art_x_deg=angles,target_contact_center_fore_aft_world_m=offsets,
   root_position_unchanged=True,pelvis_height_offset_world_m=pelvis,hip_extended_reach_reserves_m=margins),
  feet=contact,geometric_pelvis_over_contact_hull=dict(pelvis_center_xz=center.tolist(), signed_margin_inside_m=margin,
   positive_margin_means_inside=True,not_a_body_mass_or_dynamic_balance_claim=True),
  stage_only=True,current_motion_not_approved=True,native_scene_measured=False,full_deformation_and_collision_checks_done=False)
print(json.dumps(out,indent=2))
