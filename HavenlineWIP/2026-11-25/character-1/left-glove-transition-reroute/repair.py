"""Detached sparse left glove transition replay from immutable geometry and UV."""
from collections import defaultdict, Counter
from pathlib import Path
import hashlib,json
import numpy as np

here=Path(__file__).resolve().parent
sha=lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
def load_verified(folder,seal,npz):
    d=here.parent/folder; m=d/'SHA256SUMS'
    assert sha(m)==seal,(folder,sha(m))
    for line in m.read_text().splitlines():
        h,f=line.split(maxsplit=1);assert sha(d/f)==h,f
    return np.load(d/npz)
old=load_verified('hvn-l1-c1-left-tip-diagonal-v1','c951e28d0f03cebd6e621fc86f90ccbf30b2df470ae4494120d876128cd6e0d6','editable_left_tip_flip.npz')
hold=load_verified('hvn-l1-c1-left-complete-orientation-v1','0afbdefc3f0fd807bc21e5bba5b57faeddee22fe383adbc65ca7dab931a24e43','editable_missing_join_graph.npz')
F=old['combined_tri']; uv=old['corner_uv']; o=old['open']; b=old['bind']
assert np.array_equal(hold['existing_faces'],F) and np.array_equal(hold['existing_corner_uv'],uv)
assert np.array_equal(hold['existing_open'],o) and np.array_equal(hold['existing_neutral'],b)
removed=[0,42,79,80,81]
rewoven=[95,96,97,98]
preserved=[i for i in range(len(F)) if i not in removed+rewoven]
assert set(hold['verified_existing_L0_face_rows']) <= set(preserved) and 88 in preserved
# Keep cuff geometry and exact bearing fixed, trimming only the unprotected pressure-side
# crown from its shared vertex along its local three-point material envelope.
def extend(p, neutral):
    q=p[79]*.75 + p[[82,93,95]].mean(axis=0)*.25
    mid=(p[0]+p[81])*.5
    axis=p[81]-p[0]
    away=mid-p[77]; away-=axis*((away@axis)/(axis@axis))
    # One material-relief dart on the non-locked bridge edge. Its neutral
    # triangle altitude includes designed slack; the held pose folds flat.
    loose=mid+away*.85 if neutral else mid
    return np.vstack([p,q,loose])
op,bp=extend(o,False),extend(b,True)
faces={i:f.tolist() for i,f in enumerate(F) if i not in removed}
for i in rewoven:faces[i]=[102 if v==79 else int(v) for v in F[i]]
new={120:[78,0,77],121:[78,79,41],122:[77,0,103],123:[77,103,81]}
faces.update(new)
uvs={i:uv[i].copy() for i in range(len(F)) if i not in removed}
def get_uv(fid,v):
    return uv[fid][np.flatnonzero(F[fid]==v)[0]]
# Two original donor charts stay separately sampled at the dart (no averaging).
uvs[120]=np.array([get_uv(0,v) for v in new[120]])
uvs[121]=np.array([get_uv(42,v) for v in new[121]])
A77,A0,A81=get_uv(78,77),get_uv(0,0),get_uv(78,81)
Am=(A0+A81)*.5
uvs[122]=np.array([A77,A0,Am])
uvs[123]=np.array([A77,Am,A81])
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
baseline=topology(dict(enumerate(F.tolist())))
top=topology(faces)
old_weld={i:(f if i not in rewoven else [79 if v==102 else v for v in f]) for i,f in faces.items()}
bad_weld=topology(old_weld)
assert len(baseline['bad_edges'])==3 and not baseline['balanced_boundary']
assert 79 in bad_weld['bad_vertex_links'] or not bad_weld['balanced_boundary']
assert not top['bad_edges'] and top['balanced_boundary'] and len(top['loops'])==1 and not top['bad_vertex_links']
for i in preserved:
    assert faces[i]==F[i].tolist() and np.array_equal(uvs[i],uv[i])
for v in hold['pressure_vertex_indices']:
    assert np.array_equal(op[v],o[v]) and np.array_equal(bp[v],b[v])
# Exact 3D triangle intersection; collect true hits from both triangle edge directions.
# Shared indexed vertices/edges are the only permitted contacts: subtract their
# geometric point/segment. Coplanar intersections are projected and polygon-clipped.
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
focus=sorted(rewoven+list(new))
bind_hits=intersections(bp,faces,focus);open_hits=intersections(op,faces,focus)
all_old={i:F[i] for i in range(len(F))}
old_scope=sorted(removed+rewoven)
old_bind_hits=intersections(b,all_old,old_scope);old_open_hits=intersections(o,all_old,old_scope)
def norm_label(a,b,c,p):return cross(p[b]-p[a],p[c]-p[a])
areas={i:[float(np.linalg.norm(norm_label(*faces[i],p))*.5) for p in (bp,op)] for i in focus}
# A collar-side pose transport fitted only on retained local cuff and collar vertices.
fitting=np.unique(F[hold['verified_existing_L0_face_rows']].ravel())
B=np.column_stack([b[fitting],np.ones(len(fitting))]);M=np.linalg.lstsq(B,o[fitting],rcond=None)[0][:3,:].T
assert np.linalg.det(M)>0
trans=np.linalg.det(M)*np.linalg.inv(M).T
signed={}
for i in focus:
    nb=trans@norm_label(*faces[i],bp); no=norm_label(*faces[i],op)
    signed[i]=float((nb@no)/(nb@nb))
