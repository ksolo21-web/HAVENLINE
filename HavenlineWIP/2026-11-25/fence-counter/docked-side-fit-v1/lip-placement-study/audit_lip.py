"""One bounded offline probe of two original donor near edges. No scene/model edits."""
from __future__ import annotations
import contextlib,itertools,io,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
from compare_glb import bdata,digest,GLB_SHA,NATIVE_SHA
CHECKER_SHA='533edea2220e437f37f80350e7ac1404d0b740d741ed08e4c6fd6adf3793508b'
SETBACK_SHA='8c3b304dd31528cdfa2a4a53dedc3ce0a4e5d483f320e17af11bd3857cf837f9'
RAY_SCRIPT_SHA='a6306374e906998dab3d74868923231631dc2dc635015037542a6a36978469c2'
HALF=.025;HOVER=.050;EPS=.0005

def clip(poly,normal,level):
    if not len(poly):return poly
    out=[];a=poly[-1];d=float(a@normal-level)
    for b in poly:
        e=float(b@normal-level)
        if (e>0)!=(d>0):out.append(a+(b-a)*(d/(d-e)))
        if e<=0:out.append(b)
        a,d=b,e
    return np.asarray(out)

def area(poly):
    if len(poly)<3:return 0.
    q=np.roll(poly,-1,axis=0)
    return .5*float(np.sum(poly[:,0]*q[:,1]-poly[:,1]*q[:,0]))

def clip_box(poly,coords):
    for j,lo,hi in coords:
      n=np.zeros(poly.shape[1]);n[j]=1
      poly=clip(clip(poly,n,hi),-n,-lo)
      if not len(poly):break
    return poly

def prove_footprint(board,target,alltri,meta):
    bounds=[(0,target[0]-HALF,target[0]+HALF),(2,target[2]-HALF,target[2]+HALF)]
    bb=(board[:,:,0].min(1)<=bounds[0][2])&(board[:,:,0].max(1)>=bounds[0][1])&(
           board[:,:,2].min(1)<=bounds[1][2])&(board[:,:,2].max(1)>=bounds[1][1])
    # Only true top faces of worktop board, before clipping to exact square.
    u=np.cross(board[:,1]-board[:,0],board[:,2]-board[:,0])
    u=np.divide(u,np.linalg.norm(u,axis=1)[:,None],out=np.zeros_like(u),where=np.linalg.norm(u,axis=1)[:,None]>1e-12)
    bb&=(board[:,:,1].min(1)>1.06)&(np.abs(u[:,1])>.98)
    parts=[];pieces=[];heights=[]
    for i in np.flatnonzero(bb):
        poly=clip_box(board[i],bounds)
        z=poly[:,[0,2]] if len(poly) else np.empty((0,2))
        a=area(z)
        if abs(a)<1e-14:continue
        if a<0:z=z[::-1]
        parts.append(z)
        heights.extend(poly[:,1])
        pieces.append(dict(native_surface=int(meta[i][0]),native_triangle=int(meta[i][1]),
            projected_area_m2=abs(a),top_normal_absy=float(abs(u[i,1])),clipped_polygon_xyz=poly.tolist()))
    oo=[]
    for a,b in itertools.combinations(parts,2):
        c=a
        for p,q in zip(b,np.roll(b,-1,axis=0)):
            d=q-p;outer=np.array([d[1],-d[0]])
            c=clip(c,outer,p@outer)
        oo.append(abs(area(c)))
    maximum=max(heights);minimum=min(heights)
    vol=bounds+[(1,maximum+.001,float(target[1]+HOVER))]
    mask=np.ones(len(alltri),bool)
    for j,lo,hi in vol:mask&=(alltri[:,:,j].min(1)<=hi)&(alltri[:,:,j].max(1)>=lo)
    over=[i for i in np.flatnonzero(mask) if len(clip_box(alltri[i],vol))]
    total=sum(x['projected_area_m2'] for x in pieces);fraction=total/(2*HALF)**2
    assert abs(fraction-1.)<1e-7,(target, total, len(pieces))
    assert max([0.,*oo])<1e-10
    return dict(
        square_side_m=2*HALF, projected_covered_area_m2=total,coverage_fraction=fraction,
        pairwise_max_interior_projection_overlap_m2=max([0.,*oo]),
        exact_clipped_height_span_m=maximum-minimum, exact_top_height_interval_m=[minimum,maximum],
        projected_area_pieces=pieces,
        min_absolute_top_normal_dot_vertical=min(p['top_normal_absy'] for p in pieces),
        box_from_top_max_plus_1mm_to_50mm_hover_unchanged_donor_contained_facet_count=len(over),
    )

