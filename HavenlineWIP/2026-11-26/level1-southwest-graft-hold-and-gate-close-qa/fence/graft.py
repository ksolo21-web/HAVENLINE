from pathlib import Path
import hashlib,sys,json,numpy as np,itertools
r=Path(__file__).resolve().parent; R=r.parent
screen=R/'hvn-l1-fence-33036-sw-mating-screen-v1'
assert hashlib.sha256((screen/'SHA256SUMS').read_bytes()).hexdigest()=='c3dd0e560424386e9fe78942fe64bff37aa14d5e5c0c380be4bbd9963f3deb83'
source=R/'hvn-l1-fence-33036-bold-wrap-v3/build.py'; ref=R/'hvn-owner-fence-33036-33035/33036.png'; old=R/'hvn-level1-r17-normal-admission-v1/staged/HavenlineLevel1/previews/r17_fence/assets/fence_panel.obj'
prefix=source.read_text(); sys.argv=[str(source),str(ref),str(old)]
D={'__file__':str(source)}
exec(prefix[:prefix.index('C=root/')],D)
faces,groups=D['faces'],D['groups']
# Re-run only registered source with capture of each existing indexed loop/ring before emission.
Q={'__file__':str(source)}
exec(prefix[:prefix.index('def triangulated')],Q)
rings={}
def record(label,part,R,axis_cyl='across',capped=True):rings[part]=np.array(R)
Q['tube']=record
exec(prefix[prefix.index('def oval'):prefix.index('C=root/')],Q)
expected={(q,v) for q,l in groups.items() for v in set(l)}
assert len(rings)==22
N=(R/'hvn-l1-fence-33036-neutral-corner-socket-v1/candidate/Corner.obj').read_text().splitlines()
V=[]; H={};o=''
for l in N:
 if l.startswith('o '):o=l[2:];H[o]=[]
 if l.startswith('v '):V.append([float(z) for z in l.split()[1:]])
 if l.startswith('f '):H[o].append([int(z.split('/')[0])-1 for z in l.split()[1:]])
M=json.loads((screen/'result.json').read_text()); corner=np.array([-8.25,M['candidate_math_root_y_m'],9.8]); V=np.asarray(V)
O={'shared_corner':V[H['shared_corner']]+corner,'shared_corner_cap':V[H['shared_corner_cap']]+corner}
colors={k:k for k in O}; colors['shared_corner']='amber_logs';colors['shared_corner_cap']='soft_snow'
orphans={}
retained={};audit={}
low,high=.0,.0
source_verified={}
from collections import Counter
def polys(ring,cap):
 fs=[]
 for a,b in zip(ring,ring[1:]):
  for i in range(len(a)):
   j=(i+1)%len(a)
   fs.extend([(a[i],a[j],b[j]),(a[i],b[j],b[i])])
 if cap:
  a,b=ring[0],ring[-1]
  for i in range(len(a)):
   j=(i+1)%len(a);fs.extend([(a.mean(0),a[j],a[i]),(b.mean(0),b[i],b[j])])
 fs=np.array(fs)
 return fs
def frame(arm):
 if arm=='SW0':return np.array([1.,0,0]),np.array([0.,0,1.]),1.956/2.9409,0
 return np.array([0.,0,1.]),np.array([-1.,0,0.]),(8/3+.006)/2.9409,7
def as_world(x,arm):
 axis,depth,s,_=frame(arm); k=M['runs'][arm]; at=np.array([k['protected_anchor_xz_m'][0],k['donor_seat_y_m'],k['protected_anchor_xz_m'][1]])
 return at+x[...,0,None]*axis*s+x[...,1,None]*[0,1,0]+x[...,2,None]*depth*1.95
for arm in ('SW0','West2'):
 _,_,_,gone=frame(arm)
 for mat,items in faces.items():
  for part in set(groups[mat]):
   key=arm+'/'+part
   exact=np.array([f for f,k in zip(items,groups[mat]) if k==part])
   if part in (f'post{gone+1}',f'post{gone+1}_icing'):continue
   colors[key]=mat
   if part.startswith('post'):
    O[key]=as_world(exact,arm);retained[key]=len(exact);continue
   ring=as_world(rings[part],arm)
   if part.startswith('front_rail'):
    # Match each arm's actual nominal authored height; re-seat only the three corner-end rings.
    cut=ring.copy(); loc=slice(0,3) if gone==0 else slice(-3,None)
    location=ring[2 if gone==0 else -3]
    axial,normal,_,_=frame(arm); toward_arm=axial if gone==0 else -axial
    # Open from untouched original constant full profile at a signed station and return
    # to original line past this single short graft (no distant rail Y or x/z movement).
    fixed=location+.21*toward_arm
    if arm=='SW0':
     cut[loc]+= .050*toward_arm-.014*normal
    if arm=='West2' and part=='front_rail_1':
     cut[loc]+=np.array([0,.112,0])
    constructed=np.r_[cut[:3],fixed[None,:],cut[3:]] if gone==0 else np.r_[cut[:-3],fixed[None,:],cut[-3:]]
    ff=polys(constructed,True)
    signed=np.einsum('ij,ij->i',ff[:,0],np.cross(ff[:,1],ff[:,2])).sum()
    if signed<0:ff=ff[:,::-1]
    O[key]=ff
    audit[key]={'treatment':'changed three local endpoint rings, one exact full-profile fixed cut ring, distant three rings untouched','cap_points_world':(constructed[0] if gone==0 else constructed[-1]).tolist(),'fixed_cut_ring_world':fixed.tolist()}
    continue
   assert len(ring)==181
   if gone==0:
    keep=np.array(ring[6:165]); signed=[6,164]
   else:
    keep=np.r_[ring[96:180],ring[:75]]; signed=[96,74]
   a,b=keep[-1],keep[0]; ca,cb=a.mean(0),b.mean(0)
   # Replace only the cut-side return with the exact donor tube cross sections;
   # rigid-ring uplift weights at indexed stations preserve chirality instead of opposite-tangent lerp.
   removed=np.r_[ring[165:180],ring[:6]] if gone==0 else ring[75:96]
   nring=len(removed);made=[]
   for i,ring0 in enumerate(removed):
    t=(i+1)/(nring+1); row=ring0.copy()
    if arm=='West2' and 'return_1_' in part:
     row[:,1]+=.160*np.sin(np.pi*t)**1.30
    made.append(row)
   O[key]=polys(np.r_[keep,np.array(made),keep[:1]],False)
   audit[key]={'retained_cut_ring_indices_directed':signed,'signed_cut_ring_center_world':[ca.tolist(),cb.tolist()],'retained_run_between_and_opposite_end':True,'graft_saved_cross_section_rings':len(made),'local_uplift_max_m':.160 if arm=='West2' and 'return_1_' in part else 0}
