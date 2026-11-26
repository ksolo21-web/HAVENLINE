from pathlib import Path
from hashlib import sha256
import json,math
from components import *
from closed import *
P=Path(__file__).resolve().parent
p=json.loads((P.parent/'hvn-l1-fence-33036-west0-joint-feasibility-v2/result.json').read_text())
safe=4.464284666666667
parts={}
consumed={}
for name in ('timber','snow'):
 ix=np.flatnonzero(M==name)
 for j,ri in enumerate(components(U[M==name])):
  ids=ix[ri]; src=U[ids]
  if float(src[:,:,2].max())<safe:continue
  solid=list(src)
  for ring in loops(src):solid+=cap(ring)
  solid=np.array(solid);check(solid)
  shut=clip(solid,safe)
  for ring in loops(shut):
   assert np.max(abs(ring[:,2]-safe))<2e-9
   shut=np.concatenate((shut,np.array(cap(ring))))
  key=f'{name}_terminal_{j}'
  parts[key]=orient(shut)
  consumed[key]=ids.tolist()
assert [len(x) for x in consumed.values()]==[28,28,8]
def cross_support(name):
 T=N['West1/front_rounded_rails/'+name]
 end=float(T[:,:,2].min())
 at_end=T[np.max(np.abs(T[:,:,2]-end),axis=1)<2e-8]
 rings=loops(at_end)
 assert len(rings)==1
 ring=rings[0]; center=ring.mean(axis=0)
 # Bottom roots slightly narrowed and wholly behind the stock end, socket end exactly admits end cross section.
 R=[]
 for ax,m in ((end-.012,.87),(end-.007,1.0),(end-.0002,1.0)):
  ring2=center+m*(ring-center);ring2[:,2]=ax;R.append(ring2)
 how=len(ring);out=list(cap(R[0]))+list(cap(R[-1][::-1]))
 # base boundary edge A→B must pair the side B→A.
 for ra,rb in zip(R,R[1:]):
  for j in range(how):
   k=(j+1)%how
   out.extend(([ra[k],ra[j],rb[j]],[ra[k],rb[j],rb[k]]))
 T=orient(np.array(out))
 assert abs(T[:,:,2].max()+.0002-end)<2e-9
 return T
for course in ('lower','upper'):parts['rounded_rail_bearing_'+course]=cross_support(course)
def rope(above,index):
 from scipy.spatial import ConvexHull
 n,k=56,10
 cy=.144 if not above else .836
 old=parts['timber_terminal_9']
 boundary=[]
 for t in old:
  for a,b in zip(t,np.roll(t,-1,axis=0)):
   if (a[1]-cy)*(b[1]-cy)<0:
    point=a+(b-a)*((cy-a[1])/(b[1]-a[1]))
    boundary.append(point[[0,2]])
 q=np.unique(np.round(boundary,8),axis=0)
 q=q[ConvexHull(q).vertices]
 qmid=q.mean(axis=0)
 path=[p for p in q]
 # trace four beveled facets and four flat axes with a smoothed centered route
 for _ in range(2):
  path=[p*.7+j*.3 for p,j in zip(path,np.roll(path,-1,axis=0)) for p,j in [(p,j),(j,p)]]
 path=np.array(path); edges=np.roll(path,-1,axis=0)-path
 dist=np.r_[0,np.cumsum(np.linalg.norm(edges,axis=1))]
 points=[];rad=.007
 for i in range(n):
  frac=i/n
  u=2*math.pi*frac; at=dist[-1]*frac
  j=np.searchsorted(dist,at,side='right')-1
  xz=path[j]+edges[j]*(at-dist[j])/(dist[j+1]-dist[j])
  normal=xz-qmid; normal/=np.linalg.norm(normal)
  y=cy+(index-.5)*.023+.003*math.cos(2*u+index*math.pi)
  ctr=xz+.006*normal+.012*math.sin(2*u+index*math.pi)*normal
  # Respect absolute pre-existing West0 timber+snow width and protected mate plane.
  ctr=np.clip(ctr,[-8.39742+rad,4.2174+rad],[-8.10258-rad,safe-rad])
  norm=np.array([normal[0],0,normal[1]])
  center=np.array([ctr[0],y,ctr[1]])
  points.append([center+rad*(math.cos(j*2*math.pi/k)*norm+math.sin(j*2*math.pi/k)*np.array([0.,1.,0.])) for j in range(k)])
 out=[]
 for i in range(n):
  q=(i+1)%n
  for j in range(k):
   v=(j+1)%k
   out.extend(([points[i][j],points[q][j],points[q][v]],[points[i][j],points[q][v],points[i][v]]))
 return orient(np.array(out))
for high in (False,True):
 for i in (0,1):parts[('upper' if high else 'lower')+'_two_course_return_'+str(i)]=rope(high,i)