def clamp_point_seg(p,a,b):
    d=b-a
    den=np.einsum('...i,...i->...',d,d)
    v=np.divide(np.einsum('...i,...i->...',p-a,d),den,out=np.zeros_like(den),where=den>1e-32)
    q=a+np.clip(v,0,1)[...,None]*d
    return np.einsum('...i,...i->...',p-q,p-q)

def point_tri_sq(p,t):
    a,b,c=np.moveaxis(t,1,0)
    ab=b-a;ac=c-a
    n=np.cross(ab,ac)
    n2=np.einsum('ij,ij->i',n,n)
    rel=p-a
    dot=np.einsum('ij,ij->i',rel,n)
    f=np.divide(dot,n2,out=np.zeros_like(dot),where=n2>1e-30)
    v=rel-f[:,None]*n
    d00=np.einsum('ij,ij->i',ab,ab)
    d11=np.einsum('ij,ij->i',ac,ac)
    d01=np.einsum('ij,ij->i',ab,ac)
    d10=np.einsum('ij,ij->i',v,ab)
    d12=np.einsum('ij,ij->i',v,ac)
    den=d00*d11-d01*d01
    uu=np.divide(d11*d10-d01*d12,den,out=np.zeros_like(den),where=den>1e-29)
    vv=np.divide(d00*d12-d01*d10,den,out=np.zeros_like(den),where=den>1e-29)
    normalok=(den>1e-29)&(uu>=0)&(vv>=0)&(uu+vv<=1.)
    face=np.where(normalok,dot*f,np.inf)
    return np.minimum(face,np.minimum(np.minimum(clamp_point_seg(p,a,b),clamp_point_seg(p,b,c)),clamp_point_seg(p,c,a)))

def seg_seg_sq(a,b,c,d):
    # Endpoints cover all boundary cases of this convex two-param fit.
    cc=np.broadcast_to(a,c.shape);dd=np.broadcast_to(b,c.shape)
    answer=np.minimum(np.minimum(clamp_point_seg(cc,c,d),clamp_point_seg(dd,c,d)),
                      np.minimum(clamp_point_seg(c,cc,dd),clamp_point_seg(d,cc,dd)))
    u=b-a;v=d-c;w=a-c
    uu=u@u;vv=np.einsum('ij,ij->i',v,v);uv=v@u
    uw=w@u;vw=np.einsum('ij,ij->i',v,w);den=uu*vv-uv*uv
    s=np.divide(uv*vw-vv*uw,den,out=np.zeros_like(den),where=den>1e-29)
    t=np.divide(uu*vw-uv*uw,den,out=np.zeros_like(den),where=den>1e-29)
    inside=(den>1e-29)&(s>=0)&(s<=1)&(t>=0)&(t<=1)
    p=w+s[:,None]*u-t[:,None]*v
    return np.minimum(answer,np.where(inside,np.einsum('ij,ij->i',p,p),np.inf))

def trace(origin,target,tri,ids,mats,ray,distance=True):
    a,b=np.array(origin),np.array(target)
    length=float(np.linalg.norm(a-b)); hit=ray(a,b,tri,ids)
    if hit:hit['material']=mats[hit['surface']][0];hit['before_target_m']=length-hit['distance_m']
    d=dict(length_m=length,first_actual_donor_hit=hit,
        no_early_hit=(hit is None or hit['before_target_m']<=EPS))
    if distance and hit is None:  # not a solid swept hand; min straight ray tube radius only.
        best=np.minimum(point_tri_sq(a,tri),point_tri_sq(b,tri))
        for i,j in ((0,1),(1,2),(2,0)):best=np.minimum(best,seg_seg_sq(a,b,tri[:,i],tri[:,j]))
        k=int(np.argmin(best));d['minimum_segment_to_donor_surface_distance_m']=float(np.sqrt(best[k]))
        d['nearest_surface_triangle']=[int(v) for v in ids[k]]
    return d

