from pathlib import Path
import hashlib,numpy as np,json,itertools
R=Path(__file__).resolve().parent;P=R.parent
S=P/'hvn-l1-fence-33036-sw-slab-admission-v1'
assert hashlib.sha256((S/'SHA256SUMS').read_bytes()).hexdigest()=='b7acf5eb59987e22f1cb6ec980a8f20634bb3bd1ce6e402e2abb332b6546f7b3'
q=S/'slab.py';t=q.read_text();N={'__file__':str(q)}
exec(t[:t.index('results={}')],N)
S=N['A']['West1'][0];mat=N['mat'];base=N['base'];terrain=N['corner'];polys=N['d']['d']['D']['polys'];V=N['C']
K=(mat=='front_rounded_rails')&(base[:,:,1].mean(1)<.5)
M=(mat=='ivory_hemp_warm')&(base[:,:,1].mean(1)<.5)
def sub(t,lo,hi,allow_degen=False):
 out=[]
 for i,f in enumerate(t):
  if f[:,2].min()>hi or f[:,2].max()<lo:continue
  F=N['within'](f,2,lo,hi)
  if len(F)<3:continue
  for S in N['fan'](F):
   a=np.array(S)
   if np.linalg.norm(np.cross(a[1]-a[0],a[2]-a[0]))<=1e-14 and not allow_degen:continue
   out.append(a)
 return np.asarray(out)
critical={}
for key,k in [('rail',K),('warm',M)]:
 z0=float(S[k][:,:,2].max())
 t=S[k];cap=t[(abs(t[:,:,2]-z0)<1e-9).all(1)]
 ys=[]
 for i in np.arange(6.80,z0,.005):
  f=sub(t,i,min(i+.005,z0))
  if len(f):ys.append([float(i),min(float(i+.005),z0),terrain(f)['minimum_clearance_m']])
 # Do not interpret absence of planar warm cap as cold compliance.
 vals=terrain(cap) if len(cap) else None
 W=terrain(t)
 deepest_z=W['nearest_record_index_x_z_y'][2]
 clear_requirement=max(0., -W['minimum_clearance_m'])
 aperture=z0-deepest_z
 critical[key]={'section_unchanged_cap_max_station_world_z_m':z0,'clip_min_grade_requirement_from_fixed_cap':{'cap_to_deepest_ground_point_axial_m':aperture,'edge_lift_m_required_just_for_zero_ground_intersection':clear_requirement,'minimum_abs_steepness_without_moving_cap':clear_requirement/aperture,'minimum_abs_steepness_for_2mm_guard':(clear_requirement+.002)/aperture,'needed_lift_travel_at_prior_1to6_screen_m':clear_requirement*6},'deepest_indexed_y_gap_m':W['minimum_clearance_m'],'whole_cap_exact':vals,'bad_end_strip_intervals':[(a,b,c) for a,b,c in ys if c<.002], 'last_strip_without_mutation':ys[-1]}
(R/'result.json').write_text(json.dumps(critical,indent=2)+'\n')
print(critical)
