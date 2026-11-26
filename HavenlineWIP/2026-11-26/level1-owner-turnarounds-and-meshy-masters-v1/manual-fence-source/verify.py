from collections import Counter
from pathlib import Path
import hashlib,json,sys,math
import numpy as np
pred=Path('../hvn-l1-reference-panel-v2-rope-contact-v1/check_pairs.py')
exec(pred.read_text().split('before,after=')[0])
obj=Path(sys.argv[1])
a=read(obj)
expected={'amber_logs':1344,'soft_snow':1536,'front_rounded_rails':384,'ivory_hemp':4608}
assert {k:len(v) for k,v in a.items()}==expected
box=np.concatenate(tuple(a.values())).reshape(-1,3)
assert np.isfinite(box).all() and np.all(box.min(0)>=np.array([-1.47045,0,-.0806]))
assert np.all(box.max(0)<=np.array([1.47045,1.465,.0706]))
def volume(q):
    M=Counter()
    for f in q:
        vs=[tuple(v) for v in f]
        assert len(set(vs))==3
        for v,w in zip(vs,vs[1:]+vs[:1]): M[(v,w)]+=1
    assert all(n==1 and M[(w,v)]==1 for (v,w),n in M.items())
    q=q-q.mean((0,1))
    metric=float(np.einsum('ni,ni->n',q[:,0],np.cross(q[:,1],q[:,2])).sum()/6)
    assert metric>0
    return metric
bounds={}
for label,n in [('amber_logs',8),('soft_snow',8),('front_rounded_rails',2),('ivory_hemp',2)]:
    x=np.split(a[label],n)
    bounds[label]={'closed_shells':len(x),'triangles':len(a[label]),'min_closed_volume_m3':min(volume(j) for j in x)}
posts=np.split(a['amber_logs'],8)
caps=np.split(a['soft_snow'],8)
rails=np.split(a['front_rounded_rails'],2)
track=np.split(a['ivory_hemp'],2)
crowned=[]
for i,p in enumerate(posts):
    assert len(witnesses(p,caps[i]))>0
    crowned.append(len(witnesses(p,caps[i])))
    for j in (i-1,i+1):
        if 0<=j<8:
            assert not witnesses(p,posts[j]) and not witnesses(caps[i],caps[j]) and not witnesses(p,caps[j])
ropes=[]
for k,R in enumerate(track):
    assert not witnesses(R,R,True)
    assert not witnesses(R,track[1-k])
    assert not witnesses(rails[k],rails[1-k])
    assert not witnesses(R,rails[1-k])
    assert not witnesses(R,a['soft_snow'])
    sections=[]
    for i,P in enumerate(posts):
        f=R[R[:,:,2].max(1)<0.]
        hits=witnesses(f,P)
        assert len(hits)>0,('rear rope floats',i,k)
        fhit=witnesses(R[R[:,:,2].min(1)>0.],rails[k])
        assert len(fhit)>0,('front floats',i,k)
        c=min(fhit,key=lambda x:abs(float(R[R[:,:,2].min(1)>0.][x[0],:,0].mean())-float(P[:,:,0].mean())))
        near=float(R[R[:,:,2].min(1)>0.][c[0],:,0].mean())
        assert abs(near-float(P[:,:,0].mean()))<.14
        sections.append({'post':i+1,'rear_rope_strict_pairs_with_same_log':len(hits),'front_rail_strict_contact_near_post_x_m':near})
    planes=R.reshape(-1,16,3,3)[:,::2,0,:].mean(1)
    front=planes[:65]; rear=planes[72:137]
    assert (front[:,2]>0).all() and (rear[:,2]<0).all()
    assert np.ptp(front[:,1])>.075 and np.ptp(rear[:,1])<.010
    angles=np.roll(planes,-1,axis=0)-planes
    angles*=np.array([1.956/2.9409,1,1.95])
    tangents=angles/np.linalg.norm(angles,axis=1)[:,None]
    turn=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',tangents,np.roll(tangents,1,axis=0)),-1,1)))
    ropes.append({'track':k+1,'front_y_range_m':float(np.ptp(front[:,1])),'rear_y_range_m':float(np.ptp(rear[:,1])),
                 'seated_sections':sections,'maximum_centerline_turn_degrees_in_sw_stock_scale':float(turn.max())})
print(json.dumps({'asset_sha':hashlib.sha256(obj.read_bytes()).hexdigest(),'independent_mesh_shells':bounds,
      'strict_rope_crossings':'only intended material contact with own timber or same-level rounded rail, no self or other assemblies',
      'own_snow_timber_strict_pairs':crowned,'lashing_receipt':ropes,
      'no_stock_authority_or_native_appearance_claim':True},indent=2))
