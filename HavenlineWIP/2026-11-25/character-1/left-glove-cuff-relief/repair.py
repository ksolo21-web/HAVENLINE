"""One authored pressure-border fold reroute, retaining every vertex and four external edges."""
from collections import defaultdict, Counter
from pathlib import Path
import hashlib,json
import numpy as np

here=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
d=here.parent/'hvn-l1-c1-pressure-border-reroute-v1'
m=d/'SHA256SUMS'
assert sha(m)=='87965c12e6987231cfa6d8135527c6b1470a4be95ca0a03c2c1b29af88e9a9bb'
for line in m.read_text().splitlines():
    h,f=line.split(maxsplit=1); assert sha(d/f)==h,f
q=np.load(d/'editable_pressure_border.npz'); bp=q['bind']; op=q['open']
F={int(i):list(map(int,f)) for i,f in zip(q['original_face_ids'],q['triangles'])}
UV={int(i):u.copy() for i,u in zip(q['original_face_ids'],q['corner_uv'])}
assert [F[i] for i in [120,122,123]]==[[78,0,77],[77,0,103],[77,103,81]]
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
def unit(x):return x/np.linalg.norm(x)
def normal(p,f):
    a,b,c=p[f]; return cross(b-a,c-a)
def turn(a,b):
    return float(np.degrees(np.arccos(np.clip(unit(a)@unit(b),-1.,1.))))
def sculpt(p):
    # Move one new interior support toward the cuff-side tangent, distributing
    # the old hard hinge over a fixed triangular opening without moving the rim.
    a,b,c=p[F[122]]; axis=unit(b-a)
    mid=(a+b+c)/3; foot=a+((mid-a)@axis)*axis; radial=mid-foot
    oldn=unit(normal(p,F[122])); cuffn=unit(normal(p,F[120]))
    raw=np.arctan2(axis@cross(oldn,cuffn),oldn@cuffn)
    # Follow the shorter signed turn by 37%, constrained at the same authored
    # opening in both samples (one geometric rule, no per-pose tuning).
    theta=.37*raw
    v=foot+np.cos(theta)*radial+np.sin(theta)*cross(axis,radial)
    return np.vstack([p,v]),float(np.degrees(theta))
P0,rot0=sculpt(bp); P1,rot1=sculpt(op)
faces={i:f.copy() for i,f in F.items()}; uvs={i:u.copy() for i,u in UV.items()}
faces[122]=[77,0,104]; faces[124]=[0,103,104]; faces[125]=[103,77,104]
u77,u0,u103=UV[122]; ua=UV[122].mean(axis=0)
uvs[122]=np.array([u77,u0,ua]);uvs[124]=np.array([u0,u103,ua]);uvs[125]=np.array([u103,u77,ua])
focus=[122,124,125]
def rim(fs,uv,scope):
    d={}
    for rec in edge_map({i:fs[i] for i in scope}).values():
        if len(rec)==1:
            a,b,i=rec[0];f=fs[i]
            d[(a,b)]=[uv[i][f.index(a)].tolist(),uv[i][f.index(b)].tolist()]
    return d
assert rim(faces,uvs,focus)==rim(F,UV,[122])
kept=[i for i in F if i!=122]
assert np.array_equal(P0[:len(bp)],bp) and np.array_equal(P1[:len(op)],op)
assert all(F[i]==faces[i] and np.array_equal(UV[i],uvs[i]) for i in kept)
assert set(map(int,q['verified_existing_L0_face_rows']))<=set(kept) and set([88,118,119])<=set(kept)
before_top=topology(F); after_top=topology(faces)
assert before_top==after_top
cross_before=[intersections(p,F,[122]) for p in (bp,op)]
cross_after=[intersections(p,faces,focus) for p in (P0,P1)]
angles={}
for e,rr in edge_map(faces).items():
    if len(rr)==2 and any(a[-1] in focus for a in rr):
        a,b=sorted(v[-1] for v in rr)
        angles[f'{a}:{b}']=[turn(normal(p,faces[a]),normal(p,faces[b])) for p in (P0,P1)]
