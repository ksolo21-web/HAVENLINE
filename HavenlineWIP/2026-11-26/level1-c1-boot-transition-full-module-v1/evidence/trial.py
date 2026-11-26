import io,hashlib,contextlib,sys,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
root=Path(__file__).resolve().parents[1]
pins={'hvn-l1-stock66-lowerbody-module-stage-v1':'880044262bf19771491c6ad0fa427b2b1407e03e07132400030a161a9cef6e2b','hvn-l1-stock66-rigid-boot-adapter-trial-v1':'85b23495f94dbe8869a59bba392afd5a86fd286931bcc63947ca84bf0b29f0b5'}
for n,h in pins.items():
 d=root/n
 assert hashlib.sha256((d/'SHA256SUMS').read_bytes()).hexdigest()==h
 for line in (d/'SHA256SUMS').read_text().splitlines():
  h,p=line.split();assert hashlib.sha256((d/p).read_bytes()).hexdigest()==h
with contextlib.redirect_stdout(io.StringIO()):
 import field as f
 from runpy import run_path
 a=run_path(str(root/'hvn-l1-stock66-rigid-boot-adapter-trial-v1/trial.py'))
r=f.r
Z=a['Z']; end=a['end']; V=r.V; TR=r.TR; E=r.edges; W=r.W; JS=r.JS; weld=r.weld
assert np.isfinite(Z).all() and np.array_equal(end[r.names.index('Root')],r.J[r.names.index('Root')])
out=Z.copy();report={}; touched=np.zeros(len(V),bool)
compat=json.loads((root/'hvn-l1-stock66-lowerbody-module-stage-v1/result.json').read_text())
assert compat['parts']==f.out
world=r.asset_world
S=world[0,0]
WInv=np.linalg.inv(world)
for side,(idx,low,up,free,U,K,elig,val) in f.fields.items():
 th,calf,foot,toe=idx
 def bake(T,source):
  mat=WInv@T@r.inv[source]
  M=mat[:3,:3]; Q=Rotation.from_matrix(M).as_matrix()
  assert np.max(abs(M-Q))<3e-6
  return Q,mat[:3,3]
 lo,to=bake(end[foot],foot); hi,ti=bake(end[calf],calf)
 faxis=Rotation.from_matrix(lo.T@hi).as_rotvec()
 UV=U[weld]
 rotations=Rotation.from_rotvec(UV[:,None]*faxis).as_matrix()
 rotations=lo@rotations
 assert np.min(np.linalg.det(rotations))>.999999
 # Screw-frame rotation and linear anchor translation chosen in actor space.
 xyz=(rotations@V[:,:,None])[:,:,0]+to+(ti-to)*UV[:,None]
 xyz=xyz@world[:3,:3].T+world[:3,3]
 # Residual on exact actual anchors is independent of the position parameterization.
 # Equality of source key on aliases is checked before any movement.
 wall=np.r_[low,up]
 anchor=np.isin(weld,wall)
 rr=Z-xyz
 gg=np.zeros((weld.max()+1,3));gg[weld[anchor]]=rr[anchor]
 alias_error=float(np.max(np.linalg.norm(rr[anchor]-gg[weld[anchor]],axis=1)))
 assert alias_error<2e-6,alias_error
 add=spsolve(K[free][:,free],-K[free][:,wall]@gg[wall])
 assert np.isfinite(add).all()
 gg[free]=add
 candidates=np.isin(weld,free)
 assert not np.any(candidates&touched)
 assert not np.any(candidates&anchor)
 # Keep exact source split seam separation, avoiding any wholesale neutral merge.
 G=np.zeros((len(gg),3));G[weld[candidates]]=Z[candidates]
 twin=float(np.max(np.linalg.norm(Z[candidates]-G[weld[candidates]],axis=1)))
 result=xyz[candidates]+gg[weld[candidates]]
 out[candidates]=result
 touched|=candidates
 # Keep designated real authored bands, actual hardware & all ToeBase influenced rows.
 toe_weight=(W*(JS==toe)).sum(1)
 hw_weight=(W*np.isin(JS,a['hw'])).sum(1)
 assert np.array_equal(out[(toe_weight>0)|(hw_weight>0)],Z[(toe_weight>0)|(hw_weight>0)])
 report[side]=dict(free_weld_rows=len(free),source_rows_moved=int(candidates.sum()),anchor_count=len(wall),alias_anchor_disagreement_um=alias_error*1e6,existing_animated_free_alias_max_gap_mm=twin*1000,median_delta_mm=float(np.median(np.linalg.norm((out-Z)[candidates],axis=1))*1000),maximum_delta_mm=float(np.max(np.linalg.norm((out-Z)[candidates],axis=1))*1000),rotation_determinant_floor=float(np.linalg.det(rotations[candidates]).min()))
