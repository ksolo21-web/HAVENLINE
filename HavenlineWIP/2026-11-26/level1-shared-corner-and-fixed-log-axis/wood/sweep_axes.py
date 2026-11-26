"""One fixed-origin, common-local-axis screening grid on three observed native ticks."""
from pathlib import Path
d=Path(__file__).resolve().parent.parent/'hvn-l1-crown-dark-end-source-v1'/'inspect_end.py'
exec(d.read_text().split('rows=[]\nfor r')[0])
from scipy.spatial.transform import Rotation
ticks=[128,129,142]; step=[-15,-10,-5,0,5,10,15]
fixed={}
for r in data['rows']:
 t=r['tick']
 if t not in ticks:continue
 c=v[t]; assert all(c[k]==o[t][k] for k in c if k not in {'scenario','rid','source_mesh_rid'})
 mb,mp=tr(r['mesh']);original,origin=tr(c['prop_submitted_transform']);kb,kp=tr(c['camera'])
 U,sv,Vt=np.linalg.svd(original);basis=U@Vt
 assert np.linalg.det(basis)>.9999 and np.max(abs(sv-3.522754))<.0001
 L=-np.array(c['sun_direction']);L/=np.linalg.norm(L)
 src,ix,J,wt=sh[0]
 pal=np.array([M(s[1]) for s in r['pose_and_product_by_slot']])
 body=(np.einsum('nwij,nj,nw->ni',pal[J],src,wt)[:,:3]@mb.T+mp)[ix]
 h=depth(project(body,kb,kp)); hy,hx=np.where(np.isfinite(h))
 fixed[t]=(body,original,origin,kb,kp,L,h,int(hy.max()-hy.min()+1))
center=(np.concatenate([q[0] for q in raw]).min((0,1))+np.concatenate([q[0] for q in raw]).max((0,1)))/2
def screen(yaw,pitch):
 Ry=Rotation.from_euler('y',yaw,degrees=True).as_matrix()
 Rz=Rotation.from_euler('z',pitch,degrees=True).as_matrix()
 rot=Ry@Rz
 assert np.allclose(rot.T@rot,np.eye(3))
 out=[]
 for t in ticks:
  b,F,old,k,p,L,H,hero_h=fixed[t]
  # Native original raw GLB translation could encode nonzero bounds center.
  # Rotate only about the exact old Crown geometric center; preserve center in every world frame.
  pivot=old+center@F.T
  xf=F@rot
  convert=lambda xyz:(xyz-center)@xf.T+pivot
  W=[convert(q[0]) for q in raw]
  # Maintain a horizontal cross-back log, with a hard bound relative to world up.
  shaft=xf[:,0]/np.linalg.norm(xf[:,0]);world_tilt=float(np.degrees(np.arcsin(abs(shaft[1]))))
  if world_tilt>15.00001:return dict(yaw_deg=yaw,pitch_deg=pitch,reject_world_tilt_tick=t,world_tilt_deg=world_tilt)
  distval,ids=clearance(np.concatenate(W),b)
  barkd=depth(project(W[0],k,p)); T=np.linalg.inv(xf).T
  cap=[detail(project(W[1][m],k,p),raw[1][1][m]@T.T,W[1][m]) for m in ends]
  G=np.maximum.reduce([barkd,cap[0][0],cap[1][0]])
  vis=(G>H)&np.isfinite(G); pvY,pvX=np.where(vis); solo=np.isfinite(G)
  row=dict(tick=t,gap_mm=distval*1000,pair=ids[:2],intersections=ids[2],
     world_tilt_deg=world_tilt,crown_visible_px=int(vis.sum()),visible_wood_width_px=int(np.ptp(pvX)+1) if len(pvX) else 0,
     projected_hero_height_px=hero_h,visual_body_cover_count=int((vis&np.isfinite(H)).sum()),
     crown_solo_px=int(solo.sum()),body_hide_fraction=float((solo&~vis).sum()/solo.sum()),ends=[])
  for i,(dd,N,pts) in enumerate(cap):
   vi=np.isfinite(dd)&(dd>np.maximum.reduce([H,barkd,cap[1-i][0]])+.001)
   nn=N[vi];dots=(nn/np.linalg.norm(nn,axis=1)[:,None])@L
   body_blocks=blocked(pts[vi][dots>0],b,L)
   row['ends'].append(dict(x_sign=(-1,1)[i],visible_px=int(vi.sum()),
    positive_direct_incidence_px=int((dots>0).sum()),positive_unblocked_direct_px=sum(a is None for a in body_blocks),
    visible_normal_dot_range=list(map(float,[np.min(dots),np.max(dots)])) if dots.size else []))
  out.append(row)
 return dict(yaw_deg=yaw,pitch_deg=pitch,rows=out,
    clearance_pass=all(f['gap_mm']>=25 and f['intersections']==0 for f in out),
    minimal_direct_visibility_pass=all(sum(a['positive_unblocked_direct_px'] for a in f['ends'])>=1 for f in out))
scan=[screen(y,p) for y in step for p in step]
valid=[q for q in scan if 'rows' in q]
baseline=next(q for q in valid if q['yaw_deg']==q['pitch_deg']==0)
assert [sum(a['visible_px'] for a in q['ends']) for q in baseline['rows']]==[127,73,68]
assert [sum(a['positive_unblocked_direct_px'] for a in q['ends']) for q in baseline['rows']]==[127,0,0]
print(json.dumps(dict(grid_deg=step,rotation='local R_y(yaw) @ R_z(pitch), original Crown geometric center fixed; no rolling, pose nor scale change',
  world_shaft_tilt_max_deg=15,screened_all_three=len(valid),direct_pass_count=sum(q['minimal_direct_visibility_pass'] for q in valid),
  geometric_pass_count=sum(q['clearance_pass'] for q in valid),both_pass_count=sum(q['clearance_pass'] and q['minimal_direct_visibility_pass'] for q in valid),results=scan),indent=2))
