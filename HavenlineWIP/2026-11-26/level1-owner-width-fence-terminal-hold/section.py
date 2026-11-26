from pathlib import Path
import hashlib,json,numpy as np
R=Path(__file__).resolve().parent;P=R.parent
b=P/'hvn-l1-fence-33036-sw-outer-seams-v1'
assert hashlib.sha256((b/'SHA256SUMS').read_bytes()).hexdigest()=='3c3c11205d737641a489a78380e67371d59c9e8b41b326319e5f140e77bb4833'
s=(b/'repair.py').read_text(); C={'__file__':str(b/'repair.py')}
# Previous pure-world assembly and helper definitions; no outputs into other package.
exec(s[:s.index('evidence={')],C)
exec(s[s.index('def tube(A,B'):s.index('rep={}')],C)
locals().update({k:C[k] for k in ('O','A','tube','spec','terrain','bound')})
from scipy.spatial import ConvexHull
from collections import defaultdict
results={}
for nb,(run,pk,rem,(ra,rb),ax,sign) in spec.items():
 groups={k:v for k,v in O.items() if k.startswith(run+'/')}
 Y=A[nb][0]
 rest=[i for i in range(len(Y)) if not any(a<=i<=b for a,b in rem)]
 expect_stock_next=Y[ra:rb+1]
 timber=groups[run+'/'+pk]
 N=ConvexHull(np.unique(timber.reshape(-1,3),axis=0))
 N2=ConvexHull(np.unique(expect_stock_next.reshape(-1,3),axis=0))
 rows=[]
 for bi in range(2):
  key=run+f'/front_rail_{bi+1}'
  old=groups[key];tip0=float(old[:,:,ax].max() if sign==1 else old[:,:,ax].min())
  old_faces=old[np.abs(old[:,:,ax].mean(1)-tip0)<.008].reshape(-1,3)
  trans=2 if ax==0 else 0
  old_full=old.reshape(-1,3)
  c=(old_faces.min(0)+old_faces.max(0))*.5
  ownerH=.064;ownerD=.05655
  normal=np.eye(3)[trans];angle=np.arange(16)*np.pi/8
  ring=ownerH*np.cos(angle)[:,None]*[0.,1.,0.]+ownerD*np.sin(angle)[:,None]*normal
  hh=N.equations[:,:3];hn=N.equations[:,3]
  sc=(sign*c[ax])-np.arange(0,.201,.005)
  def signed_pts(a,b):return a@b[:,:3].T+b[:,3]
  candidates=[]; amount={}
  c_min=1e9;worstpos=None
  for tau in sc:
   q=c.copy();q[ax]=tau*sign
   m=float(signed_pts(q+ring,N.equations).max())
   if m<c_min:c_min=m;worstpos=q.tolist()
   if m<-.002:candidates.append(q.tolist())
  # Closed-form necessary depth offset to even fit the outwardmost full contour
  # into the world outwardmost exact timber vertex (convex hull bound).
  outward=(1 if nb=='SW1' else -1)
  out=float(max(outward*timber[:,:,trans].ravel()))
  minmove=(outward*c[trans]+ownerD-out)
  # A genuinely re-centered full contour would need a new rail/rope neighborhood,
  # not the proposed continuation in exterior rail plane.
  kin=[]
  for inward in np.arange(0,.1301,.005):
   for tau in sc:
    q=c.copy();q[ax]=tau*sign;q[trans]-=inward*outward
    m=float(signed_pts(q+ring,N.equations).max())
    if m<-.002:kin.append((inward,q.tolist(),m))
   if kin:break
  p=min(kin,key=lambda y:(y[0],abs(y[1][ax]-c[ax]))) if kin else None
  rows.append(dict(band=bi,exact_owner_tip_plane_xyz_m=c.tolist(),existing_owner_rail_depth_center_m=c[trans],
   tested_axial_socket_stations=len(sc),full_section_height_depth_m=[.128,.1131],available_unchanged_exterior_plane_socket_count=len(candidates),
   best_unchanged_plane_convex_timber_exceed_mm=c_min*1000,closest_station_xyz_m=worstpos,
   absolute_necessary_inward_recenter_mm=minmove*1000,
   first_possible_recentered_hull_only=p))
 results[nb]=rows
(R/'result.json').write_text(json.dumps(dict(scope='owner-size orthogonal ring outline, necessary convex containment screen; no rods/lashing actually authored',required_profile_mm=[128,113.1],joins=results),indent=2)+'\n')
