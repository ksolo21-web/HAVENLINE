"""One authored pressure-border fold reroute, retaining every vertex and four external edges."""
from collections import defaultdict, Counter
from pathlib import Path
import hashlib,json
import numpy as np

here=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
src=here.parent/'hvn-l1-c1-glove-exterior-return-v1'
assert sha(src/'SHA256SUMS')=='fa4494dc62b7512bc9bda16eac298c543ebd43369d9a7204b2097d668121419e'
for z in (src/'SHA256SUMS').read_text().splitlines():
    h,f=z.split(maxsplit=1);assert sha(src/f)==h
q=np.load(src/'editable_exterior_return.npz')
base_ids=np.r_[q['original_face_ids'],q['new_face_ids']]
base={int(i):f.tolist() for i,f in zip(base_ids,q['combined_faces'])}
assert base[138]==[115,114,113]
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
assert N==116
# One physical contour: two short panel rows across the owner-measured gap.
# Preserve both frozen edge points for UV/normal handoff, and keep all other
# exterior and return geometry exactly. The outer row follows external face
# 138. The narrow lip turns toward the sheltered side without sewing a second
# far edge into the already single existing perimeter.
def points(src):
    p=np.asarray(src,dtype=float)
    ed=U(p[a]-p[b]); d=p[c]-p[b]; out=U(-(d-ed*(ed@d)))
    normal=U(np.cross(p[a]-p[b],p[c]-p[b]))
    shoulder=.0026*out-.00015*normal
    lip=.0009*out-.0008*normal
    return np.vstack([p,p[a]+shoulder,p[b]+shoulder,p[a]+shoulder+lip,p[b]+shoulder+lip]),out,normal
p0,T0,N0=points(q['bind']);p1,T1,N1=points(q['open'])
Fnew={141:[114,115,117],142:[114,117,116],143:[116,117,119],144:[116,119,118]}
faces={**base,**Fnew}
old=topology(base); t=topology(faces)
assert len(old['loops'])==1 and len(old['loops'][0])==98
assert len(t['loops'])==1 and len(t['loops'][0])==102 and not t['bad_edges'] and not t['bad_vertex_links']
assert np.array_equal(q['bind'],p0[:N]) and np.array_equal(q['open'],p1[:N])
assert edge_map(faces)[(114,115)]==[(115,114,138),(114,115,141)]
I=[intersections(p,faces,list(Fnew)) for p in (p0,p1)]
def normal(p,f):return np.cross(p[f[1]]-p[f[0]],p[f[2]]-p[f[0]])
fixed=[113,114,115]
x=q['bind'][fixed]-q['bind'][fixed].mean(0)
y=q['open'][fixed]-q['open'][fixed].mean(0)
uu,_,vv=np.linalg.svd(x.T@y); vv[-1]*=np.linalg.det(uu@vv); rot=uu@vv
def turn(p,a,b):return float(np.degrees(np.arccos(np.clip(U(normal(p,faces[a]))@U(normal(p,faces[b])),-1,1))))
ess={(x[-1],y[-1]) for rr in edge_map(faces).values() if len(rr)==2 for x,y in [rr] if x[-1] in Fnew or y[-1] in Fnew}
ang={f'{a}:{b}':[turn(p,a,b) for p in (p0,p1)] for a,b in sorted(ess)}
rat={i:float((normal(p0,f)@rot)@normal(p1,f)/(normal(p0,f)@normal(p0,f))) for i,f in Fnew.items()}
area={i:[float(.5*np.linalg.norm(normal(p,faces[i]))*1e6) for p in (p0,p1)] for i in Fnew}
verified=not any(I) and all(.5<x<2 for x in rat.values()) and max(a for v in ang.values() for a in v)<135
result={'status':'LOCAL_GEOMETRY_CLEAR_AWAIT_SHELL_RAYS' if verified else 'HOLD_LOCAL_GEOMETRY',
        'geometric_neutral_and_open_contact_pairs':I,'maximum_turn_degrees':max(a for v in ang.values() for a in v),
        'turns_neutral_open_deg':ang,'signed_transport_area_ratios':rat,'face_area_mm2_both':area,
        'unchanged_116_original_positions_and_old_faces':len(base),'new_corner_faces':Fnew,'fixed_boundaries':[[114,115],[81,82]],
        'unchanged_cuff_pressure_tip_and_UV':True,'new_rows_UV_unassigned':True,
        'single_directed_boundary_count':len(t['loops'][0]),'boundary_vertex_order':t['loops'][0],
        'geometry_construction_mm':{'outer_web_widening':2.6,'outer_web_drop':.15,'lip_extra_widening':.9,'lip_extra_inward_turn':.8}}
np.savez_compressed(here/'editable_thumb_web.npz',bind=p0,open=p1,original_face_ids=q['original_face_ids'],
    new_face_ids=np.r_[q['new_face_ids'],list(Fnew)],corner_face_ids=list(Fnew),combined_faces=list(faces.values()),
    exact_immutable_corner_uv=q['old_corner_uv'],edited_region_uv_available=np.zeros(len(Fnew),np.bool_))
dump=json.dumps(result,indent=2)+'\n';(here/'build_result.json').write_text(dump);print(dump,end='')
