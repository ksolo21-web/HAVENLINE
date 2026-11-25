"""One authored pressure-border fold reroute, retaining every vertex and four external edges."""
from collections import defaultdict, Counter
from pathlib import Path
import hashlib,json
import numpy as np

here=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
import gzip
src=here.parent/'hvn-l1-c1-thumb-web-return-v1'
assert sha(src/'SHA256SUMS')=='4c724cdaccf01f30817982a80255cf31e303a5ac0d3327f84d34a0a2dc33d7ca'
for z in (src/'SHA256SUMS').read_text().splitlines():
    h,f=z.split(maxsplit=1);assert sha(src/f)==h
q=np.load(src/'editable_thumb_web.npz')
ref=json.loads(gzip.decompress((src/'native_rays.json.gz').read_bytes()))
D={int(i):f.tolist() for i,f in zip(np.r_[q['original_face_ids'],q['new_face_ids']],q['combined_faces'])}
assert D[138]==[115,114,113] and [D[i] for i in (141,142,143,144)]==[[114,115,117],[114,117,116],[116,117,119],[116,119,118]]
def edge_map(fs):
    e=defaultdict(list)
    for i,f in fs.items():
        for a,v in zip(f,np.roll(f,-1)):
            e[tuple(sorted((a,int(v))))].append((a,int(v),i))
    return e
def topology(fs):
    e=edge_map(fs); bad=[(key,rec) for key,rec in e.items() if len(rec)>2 or (len(rec)==2 and rec[0][:2]==rec[1][:2])]
    free=[rec[0] for rec in e.values() if len(rec)==1]
    s=Counter(v[0] for v in free); t=Counter(v[1] for v in free)
    balanced=(s==t and max(s.values(),default=0)==1)
    loops=[]
    if balanced:
        g={a:c for a,c,_ in free}
        while g:
            start=next(iter(g)); walk=[start]; c=g.pop(start)
            while c!=start:
                walk.append(c);c=g.pop(c)
            loops.append(walk)
    broken=[]
    for v in {v for f in fs.values() for v in f}:
        nbr=defaultdict(set)
        for f in fs.values():
            if v in f:
                x,y=[z for z in f if z!=v];nbr[x].add(y);nbr[y].add(x)
        open_valence=v in s
        if not nbr:continue
        seen=set(); todo=[next(iter(nbr))]
        while todo:
            n=todo.pop()
            if n in seen:continue
            seen.add(n);todo.extend(nbr[n]-seen)
        if seen!=set(nbr) or sorted(map(len,nbr.values())).count(1)!=(2 if open_valence else 0) or max(map(len,nbr.values()))>2:broken.append(v)
    return {'bad_edges':bad,'balanced_boundary':balanced,'loops':loops,'bad_vertex_links':broken}
eps=2e-8
def cross(a,b):return np.cross(a,b)
def polyclip(A,B):
    n=cross(B[1]-B[0],B[2]-B[0]); norm=np.linalg.norm(n)
    if norm<eps**2:return []
    n/=norm
    P=list(A)
    for a,b in zip(B,np.roll(B,-1,axis=0)):
        R=[];d=b-a
        S=lambda q:np.dot(cross(d,q-a),n)/max(np.linalg.norm(d),eps)
        for x,y in zip(P,np.roll(np.array(P),-1,axis=0)) if P else []:
            sx,sy=S(x),S(y)
            if sx>=-eps:R.append(x)
            if sx*sy<0:R.append(x+(y-x)*sx/(sx-sy))
        P=R
    return P
def hit_points(A,B):
    normals=[cross(Q[1]-Q[0],Q[2]-Q[0]) for Q in (A,B)]
    normals=[n/np.linalg.norm(n) for n in normals]
    if np.linalg.norm(cross(*normals))<1e-10 and max(abs((A-B[0])@normals[1]))<eps:
        return polyclip(A,B)
    H=[]
    for X,Y,n in [(A,B,normals[1]),(B,A,normals[0])]:
        d=(X-Y[0])@n
        for i,j in [(0,1),(1,2),(2,0)]:
            cand=[]
            if abs(d[i])<=eps:cand.append(X[i])
            if d[i]*d[j]<0:cand.append(X[i]+(X[j]-X[i])*d[i]/(d[i]-d[j]))
            for p in cand:
                if all(np.dot(cross(y-x,p-x),n)>=-eps*np.linalg.norm(y-x) for x,y in zip(Y,np.roll(Y,-1,axis=0))):
                    H.append(p)
    return H
def proper(A,B,shared):
    P=hit_points(A,B)
    if not P:return False
    if len(shared)==0:return True
    if len(shared)==1:return max(np.linalg.norm(x-shared[0]) for x in P)>eps*8
    if len(shared)==2:
        a,b=shared;t=b-a;d=np.dot(t,t)
        return any(np.linalg.norm(x-(a+t*np.clip(np.dot(x-a,t)/d,0,1)))>eps*8 for x in P)
    return True
probeA=np.asarray([[0.,0,0],[1,0,0],[0,1,0]])
assert not proper(probeA,np.array([[0.,0,0],[-1,0,0],[0,-1,0]]),probeA[:1])
assert proper(probeA,np.array([[0.,0,-1],[0,0,1],[.6,.2,0]]),[])
assert not proper(probeA,np.array([[0.,0,0],[1,0,0],[1,-1,0]]),probeA[:2])
assert proper(probeA,np.array([[0.,0,0],[1,0,0],[.3,.3,0]]),probeA[:2])
def intersections(p,fs,focus):
    f=np.asarray(list(fs.values()));ids=list(fs);lookup={x:i for i,x in enumerate(ids)}
    V=p[f]; LO=V.min(1);HI=V.max(1);rec=set()
    for i in focus:
        k=lookup[i]
        C=np.flatnonzero(((LO<=HI[k]+eps)&(HI>=LO[k]-eps)).all(1))
        for j in C:
            if k==j:continue
            common=np.intersect1d(f[k],f[j])
            if proper(V[k],V[j],p[common]):rec.add(tuple(sorted((i,ids[j]))))
    return sorted(rec)
