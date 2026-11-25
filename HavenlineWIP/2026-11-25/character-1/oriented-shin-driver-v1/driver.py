"""One analytical in-stock bend-strip preflight, no renderer/action exporter."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.spatial.transform import Rotation as Rot
p=Path(__file__).resolve().parent
base=p.parent/'hvn-l1-c1-stride-broad-repair-v1'
cage=p.parent/'hvn-l1-c1-boot-cage-v1'
for folder,seal in [(base,'649df17ed50eadcd56cd8077f8ad16dc7bee314282d8efbaf14cc396af9d49f2'),(cage,'322deeca7d59384d2daf79b231b848f2cc60692030a12f3a20c2148397008031')]:
 m=folder/'SHA256SUMS';sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
 assert sha(m)==seal
 for line in m.read_text().splitlines():
  h,n=line.split('  ',1);assert sha(folder/n)==h
D=np.load(base/'pose-inputs.npz'); rest=D['rest']; frames=D['xyz']; offsets=D['offset']; sc=float(D['scale'])
names=list(D['weight_names']); weights=dict(zip(names,D['weights']))
_,weld=np.unique(np.rint(rest/1e-6).astype('int64'),axis=0,return_inverse=True)
E,F=D['edge'],D['tri']
# Broad intact transition between planted vamp side and lower shin. Physical
# interval fixed before inspecting poses; width from protected support and
# stock measured ankle/shin region, not from normalized animation key time.
low,high=.043,.343
H=high-low
u=np.linspace(0.,1.,2049); z=low+u*H
s=u**3*(10.-15.*u+6.*u*u)
ds=(30*u*u*(u-1)**2)/H
ex=np.array([0.,0.,1.])
norm=lambda x:np.linalg.norm(x,axis=-1)
smooth=lambda t: np.clip(t,0,1)**3*(10+np.clip(t,0,1)*(-15+6*np.clip(t,0,1)))
def transforms(side,k):
 raw=D['skin_world'][k]
 out=[]
 for bone in ['Foot','Calf']:
  M=raw[names.index(side+'_'+bone)]
  assert np.linalg.det(M[:3,:3])>0 and np.max(abs(M[:3,:3].T@M[:3,:3]-np.eye(3)))<2e-6
  G=Rot.from_matrix(M[:3,:3])
  # Convert world-space transform into original normalized stock units.
  t=(M[:3,:3]@offsets+M[:3,3]-offsets)*sc
  out.append((G,t))
 return out
def strip(Foot,Shank,pivot,xy):
 # Geometric construction: integrate centerline tangent from the geodesic
 # orientation, not blend the locations of Foot- and Calf-driven cages.
 # Translate by a single smooth endpoint correction to meet exact shank.
 F,t0=Foot; G,t1=Shank
 rel=(F.inv()*G).as_rotvec()
 theta=np.linalg.norm(rel)
 Q=F*Rot.from_rotvec(s[:,None]*rel)
 tangents=Q.apply(np.broadcast_to(ex,(len(u),3)).copy())
 lower=pivot+ex*low; upper=pivot+ex*high
 origin=(F.apply(lower)+t0)+cumulative_trapezoid(tangents,z,axis=0,initial=0.)
 eps=(G.apply(upper)+t1)-origin[-1]
 center=origin+s[:,None]*eps
 # Signed determinant in the oriented cross-section:
 # det J = 1 + s'(z) * [ e_z·(Q^-1 eps) + e_z·(rel × r_xy) ].
 angular=np.cross(np.broadcast_to(rel,(len(xy),3)),xy)[:,2]
 shift=Q.inv().apply(np.broadcast_to(eps,(len(u),3)).copy())[:,2]
 J=1+ds[:,None]*(shift[:,None]+angular[None,:])
 # Radial term is linear in (x,y); box corners suffice for each z.
 # Bound missed minima on z with derivative Lipschitz and half mesh step.
 # Max |d2s/dz2| <= 6/H^2 (bound above exact 10/sqrt(3)).
 L=6/H**2*(np.linalg.norm(eps)+max(norm(xy))*theta)+(1.875/H)**2*theta*np.linalg.norm(eps)
 return {'relative_orientation_deg':float(np.rad2deg(theta)),
  'endpoint_correction_mm':float(np.linalg.norm(eps)*1e3),
  'min_signed_jacobian_on_grid':float(J.min()),
  'minimum_bound_over_box':float(J.min()-L*(z[1]-z[0])*.5),
  'argmin_z_m':float(z[np.unravel_index(J.argmin(),J.shape)[0]]),
  'min_exact_corner_index':int(np.unravel_index(J.argmin(),J.shape)[1])},Q,center,eps
identity=(Rot.identity(),np.zeros(3))
test=strip(identity,identity,np.zeros(3),np.array([[-.1,-.2,0],[.1,.2,0]]))[0]
assert abs(test['minimum_bound_over_box']-1)<1e-12
rigid=(Rot.from_euler('x',37,degrees=True),np.array([-.4,.2,.1]))
control=strip(rigid,rigid,np.zeros(3),np.array([[-.1,-.2,0],[.1,.2,0]]))[0]
assert abs(control['minimum_bound_over_box']-1)<1e-10
negative=strip(identity,(Rot.from_euler('x',80,degrees=True),np.array([0.,0.,-.3])),np.zeros(3),np.array([[-.4,-.4,0],[.4,.4,0]]))[0]
assert negative['min_signed_jacobian_on_grid']<0
out={'axis_range_m':[low,high],'known_identity':test,'known_global_rigid':control,'known_compressive_inversion':negative,'frames':[]}
data=[]
for k,X in enumerate(frames):
 record={};spec={}
 for side in ('L','R'):
  family=sum(weights.get(side+'_'+name,0) for name in ('Foot','ToeBase','Calf','CalfTwist01','CalfTwist02','Thigh'))
  boot=D['boot'+side]
  # Fixed transverse axis near native weighted Foot/Calf boundary; identical
  # across the three keys. Center purely material, not fitted to pose.
  used=(family>.55)&(rest[:,2]>=low)&(rest[:,2]<=high)&((rest[:,0]>0) if side=='L' else (rest[:,0]<0))
  cross=rest[used & (abs(rest[:,2]-.158)<.013)]
  pivot=np.r_[np.median(cross[:,:2],axis=0),0.]
  box=rest[used]-pivot
  xy=np.array([[a,b,0.] for a in (box[:,0].min(),box[:,0].max()) for b in (box[:,1].min(),box[:,1].max())])
  result,Q,center,_=strip(*transforms(side,k),pivot,xy)
  result.update(pivot_m=pivot.tolist(),corners_m=xy.tolist(),source_domain_rows=int(used.sum()))
  record[side]=result;spec[side]=(used,pivot,Q,center)
 out['frames'].append(record);data.append(spec)
# Only one bilateral compiled mapping if the complete material box stayed
# orientation preserving at all keys, never hide a failed left/right branch.
ready=all(m['minimum_bound_over_box']>.0 for f in out['frames'] for m in f.values())
out['preflight_admits_visible_driver']=ready
if '--preflight' in sys.argv or not ready:
 out['disposition']='PREFLIGHT_ONLY' if ready else 'STOP_STOCK_LINEAGE_SIGNED_MAP_FAILED_BEFORE_VISIBLE_DRIVER'
 print(json.dumps(out,indent=2))
 sys.exit(0)
from scipy.spatial import cKDTree
from scipy.spatial.transform import Slerp
Ys=[]
for k,X in enumerate(frames):
 Y=X.copy()
 for side,(used,pivot,Q,center) in data[k].items():
  boot=D['boot'+side]; floor=float(rest[boot,2].min())
  fixed=np.zeros(len(rest),bool)
  fixed[boot[rest[boot,2]<floor+.03]]=True
  fixed[D['phase'+side]]=True
  for n,w in weights.items():
   if n.startswith(side+'_BootFastener_'):fixed[w>.001]=True
  for ref in frames:
   U=D['contact'+side];hits=((ref[U,2]>=-.001)&(ref[U,2]<=.002)).all(1);fixed[np.unique(U[hits])]=True
  lock=np.zeros(int(weld.max())+1,bool);lock[weld[~used|fixed]]=True
  edit=np.flatnonzero(used & ~lock[weld]); p0=rest[edit]; z0=p0[:,2]
  frame=Slerp(z,Q)(z0)
  C=np.column_stack([np.interp(z0,z,center[:,axis]) for axis in range(3)])
  cross_axis=p0-pivot;cross_axis[:,2]=0
  mapped=C+frame.apply(cross_axis)
  # Seam and rigid hardware: preserve all vertices and weighted fastener
  # rows in place with a compact continuous collar around protected rows.
  # This collar isn't certified invertible by the core strip test.
  frozen=rest[fixed]
  dd=cKDTree(frozen).query(p0,k=1)[0]
  collar=smooth(dd/.032)*smooth((z0-low)/.031)*smooth((high-z0)/.041)
  same,fr=np.unique(weld[edit],return_index=True)
  dv=((mapped-X[edit])*collar[:,None])[fr[np.searchsorted(same,weld[edit])]]
  Y[edit]=X[edit]+dv
  assert np.array_equal(Y[fixed],X[fixed])
  guards=D['left_ids' if side=='L' else 'right_ids']; ee=E[guards]
  ratios=norm(Y[ee[:,1]]-Y[ee[:,0]])/norm(rest[ee[:,1]]-rest[ee[:,0]])
  faces=np.flatnonzero(np.isin(F,edit).any(1))
  def tri_normal(v):
   r=v[F[faces]]
   return np.cross(r[:,1]-r[:,0],r[:,2]-r[:,0])
  orig,pose,corr=map(tri_normal,(rest,X,Y)); ar=norm(orig); nr=norm(pose); valid=ar>1e-9
  signed=(corr*pose).sum(1)/np.maximum(nr*ar,1e-15)
  edge_bad=np.flatnonzero((ratios<.5)|(ratios>2))
  signed_bad=valid&((signed<.5)|(signed>2))
  out['frames'][k][side].update({'edge_bad':len(edge_bad),'edge_minmax':[float(ratios.min()),float(ratios.max())],
   'first_failed_edge_i':int(guards[edge_bad[0]]) if len(edge_bad) else None,
   'signed_area_bad':int(signed_bad.sum()),'relative_reversals':int((valid&(signed<=0)).sum()),
   'worst_relative_face_id':int(faces[np.where(valid,signed,np.inf).argmin()]),
   'maximum_edit_mm':float(norm(dv).max()*1000),'sole_and_fastener_byte_exact':True,
   'lowest_sole_raw_and_adjusted_mm':[float(v[boot,2].min()*1000) for v in (X,Y)]})
 Ys.append(Y)
np.savez_compressed(p/'diagnostic-arrays.npz',xyz=np.stack(Ys))
out['disposition']='HOLD_PENDING_SCOPE_CHECKS' if not any(s['edge_bad'] or s['signed_area_bad'] for f in out['frames'] for s in f.values()) else 'STOP_STOCK_LINEAGE_VISIBLE_GEOMETRY_REJECT'
print(json.dumps(out,indent=2))
