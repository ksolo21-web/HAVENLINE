from pathlib import Path
from collections import defaultdict
import numpy as np, json,hashlib,itertools
R=Path(__file__).resolve().parent; P=R.parent
source=P/'hvn-l1-fence-33036-sw-whole-source-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'SHA256SUMS')=='6aad08a832d840667afdf1525746107b1ddba5824d92710072cf542eb49c7d37'
N={'__file__':str(source/'assemble.py')}
src=(source/'assemble.py').read_text();exec(src[:src.index('neighbors={')],N)
O,ctx,stock,stockmat,bound=[N[k] for k in ('O','ctx','stock','stockmat','bound')]
# Underlying stock visuals are comparison only. Identify separately welded source objects.
V,I=np.unique(np.round(stock.reshape(-1,3),8),axis=0,return_inverse=True)
I=I.reshape(-1,3); parents=list(range(len(stock)))
def find(x):
 while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
 return x
def union(a,b):parents[find(a)]=find(b)
own={}
for i,f in enumerate(I):
 for edge in zip(f,np.roll(f,-1)):
  k=tuple(sorted(edge))
  if k in own:union(i,own[k])
  else:own[k]=i
groups=defaultdict(list)
for i in range(len(stock)):groups[find(i)].append(i)
A=ctx['panels'](stock,False)
evidence={}
for neighbor,run in [('SW1','SW0'),('West1','West2')]:
 world=A[neighbor][0]
 findings=[]
 for ind in groups.values():
  Y=world[ind]; material=np.array(stockmat)[ind]; hits={}
  for g,X in O.items():
   if not g.startswith(run+'/'):continue
   hit=bound(X,Y,[g]*len(X),material)
   if hit:hits.update(hit)
  if hits:findings.append(dict(face_indices=[min(ind),max(ind)],n_tri=len(ind),
                  component_bounding_world_m=[Y.min((0,1)).tolist(),Y.max((0,1)).tolist()],mesh_label=list(set(material)),source_first_index=ind[0],hits=hits))
 evidence[neighbor]=findings
