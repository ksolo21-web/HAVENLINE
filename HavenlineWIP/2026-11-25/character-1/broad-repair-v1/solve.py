"""Single bilateral broad pose-delta feasibility solve, no production export."""
from pathlib import Path
import numpy as np,json
from scipy.sparse import coo_matrix,vstack,diags
from scipy.sparse.linalg import lsmr
p=Path(__file__).resolve().parent
D=np.load(p/'pose-inputs.npz');R=D['rest'];XYZ=D['xyz'];E=D['edge'];F=D['tri']
# Exact positional seam equivalence at original witness precision. Apply
# shared displacements, never weld/replace rig or change stock attributes.
_,W=np.unique(np.rint(R/1e-6).astype('int64'),axis=0,return_inverse=True)
S=len(set(W));mask=np.zeros(len(R),bool)
weights=dict(zip(D['weight_names'],D['weights']))
for s in ('L','R'):
 blend=sum(weights.get(s+'_'+n,0) for n in ('Foot','ToeBase','Calf','CalfTwist01','CalfTwist02','Thigh'))
 mask |= (blend>.66)&(R[:,2]<.35)
 boot=D['boot'+s]; mask[boot[R[boot,2]<R[boot,2].min()+.030]]=False
 mask[D['phase'+s]]=False
 # Preserve all original potentially participating contact-triangle vertices.
 for f in XYZ:
  tf=D['contact'+s]; take=((f[tf,2]>=-.001)&(f[tf,2]<=.002)).all(1)
  mask[np.unique(tf[take])]=False
blocked=np.zeros(S,bool);blocked[W[~mask]]=True
groups=np.where(~blocked)[0]; cols=np.full(S,-1);cols[groups]=np.arange(len(groups));J=cols[W];n=len(groups)
assert n>300
MR=(J[E]>=0).any(1);TF=(J[F]>=0).any(1)
safe_edges=np.r_[D['left_ids'],D['right_ids']]
guard=np.zeros(len(E),bool);guard[safe_edges]=True
L=np.linalg.norm(R[E[:,1]]-R[E[:,0]],axis=1)
tri_xyz=R[F]
cross=lambda m:np.cross(m[:,1]-m[:,0],m[:,2]-m[:,0])
vec=cross(tri_xyz);base_area=np.linalg.norm(vec,axis=1)
aff=np.where(TF & (base_area>1e-9))[0]
left,right=D['left_ids'],D['right_ids']
def norms(x):return np.linalg.norm(x,axis=1)
edge_face={}
for i,tri in enumerate(F):
 for a,b in zip(tri,[tri[1],tri[2],tri[0]]):
  edge_face.setdefault(tuple(sorted((a,b))),[]).append(i)