areas={i:[float(.5*np.linalg.norm(normal(p,faces[i]))) for p in (P0,P1)] for i in focus}
# Keep the exact old cuff neighborhood affine normal transport as the hard
# both-pose quality reference rather than removing the previously imposed test.
idx=np.unique(np.array([F[int(i)] for i in q['verified_existing_L0_face_rows']]).ravel())
A=np.column_stack([bp[idx],np.ones(len(idx))])
M=np.linalg.lstsq(A,op[idx],rcond=None)[0][:3,:].T; assert np.linalg.det(M)>0
trans=np.linalg.det(M)*np.linalg.inv(M).T
rat={}
for i in focus:
    a=trans@normal(P0,faces[i]);b=normal(P1,faces[i])
    rat[i]=float(a@b/(a@a))
def uv_area(u):
    a,b=u[1:]-u[0]
    return float(a[0]*b[1]-a[1]*b[0])
old_uv=uv_area(UV[122])
new_uv={i:uv_area(uvs[i]) for i in focus}
assert abs(old_uv)<1e-8 and all(abs(x)<1e-8 for x in new_uv.values())
assert abs(sum(new_uv.values())-old_uv)<1e-8
old_turn=[turn(normal(p,F[120]),normal(p,F[122])) for p in (bp,op)]
assert all(a>135 for a in old_turn)
def offplane(p):
    return float(abs((p[104]-p[F[122][0]])@unit(normal(p,F[122]))))
threshold=135.
maxangle=max(max(a) for a in angles.values())
gates={'no_crossing_both_poses':not any(cross_after),'all_adjacent_turns_below_135':maxangle<threshold,
 'nondegenerate_both_poses':all(min(a)>1e-10 for a in areas.values()),
 'signed_transported_ratio_in_0p5_to_2':all(.5<=a<=2 for a in rat.values())}
result={'status':'PASS_LOCAL_GEOMETRY_ONLY' if all(gates.values()) else 'HOLD_LOCAL_DART_RELIEF','gates':gates,
 'face_122_old_inside_reconstruction':focus, 'original_vertex_positions_and_unchanged_rows_preserved':len(kept),
 'boundary_vertices_and_split_UV_exact':True, 'manifold_polarity_and_perimeter_exact':len(after_top['loops'][0]),
 'dorsal_joint_rotation_deg_neutral_open':[rot0,rot1],
 'old_120_122_turn_deg_neutral_open':old_turn,
 'new_support_old_plane_height_neutral_open_m':[offplane(p) for p in (P0,P1)],
 'old_uv_doubled_area':old_uv,'new_uv_subtriangle_doubled_areas':new_uv,
 'triangle_turns_deg_neutral_open':angles, 'true_triangle_areas_neutral_open_m2':areas,
 'signed_area_transport_ratios':rat,'strict_changed_pair_crossings_before':cross_before,
 'strict_changed_pair_crossings_after':cross_after,
 'no_claim_rail_garment_tool_render_closure_gameplay':True,'uncorrected_stock_singular_uv_edge_84_85':True,
 'inherited_dart_uv_chart_is_collinear_parent_row_122':True, 'uv_status':'HOLD_UV_SEPARATE_RECHART_REQUIRED'}
np.savez_compressed(here/'editable_cuff_relief.npz',bind=P0,open=P1,original_face_ids=list(faces),triangles=list(faces.values()),corner_uv=[uvs[i] for i in faces],preserved_faces=kept,exact_pressure_source=q['exact_pressure_source'],verified_existing_L0_face_rows=q['verified_existing_L0_face_rows'])
dump=json.dumps(result,indent=2)+'\n';(here/'result.json').write_text(dump);print(dump,end='')