# Exact strict component intersections, closure and no exposed shared rail caps.
ctx={'__file__':str(R/'hvn-l1-fence-33036-full-perimeter-repair-bound-v1/verify.py')}
exec((R/'hvn-l1-fence-33036-full-perimeter-repair-bound-v1/verify.py').read_text().split('seams=')[0],ctx)
bound=ctx['culled_intersections']
def measure(A,B,x,y):
 d=bound(A,B,[x]*len(A),[y]*len(B));return next(iter(d.values())) if d else None
def closed_and_winding(T):
 cnt=Counter();sense=Counter()
 for f in T:
  a=[tuple(v) for v in np.round(f,8)]
  for i in range(3):
   q=(a[i],a[(i+1)%3]);k=tuple(sorted(q));cnt[k]+=1;sense[k]+=1 if q==k else -1
 return all(c==2 and sense[k]==0 for k,c in cnt.items())
bad_closed=[k for k,t in O.items() if not closed_and_winding(t)]
unrelated={};contacts={};radial={}
for x,z in itertools.combinations(sorted(O),2):
 k=measure(O[x],O[z],x,z)
 if not k:continue
 if x.split('/')[0]!=z.split('/')[0] and 'shared_' not in x and 'shared_' not in z:unrelated[x+'/'+z]=k
 if 'shared_corner' in z or 'shared_corner' in x:contacts[x+'/'+z]=k
for k,d in audit.items():
 if 'cap_points_world' in d:
  P=np.array(d.pop('cap_points_world')); distance=np.linalg.norm(P[:,[0,2]]-corner[[0,2]],axis=1)
  # Conservative inscribed radius for 20-sided cylindrical timber, and its central axial full-radius region.
  radial[k]=[float((.142*np.cos(np.pi/20)-distance.max())*1000),float(P[:,1].min()-corner[1]),float(P[:,1].max()-corner[1])]
anchor_cuts={}
for k,t in O.items():
 if 'front_rail' not in k and 'distinct_return' not in k:continue
 near=t[np.linalg.norm(t[:,:,[0,2]].mean(1)-corner[[0,2]],axis=1)<.28]
 lo,hi=t.min(1),t.max(1); n=ctx['norms'](t); count=0; top=0.; matched=None
 for f in range(len(t)):
  if np.linalg.norm(t[f][:,[0,2]].mean(0)-corner[[0,2]])>=.28:continue
  for q in np.flatnonzero((lo[f]<=hi).all(1)&(hi[f]>=lo).all(1)&(np.arange(len(lo))>f)):
   if (np.linalg.norm(t[f][:,None]-t[q][None,:],axis=-1)<1e-8).any():continue
   g=ctx['span'](t[f],t[q],n[f],n[q])
   if g>4e-7:
    count+=1
    if g>top:top=g;matched=[f,int(q)]
 ground=np.unique(np.round(near.reshape(-1,3),8),axis=0)
 minfloor=min((v[1]-ctx['height'](v[[0,2]]) for v in ground),default=None)
 anchor_cuts[k]={'strict_new_mate_nearby_self_crossings':count,'max_segment_mm':top*1000,'sample_pair':matched,'min_sampled_vertex_vs_indexed_terrain_mm':None if minfloor is None else minfloor*1000}
result=dict(status='HOLD pending actual rail/rope seat and graft evaluation',exact_matched_terrain_root_xyz_m=corner.tolist(),
 minimum_all_triangle_area_mm2=min(float(np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1).min()*.5e6) for t in O.values()),near_mate_cut_witness=anchor_cuts,gross_triangles=sum(len(t) for t in O.values()),baseline_two_donors=23808,retained_post_cap_triangle_count=sum(retained.values()),
 exact_rail_cap_conservative_embed_mm_and_y_to_post=radial,closed_winding_failed_groups=bad_closed,cross_arm_intersections=unrelated,
 shared_timber_join_contacts=contacts,component_splice_audit=audit)
(r/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(tris=result['gross_triangles'],bad_closed=bad_closed,cross_arm_count=len(unrelated),rail=radial,shared_contact_count=len(contacts))))
# Private geometry witness only; leave on HOLD. No baked texture or runnable scene.
w=['# HOLD: actual welded indexed partial corner witness; no import, no texture, no gameplay release.']
n=1
for key,triangles in sorted(O.items()):
 w.append('o '+key.replace('/','_'))
 for t in triangles:
  for p in t:w.append('v '+' '.join(f'{z:.9f}' for z in p))
  w.append(f'f {n} {n+1} {n+2}');n+=3
(r/'CornerPartial_HOLD.obj').write_text('\n'.join(w)+'\n')