def norm_label(a,b,c,p):return cross(p[b]-p[a],p[c]-p[a])
def U(v):return v/np.linalg.norm(v)
a,b,c=114,115,113
N=len(q['bind'])
assert N==120
# One reconstructed geometric fairing. Project real owner directions into
# the common 3D plane normal to the protected web-base edge. The original
# thumb-web strip meets owner source at 72–80 degrees from the prior base
# normal. Ease the transition by following 82% of the measured shoulder
# normal on the first band, then the measured full normal on band two.
# Band one has the known 0.845mm (maximum old direct-ray crossing) plus
# approximately 0.30mm local travel for the old escape rays; band two
# continues to the source tangent and uses the remaining scoped arc length.
def rebuild(src,phase):
    p=np.asarray(src,dtype=float).copy()
    ed=U(p[a]-p[b]); d=p[c]-p[b]; out=U(-(d-ed*(ed@d)))
    normal=U(np.cross(p[a]-p[b],p[c]-p[b]))
    def source_angle(lanes):
        draws=np.asarray([x['owner_direction'] for i in lanes for x in ref[phase]['new_exact_test'][str(i)] if x['owner_first_valid']])
        m=(draws.mean(0));v=U(m-ed*(m@ed))
        return float(np.arctan2(v@out,v@normal)),len(draws)
    near,nn=source_angle([141,142]); far,nf=source_angle([143,144])
    theta=(.82*near,far)
    t=[np.cos(s)*out-np.sin(s)*normal for s in theta]
    p[116]=p[a]+.00115*t[0];p[117]=p[b]+.00115*t[0]
    p[118]=p[116]+.00235*t[1];p[119]=p[117]+.00235*t[1]
    assert np.array_equal(p[:116],src[:116])
    return p,{'actual_reference_sample_count_near_far':[nn,nf],
              'original_owner_fit_normal_degrees_near_far':np.degrees([near,far]).tolist(),
              'actual_constructed_turn_from_base_degrees':np.degrees(theta).tolist()}
p0,m0=rebuild(q['bind'],'neutral');p1,m1=rebuild(q['open'],'open')
T=topology(D)
assert len(T['loops'])==1 and len(T['loops'][0])==102 and not T['bad_edges'] and not T['bad_vertex_links']
I=[intersections(p,D,[141,142,143,144]) for p in (p0,p1)]
def normal(p,f):return np.cross(p[f[1]]-p[f[0]],p[f[2]]-p[f[0]])
fixed=[113,114,115]
xx=q['bind'][fixed]-q['bind'][fixed].mean(0); yy=q['open'][fixed]-q['open'][fixed].mean(0)
uu,_,vv=np.linalg.svd(xx.T@yy);vv[-1]*=np.linalg.det(uu@vv);rot=uu@vv
def turn(p,a,b):return float(np.degrees(np.arccos(np.clip(U(normal(p,D[a]))@U(normal(p,D[b])),-1,1))))
turns={f'{i}:{j}':[turn(p,i,j) for p in (p0,p1)] for i,j in [(138,141),(141,142),(142,143),(143,144)]}
rat={i:float((normal(p0,D[i])@rot)@normal(p1,D[i])/(normal(p0,D[i])@normal(p0,D[i]))) for i in (141,142,143,144)}
ww=[np.linalg.norm(p[qid]-q[pose][qid],axis=1) for p,pose,qid in [(p0,'bind',[116,117,118,119]),(p1,'open',[116,117,118,119])]]
area={i:[float(.5*np.linalg.norm(normal(p,D[i]))*1e6) for p in (p0,p1)] for i in (141,142,143,144)}
out={'status':'AWAIT_WHOLE_SHELL_POSE_RAYS' if not any(I) else 'HOLD_STRICT_LOCAL_INTERSECTIONS',
     'authored_shape_contour':{'neutral':m0,'open':m1,'first_second_arc_lengths_mm':[1.15,2.35]},
     'local_intersection_pairs_neutral_open':I,'single_boundary_102_edges':len(T['loops'][0]),
     'normal_turns_neutral_open_deg':turns,'signed_surface_area_ratios':rat,'geometry_areas_mm2_neutral_open':area,
     'only_movable_ids':[116,117,118,119], 'all_protected_outside_patch_keep_position_UV_topology':True,
     'movement_mm_for_only_four_rows_in_scope':[list(a*1000) for a in ww]}
np.savez_compressed(here/'editable_thumb_web_fairing.npz',bind=p0,open=p1,
                    original_face_ids=q['original_face_ids'],new_face_ids=q['new_face_ids'],
                    moved_vertex_ids=[116,117,118,119],corner_face_ids=q['corner_face_ids'],
                    combined_faces=q['combined_faces'],exact_immutable_corner_uv=q['exact_immutable_corner_uv'],
                    edited_region_uv_available=q['edited_region_uv_available'])
dump=json.dumps(out,indent=2)+'\n';(here/'build_result.json').write_text(dump);print(dump,end='')
