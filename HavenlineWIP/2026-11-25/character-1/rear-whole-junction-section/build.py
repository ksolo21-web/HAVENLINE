"""One authored pressure-border fold reroute, retaining every vertex and four external edges."""
from collections import defaultdict, Counter
from pathlib import Path
import hashlib,json
import numpy as np

here=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
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
def confirm(n,manifest):
    d=here.parent/n
    assert sha(d/'SHA256SUMS')==manifest
    for z in (d/'SHA256SUMS').read_text().splitlines():
        h,p=z.split(maxsplit=1);assert sha(d/p)==h,p
    return d
hand=confirm('hvn-l1-c1-garment-td-handoff-v1.u5TyEs','e966c85b84355f314414452f172297ed42b940ccb8ae0770d60f362081ea4b1f')
own=confirm('hvn-l1-c1-approved-rear-fold-v1.kD1WNv','1a64d744fc99d4b3cc1af7e7e4d790aa1611fc0b9b929f1659c7c33c5a348e30')
old=confirm('hvn-l1-c1-rear-pocket-volume-v1.hftpls','73cee1151bcd82f9de6d9a3cbedf700595b91af61d21186297824a8f0c9db59f')
front=confirm('hvn-l1-c1-anterior-seam-binding-v1.ZeubUc','aaa19c60d3aab56082ca7290e0c28cbef85d48938381452027b0a5d40e47a9ac')
src=json.loads((hand/'sections-and-motion.json').read_text()); A=np.load(own/'new-rear-panel.npz')
B=np.load(old/'pocket-solids.npz'); V=A['v'];H=B['retained'][-1].astype(float); F=A['tri']; reg=list(map(int,A['region']))
assert np.array_equal(F,B['shell_tri']) and len(reg)==147
assert set(range(42528,42534))<=set(reg)
assert np.max(np.abs(V-B['retained'][0]))<1e-7
for name,P in [('neutral',V),('held-original-0ms',H)]:
    for k,v in src['states'][name]['exact_rear_and_collar_vertices'].items():assert np.array_equal(P[int(k)],v)
for k,z in zip(('neutral','held-original-0ms'),(V,H)):
    assert np.array_equal(z[np.unique(src['collar_boundary_edge_vertex_ids'])],[[src['states'][k]['exact_rear_and_collar_vertices'][str(i)][j] for j in range(3)] for i in np.unique(src['collar_boundary_edge_vertex_ids'])])
rim_edges=src['collar_boundary_edge_vertex_ids']
assert len(rim_edges)==162
PIV=np.asarray(src['motion']['source_origin_raw']);scale=src['motion']['source_to_m_scale']
M=np.asarray(src['motion']['right_bone_delta_matrices_raw_local'][0])
def Xform(p,b):
    Q=np.asarray(p)/scale+PIV
    return (Q@M[b,:3,:3].T+M[b,:3,3]-PIV)*scale
axis_x=np.array([1.,0.,0.]);Y=np.array([0.,1.,0.]);Z=np.array([0.,0.,1.])
T=F[reg]; E=defaultdict(list)
for i,f in zip(reg,T):
    for a,b in zip(f,np.roll(f,-1)):E[tuple(sorted([int(a),int(b)]))].append((int(a),int(b),i))
rim={a:(b,i) for e,L in E.items() if len(L)==1 for a,b,i in L}
assert len(rim)==41
walker=min(rim);cycle=[walker]
while True:
    walker=rim[walker][0]
    if walker==cycle[0]:break
    assert walker not in cycle;cycle.append(walker)
assert len(cycle)==41
def seam_arc(a,b):
    j=cycle.index(a);k=cycle.index(b)
    return cycle[j:k+1] if j<=k else cycle[j:]+cycle[:k+1]
full_boundary_arcs={
 'first_X_side_exact_end_seam':seam_arc(13810,14016),
 'upper_exact_circumference_seam':seam_arc(14016,20964),
 'second_X_side_exact_end_seam':seam_arc(20964,20643),
 'lower_exact_circumference_seam':seam_arc(20643,13810)}
assert sum(len(x)-1 for x in full_boundary_arcs.values())==41
rverts=V[np.asarray(cycle)]
retids=np.flatnonzero(~np.isin(np.arange(len(F)),reg))
assert len(retids)==42393
def find_rim_on_axis(s,ax):
    hits=[]
    for start in cycle:
        end,face=rim[start];a,b=V[start],V[end]
        u=(s-a[ax])/(b[ax]-a[ax]) if abs(a[ax]-b[ax])>1e-12 else -1
        if 0<u<1:
            w=np.array([1-u,u]);vid=[start,end]
            hits.append({'source_edge':vid,'source_face':face,'weights':w,'neutral':w@V[vid],'held_0ms':w@H[vid]})
    return hits
