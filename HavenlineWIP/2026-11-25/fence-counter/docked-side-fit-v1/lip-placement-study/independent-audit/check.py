"""Independent bounded native triangle and pivot analysis using archived data only."""
import hashlib,json,struct,sys,numpy as np
from itertools import permutations
from pathlib import Path
from scipy.spatial import ConvexHull
from scipy.optimize import minimize
p,s,g=map(Path,sys.argv[1:])
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert H(p/'SHA256SUMS')=='7bd474cebcd6a0c4779b80b6476675ca92df65b9c4d5fbee86c3d3760da55d7d'
for a,n in (x.split(maxsplit=1) for x in (p/'SHA256SUMS').read_text().splitlines()):assert H(p/n)==a
R=json.loads((p/'result.json').read_text())
F=R['source_exact_hashes']; assert H(g)==F['donor_binary'] and H(s/'native/counter.json')==F['native_donor_surface'] and H(s/'result.json')==F['prior_frozen_poses']
prev=json.loads((s/'result.json').read_text())
raw=json.loads((s/'native/counter.json').read_text())
TT={x['surface']:np.asarray(x['positions'])[np.asarray(x['triangles']).reshape(-1,3)] for x in raw}
D=np.concatenate(list(TT.values()));snum=np.concatenate([np.full(len(x),i) for i,x in TT.items()]); tid=np.concatenate([np.arange(len(x)) for x in TT.values()])
assert len(D)==13624
normal=np.cross(D[:,1]-D[:,0],D[:,2]-D[:,0]);N=normal/np.maximum(np.linalg.norm(normal,axis=1),1e-30)[:,None]
B=g.read_bytes();l=struct.unpack_from('<I',B,12)[0];G=json.loads(B[20:20+l])
def ac(i):
 a=G['accessors'][i]; b=G['bufferViews'][a['bufferView']]; v={'VEC3':3,'SCALAR':1}[a['type']]
 return np.frombuffer(B,{5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']],count=a['count']*v,offset=l+28+a.get('byteOffset',0)+b.get('byteOffset',0)).reshape(-1,v)
pr=G['meshes'][0]['primitives'][2]; assert G['materials'][pr['material']]['name']=='HL_wood'; source_wood=ac(pr['attributes']['POSITION'])[ac(pr['indices']).reshape(-1,3)]
mat=lambda k:int(np.flatnonzero((snum==k[0])&(tid==k[1]))[0])
def cast(A,B):
 X=np.asarray(A,float);Q=np.asarray(B,float);W=Q-X; d=np.linalg.norm(W); u=W/d
 n=N@u;ok=np.abs(n)>1e-12
 t=np.einsum('ij,ij->i',D[:,0]-X,N)/np.where(ok,n,1.)
 P=X+t[:,None]*u
 for j in range(3):ok&=np.einsum('ij,ij->i',np.cross(D[:,(j+1)%3]-D[:,j],P-D[:,j]),N)>=-1e-10
 idx=np.flatnonzero(ok&(t>1e-5)&(t<d+5e-6))
 if not len(idx):return None,d
 i=idx[np.argmin(t[idx])]
 return (int(snum[i]),int(tid[i]),float(t[i])),d
def dmin_bound(A,B,T):
 # Independent convex minimization on reported nearest triangle; it verifies
 # upper bounds on clear path sizes, not claimed global clearance.
 X=np.asarray(A); Y=np.asarray(B);T=np.asarray(T)
 V=np.column_stack((Y-X,T[0]-T[1],T[0]-T[2])); O=X-T[0]
 c=lambda x: (O+V@x)@(O+V@x)
 o=minimize(c,[.5,.3,.3],jac=lambda x:2*V.T@(O+V@x),bounds=[(0.,1.)]*3,constraints={'type':'ineq','fun':lambda x:1-x[1]-x[2],'jac':lambda x:np.array([0.,-1.,-1.])},method='SLSQP',options={'ftol':1e-17,'maxiter':200})
 assert o.success;return float(np.sqrt(o.fun))
def clip_points(T, target):
 X=T[:,[0,2]]
 inv=np.linalg.inv((X[1:]-X[0]).T)
 xy=target[[0,2]]; amin,amax=xy-.025,xy+.025
 R=[np.array([x,z]) for x in (amin[0],amax[0]) for z in (amin[1],amax[1])]
 all_=[]
 def triCoords(p):u=inv@(p-X[0]);return np.r_[1-u.sum(),u]
 for v in X:
  if np.all(v>=amin-1e-12) and np.all(v<=amax+1e-12):all_.append(v)
 for v in R:
  if min(triCoords(v))>=-1e-12:all_.append(v)
 for u,v in zip(X,np.roll(X,-1,axis=0)):
  D=v-u
  for k in range(2):
   if abs(D[k])<1e-15:continue
   for c in (amin[k],amax[k]):
    p=(c-u[k])/D[k]
    if 0<=p<=1 and amin[1-k]-1e-13<=(u+p*D)[1-k]<=amax[1-k]+1e-13:all_.append(u+p*D)
 all_=np.array(all_)
 if len(all_)<3 or np.linalg.matrix_rank(all_[1:]-all_[0])<2:return 0.,[]
 return ConvexHull(all_).volume,[float(triCoords(x)@T[:,1]) for x in all_]
def intersects_box(T, C, r):
 # separating axis test for a triangle vs axis-aligned air box
 X=T-C;E=np.eye(3);edges=np.roll(X,-1,axis=0)-X
 axes=np.vstack([E,np.cross(edges[0],edges[1]),np.cross(edges[:,None,:],E[None,:,:]).reshape(-1,3)])
 m=X@axes.T;b=np.abs(axes)@r
 return not np.any((m.max(0)<-b-1e-12)|(m.min(0)>b+1e-12))
cot={};checks=[]
for side,rep in R['proposed_unbound_two_sided_patches'].items():
 center=np.array(rep['actual_rest']['point']); hover=np.array(rep['point_50mm_above']);assert np.allclose(hover-center,[0,.05,0],atol=1e-14,rtol=0)
 c=rep['actual_rest'];k=mat([c['surface'],c['triangle']]); sf=c['source_glb_facet'][1]
 facet=source_wood[sf]
 assert min(np.max(abs(D[k]-facet[list(i)])) for i in permutations(range(3)))<4.805e-5
 # Read full donor, not a worktop proxy, and require known original wood rest.
 hit,d=cast([center[0],1.19,center[2]],[center[0],.89,center[2]])
 assert hit[:2]==(c['surface'],c['triangle']) and abs(1.19-hit[2]-center[1])<1e-12
 A=[];Y=[];foot=rep['footprint']
 for v in foot['projected_area_pieces']:
  ix=mat([v['native_surface'],v['native_triangle']]);f=source_wood[v['source_glb_triangle']]
  assert min(np.max(abs(D[ix]-f[list(i)])) for i in permutations(range(3)))<4.805e-5
  xx,yy=clip_points(D[ix],center);assert abs(xx-v['projected_area_m2'])<1e-14
  A.append(xx);Y.extend(yy)
 assert abs(sum(A)-.0025)<1e-13
 assert abs(max(Y)-min(Y)-foot['exact_clipped_height_span_m'])<1e-12
 lo=np.array([center[0]-.025,max(Y)+.001,center[2]-.025]); hi=np.array([center[0]+.025,hover[1],center[2]+.025])
 pre=np.flatnonzero(((D.max(1)>=lo)&(D.min(1)<=hi)).all(1))
 assert not any(intersects_box(D[ix],(lo+hi)/2,(hi-lo)/2) for ix in pre)
 hit,l=cast(hover,center);assert hit[:2]==(c['surface'],c['triangle']) and abs(hit[2]-l)<1e-9
 def test(origin,target,q):
    rr,d=cast(origin,target);other=q['first_actual_donor_hit']
    assert abs(d-q['length_m'])<1e-9
    if rr is None:assert other is None
    else:assert rr[:2]==(other['surface'],other['triangle']) and abs(rr[2]-other['distance_m'])<1e-9
    return bool(other is None or d-other['distance_m']<=.0005)
 calls=[];dists=[]
 for tag,row in rep['exact_axial_and_sideways_pivot_probes'].items():
  saved=prev['sites'][tag]; assert H(s/'native'/(tag+'.json'))==row['pose_sha256']==saved['real_readback_sha256']
  for k,o in row['origins'].items():
   X=np.array(o['exact_pose_pivot']);assert np.array_equal(X,saved['native_pose']['anatomy'][k])
   r1=test(X,center,o['direct_to_actual_rest']);h1=test(X,hover,o['direct_to_hypothetical_50mm_hover'])
   sig={'native_pose':tag,'pivot':k,'unobstructed_direct_rest':r1,'unobstructed_direct_hover':h1}
   if k!='Head':
    c=o['concept_only_lift_then_level_hover'];W=np.array([X[0],hover[1],X[2]]);assert np.array_equal(W,c['waypoint'])
    assert test(X,W,c['vertical_lift']) and test(W,hover,c['level_transfer'])
    ds=[]
    for f,a,b in [(c['vertical_lift'],X,W),(c['level_transfer'],W,hover)]:
      bound=dmin_bound(a,b,TT[f['nearest_surface_triangle'][0]][f['nearest_surface_triangle'][1]])
      assert abs(bound-f['minimum_segment_to_donor_surface_distance_m'])<1e-6
      ds.append(bound)
    dists.append(min(ds));sig['lift_and_level_min_witness_upperbound_m']=min(ds)
    w=o['direct_to_hypothetical_50mm_hover']
    if h1:
      bound=dmin_bound(X,hover,TT[w['nearest_surface_triangle'][0]][w['nearest_surface_triangle'][1]])
      assert abs(bound-w['minimum_segment_to_donor_surface_distance_m'])<1e-6
      sig['direct_hover_min_witness_upperbound_m']=bound
   calls.append(sig)
 assert not any(x['unobstructed_direct_rest'] for x in calls)
 assert all(x['unobstructed_direct_hover'] for x in calls if x['pivot']=='Head')
 cot[side]={'exact_wood_surface_and_center_3d':center.tolist(),'square_area_m2':sum(A),'height_span_m':max(Y)-min(Y),'donor_facets_touch_hover_air_box':0,'pivot_traces':calls,'minimum_existing_knife_edge_clearance_witness_for_lift_m':min(dists)}
print(json.dumps({'no_live_or_visibility_claim':True,'sides':cot},indent=2))
