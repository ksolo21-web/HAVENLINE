"""One same-identity posterior knee material-flex diagnostic, no action export."""
from pathlib import Path
import json,hashlib,numpy as np
from scipy.spatial.transform import Rotation as Q
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
P=Path(__file__).resolve().parent
A=P.parent/'hvn-l1-c1-newer-gait-v1.J5Kxuv';m=A/'SHA256SUMS'
sha=lambda b:hashlib.sha256(b.read_bytes()).hexdigest()
assert sha(m)=='61e9ddf2477fe184c6b8fba3487db9570b0d748141800d10e5ec52269e3cdff3'
for line in m.read_text().splitlines():
 h,n=line.split(maxsplit=1);assert sha(A/n)==h
assert sha(P/'baseline.json')==sha(A/'result.json')
D=np.load(P/'poses.npz')
rest=D['rest'].astype(float); native=D['frames']; E=D['E']; T=D['tri']; W=D['weights']
scale=float(D['scale']);origin=D['source_origin']
_,weld=np.unique(np.rint(rest/1e-6).astype('int64'),axis=0,return_inverse=True)
norm=lambda x:np.linalg.norm(x,axis=-1)
smooth=lambda t:np.clip(t,0,1)**3*(10+np.clip(t,0,1)*(-15+6*np.clip(t,0,1)))
all_edge=norm(rest[E[:,1]]-rest[E[:,0]])
def area(p):
 v=p[T]
 return np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0])
