"""Verify exact static geometry and sufficient continuous sweep against two threshold profiles."""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import json
import numpy as np
import sys
root=Path(__file__).resolve().parent
C=root/'candidate'
prior=root.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()
pins=(('hvn-l1-timber-leaf-hinge-redesign-v1','bc25a6d1323e50ae480cf1690318e39411dbd64ca4d37bd889b6e643ac791911'),
      ('hvn-l1-gate-art-admission-protocol','65aa400c4e8639953f29b3607ed51a40ed08312cefa50f3812165a98b5a4f3f0'))
for name,h in pins:
 f=prior/name; assert sha(f/'SHA256SUMS')==h
 for line in (f/'SHA256SUMS').read_text().splitlines():
  x,p=line.split(maxsplit=1); assert sha(f/p)==x
r=json.loads((prior/pins[0][0]/'result.json').read_text())
seat=json.loads((prior/pins[1][0]/'result.json').read_text())['results']
def read(p):
 v=[];faces=[];gn=[];ms=[];fc={};direct={}
 for l in p.read_text().splitlines():
  s=l.split()
  if not s:continue
  if s[0]=='v':v.append(list(map(float,s[1:])))
  if s[0]=='g':g=s[1];fc[g]=Counter();direct[g]=Counter()
  if s[0]=='usemtl':m=s[1]
  if s[0]=='f':
   f=[int(k)-1 for k in s[1:]]; assert len(f)==3 and len(set(f))==3
   faces.append(f);gn.append(g);ms.append(m)
   for a,b in zip(f,f[1:]+f[:1]):
    i,j=sorted((a,b));fc[g][(i,j)]+=1; direct[g][(i,j)]+=1 if a==i else -1
 xyz=np.array(v); t=xyz[faces];gn=np.array(gn)
 assert np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1).min()>1e-9
 for g in fc:
  assert set(fc[g].values())=={2} and set(direct[g].values())=={0}
  a,b,c=t[gn==g].transpose(1,0,2)
  assert np.einsum('ij,ij->',a,np.cross(b,c))>0,g
 return t,gn,np.array(ms)
L,lg,lm=read(C/'GateLeaf.obj')
R,rg,rm=read(C/'GateLeaf_Right.obj')
U=R[:,[0,2,1],:]*[-1,1,1]
Lbase,lbg,lbm=read(prior/'hvn-l1-gate-owner-33035-v1/candidate/GateLeaf.obj')
retain=set(lbg)-{'center_handle_owned_half','center_handle_rosette'}
assert retain|{'front_handle_rosette','front_handle_owned_bar','rear_owned_knob_dot'} == set(lg)
assert retain|{'front_receiver_keeper','rear_owned_knob_dot'} == set(rg)
for name in retain:
 assert np.array_equal(L[lg==name],Lbase[lbg==name])
 assert np.array_equal(U[rg==name],Lbase[lbg==name])
 assert np.array_equal(lm[lg==name],lbm[lbg==name])
 assert np.array_equal(rm[rg==name],lbm[lbg==name])
assert np.array_equal(L[lg=='rear_owned_knob_dot'],U[rg=='rear_owned_knob_dot'])
assert L[lg=='rear_owned_knob_dot',:,2].max()<-.024
assert U[rg=='rear_owned_knob_dot',:,2].max()<-.024
assert (L[np.char.startswith(lg,'front_'),:,2].min()>0 and U[np.char.startswith(rg,'front_'),:,2].min()>0)
assert all(x not in set(lg)|set(rg) for x in ['rear_x','rear_bar','rear_brace'])
def inside(p,t):
 d=np.array([.337,.491,.661]); e=t[:,1]-t[:,0]; f=t[:,2]-t[:,0]
 h=np.cross(d,f); den=np.einsum('ij,ij->i',e,h); valid=np.abs(den)>1e-12
 e=e[valid]; f=f[valid]; h=h[valid]; den=den[valid]; g=np.asarray(p)-t[valid,0]
 u=np.einsum('ij,ij->i',g,h)/den; q=np.cross(g,e)
 v=q@d/den; a=np.einsum('ij,ij->i',f,q)/den
 hits=(a>1e-9)&(u>1e-9)&(v>1e-9)&(u+v<1-1e-9)
 return np.count_nonzero(hits)%2==1
contacts=[
 (L,lg,'front_handle_rosette','center_stile',[1.077,.681,.055]),
 (L,lg,'front_handle_owned_bar','front_handle_rosette',[1.094,.681,.056]),
 (U,rg,'front_receiver_keeper','center_stile',[1.152,.681,.054]),
 (L,lg,'rear_owned_knob_dot','center_stile',[1.138,.681,-.026]),
 (U,rg,'rear_owned_knob_dot','center_stile',[1.138,.681,-.026])]
