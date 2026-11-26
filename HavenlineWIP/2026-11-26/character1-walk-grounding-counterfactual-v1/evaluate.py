"""One offline +/- 15mm visual-foot counterfactual; does not produce rig or pose files."""
from pathlib import Path
p=Path(__file__).resolve().parent.parent
prior=p/'hvn-l1-c1-stock-walk-sparse-ground-v1/check.py'
script=prior.read_text(); seg=script[:script.index('log=(N/')]
ns={'__file__':str(prior)};exec(compile(seg,str(prior),'exec'),ns)
import numpy as np,hashlib,json
N=ns['N'];ground=ns['ground'];oldexact=ns['exact_gap'];ix=ns['ix']; groups=ns['groups']; clip=ns['clip']
A=p/'hvn-l1-c1-stock-walk-adjacent-native-v1/native.F8xorDH1'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(A/'SHA256SUMS')=='dd6cfd4f073fb3e97eee5016af644e684b64847efd9432709f0be6bfe4607795'
for l in (A/'SHA256SUMS').read_text().splitlines():
 h,n=l.split('  ',1);assert sha(A/n)==h
adj=json.loads((A/'adjacent-pose-result.json').read_bytes())
assert adj['all_original_174_rows_exact'] and adj['paired_t160_exact']
raws=ns['src']; W=ns['wt']; J=ns['J']
FLOOR=.035; LIMIT=.015; BAND=.002
def pose_at(base,t):
 d=base/'walk-trace-only';w=json.loads((d/'palette.json').read_bytes())
 j=next(r for r in w['rows'] if r['tick']==t)
 f=d/f'{t}-s0-baked.f32';assert sha(f)==w['streams'][f.name]['sha256']
 m=np.array(j['mesh']);pose=np.fromfile(f,'<f4').reshape(-1,3).astype(float)@m[1:]+m[0]
 sb=np.array(j['skeleton'])
 bones={b['name']: np.array(j['pose_and_product_by_slot'][b['slot']][0][0])@sb[1:]+sb[0] for b in w['bindings']}
 return pose,bones,w
# Exact projected triangle fragment signed height band. Sum area can count
# overlapping underside patches; bounding spans are not connected support.
def fragments(nums,world):
 area=0.; pool=[]
 for i in nums:
  tri=world[ix[i]]
  lo=np.floor(tri[:,[0,2]].min(0)*4).astype(int);hi=np.floor(tri[:,[0,2]].max(0)*4).astype(int)
  for q in range(lo[0],hi[0]+1):
   x=q/4
   for r in range(lo[1],hi[1]+1):
    z=r/4;poly=list(tri)
    for fn in (lambda p:p[0]-x,lambda p:x+.25-p[0],lambda p:p[2]-z,lambda p:z+.25-p[2]):
     poly=clip(poly,fn)
     if not poly:break
    if not poly:continue
    for side in [-1,1]:
     pp=clip(poly,lambda p:side*(p[0]-x+p[2]-z-.25))
     if len(pp)<3:continue
     signed=[np.r_[t,t[1]-ground(t[0],t[2])] for t in pp]
     use=clip(clip(signed,lambda p:p[3]),lambda p:BAND-p[3])
     if len(use)<3:continue
     xy=np.array(use)[:,[0,2]]
     sz=.5*abs(np.sum(xy[:,0]*np.roll(xy[:,1],1)-xy[:,1]*np.roll(xy[:,0],1)))
     if sz>1e-12:area+=sz;pool.extend(xy)
 return area*1e6, (np.ptp(pool,axis=0)*1000).tolist() if pool else [0,0]
r=[]
track={}
for t in [20,159,160,161]:
 world,bones,w=pose_at(N if t==20 else A,t)
 snap=dict(tick=t,feet={})
 track[t]={f:world[i,[0,2]].tolist() for f,i in [('L',50066),('R',31325)]}
 for f,(mask,faces) in groups.items():
  old=oldexact(faces,world)[0][0]
  # One analytic objective, both names separately tested as potential
  # support; this is NOT assigning load using capsule is_on_floor.
  req=-old-FLOOR+.00015
  assert abs(req)<=LIMIT
  xyz=world.copy(); xyz[:,1]+=FLOOR+req
  a,sz=fragments(faces,xyz)
  ankles=bones[f+'_Foot'];hip=bones[f+'_Thigh'];knee=bones[f+'_Calf']
  l1,l2=np.linalg.norm(knee-hip),np.linalg.norm(ankles-knee)
  goal=ankles+np.array([0.,req,0.]); x=np.linalg.norm(goal-hip)
  olddist=np.linalg.norm(ankles-hip)
  d=x
  feasible=abs(l1-l2)<d<l1+l2
  slots=[b['slot'] for b in w['bindings'] if b['name'] in (f+'_Foot',f+'_ToeBase')]
  weight=(W*np.isin(J,slots)).sum(1).astype(float)
  wxyz=world.copy();wxyz[:,1]+=FLOOR+req*weight
  worstdif=float(max(abs(wxyz[mask,1]-xyz[mask,1])))*1000
  wr=oldexact(faces,wxyz)[0]
  source=(world[ix[faces,1]]-world[ix[faces,0]]); footonly=(wxyz[ix[faces,1]]-wxyz[ix[faces,0]])
  B=(world[ix[faces,2]]-world[ix[faces,0]]); BB=(wxyz[ix[faces,2]]-wxyz[ix[faces,0]])
  ori0=np.cross(source,B);ori1=np.cross(footonly,BB)
  orient=np.einsum('ij,ij->i',ori0,ori1)
  nonzero=np.linalg.norm(ori0,axis=1)>1e-11
  # Only real edges >= 1mm; report geometry distortion (not whole sock).
  faces0=world[ix[faces]]
  faces1=wxyz[ix[faces]]
  e0=np.linalg.norm(faces0-np.roll(faces0,1,axis=1),axis=2)
  e1=np.linalg.norm(faces1-np.roll(faces1,1,axis=1),axis=2)
  ratios=e1[e0>=.001]/e0[e0>=.001]
  snap['feet'][f]=dict(original_mm=1000*old,rigid_visual_35mm_plus_foot_offset_mm=1000*req,
    pure_foot_offset_in_reach=bool(feasible),new_ankle_reach_margin_mm=1000*(l1+l2-x),
    stock_ankle_reach_margin_mm=1000*(l1+l2-olddist),segment_lengths_mm=[1000*l1,1000*l2],
    optimistic_rigid_contact_sum_area_mm2=a,optimistic_rigid_band_max_xz_span_mm=sz,
    weighted_foot_only_exact_patch_gap_mm=1000*wr[0],weighted_foot_only_face=wr[1],
    weighted_only_max_low_row_shortfall_from_rigid_mm=worstdif,new_opposed_face_normals=int((orient[nonzero]<0).sum()),model_weighted_edge_length_ratio_minmax=[float(ratios.min()),float(ratios.max())],
    control_sole_turn_or_load_verified=False)
 r.append(snap)
displacement={k:[float(1000*np.linalg.norm(np.array(track[b][k])-track[a][k])) for a,b in [(159,160),(160,161)]] for k in 'LR'}
print(json.dumps(dict(fixed_original_sole_rows_world_xz_m=track,adjacent_fixed_original_row_horizontal_motion_mm=displacement,scope='bounded offline alternatives, fixed physical actor and topology, exact captured frames/no support score',
 known_35mm_origin_correction_only_counterfactual=True,fixed_horizontal_and_rig_proportions=True,
 support_label='none: test each side as possible support without capsule label',results=r),indent=2))
