from pathlib import Path
import hashlib,json,numpy as np,itertools
r=Path(__file__).resolve().parent;R=r.parent
prior=R/'hvn-l1-fence-33036-sw-socket-graft-v1'
assert hashlib.sha256((prior/'SHA256SUMS').read_bytes()).hexdigest()=='cd6e5e661e373ef99f0cf5897f84d5fc9cf86c47b13d48ac16397cd76f948314'
ctx={'__file__':str(R/'hvn-l1-fence-33036-full-perimeter-repair-bound-v1/verify.py')}
v=Path(ctx['__file__']);exec(v.read_text().split('seams=')[0],ctx)
T=ctx['tr']; labels=np.array(ctx['labels']);world=ctx['panels'](T,True)['West2'][0];height=ctx['height']
def h(p):return height(np.asarray(p))
cut=np.isin(labels,['front_rounded_rails','ivory_hemp_warm','ivory_hemp_cream'])
lower=world[cut&(T[:,:,1].mean(1)<.50)]; upper=world[cut&(T[:,:,1].mean(1)>.50)]
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def clip(poly,t):
 winding=np.sign(cross(t[1]-t[0],t[2]-t[0]))
 for a,b in zip(t,np.roll(t,-1,axis=0)):
  if not len(poly):return []
  out=[]
  for c,d in zip(poly,np.roll(poly,-1,axis=0)):
   p=winding*cross(b-a,c[:2]-a);q=winding*cross(b-a,d[:2]-a)
   if p>=-1e-13:out.append(c)
   if (p < -1e-13 and q>1e-13) or (q < -1e-13 and p>1e-13):out.append((q*c-p*d)/(q-p))
  poly=np.asarray(out)
 return poly
vals=[];dug=[];max_ground=-1e9
from functools import lru_cache
@lru_cache(maxsize=None)
def grids(i,j):
 x=i*.25; z=j*.25;a,b,c,d=np.array([[x,z],[x+.25,z],[x,z+.25],[x+.25,z+.25]])
 def sub(t):
  t=np.array(t);coeff=np.linalg.solve(np.c_[t,np.ones(3)],[h(p) for p in t]);return t,coeff
 return [sub((a,b,c)),sub((b,d,c))]
for i,tr in enumerate(lower):
 # Clip actual 3D art triangles to footprint of each actual indexed terrain triangle.
 # The extra coordinate carries interpolated art y, even for vertically projected facets.
 A=tr[:,[0,2,1]];lo,hi=np.floor(A[:,:2].min(0)*4).astype(int),np.floor(A[:,:2].max(0)*4).astype(int)
 for u,w in itertools.product(range(lo[0],hi[0]+1),range(lo[1],hi[1]+1)):
  for tile,coef in grids(u,w):
   out=clip(A,tile)
   if not len(out):continue
   for p in out:
    gap=float(p[:2]@coef[:2]+coef[2]-p[2])
    vals.append((float(p[1]),gap,float(p[0]),i,float(p[2])))
   # Exact (linear) crossings against ground within clipped polygon.
   for p,q in zip(out,np.roll(out,-1,axis=0)):
    a=float(p[:2]@coef[:2]+coef[2]-p[2]);b=float(q[:2]@coef[:2]+coef[2]-q[2])
    if a*b<0:
     seq=(b*p-a*q)/(b-a)
     dug.append((float(seq[1]),float(seq[0]),i))
arr=np.array(vals)
ix=int(np.argmax(arr[:,1]));worst=arr[ix]
buried=arr[arr[:,1]>1e-8]
limit=max(x[0] for x in dug if x[0]<worst[0])
earliest=min(x[0] for x in dug)
# Earliest buried polygon vertex or exact zero intersection, not a sampled station.
begin=min(earliest,float(buried[:,0].min()))
end=max(float(buried[:,0].max()),max(x[0] for x in dug))
L=1/6
mate=float(lower[:,:,2].min()); protected=.002
arr2=arr[arr[:,1]+protected>0]
guard_raw=arr2[:,1]+protected
need_at_immutable_side=float(np.max(guard_raw-L*(arr2[:,0]-mate)))
q=arr2[np.argmax(guard_raw-L*(arr2[:,0]-mate))]
derived=float(np.min(arr2[:,0]-6*guard_raw))
max_pitch=float(np.max(guard_raw/(arr2[:,0]-mate)))
last=float(lower[:,:,2].max())
# Fixed-XZ minimal Lipschitz majorant at stations; all polygon constraints between
# stations are bounded via the affine facet vertices (reported gradient is a screening bound).
def target(z):return max(0.,float(np.max(guard_raw-L*abs(arr2[:,0]-z))))
pinz=[mate,derived,begin,7.75,8.,8.25,8.5,8.79775,9.,9.25,9.5,last]
screens={f'{z:.9f}':target(z) for z in pinz}
# Math-only fixed XZ warp: no change to source. Look for concrete corner interference
# witnesses even after grade is deferred. Apply to exact untouched V3 lower branch.
W=lower.copy()
W[:,:,1]+=np.asarray([target(z) for z in W[:,:,2].ravel()]).reshape(W.shape[:2])
S=ctx['panels'](T,True)['SW0'][0]
S=S[cut&(T[:,:,1].mean(1)<.50)]
M=labels[cut&(T[:,:,1].mean(1)<.50)]
contra=ctx['culled_intersections'](W,S,M,M)
out=dict(status='HOLD: fixed-XZ grade lower bound clears the mate on paper; real cut, authored rope/graft and fixture clearance are not proven',source='exact owner bold V3 West2, no new geometry; indexed ground-triangle footprint clipping with affine crossings',terrain_overlap_polygon_vertex_records=len(vals),interference_scope='positive terrain-minus-art world Y; triangle-clipped vertices and affine zero crossings vs log parts not assessed',
 donor_world_z_span_m=[mate,last],first_zero_point_and_last_buried_envelope_world_z_m=[begin,end],worst_coordinate_order_z_penetration_x_triangle_arty=worst.tolist(),positive_buried_polygon_points=len(buried),
 grade_budget=dict(preserved_left_mate_z_m=mate,allowed_screening_gradient=1/6,noncontact_guard_m=protected,minimum_grade_bounded_offset_required_at_mate_m=need_at_immutable_side,dominant_support_constraint=q.tolist(),latest_theoretical_zero_offset_extension_z_m=derived,extra_distance_past_immutable_mate_m=mate-derived,minimum_peak_gradient_for_any_zero_offset_mate=max_pitch),
 minimum_fixed_xz_grade_station_lift_m=screens,warped_lower_vertex_proxy_cross_arm_untrimmed_control=contra,upper_lower_separation_global_y_before_and_worst_uniform_offset_m=[float(upper[:,:,1].min()-lower[:,:,1].max()),float(upper[:,:,1].min()-lower[:,:,1].max()-(worst[1]+protected))],
 nearby_other_band_and_post_intersection_approval=False,actual_body_and_rope_edits=False)
print(json.dumps(out,indent=2))
