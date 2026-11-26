"""Build an actual source-anchored continuous field; no weights, transforms, or meshes are edited."""
import hashlib,contextlib,io,sys,json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.csgraph import connected_components,dijkstra
from scipy.sparse.linalg import spsolve
d=Path(__file__).resolve().parents[1]/'hvn-l1-c1-stock66-contact-first-v1'
assert hashlib.sha256((d/'SHA256SUMS').read_bytes()).hexdigest()=='5894bae40aa1486de7ea979eeabe2c1a0007124afe35c6114a75ca4e2a7d21fd'
for ln in (d/'SHA256SUMS').read_text().splitlines():
 h,p=ln.split();assert hashlib.sha256((d/p).read_bytes()).hexdigest()==h
sys.path.insert(0,str(d))
with contextlib.redirect_stdout(io.StringIO()):
 import run as r
V,TR,E=r.V,r.TR,r.edges
n=r.weld.max()+1
bits=np.eye(4,dtype=bool)
# Graph of actual source triangles at 1 micrometre welded rest seams: no off-surface shortcut.
ed=np.unique(np.sort(r.weld[E],axis=1),axis=0);ed=ed[ed[:,0]!=ed[:,1]]
v=np.zeros((n,3));v[r.weld]=V
g=np.linalg.norm(v[ed[:,0]]-v[ed[:,1]],axis=1)
hw=[n for n,v in enumerate(r.names) if 'BootFastener' in v]
assert len(hw)==8
out={}
fields={}
for s,idx,sector,near,F,qs,fwd in r.RPT:
 th,c,f,t=idx
 weight=lambda a:(r.W*np.isin(r.JS,a)).sum(1)
 own=weight(r.sub(th))
 toe=weight([t]); rigid_foot=weight([f]); calf=weight([g for g in r.sub(c) if g not in set(r.sub(f)) and g not in hw])
 hardware=weight(hw)
 y=V[:,1]; low=np.min(y[near])
 ankle=np.linalg.inv(r.inv[f])[1,3]; knee=np.linalg.inv(r.inv[c])[1,3]
 # Complete source lower-leg graph capped in a protected anchor belt below knee.
 region=(own>.45)&(y<=knee+.015)
 eligible=np.zeros(n,bool); np.logical_or.at(eligible,r.weld,region)
 opposite=np.zeros(n,bool);np.logical_or.at(opposite,r.weld,(own<.10))
 eligible&=~opposite
 E0=ed[eligible[ed].all(1)];length=np.linalg.norm(v[E0[:,0]]-v[E0[:,1]],axis=1)
 D=coo_matrix((np.r_[length,length],(np.r_[E0[:,0],E0[:,1]],np.r_[E0[:,1],E0[:,0]])),shape=(n,n)).tocsr()
 core=((y<low+.045)&near)|(toe>0)|(hardware>0)|sector
 cuff=region&(calf>=rigid_foot)&(calf>.25)&(y>ankle+.6*(knee-ankle))&~core
 def seeds(mask):return np.unique(r.weld[region&mask])
 lower,upper=seeds(core),seeds(cuff)
 conflict=np.intersect1d(lower,upper)
 print(s,"lower/upper",len(lower),len(upper),"overlap",len(conflict),"ankle/knee",ankle,knee,file=sys.stderr)
 assert not len(conflict) and min(len(lower),len(upper))>0
 dl=dijkstra(D,indices=lower,min_only=True,directed=False)
 du=dijkstra(D,indices=upper,min_only=True,directed=False)
 valid=np.isfinite(dl)&np.isfinite(du)&eligible
 U=np.zeros(n);U[upper]=1
 Free=np.flatnonzero(valid&~np.isin(np.arange(n),np.r_[lower,upper]))
 allowed=E0[valid[E0].all(1)]; L=np.linalg.norm(v[allowed[:,0]]-v[allowed[:,1]],axis=1)
 A=coo_matrix((np.r_[1/L,1/L],(np.r_[allowed[:,0],allowed[:,1]],np.r_[allowed[:,1],allowed[:,0]])),shape=(n,n)).tocsr()
 K=diags(np.asarray(A.sum(1)).ravel())-A
 val=spsolve(K[Free][:,Free],np.asarray(A[Free][:,upper].sum(1)).ravel())
 U[Free]=val
 assert np.isfinite(val).all() and np.min(val)>=-1e-9 and np.max(val)<=1+1e-9
 assert (U[lower]==0).all() and (U[upper]==1).all()
 one=np.flatnonzero(eligible&np.isfinite(dl)&~np.isfinite(du));two=np.flatnonzero(eligible&~np.isfinite(dl)&np.isfinite(du))
 detached=np.flatnonzero(eligible&~np.isfinite(dl)&~np.isfinite(du))
 worst=(42935,43501) if s=='L' else (9389,10731)
 fields[s]=(idx,lower,upper,Free,U,K,eligible,valid)
 out[s]=dict(graph_rows=int(eligible.sum()),anchor_heel_toe_hardware_weld_rows=len(lower),proximal_calf_anchor_weld_rows=len(upper),transition_between_anchors_weld_rows=len(Free),one_sided_distal_rows=len(one),one_sided_proximal_rows=len(two),unanchored_rows=len(detached),transition_source_unsigned_min_max=[float(val.min()),float(val.max())],old_decisive_edge_rows=list(worst),old_decisive_edge_in_transition=[bool(i in set(Free)) for i in r.weld[np.array(worst)]],old_decisive_edge_proximal_coord=[float(U[i]) for i in r.weld[np.array(worst)]],preserved_scope='source weights/rest/mesh/assets unchanged; unitless graph development coordinate only')
print(json.dumps(dict(status='STAGED_GEODESIC_ARTICULATION_COORDINATE_NOT_A_BIND_OR_POSE',native_skin=r.mp['native_array_sha256'],parts=out),indent=2))
