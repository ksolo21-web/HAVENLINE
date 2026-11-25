"""One authored pressure-border fold reroute, retaining every vertex and four external edges."""
from collections import defaultdict, Counter
from pathlib import Path
import hashlib,json
import numpy as np

here=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
import gzip
base=here.parent
def folder(name,seal):
    d=base/name
    assert sha(d/'SHA256SUMS')==seal
    for line in (d/'SHA256SUMS').read_text().splitlines():
        h,f=line.split(maxsplit=1);assert sha(d/f)==h
    return d
physical=folder('hvn-l1-c1-glove-physical-side-v1','44db716e542ece793bf1a43fb476001f091b57cbf9d938693fb8d67e0c6edefa')
uvpkt=folder('hvn-l1-c1-glove-uv-custody-v1','25d381d1c5ba5e82c23b1a71b828178228b63e40ddb9538c374c5f02a8cc7f9b')
q=np.load(uvpkt/'editable_dart_uv_only.npz')
ray=json.loads(gzip.decompress((physical/'ray_evidence.json.gz').read_bytes()))
R=json.loads((physical/'result.json').read_text())
ids=list(map(int,q['original_face_ids']))
F={i:f.tolist() for i,f in zip(ids,q['triangles'])}
UV={i:u.copy() for i,u in zip(ids,q['corner_uv'])}
target=R['both_pose_strong_exterior_with_inward_sign_candidate_rows']
assert target==[78,82,83,84,85,105,106,108,111]
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
existing=topology(F); assert len(existing['loops'])==1 and len(existing['loops'][0])==87
target_disk={i:F[i] for i in target}; d=topology(target_disk)
assert len(d['loops'])==1 and len(d['loops'][0])==11 and not d['bad_edges'] and not d['bad_vertex_links']
rim=d['loops'][0]
new_vertices={v:i+len(q['bind']) for i,v in enumerate(rim)}
def extrude(s,name):
    p=np.asarray(s,dtype=np.float64)
    O=[]; metrics={}
    for v in rim:
        incident=[i for i in target if v in F[i]]
        samples=np.array([z['owner_outward_direction_unit'] for i in incident for z in ray[name][str(i)]['measures'] if z['perturbation']==0 and z['outward_ray_agrees_original_first_hit']])
        # Author one coherent skin. Use real measured owner-facing local
        # field, not reversing the old faces in place. Contract only the new
        # outer lip very slightly to reduce spill over known protected rim.
        exterior=unit(samples.mean(0))
        ct=np.mean([p[F[i]].mean(0) for i in incident],0)-p[v]
        tangent=unit(ct-(ct@exterior)*exterior)
        off=.002*exterior+.0007*tangent
        O.append(p[v]+off)
        metrics[v]={'actual_direction_sample_count':len(samples),'owner_direction_mean_unit':exterior.tolist(),'outline_displacement_mm':1000*np.linalg.norm(off)}
    return np.vstack([p,O]),metrics
p0,met0=extrude(q['bind'],'neutral');p1,met1=extrude(q['open'],'open')
copies={i:130+k for k,i in enumerate(target)}
new={copies[i]:[new_vertices[v] for v in F[i][::-1]] for i in target}
assert edge_map(F)[(81,82)]==[(81,82,85)]
aa,bb=81,82;A,B=new_vertices[aa],new_vertices[bb]
# One actual capward cut edge is the only topological entry into the lifted
# skin. The retained nine rows now act as a true separate return layer.
new.update({139:[bb,aa,A],140:[bb,A,B]})
faces={**F,**new}
top=topology(faces)
assert len(top['loops'])==1 and len(top['loops'][0])==98 and not top['bad_edges'] and not top['bad_vertex_links']
assert all(faces[i]==F[i] for i in ids)
assert np.array_equal(p0[:len(q['bind'])],q['bind']) and np.array_equal(p1[:len(q['open'])],q['open'])
matches={a:UV[a].copy() for a in ids}
# No duplicate placeholder UV is represented as new geometry's authority.
# The new rows do not have UV charts in this geometry-only candidate.
changed=list(new); I=[intersections(p,faces,changed) for p in (p0,p1)]
def norm(p,f):return np.cross(p[f[1]]-p[f[0]],p[f[2]]-p[f[0]])
areas={i:[float(.5*np.linalg.norm(norm(p,faces[i]))) for p in (p0,p1)] for i in changed}
report={'status':'GEOMETRY_CHECKS_ONLY' if not any(I) else 'HOLD_RECONSTRUCTION_INTERSECTS',
        'same_old_faces_positions_and_uv':len(ids),'new_outer_near_skin_row_map':copies,
        'kept_previous_inner_toward_sheltered_cap':target,'new_true_connected_capward_fold_faces':[139,140],
        'topology':top,'specification_authoritative_2mm_skin_0p7mm_inset_trial_neutral':met0,
        'same_law_open':met1,'tested_local_strict_contact_pairs_both_poses':I,
        'new_geometric_triangle_areas_mm2':{i:[x*1.e6 for x in a] for i,a in areas.items()},
        'new_faces_uv_unassigned_no_material_writes':True}
assert all(min(a)>1e-10 for a in areas.values())
np.savez_compressed(here/'editable_exterior_return.npz',bind=p0,open=p1,original_face_ids=ids,
                    new_face_ids=changed,combined_faces=list(faces.values()),old_corner_uv=q['corner_uv'],
                    new_uv_chart_available=np.zeros(len(new),np.bool_),new_outer_legacy_face_ids=target,
                    new_outer_legacy_vertex_ids=rim,new_outer_vertex_ids=list(new_vertices.values()))
dump=json.dumps(report,indent=2)+'\n';(here/'initial_geometry.json').write_text(dump);print(dump,end='')
