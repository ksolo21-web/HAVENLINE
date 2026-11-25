import contextlib,io,json,types,hashlib,os
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
pros=Path(os.environ['SEALED_OPEN_PACKET']); seal=os.environ['OPEN_MANIFEST_SHA256']; assert hashlib.sha256((pros/'SHA256SUMS').read_bytes()).hexdigest()==seal
for row in (pros/'SHA256SUMS').read_text().splitlines():
 h,n=row.split(); assert hashlib.sha256((pros/n).read_bytes()).hexdigest()==h
source=(pros/'audit.py').read_text(); d=types.SimpleNamespace()
exec(compile(source[:source.index('old_c,old_cand=')],str(pros/'audit.py'),'exec'),vars(d))
D=json.loads((pros/'result.json').read_text())
for id0,label in [('source_positions','original_52j_candidate_positions_sha256'),('right_positions','right_patch_candidate_positions_sha256')]:
 assert hashlib.sha256(np.ascontiguousarray(getattr(d,id0)).tobytes()).hexdigest()==D[label]
P,V,F,tool=d.P,d.V,d.F,d.tool
b0=np.vstack([V,d.local['vertices']]); b1=np.vstack([d.source_positions,d.right_positions])
allF=np.vstack([d.remain,d.pface])
source_idx=np.r_[d.keep_face,np.arange(len(d.F),len(d.F)+len(d.pface))]
admitted=np.unique(allF)
assert np.array_equal(b0[d.unchanged],b1[d.unchanged]) and np.array_equal(b0[:len(V)][P[:,2]<-.2],b1[:len(V)][P[:,2]<-.2])
gaps={}
for side in ['R','L']:
 r=D['rig_two_hands'][side]; j=d.J['sides'][side]; assert r['own_finite_facet']==({'R':124,'L':276}[side])
 w=np.array(j['bary']); assert w.min()>0 and abs(w.sum()-1)<1e-12
 st=w@tool[r['own_finite_facet']]
 assert np.max(abs(st-r['old_band_station_m']))<1e-13
 ix=j['palm_vertex']; n=np.array(j['outward']); gap=(b1[ix]-st)@n
 gaps[side]={'direct_skin_palm_gap_mm':float(gap*1000),'published_rigid_prediction_mm':r['actual_anchor_signed_open_gap_mm'],'axis_angle_deg':r['axis_angle_deg']}
 assert abs(gap*1000-r['actual_anchor_signed_open_gap_mm'])<.001
def tnormal(f):
 n=np.cross(f[1]-f[0],f[2]-f[0]); return n/np.linalg.norm(n)
# Intersect each triangle independently with the other supporting plane; overlap in
# common-line coordinates. Strict if interior on either triangle (the other may
# be a refinement edge). Coplanars and endpoint-only contacts are not counted.
def interval(f,h,u):
 xyz=(f-h[0])@tnormal(h)
 tol=1e-10
 if np.max(np.abs(xyz))<=tol: return None
 dots=[]
 for i,j in zip(range(3), (1,2,0)):
  if abs(xyz[i])<=tol: dots.append(f[i]@u)
  if xyz[i]*xyz[j]<-tol**2: dots.append((f[i]+(f[j]-f[i])*xyz[i]/(xyz[i]-xyz[j]))@u)
 if len(dots)<2:return None
 return min(dots),max(dots), bool(xyz.min()<-tol and xyz.max()>tol)
def cross(a,b):
 u=np.cross(tnormal(a),tnormal(b)); mag=np.linalg.norm(u)
 if mag<1e-10:return False
 u/=mag
 z=interval(a,b,u); zz=interval(b,a,u)
 return z is not None and zz is not None and (z[2] or zz[2]) and min(z[1],zz[1])-max(z[0],zz[0])>1e-9