assert all(len(loops(T))==0 for T in parts.values())
# Preserve other exact West0 indexed faces, use only last 28+28+8 source triangles changed.
reserved=set(v for nums in consumed.values() for v in nums)
assert len(reserved)==64
untouched=U[~np.isin(np.arange(len(U)),list(reserved))]
assert untouched[:,:,2].max() < min(t[:,:,2].min() for t in N.values())
stock_extent=np.array([U.min((0,1)),U.max((0,1))])
T=np.concatenate(list(parts.values()))
assert T[:,:,0].min()>=stock_extent[0,0]-1e-10 and T[:,:,0].max()<=stock_extent[1,0]+1e-10
assert T[:,:,2].min()>4.2 and T[:,:,2].max()<4.467

# Purchase/grade, protected colliders and neighboring parts are not mutated.
exam=env['env']['C']['culled_intersections']
groups=[]
for k,V in parts.items():
 # strict check against every adjacent source component on the same signed axis.
 for name,W in N.items():
  assert not exam(V,W,[k]*len(V),[name]*len(W)), (k,name)
 groups.append(k)
for band in ('lower','upper'):
 A=parts[f'{band}_two_course_return_0'];B=parts[f'{band}_two_course_return_1']
 assert not exam(A,B,[band+'a']*len(A),[band+'b']*len(B)),band
# Directly isolate a source-point interior parity check; no bounding-box containment masquerade.
def inside(points,tri):
 A,e,f=tri[:,0],tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
 ray=np.array([.337,.491,.661])
 h=np.cross(ray,f);t=np.einsum('ij,ij->i',e,h);ok=np.abs(t)>1e-12
 A,e,f,h,t=A[ok],e[ok],f[ok],h[ok],t[ok]
 res=[]
 for p in points:
  u0=p-A; u=np.einsum('ij,ij->i',u0,h)/t; q=np.cross(u0,e);v=q@ray/t
  r=np.einsum('ij,ij->i',f,q)/t
  res.append(bool(np.count_nonzero((u>1e-8)&(v>1e-8)&(u+v<1-1e-8)&(r>1e-8))%2))
 return res
old=parts['timber_terminal_9']
seats={}
for band in ('lower','upper'):
 # Bearing must share a finite piece of material while still extending toward its exact partner.
 seat=parts[f'rounded_rail_bearing_{band}']
 lo,hi=seat.min((0,1)),seat.max((0,1))
 samples=np.array(list(__import__('itertools').product(*(np.linspace(l+.0005,h-.0005,8) for l,h in zip(lo,hi)))))
 inter=np.count_nonzero(np.array(inside(samples,old))&np.array(inside(samples,seat)))
 assert inter>=30,(band,inter)
 seats[band]=int(inter)
compare_closed=dict(N)
for k in ('West1/amber_logs/whole','West1/meshy_bold_amber_front/whole'):compare_closed.pop(k)
compare_closed['West1/amber_and_source_front']=np.concatenate([N[k] for k in ('West1/amber_logs/whole','West1/meshy_bold_amber_front/whole')])
check(compare_closed['West1/amber_and_source_front'])
bounds={}
for key,v in parts.items():
 if key.startswith('snow') or 'bearing' in key or 'course_return' in key:
  b=env['env']['c']['c']['terrain'](v)
  assert b['minimum_clearance_m']>0,(key,b['minimum_clearance_m'])
  bounds[key]=b['minimum_clearance_m']
  # Containment with other assembly none, even if a closed source volume does not cross the small shell.
 for name,W in compare_closed.items():
  if (W.min((0,1))>v.max((0,1))).any() or (v.min((0,1))>W.max((0,1))).any():continue
  assert not any(inside(v.reshape(-1,3),W)),(key,name,'inside mate solid')
  assert not any(inside(W.reshape(-1,3),v)),(key,name,'contains mate solid')
foam={}
for name in groups:
 if 'course_return' not in name:continue
 V=parts[name]
 center=V.reshape(-1,3)
 points=V.mean(axis=1)
 inset=V.min((0,1))
 embedded=np.array(inside(points, old))
 assert np.count_nonzero(embedded)>=15,(name,'no physically rooted stock timber strip')
 visible=(points[:,0] < -8.35) & ~embedded
 assert np.count_nonzero(visible)>=15,(name,'bare stock timber has no exposed rope edge')
 foam[name]=int(np.count_nonzero(visible))
# Emit only after every static gate passes; no UV claim or material substitutions.
obj=['# Detached terminal, transformed CAD geometry only; old West0 retains nonterminal indices']
count=1
for name,W in parts.items():
 obj.append('o '+name)
 for tri in W:
  for a,b,c in tri:obj.append(f'v {a:.10f} {b:.10f} {c:.10f}')
  obj.append(f'f {count} {count+1} {count+2}');count+=3
(P/'West0_closed_terminal_detached_HOLD.obj').write_text('\n'.join(obj)+'\n')
print(json.dumps({'scope':'Visual source without material/engine, four-slot source untouched','retired_exact_original_64_indices':consumed,
  'new_components':{k:{'outward_volume_m3':check(t),'triangles':len(t)} for k,t in parts.items()},
  'original_west0_untouched_triangles':len(U)-64,'mate_positive_boundary_intersections':0,
  'real_stock_bearing_overlap_sample_count':seats,'cross_volume_containment_rejected_stitched_owner_log_solid':True,
  'rope_exterior_face_centroid_candidates':foam,'exact_T02_ground_slack':bounds,'no_install_approval':True},indent=2))
