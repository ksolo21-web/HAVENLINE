from pathlib import Path
import sys,json,hashlib,contextlib,io
import numpy as np
from scipy.sparse import coo_matrix
from scipy.optimize import lsq_linear
repo=Path(__file__).resolve().parent.parent/'hvn-l1-c1-stock66-contact-first-v1'
assert hashlib.sha256((repo/'SHA256SUMS').read_bytes()).hexdigest()=='5894bae40aa1486de7ea979eeabe2c1a0007124afe35c6114a75ca4e2a7d21fd'
for line in (repo/'SHA256SUMS').read_text().splitlines():
 sha,f=line.split();assert hashlib.sha256((repo/f).read_bytes()).hexdigest()==sha
sys.path.insert(0,str(repo))
with contextlib.redirect_stdout(io.StringIO()):
 import run as r
V,TR,JS,W=r.V,r.TR,r.JS,r.W
J=r.new.copy()
# Exact original ToeBase relative transform from captured stance, no candidate pitch tune.
i=r.names.index('R_ToeBase');ft=r.names.index('R_Foot');desired=J[ft]@np.linalg.inv(r.J[ft])@r.J[i]
J[r.sub(i)]=(desired@np.linalg.inv(J[i]))@J[r.sub(i)]
assert np.max(np.abs(np.linalg.inv(J[ft])@J[i]-np.linalg.inv(r.J[ft])@r.J[i]))<2e-12
start=r.verts(J); X=start.copy()
weights=np.zeros((len(V),66),dtype=np.int32)
np.add.at(weights,(np.arange(len(V))[:,None],JS),np.rint(W*65535).astype(np.int32))
new=weights.copy(); ed=r.edges; p4=r.p4; widx=r.weld
report={}
mat=J@r.inv
for side,idx,sector,near,F,qs,fwd in r.RPT:
 # Candidate uses only principal Calf and Foot shares; untouched twist channels stay fixed.
 calf,foot,toe=idx[1:]
 sums=weights[:,idx[1:]].sum(1)/65535
 rs=1.75/np.ptp(V[:,1])
 H=(sums[ed].mean(1)>.9)&(r.lengths*rs/r.asset_world[0,0]>.0008)&((V[ed,1].mean(1)-V[:,1].min())*rs<.30)
 pairs=ed[H]; lens=r.lengths[H]
 ratios=lambda S:np.linalg.norm(S[pairs[:,1]]-S[pairs[:,0]],axis=1)/lens
 b=ratios(start); bad=(b<.5)|(b>2.)
 ring=np.unique(ed[np.isin(ed,pairs[bad]).any(1)])
 support=np.unique(np.r_[np.flatnonzero(sector),F.ravel()])
 weight_mat=weights[:,[calf,foot]]
 # Lock all source toe classes, rest outsole floor band, actual authored soft support patch,
 # and any row influenced by a boot fastener. Do not add a slot to existing full rows.
 hardware=[k for k,name in enumerate(r.names) if 'BootFastener' in name]
 live_slots=(weights>0).sum(1)
 allowed=np.isin(np.arange(len(V)),ring)&~np.isin(np.arange(len(V)),support)&(weights[:,toe]==0)&(weights[:,hardware].sum(1)==0)&(V[:,1]>V[near,1].min()+.040)&(weight_mat.sum(1)>0)&((live_slots<4)|(weight_mat>0).all(1))
 groups=[]; active={}
 for group in np.unique(widx[allowed]):
  g=np.flatnonzero(widx==group)
  if not allowed[g].all() or not np.array_equal(weights[g],np.broadcast_to(weights[g[0]],weights[g].shape)):continue
  active[group]=len(groups);groups.append(g)
 col=np.array([active.get(g,-1) for g in widx])
 C=(p4@(mat[foot]-mat[calf]).T)[:,:3]
 if not groups: raise SystemExit('no safe groups')
 ir=[];ic=[];vv=[]; rhs=[]
 def add(seq,y):
  n=len(rhs);rhs.append(y)
  for c,x in seq:
   if c>=0:ir.append(n);ic.append(c);vv.append(x)
 for k,(a,d) in enumerate(pairs):
  ia,ib=col[[a,d]]
  if ia<0 and ib<0:continue
  D=start[d]-start[a]; dist=np.linalg.norm(D); L=lens[k]
  if dist<1e-8:continue
  v=D/dist
  goal=np.clip(b[k],.80,1.25) if bad[k] else b[k]
  importance=1. if bad[k] else .25
  add([(ia,-importance*(v@C[a])/L),(ib,importance*(v@C[d])/L)],importance*(goal-b[k]))
  if ia!=ib:add([(ia,-.2),(ib,.2)],0)
 for j in range(len(groups)):add([(j,.10)],0)
 n=np.array([g[0] for g in groups])
 lo=-weights[n,foot]/65535;hi=weights[n,calf]/65535
 fit=lsq_linear(coo_matrix((vv,(ir,ic)),shape=(len(rhs),len(groups))).tocsr(),np.array(rhs),bounds=(lo,hi),tol=1e-8,max_iter=80)
 m=0
 for g,d in zip(groups,np.rint(fit.x*65535).astype(int)):
  if d==0:continue
  new[g,foot]+=d;new[g,calf]-=d;m+=len(g)
  X[g]+=C[g]*(d/65535)
 assert (new>=0).all() and np.array_equal(new.sum(1),weights.sum(1)) and ((new>0).sum(1)<=4).all() and np.array_equal(new[:,toe],weights[:,toe])
 assert np.array_equal(X[support],start[support]),side
 def support_state(data):
  P=data[:,[0,2,1]].copy()
  for i in np.unique(np.r_[np.flatnonzero(near),F.ravel()]):P[i,2]-=r.height(*P[i,:2])
  return dict(min_mm=float(P[near,2].min()*1000),triangle_contact=r.connected(P,F,r.weld))
 f=ratios(X); reject=(f<.5)|(f>2.)
 fixed=np.flatnonzero(bad&(col[pairs]<0).all(1)); first=int(fixed[np.argmin(b[fixed])]) if len(fixed) else None
 remaining=dict(rows=pairs[first].tolist(),length_rest_mm=float(lens[first]*1000),ratio_before_after=[float(b[first]),float(f[first])],pins=dict(toe=(weights[pairs[first],toe]>0).tolist(),sole_height_mm=((V[pairs[first],1]-V[near,1].min())*1000*r.asset_world[0,0]).tolist(),hardware=(weights[pairs[first]][:,hardware].sum(1)>0).tolist(),touches_support_region=np.isin(pairs[first],support).tolist(),all_weight_slots_used=(live_slots[pairs[first]]==4).tolist())) if first is not None else None
 bootrows=np.flatnonzero(near); d0=[start[row,1]-r.height(*start[row,[0,2]]) for row in bootrows]; bottom=bootrows[int(np.argmin(d0))]
 source_min=dict(row=int(bottom),candidate_unchanged=bool(np.array_equal(start[bottom],X[bottom])),height_before_mm=float(min(d0)*1000),has_protected_toe=bool(weights[bottom,toe]>0),is_contact_patch=bool(np.isin(bottom,support)))
 report[side]=dict(admitted_groups=len(groups),changed_rows=m,hard_fixed_failed_at_start=int((bad&(col[pairs]<0).all(1)).sum()),narrow_guard_before_after=[int(bad.sum()),int(reject.sum())],new_bad=int((reject&~bad).sum()),old_bad_cleared=int((~reject&bad).sum()),min_after=float(f.min()),solver_status=int(fit.status),fixed_edge_witness=remaining,most_penetrating_source_point=source_min,lowest_and_support_before=support_state(start),lowest_and_support_after=support_state(X))
changed=np.any(new!=weights,axis=1)
mix=np.einsum('nc,ncb->nb',new[changed].astype(float)/65535,np.array([p4[changed]]*66).transpose(1,0,2))
assert np.max(np.abs(mix-(weights[changed].sum(1)/65535)[:,None]*p4[changed]))<1e-13
assert np.array_equal(new[~changed],weights[~changed])
print(json.dumps(dict(status='NO_ADMISSION',scope='same failed authored stance, exact original toe channel restored, one detached weight solution',report=report),indent=2))