N0=area(rest); A0=norm(N0)
report=[]
protos=[]
for k,pose in enumerate(native):
 X=pose.astype(float);Y=X.copy(); obs={}
 for i,side in enumerate('LR'):
  ankles=D['joints'][i]; knee=ankles[1]
  w=W[:,4*i:4*i+4]; other=W[:,(4-4*i):(8-4*i)]
  proximal=ankles[0]-knee; proximal/=norm(proximal)
  distal=knee-ankles[2];distal/=norm(distal)
  axis=proximal+distal;axis/=norm(axis)
  rel=rest-knee;x=rel@axis
  radial=rel-x[:,None]*axis
  back=np.array([0,1.,0]);back-=axis*(back@axis);back/=norm(back)
  y=radial@back
  # Predeclared local hard/soft support follows exact material slots around
  # the anatomical knee and excludes outsoles and ALL Foot/Toe influence.
  enable=(abs(x)<.072)&(norm(radial)<.12)&(y>-.050)&(w[:,:2].sum(1)>.995)&(w[:,2:].sum(1)<1e-8)&(other.sum(1)<1e-8)&(abs(rest[:,0])>.025)&(rest[:,2]>.10)
  lock=np.zeros(weld.max()+1,bool);lock[weld[~enable]]=True
  edit=np.flatnonzero(enable & ~lock[weld])
  assert len(edit)>600
  q_th,q_sh=[Q.from_matrix(M[:3,:3]) for M in D['bones'][k,i,:2]]
  theta=(q_sh.inv()*q_th).as_rotvec()
  raw=knee/scale+origin
  def kpose(M):return (M[:3,:3]@raw+M[:3,3]-origin)*scale
  a,b=[kpose(M) for M in D['bones'][k,i,:2]]
  assert norm(a-b)<1e-6,(side,k,norm(a-b))
  center=(a+b)*.5
  # Shared bend-oriented sleeve around the actual knee pivot. A single
  # near-knee bisector orientation suppresses tiny material gradient jumps;
  # it smoothly reaches original orientation on each distal/proximal flank.
  def t_on(s):
   return .5+.5*np.sign(s)*smooth((abs(s)-.017)/.045)
  frame=q_sh*Q.from_rotvec(t_on(x[edit])[:,None]*theta)
  mapped=center+frame.apply(rel[edit])
  taper=smooth((.072-abs(x[edit]))/.021)*smooth((.12-norm(radial[edit]))/.025)*smooth((y[edit]+.050)/.043)
  same,fr=np.unique(weld[edit],return_index=True)
  delta=((mapped-X[edit])*taper[:,None])[fr[np.searchsorted(same,weld[edit])]]
  Y[edit]+=delta
  ee=D['edge'+side]; ij=E[ee]
  calc=lambda g:norm(g[ij[:,1]]-g[ij[:,0]])/all_edge[ee]
  old,new=calc(X),calc(Y)
  bad=(old<.5)|(old>2)
  bh=E[ee[bad]]
  _,iw=np.unique(weld[bh.ravel()],return_inverse=True)
  u,v=iw.reshape(-1,2).T; n_comps,labels=connected_components(coo_matrix((np.ones(len(u)),(u,v)),shape=(len(set(iw)),)*2),directed=False)
  gr=labels[u];top=bh[gr==np.argmax(np.bincount(gr))]
  vx=np.unique(top)
  worst=ee[old.argmin()];wa=E[worst]
  fids=np.flatnonzero(np.isin(T,wa).sum(1)==2)
  source_faces=np.isin(T,np.unique(bh)).sum(1)>=2
  pin=D['footprint'+side]; boot=D['boot'+side]
  fixed_out=boot[rest[boot,2]<.040]
  assert np.array_equal(Y[pin],X[pin]) and np.array_equal(Y[fixed_out],X[fixed_out])
  assert np.array_equal(Y[w[:,2:].sum(1)>=1e-8],X[w[:,2:].sum(1)>=1e-8])
  affected=np.isin(T,edit).any(1)
  focus=((source_faces|affected)&(A0>2e-8))
  fd=np.flatnonzero(focus)
  N=area(Y); B0=area(X)
  orientation_ref=(q_sh*Q.from_rotvec(t_on(x[T[fd]].mean(axis=1))[:,None]*theta)).apply(N0[fd]/A0[fd,None])
  # Compare signed region to bone-transported material normal; original
  # stock-pose dot is retained as separate, not as corrective allowance.
  sig=(N[fd]*orientation_ref).sum(1)/A0[fd]
  sig0=(B0[fd]*orientation_ref).sum(1)/A0[fd]
  region=np.isin(ij,edit).any(1)
  obs[side]={
   'original_edge_fail':int(bad.sum()), 'post_edge_fail':int(((new<.5)|(new>2)).sum()),
   'nearby_affected_edge_fail_before_after':[int(((r<.5)|(r>2))[region].sum()) for r in (old,new)],
   'unaffected_failed_edges':int((bad&~region).sum()),'edge_range':list(map(float,[new.min(),new.max()])),
   'rest_lengths_bad_median_mm':float(np.median(all_edge[ee[bad]])*1000),
   'exact_worst_edge_i':int(worst),'worst_edge_vertices':wa.tolist(),'worst_adjacent_face_ids':fids.tolist(),
   'worst_foot_toe_weights':w[wa,2:].tolist(),'worst_thigh_shin_weights':w[wa,:2].tolist(),'worst_rest_mm':float(all_edge[worst]*1000),
   'largest_cluster_edges':len(top),'largest_cluster_mm':(np.ptp(rest[vx],axis=0)*1000).tolist(),
   'key_local_relative_bend_deg':float(norm(theta)*180/np.pi),'knee_join_residual_um':float(norm(a-b)*1e6),
   'number_of_edited_material_rows':len(edit),'max_local_pose_delta_mm':float(norm(delta).max()*1000),
   'signed_bad_before_after':[int(((z<.5)|(z>2)).sum()) for z in (sig0,sig)],
   'signed_reversals_before_after':[int((z<=0).sum()) for z in (sig0,sig)],
   'worst_signed_face_id':int(fd[sig.argmin()]),'worst_signed_new':float(sig.min()),
   'pin_byte_exact':True,'entire_foot_toe_influenced_geometry_exact':True,
   'lowest_boot_mm':[float(g[boot,2].min()*1000) for g in (X,Y)]
  }
 report.append(obs);protos.append(Y)
(P/'visible-report.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez_compressed(P/'rejected-material-arrays.npz',xyz=np.stack(protos))
