"""Continuous zero-start and allowed right thumb acquisition admission; no clip export."""
from pathlib import Path
import hashlib
p=Path('../hvn-c1-right-digit-anatomical-specimen-v1')
seal='42d7b3416fcdbf427cbd14ab2640e7c31d438cd7b34ad95f9332299a04b4dc4e'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()==seal
for ln in (p/'SHA256SUMS').read_text().splitlines():
 h,n=ln.split();assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h
prior=(p/'audit.py').read_text()
prefix=prior[:prior.index("# Deliberately minimal fixed sample, no fitting")]
assert "def pose_test(spec):" in prefix
exec(compile(prefix,str(p/'audit.py'),'exec'))
# Exact signed .03 anchor and right off-band index rows, in same fixed acquisition pose.
pivot=deltas[selected][-1]
axis=deltas[selected][-2]
offids=np.unique(F[np.unique(off_pairs[:,0])])
pure=offids[R[offids,ix[selected]]==1]
assert len(pure)>100
def wind(points):
 v=tool[None]-points[:,None,None]
 a,b,c=np.moveaxis(v,2,0)
 A,B,C=(np.linalg.norm(z,axis=2) for z in (a,b,c))
 den=A*B*C+(a*b).sum(2)*C+(a*c).sum(2)*B+(b*c).sum(2)*A
 return np.arctan2((np.cross(a,b)*c).sum(2),den).sum(1)/(2*np.pi)
def dist(p):
 v=np.roll(tool,-1,axis=1)-tool
 n=np.cross(v[:,0],-v[:,2]);lens=np.linalg.norm(n,axis=1)
 assert lens.min()>1e-10
 n=n/lens[:,None]
 # Distance to actual finite facet: plane projection if within all directed edges;
 # otherwise nearest finite edge. This is not distance to an infinite slab.
 gap=((p-tool[:,0])*n).sum(1); projected=p-gap[:,None]*n
 edsign=(np.cross(v,projected[:,None]-tool)*n[:,None]).sum(2)
 inplane=(edsign>=-1e-12).all(1)
 t=np.clip(((p-tool)*v).sum(2)/ (v*v).sum(2),0,1)
 e=((p-tool-t[...,None]*v)**2).sum(2).min(1)
 dd=np.where(inplane,gap**2,e);return float(np.sqrt(dd.min())),int(dd.argmin())
# Every candidate at fixed pivots without parent joint motion lies on a sphere
# around .03 pivot; the off-band starts inside a closed-tool volume.
pure_w=wind(V[pure]);nd=np.linalg.norm(V[pure]-pivot,axis=1)
angle_w=[];sphere_w=[]
for i,kd in enumerate(pure):
 if abs(pure_w[i])<.99:continue
 p0=V[kd]
 delta=p0-pivot
 c=pivot+(delta@axis)*axis
 radius=float(np.linalg.norm(p0-c))
 dc,facet=dist(c)
 if dc<=radius:continue
 if abs(wind(c[None])[0])<.99:continue
 angle_w.append((int(kd),dc-radius,dc,radius,facet,c.tolist()))
 dp,fi=dist(pivot)
 if dp<=nd[i]:continue
 if abs(wind(pivot[None])[0])<.99:continue
 sphere_w.append((int(kd),dp-nd[i],dp,float(nd[i]),fi))
# Exact additional chain constraints are algebraic on source data, without posing.
# At frozen idle joints base transforms coincide in the hand subgroup. For one
# rigid inherited rotation, an active weighted seam pin off its rotation axis
# must move (show at least two nonparallel positive-weight pin rays).
per={}
for j in (1,2):
 name=f'thumb.{j:02}.R'
 ixj=[ix[f'thumb.{k:02}.R'] for k in range(j,4)]
 ww=R[se][:,ixj].sum(1); good=ww>0
 knots=np.array(bind_digs['thumb']);knots[:,0]*=-1
 center=rh@knots[j-1]+th
 rad=V[se[good]]-center
 e=np.linalg.svd(rad,compute_uv=False)
 per[name]={'held_origin':center.tolist(),'positive_inherited_weight_seam_pins_n':len(rad),'source_rank_2_or_more_offsets':bool(len(e)>1 and e[1]>1e-4),'singular_m':e.tolist(),'pin_ids':se[good].tolist(),'positive_weight_range':[float(ww[good].min()),float(ww[good].max())]}
# Exact analytic event intervals for pure tip vertices and a fixed anatomical
# axis: intersect a point orbit with ALL actual finite tool triangles.
# This enumerates plane/triangle events, not authored angle-offset sweeps.
from math import pi
tf=tool
v0,v1,v2=np.moveaxis(tf,1,0); E1=v1-v0; E2=v2-v0
normals=np.cross(E1,E2); normals/=np.linalg.norm(normals,axis=1)[:,None]
g11=(E1*E1).sum(1); g12=(E1*E2).sum(1);g22=(E2*E2).sum(1)
den=g11*g22-g12*g12; assert min(den)>1e-19
period=2*pi; intervals=[]; ng=0; exact_event_n=0
def inside_at(c,u,v,theta):
 ts=np.array(theta)
 return abs(wind(c+np.cos(ts[:,None])*u+np.sin(ts[:,None])*v))>.99
