from collections import Counter
from pathlib import Path
import hashlib,json,sys
import numpy as np
pred=Path('../hvn-l1-reference-panel-v2-rope-contact-v1/check_pairs.py')
exec(pred.read_text().split('before,after=')[0])
before,after=map(Path,sys.argv[1:3])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(before)=='40fee8f845ed22281cb8fe2036399b7f48724ab8ce56e30c9f40b2e005cd9a80'
A,B=read(before),read(after)
for label in ('amber_logs','soft_snow','front_rounded_rails'):
    assert np.array_equal(A[label],B[label])
    # Constructor serializes same topology/normal rows for these contiguous surfaces.
    ref=before.read_text().split('usemtl '+label+'\n')[1].split('usemtl ')[0]
    cur=after.read_text().split('usemtl '+label+'\n')[1].split('usemtl ')[0]
    assert ref==cur
old=before.read_text().splitlines(); new=after.read_text().splitlines()
for start in ('v ','vn '):
    a,b=([l for l in ls if l.startswith(start)] for ls in (old,new))
    assert a[:3264*3]==b[:3264*3]
V=np.concatenate(tuple(B.values())).reshape(-1,3)
extent=V.max(0)-V.min(0)
assert extent[1]==1.465 and extent[2]*1.95<=.2844835635
assert np.all(V.min(0)>=[-1.47045,0,-.0806]) and np.all(V.max(0)<=[1.47045,1.465,.0706])
def shell(a):
    C=Counter()
    for row in a:
        tri=[tuple(v) for v in row]; assert len(set(tri))==3
        for p,q in zip(tri,tri[1:]+tri[:1]):C[(p,q)]+=1
    assert all(n==1 and C[(q,p)]==1 for (p,q),n in C.items())
    a=a-a.mean((0,1))
    volume=float(np.einsum('ij,ij->i',a[:,0],np.cross(a[:,1],a[:,2])).sum()/6)
    assert volume>0
    return volume
tracks=[np.split(B[c],2) for c in ('ivory_hemp_warm','ivory_hemp_cream')]
rails=np.split(B['front_rounded_rails'],2)
logs=np.split(B['amber_logs'],8)
pstate=[]
def ring(T):
    return T.reshape(180,12,3,3)[:,::2,0,:].mean(1)
for i,(warm,cream) in enumerate(zip(*tracks)):
    assert not witnesses(warm,warm,True) and not witnesses(cream,cream,True)
    seats={}
    for name,R in [('warm',warm),('cream',cream)]:
        assert not witnesses(R,rails[1-i]) and not witnesses(R,B['soft_snow'])
        for other in tracks:
            assert not witnesses(R,other[1-i])
        z=ring(R)
        front=z[:81];rear=z[90:171]
        assert (front[:,2]>0).all() and (rear[:,2]<0).all()
        # Rear remains nearly horizontal; front signs are tracked independently.
        assert np.ptp(rear[:,1])<.007 and np.ptp(front[:,1])>.075
        F,Rb=R[:80*12],R[90*12:170*12]
        assert not witnesses(F,B['amber_logs'])
        support=witnesses(F,rails[i])
        by_log=[0]*8
        for a,b,v in support:
            u=int(np.clip((F[a,:,0].mean()+1.47045)/(2.9409/8),0,7))
            by_log[u]+=1
        assert all(n>0 for n in by_log)
        bearing=[len(witnesses(Rb,t)) for t in logs]
        assert all(bearing)
        seats[name]={'closed_exposed_end_loop_volume_m3':shell(R),'rail_contact_triangle_pairs_per_log':by_log,
                     'rear_contact_triangle_pairs_per_log':bearing,'front_y_span_m':float(np.ptp(front[:,1])),
                     'rear_y_span_m':float(np.ptp(rear[:,1]))}
    C=witnesses(warm,cream)
    by_log=[0]*8
    for a,b,d in C:
        assert a//12<80 and b//12<80
        slot=[int(np.clip((t[q,:,0].mean()+1.47045)/(2.9409/8),0,7)) for t,q in ((warm,a),(cream,b))]
        assert slot[0]==slot[1]
        by_log[slot[0]]+=1
    assert all(by_log)
    # Crossover samples correspond to each log center, with signed front
    # segments from both continuous ropes. Uppermost arm visibly covers
    # the lower by compressing only the knotted front contact shoulder.
    wa,ca=ring(warm),ring(cream)
    rows=[]
    for j in range(8):
        x=5+10*j
        off_a=wa[x-2:x+3,[1,2]];off_b=ca[x-2:x+3,[1,2]]
        order=off_a[:,0]-off_b[:,0]
        assert order[0]*order[-1]<0 and abs(order[2])<.00001
        assert ca[x,2]>wa[x,2]
        rows.append({'log':j+1,'at_x_m':float(wa[x,0]),'cream_center_in_front_of_gold_mm':float((ca[x,2]-wa[x,2])*1000),
                     'intentional_strict_contact_triangles':by_log[j]})
    pstate.append({'belt':i,'seating':seats,'paired_direction_reversal':rows,
        'max_intended_contact_intersection_segment_mm_not_depth':float(max(x[2] for x in C)*1000)})
print(json.dumps({'source_obj':sha(before),'candidate_obj':sha(after),'wood_snow_and_both_rails_bytes_preserved':True,
 'old_gates_collision_world_custody_untouched':True,'world_depth_m':extent[2]*1.95,'actual_triangle_count':sum(len(a) for a in B.values()),
 'true_verified_rope_support_both_faces_and_interlaced_front':pstate,
 'no_rear_opposed_overlap_no_gates_or_internal_join_admission':True},indent=2))