stats=[]
solves=[]
for q,X in enumerate(XYZ):
 def geometry(Y):
  ds=Y[E[:,1]]-Y[E[:,0]];l=norms(ds)
  return ds,l,np.divide(l,L,out=np.ones_like(l),where=L>1e-10)
 _,old_dist,old=geometry(X)
 # Anatomical rest weight probe: knee blend zone is not an outsole.
 key={}
 for side,ee in [('L',left),('R',right)]:
  def edge_row(i):
   ij=E[i];return {'edge_i':int(i),'verts':ij.tolist(),'adjacent_source_triangle_indices':edge_face.get(tuple(ij),[]),'ratio':float(old[i]),
    'rest_xyz_m':R[ij].tolist(),'fixed':[bool(J[j]<0) for j in ij],
    'weight_vectors':[{k:round(float(v[j]),6) for k,v in weights.items() if v[j]>.001} for j in ij]}
  key[side]={'low':edge_row(ee[old[ee].argmin()]),'high':edge_row(ee[old[ee].argmax()])}
 # Reference signed orientation is original exact evaluated pose; collapsed
 # native triangles get a fallback rest normal transported by local rigid
 # rotation from one-ring would be needed. Never accept untestable ones.
 original=cross(X[F[aff]])
 olda=norms(original); normal=original/np.maximum(olda[:,None],1e-14)
 bad_source_degen=olda<=1e-12
 # One fixed broad trust-region solve per key with both legs in same system.
 # All graph edges exert a soft elastic continuity prior, guard edges a
 # narrow explicit target on violations, no possible floating boundaries.
 Y=X.copy(); total=np.zeros((n,3))
 use=np.where(MR & (L>.0004))[0];rel=E[use]; jj=J[rel]
 valid=jj>=0
 rr=np.broadcast_to(np.arange(len(use))[:,None,None],(len(use),2,3))
 cc=jj[:,:,None]*3+np.arange(3)[None,None,:]
 keep=np.broadcast_to(valid[:,:,None],cc.shape)
 I=diags(np.ones(n*3)*.25).tocsr()
 for it in range(12):
  dif,ll,ratio=geometry(Y)
  sel=ratio[use]
  active=guard[use]&((sel<.54)|(sel>1.84))
  target=np.where(active,np.clip(sel,.57,1.78)*L[use],old_dist[use])
  unit=dif[use]/np.maximum(ll[use,None],1e-15)
  stiff=np.where(active,15.0,.35)
  jac=np.stack((-unit,unit),axis=1)*stiff[:,None,None]
  A=coo_matrix((jac[keep],(rr[keep],cc[keep])),shape=(len(use),n*3)).tocsr()
  # Signed triangle area barrier: positive relative to original-pose normal.
  tv=Y[F[aff]]
  signed=(cross(tv)*normal).sum(1)
  risky=(signed<.32*base_area[aff])&~bad_source_degen
  chosen=aff[risky];tv=tv[risky];nn=normal[risky]
  da=np.stack((np.cross(tv[:,1]-tv[:,2],nn),np.cross(tv[:,2]-tv[:,0],nn),np.cross(tv[:,0]-tv[:,1],nn)),axis=1)
  tf=J[F[chosen]]
  ok=np.broadcast_to(tf[:,:,None]>=0,da.shape)
  ar=np.broadcast_to(np.arange(len(chosen))[:,None,None],da.shape)
  ac=tf[:,:,None]*3+np.arange(3)[None,None,:]
  cell=np.sqrt(base_area[chosen])
  aa=coo_matrix(((da/np.maximum(cell[:,None,None],1e-8)*10)[ok],(ar[ok],ac[ok])),shape=(len(chosen),n*3)).tocsr()
  br=(.45*base_area[chosen]-signed[risky])/np.maximum(cell,1e-8)*10
  step=lsmr(vstack((A,aa,I)),np.r_[(target-ll[use])*stiff,br,-.25*total.ravel()],atol=1e-5,btol=1e-5,maxiter=90)[0].reshape(n,3)
  sz=norms(step); step*=np.minimum(1,.003/np.maximum(sz,1e-8))[:,None]
  total+=step
  movable=J>=0;Y[movable]=X[movable]+total[J[movable]]
 assert np.array_equal(Y[J<0],X[J<0])
 _,_,new=geometry(Y)
 av=cross(Y[F[aff]])
 signed=(av*normal).sum(1)/base_area[aff]
 old_area=olda/base_area[aff]
 def stats_edge(r,idx):
  return {'low':float(min(r[idx])),'high':float(max(r[idx])),'bad':int(((r[idx]<.5)|(r[idx]>2)).sum())}
 stats.append({'key_ms':[0,75,150][q],'edge_provenance':key,'before_edges':{s:stats_edge(old,e) for s,e in [('L',left),('R',right)]},
  'after_edges':{s:stats_edge(new,e) for s,e in [('L',left),('R',right)]},
  'max_edit_mm':float(norms(Y-X).max()*1e3),'original_area_failed':int(((old_area<.5)|(old_area>2)).sum()),
  'corrected_signed_area_failed':int(((signed<.5)|(signed>2)|bad_source_degen).sum()),'corrected_flipped_relative_pose':int((signed<=0).sum()),
  'worst_signed_area':float(min(signed)),'max_signed_area':float(max(signed)),
  'worst_signed_face':{'id':int(aff[signed.argmin()]),'verts':F[aff[signed.argmin()]].tolist()},
  'fully_fixed_failed_guard_edges':int(np.sum((J[E[safe_edges]]<0).all(1)&((new[safe_edges]<.5)|(new[safe_edges]>2))))})
 solves.append(Y)
np.savez_compressed(p/'diagnostic-corrected-arrays.npz',xyz=np.stack(solves),edited=J>=0)
(p/'solve-report.json').write_text(json.dumps({'movable_unique':n,'affected_faces_investigated':len(aff),'source_keys':stats},indent=2)+'\n')