def finite_event_intervals(kd):
 r=V[kd]-pivot
 c=pivot+(r@axis)*axis
 u=V[kd]-c; v=np.cross(axis,u)
 a=normals@u; b=normals@v; d=(normals*(v0-c)).sum(1)
 e=np.hypot(a,b)
 if ((e<1e-10)&(abs(d)<1e-9)).any():return None
 # Preserve zero-margin degeneracies by refusing those point orbits.
 m=np.flatnonzero((e>1e-10)&(abs(d)<=e+1e-11))
 if (abs(abs(d[m])-e[m])<1e-11).any():return None
 m=m[abs(d[m])<e[m]]
 psi=np.arctan2(b[m],a[m]); off=np.arccos(d[m]/e[m])
 th=np.r_[psi+off,psi-off] % period
 mm=np.tile(m,2); pts=c+np.cos(th[:,None])*u+np.sin(th[:,None])*v
 w=pts-v0[mm];d1=(w*E1[mm]).sum(1);d2=(w*E2[mm]).sum(1)
 g=(d1*g22[mm]-d2*g12[mm])/den[mm]
 h=(d2*g11[mm]-d1*g12[mm])/den[mm]
 edge=np.minimum(np.minimum(g,h),1-g-h)
 if (abs(edge)<1e-7).any():return None
 ev=np.r_[0.,np.sort(th[edge>0]),period]
 if np.min(np.diff(ev))<2e-7:return None
 k=inside_at(c,u,v,(ev[1:]+ev[:-1])*.5)
 # Shrink every strictly inside interval by 2e-6rad so numeric event
 # rounding or physical float32 source readback cannot claim a tangency.
 eps=2e-6
 return [(max(0,lo+eps if lo else 0.),min(period,hi-eps if hi<period else period))
         for lo,hi,t in zip(ev[:-1],ev[1:],k) if t and hi-lo>4*eps],len(ev)-2
for kd in pure:
 z=finite_event_intervals(kd)
 if z is None:continue
 seq,i=z;exact_event_n+=i;ng+=1
 for lo,hi in seq: intervals.append((lo,hi,int(kd)))
# Is there any angle at which ALL certified pure points are clear?
intervals.sort(); cover=[]
for lo,hi,kd in intervals:
 if cover and lo<=cover[-1][1]: cover[-1][1]=max(cover[-1][1],hi)
 else:cover.append([lo,hi])
left=0.; possible=[]
for lo,hi in cover:
 if lo>left:possible.append([left,lo])
 left=hi
if left<period:possible.append([left,period])
def orientation_control(deg):
 theta=np.deg2rad(deg)
 Z=Rotation.from_rotvec(axis*theta).apply(V[pure]-pivot)+pivot
 wi=wind(Z); idx=np.flatnonzero(abs(wi)>.99)
 if len(idx):
  candidates=[(dist(Z[j])[0],int(pure[j])) for j in idx]
  best=max(candidates)
 else: best=(0.,None)
 return {'pure_sample_inside_count':int(len(idx)), 'one_max_depth_witness_m':best[0],
         'one_vertex_id':best[1]}
controls={str(k):orientation_control(k) for k in (0,90,-90,-100,180)}
assert all(controls[str(x)]['one_max_depth_witness_m']>1e-5 for x in (0,90,-90,-100))
assert controls['180']['pure_sample_inside_count']==0
assert len(cover)==2 and cover[0][0]==0. and cover[1][1]==period
assert cover[0][1]>pi/2 and cover[1][0]<3*pi/2
anal={'actual_vertex_controls':controls,'nearest_possible_angle_in_open_direction_deg':float(np.rad2deg(cover[1][0]-period)),
      'nearest_possible_angle_in_palmward_direction_deg':float(np.rad2deg(cover[0][1])),
      'analytic_eligible_pure_actual_vertices' :ng,'finite_triangle_non_degenerate_event_count':exact_event_n,
      'signed_axis_union_inside_subinterval_count':len(intervals),
      'intervals_excluded_for_any_safe_acquisition_deg':np.rad2deg(cover).tolist(),
      'remaining_not_certified_unsafe_deg':np.rad2deg(possible).tolist(),
      'angle_convention':'+ from source-derived thumb.03 toward palm; degrees [0,360]. Closed shaft, event intervals computed in exact triangulated domain, tiny tolerance shrink. Not an angular pose sweep.'}
# Record bone radius using intended exactly fixed inherited matrix, validated
# against actually posed row samples in previous specimen; margins well above
# registration error are required in any global proof.
report={'status':'HOLD_NO_ADMISSIBLE_ACQUISITION_CONTACT_RELEASE_TRAJECTORY','author_freeze':seal,'opening_keyframe':'exact same pinned held source; clearance rejected at entry before attempting any authored contact/release','right_scope_candidate_pair_start':len(off_pairs),'opening_inside_vertices':int((abs(wind(V[offids]))>.99).sum()),'rig_options_tested':'right thumb.03 independent with cuff, exact pressure seams, other joints and axe frozen; zero-safe-start gate; spherical containment allows any rotation at same pivot when certified, signed circle case is only fixed-axis if sphere certificate absent','tested_pure_offband_rows':len(pure),'thumb_tip_pivot_winding':float(wind(pivot[None])[0]),'thumb_tip_pivot_finite_surface_distance':dist(pivot),'whole_sphere_enclosed_witnesses':sorted(sphere_w,key=lambda x:-x[1])[:6],'whole_signed_axis_circle_enclosed_witnesses':sorted(angle_w,key=lambda x:-x[1])[:6],'positive_whole_sphere_witnesses_n':len(sphere_w),'positive_whole_signed_axis_circle_witnesses_n':len(angle_w),'other_joint_pin_constraints':per,'continuous_single_hinge_admission':anal,'no_motion_keyframes_exported':True}
print(json.dumps(report,indent=2,sort_keys=True))