def smooth_angle(i,j,p):
    a=norm_label(*faces[i],p);b=norm_label(*faces[j],p)
    return float(np.degrees(np.arccos(np.clip((a@b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
angles={f'{i}:{j}':[smooth_angle(i,j,p) for p in (bp,op)]
        for i,j in [(120,1),(121,41),(121,43),(122,120),(122,123),(123,78)]}
# Certificate of failure for ANY nondegenerate convex local trim of the crown
# within the four immutable original reference points, not a general claim.
# Let a=vertex 96 (negative halfspace), c=crown, plane d=0 be face 118.
# The homogeneous face-barycentric numerator of the 96--c split is linear
# in c; positive at three extreme points, nonnegative at face corner 95.
# Therefore strict physical crossing survives every convex trim in this
# envelope except c=95, which collapses incident face 96.
def piercing_certificate(p):
    ref=p[faces[118]]; n=norm_label(*faces[118],p); n/=np.linalg.norm(n)
    a=p[96]; da=float((a-ref[0])@n)
    P=(ref[1:]-ref[0]).T
    def candidate(i):
        c=p[i]; dc=float((c-ref[0])@n)
        x=(dc*a-da*c)/(dc-da)
        uv=np.linalg.lstsq(P,x-ref[0],rcond=None)[0]
        b=np.r_[1-uv.sum(),uv]
        assert np.linalg.norm(ref.T@b-x)<1e-12
        return {'signed_crown_mm':1000*dc,'hit_barycentric':b.tolist(),
                'coordinates_m':x.tolist(),'homogeneous_barycentric_numerator':(b*(dc-da)).tolist()}
    r={i:candidate(i) for i in [79,82,93,95,102]}
    assert da<-.0016 and all(min(r[i]['hit_barycentric'])>.004 for i in [79,82,93,102])
    assert np.allclose(r[95]['hit_barycentric'],[1,0,0],atol=1e-12)
    return {'vertex_96_signed_mm':da*1000,'edge': [96,102], 'penetrated_face':118,
            'anchor_hull': [79,82,93,95],'witnesses':r}
piercing={'neutral':piercing_certificate(bp),'open':piercing_certificate(op)}
# Narrow report: geometry here covers only exact replacement skin against old local
# assembly. Tool, retained garment, all far rails and full outward shading remain
# mandatory gated checks before any complete glove build.
accepted=not bind_hits and not open_hits and all(max(a)<135 for a in angles.values()) and all(min(a)>1e-10 for a in areas.values()) and all(.5<=s<=2 for s in signed.values())
result={'status':'PASS_LOCAL_CHANGED_SURFACE' if accepted else 'HOLD_LOCAL_CHANGED_SURFACE',
        'source_untouched_face_and_corner_uv_rows':preserved,
        'certified_locked_L0_rows_preserved':76, 'exact_pressure_face_88_preserved':True,
        'removed_rows':removed,'replacement_rows':new,'rewoven_pressure_border_rows':rewoven,
        'foldback_proxy_102_source_weights':{'79':.75,'82':1/12,'93':1/12,'95':1/12},
        'single_cyclic_boundary_after':top,
        'failed_control_reattach_old_weld':bad_weld,
        'changed_surface_counts':{'neutral':len(bind_hits),'open':len(open_hits)},
        'changed_surface_contacts':{'neutral':bind_hits, 'open':open_hits},
        'new_contact_delta':{'neutral':sorted(set(bind_hits)-set(old_bind_hits)), 'open':sorted(set(open_hits)-set(old_open_hits))},
        'convex_crown_trim_piercing_certificate':piercing,'new_join_angles_degrees_neutral_open':angles,
        'dart_103':{'source_edge':[0,81],'origin_vertex':77,'neutral_altitude_growth':1.85,'open_altitude_growth':1.0},
        'old_neighborhood_contacts':{'neutral':old_bind_hits,'open':old_open_hits},
        'changed_triangle_3d_areas_m2_neutral_open':areas,'local_affine_transported_signed_area_ratios':signed,
        'untested':['tool, retained garment and rail collision on new faces','closure and right hand','visual score and native build']}
np.savez_compressed(here/'editable_local_transition.npz',bind=bp,open=op,original_face_ids=list(faces),triangles=list(faces.values()),corner_uv=[uvs[i] for i in faces],kept_identity_rows=preserved,retired_rows=removed,changed_rows=focus,exact_pressure_source=hold['pressure_vertex_indices'],verified_existing_L0_face_rows=hold['verified_existing_L0_face_rows'])
dump=json.dumps(result,indent=2,default=lambda x:x.item())+'\n'
(here/'result.json').write_text(dump);print(dump,end='')