def local_attach(x,z):
    # Direct physical source posterior section: critical faces are not
    # retained as obstacles. Their neutral positions only seed fabric rails.
    P=np.array([x,z]);Q=V[T]
    O=Q[:,:,[0,2]]; lo=O.min(1);hi=O.max(1)
    cand=[]
    for i in np.flatnonzero(((lo<=P)&(hi>=P)).all(1)):
        A=O[i];D=(A[1:]-A[0]).T
        if abs(np.linalg.det(D))<1e-12:continue
        u=np.linalg.solve(D,P-A[0]);bc=np.r_[1-u.sum(),u]
        if min(bc)>=-1e-8:cand.append((bc@Q[i],bc,reg[i]))
    assert cand,(x,z)
    return max(cand,key=lambda a:a[0][1])
def unit(a):return np.asarray(a)/np.linalg.norm(a)
SECTIONS=[-.151,-.1435,-.1315,-.1195,-.106,-.094]
SHIN=.387;THIGH=.479; cloth_half=.00030
fixture=[]
for x in SECTIONS:
    wire=find_rim_on_axis(x,0)
    assert len(wire)>=2
    low=min(wire,key=lambda a:a['neutral'][2]); high=max(wire,key=lambda a:a['neutral'][2])
    sl,sb,si=local_attach(x,SHIN);tl,tb,ti=local_attach(x,THIGH)
    # Independently held supports from pose-native rigid deltas. Boundary
    # weld endpoints instead always use original material edge interpolation.
    S1=Xform(sl,1);T1=Xform(tl,0)
    d0=np.linalg.norm(tl-sl);material=d0/np.cos(np.radians(8.))
    fixture.append({'station_m':x,'lower':low,'upper':high,
      'lower_attachment':{'neutral':sl,'held_0ms':S1,'source_triangle':si,'source_barycentric':sb,'rigid_bone':'Shin.R','end_dof':'none'},
      'upper_attachment':{'neutral':tl,'held_0ms':T1,'source_triangle':ti,'source_barycentric':tb,'rigid_bone':'Thigh.R','end_dof':'none'},
      'rest_length_of_two_lobe_material_arc_m':material})
def build_section(kit,phase):
    a=kit['lower'][phase];b=kit['upper'][phase];s=kit['lower_attachment'][phase];t=kit['upper_attachment'][phase]
    ch=t-s;d=np.linalg.norm(ch);along=unit(ch)
    # Actual sagittal compliant joint normal lies orthogonal to independent
    # mount relation, posterior only. New ±bend DOFs are bounded by fabric
    # length and closed-form one-lobe hemisphere choice, not bone averaging.
    n=unit(Y-(Y@along)*along)
    L=kit['rest_length_of_two_lobe_material_arc_m']; k=d/L
    assert 0<k<1,(phase,k)
    h=np.sqrt(L*L-d*d)*.25
    nodes=np.array([a,s,s+ch*.25+n*h,s+ch*.5,s+ch*.75+n*h,t,b])
    # Cross-sectional fabric as a 0.60mm true finite-width miter profile.
    # Ends taper only into their exact stitch points; no occult duplicate.
    secX=unit(np.cross(n,along))
    if secX@axis_x<0:secX*=-1
    U=np.array([unit(np.cross(b-a,secX)) for a,b in zip(nodes,nodes[1:])]); off=np.zeros_like(nodes)
    for j in range(1,len(nodes)-1):
        v=unit(U[j-1]+U[j]);d2=float(v@U[j]); assert d2>0
        off[j]=v*cloth_half/d2
    outer=nodes+off;inner=nodes-off
    verts=[]; faces=[]; roles=[]
    # No closed-length solid claim; planar section CAD is joined only
    # around actual midsurface. Name each part for downstream attachment.
    for i in range(len(nodes)-1):
        var=[outer[i],outer[i+1],inner[i+1],inner[i]]
        role='shin_mount' if i==0 else ('thigh_mount' if i==5 else 'compliant_two_lobe')
        for a,b,c in [(0,1,2),(0,2,3)]:
            tri=np.array([var[a],var[b],var[c]])
            if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))>1e-11:faces.append(tri);roles.append((i,role))
    area=np.asarray([np.cross(x[1]-x[0],x[2]-x[0])@secX for x in faces])
    # This orientation uses the mounted surface convention; true width is
    # checked independently along each segment's support normal.
    seglist=np.diff(nodes,axis=0); signed=np.einsum('ij,ij->i',off[:-1]+off[1:],U)
    return {'centers':nodes,'outer':outer,'inner':inner,'section_faces':np.array(faces),'roles':roles,
            'exact_chord_m':d,'symmetric_clock_arc_h_m':h,'compressed_fold_angle_deg':np.degrees(np.arccos(k)),
            'four_compliant_lengths_m':np.linalg.norm(seglist[1:5],axis=1),
            'signed_area_twice_square_m':area,'signed_mount_thickness_m':signed}