for a,g,n,m,p in contacts:
 assert inside(p,a[g==n]) and inside(p,a[g==m]),(n,m)
assert 'Ks 0.105 0.092 0.072' in (C/'owner33035.mtl').read_text()

P,pg,pm=read(C/'ThresholdPost.obj')
PR,rpg,rpm=read(C/'ThresholdPost_Right.obj')
assert np.array_equal(PR,P[:,[0,2,1],:]*[-1,1,1]) and np.array_equal(pg,rpg) and np.array_equal(pm,rpm)
mtl=[l.split()[1] for l in (C/'owner33035.mtl').read_text().splitlines() if l.startswith('newmtl ')]
assert set(mtl)==set(lm)|set(pm)
E=np.concatenate([L,U],axis=0)
lo,hi=E.min((0,1)),E.max((0,1))
assert np.all(lo>=[0.007,.074,-.066]) and np.all(hi<=[1.178,1.336,.069])
assert all(L[np.array([x.startswith('front_x') for x in lg])].reshape(-1,3)[:,2] > .0)
center=float(1.2-np.max(np.hypot(E[:,:,0],E[:,:,2])))
assert center>.019
closed_gap=float(2.4-L[:,:,0].max()-U[:,:,0].max());assert abs(closed_gap-.044)<1e-9
def clip(poly,axis,c,sign):
 out=[]
 if len(poly)==0:return np.empty((0,3))
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  x,y=(a[axis]-c)*sign,(b[axis]-c)*sign
  if x<=0:out.append(a)
  if x*y<0:out.append(a+(b-a)*(x/(x-y)))
 return np.array(out)
old=r['post_group_conservative_bounds_m']
summary={}
for name,v in seat.items():
 s=1 if name.endswith('left') else -1
 Current=L if s==1 else U
 y=v['post_minus_hinge_height_m']; summary[name]={}
 props={'old_exact_'+key:(g['inward_limit_from_hinge'],max(abs(a) for a in g['depth_bounds']),[a+y for a in g['height_unseated_bounds']]) for key,g in old.items()}
 # New post uses this exact anchor and y offset, in meters at scale ONE.
 ref=P*[s,1,1]+[-.19616,y,0.]
 for key in sorted(set(pm)):
  p=ref[pm==key].reshape(-1,3);p0,p1=p.min(0),p.max(0)
  if key=='iron':
   # With u>=0 and θ∈[0,π/2], u cosθ+z sinθ<0 implies z<0 and
   # rotated cross-depth -u sinθ+z cosθ<=0. Fixed mate x<0,z>0 excludes collision.
   assert p1[0]<=-.007 and p0[2]>=.040
   summary[name]['new_static_iron_mate_positive_depth_half_plane_clearance']=True
   continue
  props['new_post_'+key]=(float(p1[0]),float(max(-p0[2],p1[2])),[float(p0[1]),float(p1[1])])
 for key,(x,z,(y0,y1)) in props.items():
  # If rotation sends a positive-u point to world x<0, |z'| cannot be smaller than u.
  # And negative z is then a lower bound for x'; padding both axes and Y includes the whole continuous turn.
  work=Current[(Current[:,:,0].min(1)<=z+.002)&(Current[:,:,1].min(1)<=y1+.002)&(Current[:,:,1].max(1)>=y0-.002)]
  z_min=1.
  for t in work:
   b=clip(clip(clip(t,1,y0-.002,-1),1,y1+.002,1),0,z+.002,1)
   if len(b): z_min=min(z_min,b[:,2].min())
  margin= None if z_min==1. else float(z_min-x)
  if key.startswith('new_post_') and margin is not None and margin<.002-1e-7: raise ValueError((name,key,margin,x,z,y0,y1))
  summary[name][key]=margin
print(json.dumps({'static_gate_envelope_ok':True,'left_AABB_m':[lo.tolist(),hi.tolist()],'exact_retained_v1_groups_each_leaf':len(retain),'mirrored_shape_excluding_front_hardware':True,'front_handle_owner':'left at +Z owner-facing convention; right keeper only','one_rear_knob_each':True,'static_hardware_internal_overlap_witness_count':len(contacts),
                  'closed_center_gap_m':closed_gap,'continuous_each_leaf_center_margin_m':center,
                  'independent_bounds_model_expected_post_anchor_absolute_hinge_local_m':[-.19616,'exact measured seat Y',0],
                  'proposed_post_extents_unscaled_m':[P.min((0,1)).tolist(),P.max((0,1)).tolist()],
                  'positive_closed_manifold_wound_components':{'leaf_left':len(set(lg)),'leaf_right':len(set(rg)),'post':len(set(pg))},
                  'clipped_continuous_nearest_face_margin_m':summary,
                  'not_import_lighting_nor_hardware_seam_approval':True},indent=2,sort_keys=True))