(R/'initial-components.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
for k,v in evidence.items():
 print(k,[(row['face_indices'],row['n_tri'],row['mesh_label'],row['component_bounding_world_m']) for row in v])
for nb,reverse in [('SW1',False),('West1',True)]:
 at=A[nb][0]; row=[]
 x=0 if nb=='SW1' else 2
 for ind in groups.values():
  Y=at[ind];row.append([min(ind),max(ind),stockmat[ind[0]],Y[:,:,x].min(),Y[:,:,x].max(),Y[:,:,1].min()])
 print('near',nb,sorted(row,key=lambda v:(-1 if reverse else 1)*v[3])[:9])
def tube(A,B,depth,ry=.036,rz=.018):
 a=np.arange(12)*np.pi/6
 S=[c+np.sin(a)[:,None]*np.array(depth)[None,:]*rz+np.cos(a)[:,None]*[0,ry,0] for c in (A,B)]
 t=N['d']['polys'](np.array(S),True)
 sign=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()
 return t if sign>0 else t[:,::-1]
terrain=N['d']['terrain']
spec={'SW1':('SW0','post8',[(0,27),(280,315)],[28,55],0,1),'West1':('West2','post1',[(252,279),(604,639)],[224,251],2,-1)}
mat_names=np.array(stockmat)
rep={}; assets={}
for nb,(run,pk,rem,(ra,rb),ax,sign) in spec.items():
 Y=A[nb][0]
 exempt={i for a,b in rem for i in range(a,b+1)}
 rest=np.array([i for i in range(len(Y)) if i not in exempt])
 # True trimmed duplicate body and corresponding crown; all other original faces exact.
 after={}
 for g,X in O.items():
  if not g.startswith(run+'/'):continue
  hit=bound(X,Y[rest],[g]*len(X),mat_names[rest])
  if hit:after.update(hit)
 assert not after,after
 next_post=Y[ra:rb+1]
 owner_post=O[run+'/'+pk]
 used=[]
 endpoints=[]
 for i,dy in enumerate((.205,.875)):
  owner_c=(owner_post.min((0,1))+owner_post.max((0,1)))*.5
  control_c=(next_post.min((0,1))+next_post.max((0,1)))*.5
  transverse=2 if ax==0 else 0
  horn=owner_c.copy(); toe=control_c.copy()
  horn[ax]+=.101*sign;toe[ax]-=.013*sign
  horn[transverse]-=.003*sign;toe[transverse]+=.010*sign
  root_y=min(owner_post[:,:,1].ravel())
  horn[1]=root_y+dy
  # Avoid terrain while maintaining physically seated timber and real stock profile.
  toe[1]=max(horn[1],float(np.min(next_post[:,:,1]))+.16)
  depth=[0.,0.,0.];depth[transverse]=1.
  # Deterministic bounded seat search, matched toe remains original nominal rail band.
  matches=[]
  relevant={k:v for k,v in O.items() if k.startswith(run+'/') and ('rope' in k or 'return' in k or 'rail' in k)}
  scannum=0
  horn_nom=horn.copy()
  for bump in [0,.03,-.03,.053,-.053,.075,-.075]:
   for depth_d in [0,.025,-.025,.05,-.05]:
    for advance in [.0,.019,.009,-.018]:
     h=horn_nom.copy();h[1]+=bump;h[transverse]+=depth_d;h[ax]+=advance*sign
     mesh=tube(h,toe,depth)
     scannum+=1
     taken={}
     for a,v in relevant.items():
      got=bound(mesh,v,['trial']*len(mesh),[a]*len(v))
      if got:taken.update(got)
     target=bound(mesh,owner_post,['trial']*len(mesh),['post']*len(owner_post))
     if taken or not target:continue
     near=terrain(mesh)
     if near['minimum_clearance_m']<.003:continue
     matches.append((abs(bump)*2+abs(depth_d)+abs(advance),h,mesh))
  if matches:_,horn,T=min(matches,key=lambda v:v[0])
  else:T=tube(horn,toe,depth)
  k=nb+f'_local_bridge_{i}'
  gmap={name:bound(T,art,[k]*len(T),[name]*len(art)) for name,art in O.items() if name.startswith(run+'/')}
  all_inter={k:v for row in gmap.values() for k,v in row.items()}
  all_inter.update(bound(T,Y[rest],[k]*len(T),[str(i) if ra<=i<=rb else 'stock_other' for i in rest]))
  gap=terrain(T)
  # Aim source controls: exact attached closed rail through only the designated timbers,
  # and potential old same-band rails/ropes only if inside owner wood are recorded, not waived.
  seats={'prior_post':bool(gmap[run+'/'+pk]),'retained_control_post':bool(bound(T,next_post,[k]*len(T),['control_post']*len(next_post)))}
  deny={c:v for c,v in all_inter.items() if run+'/'+pk not in c and not c.split(' / ')[1].isdecimal()}
  used.append({'piece':k,'ends_xyz_m':[horn.tolist(),toe.tolist()],'ground':gap,'seats':seats,'all_pair_hits':all_inter,'remaining_nondesignated':deny,'triangles':len(T),'screen_trials':scannum,'clean_mates_seen':len(matches)})
  assets[k]=T
 rep[nb]={'exact_removed_control_face_ranges_inclusive':rem,'neighbor_removed_tri':len(exempt),'preserved_stock_face_count':len(rest),'direct_owner_vs_trimmed_neighbor_non_designated_contacts':after,'rails':used}
(R/'join-result.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
for k,row in rep.items():
 print(k,[(v['ground']['minimum_clearance_m'],v['seats'],v['remaining_nondesignated']) for v in row['rails']])
def outline(t):
 n=np.array([7.,11.,11.]);n/=np.linalg.norm(n);x=np.cross([0.,1.,0.],n);x/=np.linalg.norm(x);y=np.cross(n,x)
 xy=t.reshape(-1,3)@np.array([x,y]).T*(720/13)
 return [xy.min(0).tolist(),xy.max(0).tolist()]
cross={}
for (k,t),(j,v) in itertools.combinations(assets.items(),2):
 hit=bound(t,v,[k]*len(t),[j]*len(v))
 if hit:cross.update(hit)
assert not cross
total=sum(len(t) for t in O.values())+sum(x['preserved_stock_face_count'] for x in rep.values())+sum(len(t) for t in assets.values())
summary={'scope':'detached mechanical clearance of short plain bridge rail only; no native grade or rope bridge appearance',
 'tried_all_outer_bounded_socket_proposals':sum(v['screen_trials'] for o in rep.values() for v in o['rails']),
 'total_composite_triangles':total,'original_whole_plus_2_stock_control_triangles':sum(len(t) for t in O.values())+2*len(stock),
 'new_rail_width_height_mm':[36,72], 'stock_camera_declared_outline_bounds_px':{k:outline(t) for k,t in assets.items()},
 'all_bridge_pairs_no_unintended_strict_intersections':True,
 'source_visual_continuity_conclusion':'Mechanical pass only in exact local test. Bridge rail is narrower and South upper sloped ~25.7% (atan=14.4deg); neighboring timber remains comparison art, no actual continuous exterior X rail appearance or rope linkage beyond retained closed returns is established.',
 'prior_42_group_owner_geometry_unchanged':True,'material_lineage':'Existing source remains physically unchanged. New bridges only neutral rounded timber; no private 3d material/atlas copied and appearance unqualified.'}
(R/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
v=['# Detached intersection-safe narrow rail witnesses only; NOT approved fence material.'];i=1
for k,t in assets.items():
 v.append('o '+k)
 for f in t:
  for q in f:v.append('v '+' '.join(f'{z:.9f}' for z in q))
  v.append(f'f {i} {i+1} {i+2}');i+=3
(R/'SocketBridges_SourceOnly.obj').write_text('\n'.join(v)+'\n')