# Orthogonal stand-ins test physical triangle overlap, separated finite facets and coplanars.
ctrl=np.array([[0,0,0],[4,0,0],[0,4,0]],float)
other=np.array([[1,1,-4],[1,1,4],[2,2,0]],float)
assert cross(ctrl,other) and not cross(ctrl,other+[8,0,0]) and not cross(ctrl,ctrl)
def winding(counted):
 gs=[]
 for arr in np.array_split(counted,max(1,(len(counted)+149)//150)):
  A,B,C=(tool[None]-arr[:,None,None]).transpose(2,0,1,3)
  a,b,c=(np.linalg.norm(k,axis=2) for k in [A,B,C]); dd=lambda x,y:np.einsum('ijk,ijk->ij',x,y)
  gs.extend(np.rint(np.arctan2(dd(np.cross(A,B),C),a*b*c+a*dd(B,C)+b*dd(C,A)+c*dd(A,B)).sum(1)/(2*np.pi)).astype(int))
 vals,n=np.unique(gs,return_counts=True)
 return dict(zip(vals.tolist(),n.tolist()))
def tool_intersections(geo):
 T=geo[allF]; lo=tool.min(1);hi=tool.max(1); mi=T.min(1);ma=T.max(1)
 near=np.flatnonzero((mi<=hi.max(0)).all(1)&(ma>=lo.min(0)).all(1)); hits=[]
 for i in near:
  for j in np.flatnonzero((mi[i]<=hi).all(1)&(ma[i]>=lo).all(1)):
   if cross(T[i],tool[j]):hits.append((int(source_idx[i]),int(j)))
 wc=geo[admitted]; wc=wc[((wc>=lo.min(0))&(wc<=hi.max(0))).all(1)]
 return hits,winding(wc)
before,w0=tool_intersections(b0); after,w1=tool_intersections(b1)
assert len(before)==298 and not after and set(w1)=={0} and sum(v for k,v in w0.items() if k!=0)==631
local={}
for side in ('R','L'):
 ids=np.unique(d.s[side+'_loop_source_vertex_edges'])
 web=np.unique(d.s['left_web_material_edges']) if side=='L' else d.web
 Q,e=d.Qp[side][1]
 def delta(ids):return float(np.max(np.linalg.norm((b1[ids]-e)@Q+e-b0[ids],axis=1)))
 entry={'cuff_rigid_rel_err_m':delta(ids),'web_rows':len(web),'web_expected_rigid_rel_err_m':delta(web)}
 if side=='R':entry['seam_rel_err_m']=delta(d.se); entry['patch_every_appended_rel_err_m']=delta(np.arange(len(V),len(b1)))
 local[side]=entry
# Exact sampled static bounds for each contacted outer arm against the unchanged
# coat/torso and opposite arm. Use all moved faces and all nonmoving source faces
# within the union of old/new arm AABBs, not visual occlusion or animation.
S=np.zeros(len(b1),np.int8)
S[d.movable['R']]=1;S[d.movable['L']]=2;S[len(V):]=1
side1=(S[allF]==1).any(1);side2=(S[allF]==2).any(1)
assert not (side1&side2).any()
static=(~side1)&(~side2)
# Collapse only preexisting exact coordinate aliases for adjacency exclusions.
_, alias=np.unique(b0,axis=0,return_inverse=True)
def pair_test(geo, lhs, rhs):
 a=geo[allF[lhs]]; b=geo[allF[rhs]]; alo=a.min(1); ahi=a.max(1); blo=b.min(1);bhi=b.max(1)
 in_rng=((blo<=ahi.max(0)).all(1)&(bhi>=alo.min(0)).all(1))
 b=b[in_rng]; rhs=rhs[in_rng];blo=blo[in_rng];bhi=bhi[in_rng]
 arad=np.linalg.norm((ahi-alo)*.5,axis=1);brad=np.linalg.norm((bhi-blo)*.5,axis=1)
 if not len(b):return set(),len(lhs),0
 bins=(0,.0015,.003,.006,.012,.024,.045,np.inf)
 out=set()
 for w,z in zip(bins[:-1],bins[1:]):
  p=np.flatnonzero((brad>=w)&(brad<z))
  if not len(p):continue
  btree=cKDTree((blo[p]+bhi[p])/2); near=btree.query_ball_point((alo+ahi)/2,arad+max(brad[p]))
  for k, js in enumerate(near):
   jq=p[np.array(js,dtype=int)]
   jq=jq[((alo[k]<=bhi[jq]).all(1)&(ahi[k]>=blo[jq]).all(1))]
   ia=lhs[k]
   for z in jq:
    ib=rhs[z]
    if not np.isin(alias[allF[ia]],alias[allF[ib]]).any() and cross(a[k],b[z]):
     out.add((int(source_idx[ia]),int(source_idx[ib])))
 return out,len(lhs),len(rhs)
controls=[]
for i,j,k,l in D['body_self_clearance']['first_20_new_face_indices_and_relative_types']:
 a,b=allF[[i,j]]
 previous=cross(b0[a],b0[b]); now=cross(b1[a],b1[b])
 controls.append([int(source_idx[i]),int(source_idx[j]),bool(previous),bool(now),k,l])
assert all(not previous and now for i,j,previous,now,k,l in controls)
print(json.dumps({'source_report_body_new_control_pairs':controls,'held_static_tool_strict_baseline_open':[len(before),len(after)],'all_source_and_mounted_palm_nonzero_wind_baseline_open':[w0,w1],
 'finite_stations':[124,276],'local_cuff_web':local,'unchanged_source_rows':len(d.unchanged),'protected_lower_unchanged':int((P[:,2]<-.2).sum()),'palm_gaps':gaps,'producer_body_totals_custody':D['body_self_clearance']['new_strict_pairs']},sort_keys=True,indent=2))
