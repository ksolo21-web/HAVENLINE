"""One authored pressure-border fold reroute, retaining every vertex and four external edges."""
from collections import defaultdict, Counter
from pathlib import Path
import hashlib,json
import numpy as np

here=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
d=here.parent/'hvn-l1-c1-left-transition-reroute-v1'
m=d/'SHA256SUMS'
assert sha(m)=='30a9acaf59a17168ac00408245abb7a45a2c75177206a7d3fa8995049aa28d41'
for line in m.read_text().splitlines():
    h,f=line.split(maxsplit=1); assert sha(d/f)==h,f
q=np.load(d/'editable_local_transition.npz');bp=q['bind'];op=q['open']
F=dict((int(i),list(map(int,f))) for i,f in zip(q['original_face_ids'],q['triangles']))
UV=dict((int(i),u.copy()) for i,u in zip(q['original_face_ids'],q['corner_uv']))
faces={i:f.copy() for i,f in F.items()}; uvs={i:u.copy() for i,u in UV.items()}
# Fold fan, same pressure-side boundary 102→95→84→85→102. Preserve 96 as
# the actual inner hinge rather than burying the fold behind a rigid cover.
assert [F[i] for i in (96,97,118,119)]==[[102,95,96],[102,96,85],[95,84,85],[85,96,95]]
faces[118]=[95,84,96]
faces[119]=[84,85,96]
def at(i,v):return UV[i][F[i].index(v)]
# Preserve the original cap UVs on its two boundary edges and independently
# preserve the authored pressure chart along 95→96→85. Existing cap seam
# changes path but none of its boundary-corner UV samples change.
uvs[118]=np.array([at(118,95),at(118,84),at(119,96)])
uvs[119]=np.array([at(118,84),at(118,85),at(119,96)])
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
patch=(96,97,118,119)
def patch_boundary(ff,uu):
    e=edge_map({i:ff[i] for i in patch});result={}
    for rec in e.values():
        if len(rec)==1:
            a,b,i=rec[0]
            result[(a,b)]=[uu[i][ff[i].index(a)].tolist(),uu[i][ff[i].index(b)].tolist()]
    return result
assert patch_boundary(faces,uvs)==patch_boundary(F,UV)
assert set(patch_boundary(faces,uvs))=={(102,95),(95,84),(84,85),(85,102)}
fixed=[i for i in faces if i not in (118,119)]
assert all(F[i]==faces[i] and np.array_equal(UV[i],uvs[i]) for i in fixed)
assert set(map(int,q['verified_existing_L0_face_rows']))<=set(fixed) and 88 in fixed
assert (84,99) in edge_map(faces) and (99,100) in edge_map(faces) and (97,100) in edge_map(faces)
top=topology(faces); oldtop=topology(F)
assert not top['bad_edges'] and not top['bad_vertex_links'] and top['balanced_boundary'] and len(top['loops'])==1
assert top['loops']==oldtop['loops']
new_before=[intersections(p,F,list(patch)) for p in (bp,op)]
new_after=[intersections(p,faces,list(patch)) for p in (bp,op)]
assert all((96,118) in r and (97,118) in r for r in new_before)
around=set()
for e,rows in edge_map(faces).items():
    if len(rows)==2 and any(r[-1] in patch for r in rows):
        around.add(tuple(sorted(r[-1] for r in rows)))
def angle(p,i,j):
    a=norm_label(*faces[i],p);b=norm_label(*faces[j],p)
    return float(np.degrees(np.arccos(np.clip((a@b)/(np.linalg.norm(a)*np.linalg.norm(b)),-1,1))))
ang={f'{i}:{j}':[angle(p,i,j) for p in (bp,op)] for i,j in sorted(around)}
area={i:[float(.5*np.linalg.norm(norm_label(*faces[i],p))) for p in (bp,op)] for i in patch}
# Material-area transport for this nearly-rigid pressure patch uses its own
# four border vertices, not a cuff fit. Report normal rotation as well.
rigid_ids=[102,95,84,85]; x=bp[rigid_ids]-bp[rigid_ids].mean(0); y=op[rigid_ids]-op[rigid_ids].mean(0)
U,_,VT=np.linalg.svd(x.T@y); rot=U@VT
assert np.linalg.det(rot)>.999999
signed={}
for i in patch:
    n=norm_label(*faces[i],bp)@rot;m=norm_label(*faces[i],op)
    signed[i]=float(n@m/(n@n))
area2=lambda u:float((u[1,0]-u[0,0])*(u[2,1]-u[0,1])-(u[1,1]-u[0,1])*(u[2,0]-u[0,0]))
uvn={i:area2(uvs[i]) for i in patch}; uv0={i:area2(UV[i]) for i in patch}
result={'status':'PASS_LOCAL' if not any(new_after) and all(max(v)<135 for v in ang.values()) and all(min(v)>1e-10 for v in area.values()) and all(.5<r<2 for r in signed.values()) and sum(abs(v)<1e-12 for v in uvn.values())<=sum(abs(v)<1e-12 for v in uv0.values()) else 'HOLD_PRESSURE_BORDER',
 'incident_and_nonincident_physical_crossings_before_neutral_open':new_before,
 'incident_and_nonincident_physical_crossings_after_neutral_open':new_after,
 'around_patch_normal_angle_degrees_neutral_open':ang,
 'true_areas_m2_neutral_open':area,
 'transported_normal_signed_area_ratio':signed,
 'corner_uv_doubled_signed_area_before':uv0,
 'corner_uv_doubled_signed_area_after':uvn,
 'orig_border_points_fixed':True,'exact_patch_boundary_direction_uv_preserved':True,'fixed_face_rows':fixed,
 'manifold_links':True,'one_boundary_count':len(top['loops'][0]),
 'changed_faces':{'118':faces[118],'119':faces[119]},
 'known_separate_dart_normal_hard_fold_degrees_neutral_open':[angle(bp,120,122),angle(op,120,122)],
 'no_tool_body_rail_closure_right_render_or_game_validation':True}
np.savez_compressed(here/'editable_pressure_border.npz',bind=bp,open=op,original_face_ids=list(faces),triangles=list(faces.values()),corner_uv=[uvs[i] for i in faces],preserved_faces=fixed,exact_pressure_source=q['exact_pressure_source'],verified_existing_L0_face_rows=q['verified_existing_L0_face_rows'])
dump=json.dumps(result,indent=2)+'\n';(here/'result.json').write_text(dump);print(dump,end='')