def scope_collisions(result,p,kit,phase):
    # Tests only the actual CAD section occupancy before any full 3D
    # exterior build. Include nonincident actual retained faces, not AABB-only.
    Rs=p[F[retids]];lo=Rs.min(1);hi=Rs.max(1)
    data=[]; segs=result['section_faces']; anchors=[kit[k][phase] for k in ('lower','upper')]
    for i,Q in enumerate(segs):
        L=Q.min(0);U=Q.max(0)
        for j in np.flatnonzero(((lo<=U+eps)&(hi>=L-eps)).all(1)):
            if np.linalg.norm(np.cross(Rs[j,1]-Rs[j,0],Rs[j,2]-Rs[j,0]))<=1e-12:continue
            legal=[]
            for key,pt in zip(('lower','upper'),anchors):
                if set(kit[key]['source_edge'])<=set(F[retids[j]]):legal.append(pt)
            hh=hit_points(Q,Rs[j])
            if hh and any(not any(np.linalg.norm(z-u)<2.e-7 for u in legal) for z in hh):
                data.append({'section_face':i,'role':result['roles'][i][1],'retained_face':int(retids[j]),'points_m':[z.tolist() for z in hh]})
    # Intra-section touch only legal exact two triangles' shared vertices.
    self=[]
    for i,a in enumerate(segs):
        for j,b in enumerate(segs[:i]):
            keep=np.asarray([u for u in a if any(np.linalg.norm(u-v)<1e-10 for v in b)])
            if proper(a,b,keep):self.append([i,j])
    return data,self
def serialize(x):
    return json.loads(json.dumps(x,default=lambda o:o.tolist()if hasattr(o,'tolist')else o.item()))
sc={}
for name,P in [('neutral',V),('held_0ms',H)]:
    R=[]
    for f in fixture:
        q=build_section(f,name);coll,ss=scope_collisions(q,P,f,name)
        q['retained_exact_occupied_face_pairs']=coll;q['strict_intra_section_face_pairs']=ss
        q['same_fabric_arc_length_error_m']=float(abs(np.sum(q['four_compliant_lengths_m'])-f['rest_length_of_two_lobe_material_arc_m']))
        R.append(q)
    sc[name]=R
# Exact upper and lower perimeter arcs came from frozen oriented 41-rim
# material edges. Preserve both full X end seams: chart them by material
# reach cuts at seven heights, using the same source edge + barycentric.
stations=[.373,.387,.401,.420,.440,.458,.479,.487]
end_seams={}
for zz in stations:
    r=find_rim_on_axis(zz,2)
    assert len(r)>=2
    end_seams[f'{zz:.3f}']=[min(r,key=lambda u:u['neutral'][0]),max(r,key=lambda u:u['neutral'][0])]
res={'status':'CAD_SECTION_ONLY_NO_WHOLE_MESH',
     'material_unknown_xyz_interpolation_after_this_stage':True,'protected_perimeter_collar_edges':rim_edges,
     'protected_full_authorized_rim_order':cycle, 'four_exact_seam_arcs_to_original_corners':full_boundary_arcs,'placed_stations':fixture,'exact_left_and_right_end_seam_map':end_seams,
     'staged_removal_authority_only_all_147_face_ids':reg,'critical_full_corridor_six_not_retained_in_occupancy':list(range(42528,42534)),
     'source_retained_triangle_count':len(retids),'prior_anterior_native_rows_same_4':src['anterior_source_native_rows'],
     'measurements':sc,'no_render_texel_motion_or_production':True}
