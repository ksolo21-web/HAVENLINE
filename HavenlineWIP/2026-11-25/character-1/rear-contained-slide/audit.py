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
td=confirm('hvn-l1-c1-rear-whole-junction-section-v1','e36ac3a34cad40937960ef29cd03f624301c70d230c5ea50803fee99fae2554a')
p=json.loads((td/'result.json').read_text()); ret=np.flatnonzero(~np.isin(np.arange(len(F)),reg))
assert len(ret)==42393 and len(p['protected_perimeter_collar_edges'])==162
assert set(range(42528,42534)).issubset(set(reg))
eye=np.eye(3); Y=eye[1]; X=eye[0]
def unit(x):return np.asarray(x)/np.linalg.norm(x)
# Closed consistently oriented prism indexing in meter frame.
Fbox=np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],
  [0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
th=.00060; strap=.0045; pocket_depth=.00130; offset=.001; drive_end_keepout=.0006
assert pocket_depth>th and strap>.004
def volume_tri(C):
    Q=C[Fbox]-C[0]
    return float(np.einsum('ij,ij->i',Q[:,0],np.cross(Q[:,1],Q[:,2])).sum()/6)
def slot(st,side,bone):
    pose=st[f'{side}_attachment']
    rail=np.asarray(pose['neutral'])
    rim=np.asarray(st[side]['neutral'])
    D=rim-rail; L=np.linalg.norm(D); k=unit(D)
    w=unit(X-k*(X@k)); n=unit(np.cross(k,w))
    if n@Y<0:w=-w;n=-n
    # One enclosed sleeve seat parallel to the exact neutral output-plane rail,
    # offset into allowable interior. The shut end stops 0.60mm before the
    # unchanged material seam. End seams and loaded pose are not retargeted.
    a=rail-n*offset; b=rim-n*offset-k*drive_end_keepout
    w0=w*strap/2;n0=n*pocket_depth/2
    C=np.vstack([np.array([q-w0-n0,q+w0-n0,q+w0+n0,q-w0+n0]) for q in (a,b)])
    E=Xform(C,bone)
    assert abs(volume_tri(C)-volume_tri(E))<2e-9*abs(volume_tri(C))+1e-13
    mm={'attachment_family':pose['rigid_bone'],'source_face':pose['source_triangle'],'source_barycentric':pose['source_barycentric'],
        'unchanged_neutral_receiving_seam':rim.tolist(),'frozen_received_held_seam':st[side]['held_0ms'],
        'source_seam_edge':st[side]['source_edge'],'source_seam_weights':st[side]['weights'],
        'slide_axis_bind':k.tolist(),'slide_axis_exact_held':(M[bone,:3,:3]@k).tolist(),
        'zero_allowance_upper_storage_m':float(L),'finite_travel_m':float(L-drive_end_keepout),
        'seat_inward_orientation_bind':(-n).tolist(),
        'seat_neutral_in_serial_m':[a.tolist(),b.tolist()],
        'seat_held_exact_in_serial_m':Xform(np.stack([a,b]),bone).tolist()}
    return C,E,mm
def raysection(P,z):
    A=P[F];lo=A[:,:,2].min(1);hi=A[:,:,2].max(1)
    ids=np.flatnonzero((lo<=z)&(hi>=z)); T=A[ids];rr=[]
    for j,k in [(0,1),(1,2),(2,0)]:
        a=T[:,j,:];b=T[:,k,:];d=a[:,2]-b[:,2]
        ok=np.flatnonzero(abs(d)>1e-15);u=(a[ok,2]-z)/d[ok];take=(u>=-1e-12)&(u<=1+1e-12)
        K=a[ok[take]]+(b[ok[take]]-a[ok[take]])*u[take,None]
        rr.extend((int(i),w) for i,w in zip(ids[ok[take]],K))
        kk=np.flatnonzero((abs(d)<=1e-15)&(abs(a[:,2]-z)<=1e-13));rr.extend((int(ids[c]),q) for c in kk for q in T[c,[j,k]])
    return rr
def exterior_seal(C,V):
    out=[]
    for v in C:
        a=max(raysection(V,float(v[2])),key=lambda x:x[1][1]);x,y=a
        out.append({'new_xyz':v.tolist(),'exact_native_original_side_y_face':x,'native_side_xyz':y.tolist(),'posterior_overrun_mm':1000*float(v[1]-y[1])})
    return max(out,key=lambda x:x['posterior_overrun_mm'])
def retained_overlaps(C,V):
    orig=V[F[ret]]
    lo=orig.min(1);hi=orig.max(1);hits=[]
    for i,f in enumerate(Fbox):
        v=C[f];Min=v.min(0);Max=v.max(0)
        for j in np.flatnonzero(((lo<=Max+eps)&(hi>=Min-eps)).all(1)):
            w=orig[j];n=np.cross(w[1]-w[0],w[2]-w[0])
            if np.linalg.norm(n)<1e-12:continue
            H0=hit_points(v,w)
            if H0:hits.append({'seat_face':i,'exact_retained_source_face':int(ret[j]),'xyz':H0[0].tolist()})
    return hits
def overlap(C,D):
    pairs=[]
    for i,f in enumerate(Fbox):
        a=C[f]
        for j,g in enumerate(Fbox):
            b=D[g]
            if ((a.min(0)>b.max(0)+eps)|(b.min(0)>a.max(0)+eps)).any():continue
            if proper(a,b,[]):pairs.append([i,j])
    return pairs
def inside_box(A,c):
    det=A[[1,3,4]]-A[0]
    w=np.linalg.solve(det.T,c-A[0])
    return bool(np.all(w>eps) and np.all(w<1-eps))
out=[]; a0=[];a1=[]
for i,st in enumerate(p['placed_stations']):
    slots=[slot(st,side,bone) for side,bone in [('lower',1),('upper',0)]]
    s0=np.stack([a for a,b,z in slots]);s1=np.stack([b for a,b,z in slots])
    assert min(map(volume_tri,s0))>0 and min(map(volume_tri,s1))>0
    # Exact same demanded laminate chart length as frozen proposed cloth,
    # reduce it by the held connecting straight-run length. This direct
    # storage budget is specific to the simple two-seat linear architecture;
    # an authored longer in-shape arc changes that mechanical architecture.
    rail=[a['held_0ms'] for a in (st['lower_attachment'],st['upper_attachment'])]
    chord=float(np.linalg.norm(np.asarray(rail[0])-rail[1]))
    L=st['rest_length_of_two_lobe_material_arc_m']
    bound=sum(z['zero_allowance_upper_storage_m'] for a,b,z in slots)
    phys=sum(z['finite_travel_m'] for a,b,z in slots)
    out.append({'station_X_m':st['station_m'],'fixed_chart_material_length_m':L,'exact_held_two_mount_chord_m':chord,
      'required_tail_travel_direct_connector_m':L-chord,'permitted_architecture_two_seat_upper_bound_ignore_contact_m':bound,
      'finite_actual_seat_axial_travel_m':phys,'necessary_connector_minimum_if_both_seats_dispatched_m':L-bound,'strict_geometric_travel_deficit_before_collisions_m':L-chord-bound,
      'transport_lanes':[z for a,b,z in slots],
      'neutral':{'signed_seat_prism_volumes_mm3':[1e9*volume_tri(u) for u in s0],'source_retained_crossings':[retained_overlaps(a,V) for a in s0],
       'strict_between_seat_surface_contacts':overlap(*s0),'strict_center_containment':bool(inside_box(s0[0],s0[1].mean(0)) or inside_box(s0[1],s0[0].mean(0))),
       'true_side_projection_node_worst':[exterior_seal(v,V) for v in s0]},
      'held_0ms':{'signed_seat_prism_volumes_mm3':[1e9*volume_tri(u) for u in s1],'source_retained_crossings':[retained_overlaps(a,H) for a in s1],
       'strict_between_seat_surface_contacts':overlap(*s1),'strict_center_containment':bool(inside_box(s1[0],s1[1].mean(0)) or inside_box(s1[1],s1[0].mean(0))),
       'true_side_projection_node_worst':[exterior_seal(v,H) for v in s1]}})
    a0.append(s0);a1.append(s1)
assert min(z['strict_geometric_travel_deficit_before_collisions_m'] for z in out)>.034
# Record all exact available CAD sections/seat/end wires, but do not build any
# exterior front/side cloth or mutate the exact restore geometry.
A0=np.array(a0);A1=np.array(a1);cc=np.array(p['protected_perimeter_collar_edges']);rr=np.array(p['protected_full_authorized_rim_order'])
np.savez_compressed(here/'editable_slide_seat_diagnostic.npz',neutral_seats=A0,held_exact_seats=A1,seat_face_indices=Fbox,
    protected_collar_neutral=V[cc],protected_collar_held=H[cc],approved_seam_neutral=V[rr],approved_seam_held=H[rr])
with (here/'editable_slide_seats.obj').open('w') as f:
    cur=1
    for ph,P0,Z in [('neutral',V,A0),('held_0ms',H,A1)]:
        for i,group in enumerate(Z):
            for j,C in enumerate(group):
                f.write(f'o {ph}_section_{i}_'+('Shin_rail_closed_seat' if j==0 else 'Thigh_rail_closed_seat')+'\n')
                for v in C:f.write('v %.10f %.10f %.10f\n'%tuple(v))
                for t in Fbox:f.write('f '+' '.join(str(cur+int(i)) for i in t)+'\n')
                cur+=8
        for label,L in [('protected_collar_162_edges',P0[cc]),('exact_authorized_41_edge_rim',P0[np.stack([rr,np.roll(rr,-1)],axis=1)])]:
            f.write('o '+ph+'_'+label+'\n')
            for ea,eb in L:
                for v in [ea,eb]:f.write('v %.10f %.10f %.10f\n'%tuple(v))
                f.write(f'l {cur} {cur+1}\n');cur+=2
def validate_whole_seat_bank(bank):
    Rt=bank.reshape(-1,8,3)
    touch=[]
    for i,A in enumerate(Rt):
        for j,B in enumerate(Rt[:i]):
            p=overlap(A,B)
            if p or inside_box(A,B.mean(0)) or inside_box(B,A.mean(0)):
                touch.append({'seat_indices':[j,i],'strict_face_contacts':p,'center_containment':bool(inside_box(A,B.mean(0)) or inside_box(B,A.mean(0)))})
    return touch
bank_results={'neutral':validate_whole_seat_bank(A0),'held_0ms':validate_whole_seat_bank(A1)}
res={'state':'REJECT_DIRECT_LONGITUDINAL_TWO_SEAT_MATERIAL_TRAVEL',
 'entire_12_seat_bank_between_seat_contacts_or_center_containment':bank_results,'unchanged_protected_collar_edge_count':len(cc),'unchanged_approved_seam_edge_count':len(rr),
 'anterior_source_four_rows_preserved':src['anterior_source_native_rows'],'excluded_only_approved_replacement_rows':147,
 'actual_retained_obstacle_source_triangle_count':len(ret),'solid_seat_depth_mm':pocket_depth*1000,'strap_nominal_width_mm':strap*1000,
 'strap_t_m':th,'finite_end_allowance_mm':drive_end_keepout*1000,'station_rows':out,
 'primary_stop':'Even optimistic traversal without ends/stops/contact is insufficient for this direct independent pair of slide seats. No sleeve or exterior has been authored.',
 'cavity_limit':'Finite sleeves intersect/or clear the actual retained surfaces as recorded; a closed body volume cannot be inferred from a retained source with 162 collar and 41 omitted edges.',
 'not_a_proof_for_all_path_architectures':True,
 'only_two_exact_pose_source_snapshots_no_interpolation_claim':True}
(here/'result.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps([{'station_mm':i['station_X_m']*1000,'desired_tail_mm':i['required_tail_travel_direct_connector_m']*1000,
        'upper_bound_mm':i['permitted_architecture_two_seat_upper_bound_ignore_contact_m']*1000,'finite_mm':i['finite_actual_seat_axial_travel_m']*1000,
        'deficit_mm':i['strict_geometric_travel_deficit_before_collisions_m']*1000,
        'neutral_cross':[len(h) for h in i['neutral']['source_retained_crossings']],
        'held_cross':[len(h) for h in i['held_0ms']['source_retained_crossings']],
        'max_held_side_excess_mm':max(j['posterior_overrun_mm'] for j in i['held_0ms']['true_side_projection_node_worst'])} for i in out],indent=2))