assert np.array_equal(out[~touched],Z[~touched])
for side,idx,sector,near,F,qs,x in r.RPT:
 P=out[:,[0,2,1]].copy()
 for i in np.unique(np.r_[np.flatnonzero(near),F.ravel()]):P[i,2]-=r.height(*P[i,:2])
 metrics=report[side]
 metrics.update(visible_boot_low_mm=float(P[near,2].min()*1000),finite_support=r.connected(P,F,weld))
 H0=(W*np.isin(JS,idx[1:])).sum(1)
 rs=1.75/np.ptp(V[:,1])
 historical=(H0[E].mean(1)>.9)&(r.lengths*rs/S>.0008)&((V[E,1].mean(1)-V[:,1].min())*rs<.30)
 extended=(np.sum(W*np.isin(JS,r.sub(idx[0])),axis=1)[E].mean(1)>.9)&(r.lengths>.0008)&(V[E,1].mean(1)<V[near,1].min()+.30)
 ratio=lambda O:np.linalg.norm(O[E[:,0]]-O[E[:,1]],axis=1)/np.maximum(r.lengths,1e-12)
 old=ratio(Z);new=ratio(out)
 fail=lambda v:(v<.5)|(v>2.)
 tests=lambda m:dict(old=int((fail(old)&m).sum()),candidate=int((fail(new)&m).sum()),newly_failed=int((fail(new)&~fail(old)&m).sum()),worst_ratio=float(new[m].min()),max_ratio=float(new[m].max()))
 metrics.update(historical=tests(historical),extended=tests(extended))
# Exact triangle scope: all edited facets vs all potentially overlapping local or remote facets.
active=np.flatnonzero(touched[TR].any(1))
def pairs(p):
 P=p[TR]; mn=P.min(1); mx=P.max(1); center=(mn+mx)*.5
 radix=np.linalg.norm(mx-center,axis=1); view=cKDTree(center)
 # Global largest bound is a safe broad-phase radius; per-axis AABB follows.
 maximum=radix.max()
 found=set()
 for i in active:
  ids=np.array(view.query_ball_point(center[i],maximum+radix[i]+1e-9),dtype=int)
  ids=ids[((mn[ids]<=mx[i]+1e-9)&(mx[ids]>=mn[i]-1e-9)).all(1)]
  ids=ids[~np.isin(weld[TR[ids]],weld[TR[i]]).any(1)]
  for j in ids:
   e=tuple(sorted((i,int(j))))
   if e in found:continue
   if a['strict'](P[i],P[j]):found.add(e)
 return found
p0=pairs(Z);p1=pairs(out)
X=Z[TR[active]];Y=out[TR[active]]
normal=lambda P:np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0])
n0,n1=normal(X),normal(Y)
dot=(n0*n1).sum(1)
print(json.dumps(dict(status='REJECT_OR_HOLD_EXACT_ONE_OFFLINE_TRANSPORT',parts=report,patch_triangles=len(active),strict_nonadjacent_source_pairs=[len(p0),len(p1)],new_strict_pairs=len(p1-p0),example_new_strict_pair=list(map(int,min(p1-p0))) if p1-p0 else None,posed_base_to_candidate_orientation_nonpositive=int((dot<=0).sum()),unchanged_actual_untargeted_rows=int((~touched).sum()),toe_vertex_19335_snow_height_mm=float((out[19335,1]-r.height(*out[19335,[0,2]]))*1000)),indent=2))