(p:=here/'result.json').write_text(json.dumps(serialize(res),separators=(',',':'))+'\n')
with (here/'editable_section_rails.obj').open('w') as f:
    j=1
    def wire(n,pts,kind):
        global j
        pts=np.asarray(pts).reshape(-1,3)
        f.write('o '+n+'\n')
        for v in pts:f.write('v %.10f %.10f %.10f\n'%tuple(v))
        k=2 if kind=='l' else 3
        for i in range(0,len(pts),k):f.write(kind+' '+' '.join(str(j+i+k0) for k0 in range(k))+'\n')
        j+=len(pts)
    for name,P in [('neutral',V),('held_0ms',H)]:
        wire(name+'_162_edge_protected_collar',P[np.asarray(rim_edges)],'l')
        wire(name+'_41_edge_authorized_directional_shaped_boundary',P[np.array([[a,rim[a][0]] for a in cycle])],'l')
        for arcn,ids in full_boundary_arcs.items():
            nodes=P[np.array(ids)]
            wire(name+'_'+arcn,[t for n1,n2 in zip(nodes,nodes[1:])for t in (n1,n2)],'l')
        for i,z in enumerate(sc[name]):
            wire(name+'_cloth_section_signed_occupancy_'+str(i),z['section_faces'],'f')
        for k,anchor in enumerate(('lower_attachment','upper_attachment')):
            pts=[f[anchor][name] for f in fixture]
            nodes=[end_seams[f'{[SHIN,THIGH][k]:.3f}'][0][name],*pts,end_seams[f'{[SHIN,THIGH][k]:.3f}'][1][name]]
            wire(name+'_'+['shin_supported_rail','thigh_supported_rail'][k],[i for a,b in zip(nodes,nodes[1:]) for i in (a,b)],'l')
# True geometric test of transverse support rods: attachments are proposed
# centerline rails, not yet clearance proof for tubular material volume.
def rail_path(phase,k):
    anchor=('lower_attachment','upper_attachment')[k]
    return np.array([end_seams[f'{[SHIN,THIGH][k]:.3f}'][0][phase],*[s[anchor][phase] for s in fixture],end_seams[f'{[SHIN,THIGH][k]:.3f}'][1][phase]])
def xyz_boundary(segment,triangle):
    a,b=segment;c,d,e=triangle;D=np.stack([b-a,c-d,c-e],axis=1)
    det=np.linalg.det(D)
    if abs(det)<1e-13:return None
    t,u,v=np.linalg.solve(D,c-a)
    return a+(b-a)*t if -1.e-8<=t<=1+1.e-8 and min(u,v)>=-1.e-8 and u+v<=1+1.e-8 else None
def between_segments(A,B):
    a,b=A;c,d=B;u=b-a;v=d-c;q=a-c
    DD=np.stack([u,-v],axis=1)
    AA=np.linalg.lstsq(DD,-q,rcond=None)[0]
    if min(AA)>=0 and max(AA)<=1: return float(np.linalg.norm(q+DD@AA))
    def test(z,x,y):
        dd=y-x
        return float(np.linalg.norm(z-(x+np.clip((z-x)@dd/(dd@dd),0,1)*dd)))
    return min(test(a,c,d),test(b,c,d),test(c,a,b),test(d,a,b))
rprog={}
for phase,P in [('neutral',V),('held_0ms',H)]:
    actual=P[F[retids]];lo,hi=actual.min(1),actual.max(1)
    rails=[rail_path(phase,k) for k in range(2)]
    segs=[[np.array([a,b]) for a,b in zip(x,x[1:])] for x in rails]
    sub=[]
    for k,r in enumerate(segs):
        hits=[]
        seam=end_seams[f'{[SHIN,THIGH][k]:.3f}']
        for i,t in enumerate(r):
            for j in np.flatnonzero(((lo<=t.max(0)+eps)&(hi>=t.min(0)-eps)).all(1)):
                p=xyz_boundary(t,actual[j])
                if p is None:continue
                fi=int(retids[j])
                if any(set(z['source_edge'])<=set(F[fi]) and np.linalg.norm(z[phase]-p)<2.e-7 for z in seam):continue
                hits.append({'rail_span':i,'retained_face':fi,'proper_hit_m':p.tolist()})
        sub.append(hits)
    rprog[phase]={'thigh_shin_min_centerline_separation_mm':1000*min(between_segments(u,v) for u in segs[0] for v in segs[1]),
          'new_actual_shin_rail_transverse_hits_retained':sub[0],
          'new_actual_thigh_rail_transverse_hits_retained':sub[1],
          'not_tube_or_surface_between_patches_proof':True}
(here/'rail_readback.json').write_text(json.dumps(rprog,indent=2)+'\n')
summary={n:[{'x':f['station_m'],'retained':len(x['retained_exact_occupied_face_pairs']),'self':len(x['strict_intra_section_face_pairs']),
 'arc_angle':float(x['compressed_fold_angle_deg']),'signed_thickness_min_mm':float(1000*min(x['signed_mount_thickness_m'])),
 'arc_error_m':x['same_fabric_arc_length_error_m'],'negative_twice_signed_area_count':int(sum(x['signed_area_twice_square_m']<=0))}
 for f,x in zip(fixture,rr)] for n,rr in sc.items()}
(here/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