if __name__=='__main__':
    glb,posed_dir,result,ch,ray_script=map(Path,sys.argv[1:])
    assert digest(result)==SETBACK_SHA and digest(ch)==CHECKER_SHA and digest(ray_script)==RAY_SCRIPT_SHA
    matched,mats=bdata(glb,posed_dir/'counter.json')
    source=result.read_text();poses=json.loads(source)
    sys.argv=[str(ch),str(posed_dir)]
    raw=ch.read_text();outside="z={s:check_hero("
    assert raw.count(outside)==1
    ns={}
    with contextlib.redirect_stdout(io.StringIO()):exec(compile(raw[:raw.index(outside)],str(ch),'exec'),ns)
    helper=runpy.run_path(str(ray_script))
    ray=helper['nearest_hit'];allc=ns['allcounter'];tri=ns['donor']
    ids=np.array([x[:2] for x in allc]);board=np.array([x[2] for x in allc],bool)
    candidates={};controls={}
    for side,s in [('inboard',1),('outboard',-1)]:
        q=ray([0,1.19,.66*s],[0,.89,.66*s],tri[board],ids[board])
        assert q is not None
        surface=q['surface'];q['source_glb_facet']=[surface,mats[surface][1][q['triangle']]];q['owner_material']=mats[surface][0]
        target=np.array(q['point']);hover=target+np.array([0.,HOVER,0.])
        support=prove_footprint(tri[board],target,tri,ids[board])
        for row in support['projected_area_pieces']:
            i=row['native_surface'];row['source_glb_triangle']=mats[i][1][row['native_triangle']]
            row['source_glb_material']=mats[i][0]
        down=trace(hover,target,tri,ids,mats,ray,distance=False)
        assert down['no_early_hit']
        rays={}
        for deg in [0,-90,90]:
            label=f'temp-{side}-{deg:+d}'
            stored=poses['sites'][label];pose=stored['native_pose'];anchors=pose['anatomy']
            assert digest(posed_dir/(label+'.json'))==stored['real_readback_sha256']
            rays[label]={'pose_sha256':stored['real_readback_sha256'],'native_yaw_already_frozen':pose['yaw'],'origins':{}}
            refs=stored['donor_only_segment_lines_to_actual_stock_payment_surfaces']
            controls[label]=refs
            for origin,p in anchors.items():
                rays[label]['origins'][origin]={'exact_pose_pivot':p,
                    'direct_to_actual_rest':trace(p,target,tri,ids,mats,ray,distance=False),
                    'direct_to_hypothetical_50mm_hover':trace(p,hover,tri,ids,mats,ray)}
                if origin in ('L_Hand','R_Hand'):
                    # A single fixed diagnostic construction: raise the sampled
                    # pivot vertically outside the donor before transferring
                    # at the exact +50mm hover height. No search or IK;
                    # compare only donor surface clearance along two segments.
                    el=np.array([p[0],hover[1],p[2]])
                    a=trace(p,el,tri,ids,mats,ray)
                    b=trace(el,hover,tri,ids,mats,ray)
                    m=[x.get('minimum_segment_to_donor_surface_distance_m') for x in (a,b)]
                    rays[label]['origins'][origin]['concept_only_lift_then_level_hover']={
                        'waypoint':el.tolist(),'vertical_lift':a,'level_transfer':b,
                        'intentionally_excludes_final_surface_contact_segment':True,
                        'combined_path_length_m':a['length_m']+b['length_m'],
                        'combined_minimum_centerline_to_donor_surface_distance_m':min(m) if all(x is not None for x in m) else None,
                        'not_ik_contact_or_authored_animation':True}
        candidates[side]=dict(actual_rest=q,point_50mm_above=hover.tolist(),footprint=support,
            hover_to_rest_zero_radius_descent=down,exact_axial_and_sideways_pivot_probes=rays)
    print(json.dumps(dict(
        status='bounded geometry source brief only; handoff/placement roles, apparent visibility, gameplay not approved',
        source_exact_hashes={'donor_binary':GLB_SHA,'native_donor_surface':NATIVE_SHA,'prior_frozen_poses':SETBACK_SHA},
        decoded_glb_to_native_triangle_bijection=matched,existing_stock_payment_unchanged=poses['exact_actual_worktop_endpoints'],
        existing_blocked_reach_controls_reused_not_rerun=controls, proposed_unbound_two_sided_patches=candidates,
        no_edits=True,no_native_rerun=True,no_images=True),indent=2,sort_keys=True))
