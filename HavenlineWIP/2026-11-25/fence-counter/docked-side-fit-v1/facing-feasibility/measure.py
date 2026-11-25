"""Measure true native planned facing samples and bounded all-yaw planning hull."""
import contextlib, hashlib, io, json, multiprocessing, runpy, sys, tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np

CHECKER_HASH='533edea2220e437f37f80350e7ac1404d0b740d741ed08e4c6fd6adf3793508b'
DONOR_HASH='7825ba134e6b13ce6539e3cbab16899f64a2cd83de0e085a50e6443fc08d36b4'
SLAB=.020
METRIC_MARGIN=.010
EDGE=1.825
A=None

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def physical(p): return A['check_hero'](Path(p))
def facets(p):
    return np.concatenate([np.array(q['positions'],dtype=np.float64)[np.array(q['triangles']).reshape(-1,3)]
                           for q in json.loads(p.read_text())])

def donor_overlap(a,b,i):
    s=i*SLAB
    return (a<=s+SLAB)&(b>=s)

def gap_side(d,h,side):
    xlo,xhi=h[:,:,0].min(),h[:,:,0].max()
    d=d[(d[:,:,0].min(1)<=xhi)&(d[:,:,0].max(1)>=xlo)]
    dy0,dy1=d[:,:,1].min(1),d[:,:,1].max(1)
    hy0,hy1=h[:,:,1].min(1),h[:,:,1].max(1)
    result=[]
    for i in range(int(np.floor(hy0.min()/SLAB)),int(np.floor(hy1.max()/SLAB))+1):
        dd=donor_overlap(dy0,dy1,i);hh=donor_overlap(hy0,hy1,i)
        if dd.any() and hh.any():
            result.append(float((h[hh,:,2]*side).min()-(d[dd,:,2]*side).max()))
    return min(result) if result else None

def polygon_clip(poly,n,s):
    out=[]
    prev=poly[-1]
    dp=prev@n-s
    for q in poly:
        dq=q@n-s
        if (dq>0.0)!=(dp>0.0):
            out.append(prev+(q-prev)*(dp/(dp-dq)))
        if dq<=0.0:out.append(q)
        prev,dp=q,dq
    return np.array(out)

def planning_contour(raw_donor,hs):
    # For any collision point p, anchorXZ lies in D_i - rotated(H_i)
    # for an overlapping Y slab i. Its projection along any axis cannot
    # exceed max(D_i dot n) + max(||H_i relative to foot||). This remains
    # true through all rigid yaws of the sampled skin poses. It says
    # nothing about unobserved locomotion/animation or different floor heights.
    d0,d1=raw_donor[:,:,1].min(1),raw_donor[:,:,1].max(1)
    slab_support={}
    for pose,row in hs:
        foot=np.array(row['actor_foot'])[[0,2]]
        relmax=np.linalg.norm(pose[:,:,[0,2]]-foot,axis=2).max(1)
        y0,y1=pose[:,:,1].min(1),pose[:,:,1].max(1)
        for i in range(int(np.floor(y0.min()/SLAB)),int(np.floor(y1.max()/SLAB))+1):
            hh=donor_overlap(y0,y1,i)
            if hh.any():
                slab_support[i]=max(float(relmax[hh].max()),slab_support.get(i,0.))
    angle=np.arange(0,360,5.)*np.pi/180.
    axes=np.stack([np.cos(angle),np.sin(angle)],1)
    q=[]
    for i,r in sorted(slab_support.items()):
        chosen=donor_overlap(d0,d1,i)
        if chosen.any():
            d=raw_donor[chosen][:,:,[0,2]].reshape(-1,2)
            q.append(((d @ axes.T).max(0)+r+METRIC_MARGIN, i))
    maxsupport=np.max([a for a,i in q],axis=0)
    # Intersect halfplanes after strict support+margin expansion.
    poly=np.array([[-10.,-10.],[10.,-10.],[10.,10.],[-10.,10.]])
    for n,s in zip(axes,maxsupport):
        poly=polygon_clip(poly,n,s)
        assert len(poly)>=3
    # Report candidate hull overlap with the retained fence strip as a
    # planning property only. Do not mount this shape: legal markers conflict.
    def envelope_at_x(x):
        return [float(z) for j,(a,z0) in enumerate(poly) for b,z1 in [poly[(j+1)%len(poly)]]
                if abs(a-b)>1e-10 and min(a,b)<=x<=max(a,b)
                for z in [z0+(z1-z0)*(x-a)/(b-a)]]
    return dict(
        scope='computed half-plane envelope of potential overlap across all rigid yaw for the sampled pose and Y bands, not an implemented collider',
        vertices_xz=poly.tolist(),support_axes_xz=axes.tolist(),max_outward_support_m=maxsupport.tolist(),
        radius_per_height_slab_m=slab_support, source_plane_slab_m=SLAB,added_outline_margin_m=METRIC_MARGIN,
        marker_inside={str(m):bool(np.all(axes@np.array([0.,m])<maxsupport)) for m in (1.35,-1.45)},
        envelope_z_at_old_seams={str(x): sorted(envelope_at_x(x)) for x in (-EDGE,EDGE)},
        normal_line_extent_for_minmax_z=[float(poly[:,1].min()),float(poly[:,1].max())],
        lateral_extent=[float(poly[:,0].min()),float(poly[:,0].max())],
    )

if __name__=='__main__':
    path,checker=map(Path,sys.argv[1:])
    assert sha(checker)==CHECKER_HASH
    assert sha(path/'counter.json')==DONOR_HASH
    log=(path/'route.log').read_text().splitlines()
    angles=[json.loads(x.removeprefix('ACTUAL_ANGLE ')) for x in log if x.startswith('ACTUAL_ANGLE ')]
    assert len(angles)==14,len(angles)
    assert all(x['floor'] and x['planar_marker_error']<=.002 for x in angles)
    allfiles=sorted(path.glob('*.json'))
    paths=[f for f in allfiles if f.name!='counter.json']
    assert len(paths)==26,len(paths)
    byid={r['id']:r for r in angles}
    sys.argv=[str(checker),str(path)]
    with contextlib.redirect_stdout(io.StringIO()):A=runpy.run_path(str(checker))
    work=[p for p in paths if p.stem not in ('center-inboard-hard-stop','center-outboard-hard-stop')]
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('fork')) as pool:
        result={p.stem:x for p,x in zip(work,pool.map(physical,map(str,work)))}
    result.update((f'center-{k}-hard-stop',v) for k,v in A['z'].items())
    d=facets(path/'counter.json'); measurements={}; hh=[]
    for p in paths:
        r=result[p.stem]
        h=facets(p); side=1 if 'inboard' in p.stem else -1
        row=byid.get(p.stem)
        if row: hh.append((h,row))
        measures=dict(
            born_from_actual_mesh_sha256=sha(p),
            native_angle=row,
            worktop_pairs=sum(y['worktop_intersections'] for y in r['surfaces']),
            all_donor_pairs=sum(y['all_counter_intersections'] for y in r['surfaces']),
            max_strict_other_segments=r['longest_other_hits'][:3],
            max_strict_worktop_segments=r['longest_worktop_hits_m_with_triangle_ids_and_contact_point'][:3],
            conservative_signed_z_gap_m=gap_side(d,h,side),
        )
        measurements[p.stem]=measures
    shared_foot = {}
    # A pure translation normalized specifically to each native 0-degree foot.
    # This is analytic, not a native pose replay or a render.
    with tempfile.TemporaryDirectory(prefix='hvn-coincident-') as tmp:
        for side_id in ('inboard','outboard'):
            foot0=np.array(byid[f'facing-{side_id}-+0']['actor_foot'],dtype=np.float64)
            for deg in (-90,90):
                key=f'facing-{side_id}-{deg:+d}'
                src=path/(key+'.json')
                foot1=np.array(byid[key]['actor_foot'],dtype=np.float64)
                delta=foot0-foot1
                surfaces=json.loads(src.read_text())
                for surf in surfaces:
                    surf['positions']=(np.array(surf['positions'],dtype=np.float64)+delta).tolist()
                normalized=Path(tmp)/(key+'.json')
                normalized.write_text(json.dumps(surfaces,separators=(',',':')))
                strict=A['check_hero'](normalized)
                shared_foot[key]={'translation_to_same_xyz_as_actual_axial_foot':delta.tolist(),
                  'common_axial_foot_xyz':foot0.tolist(),
                  'strict_pairs_at_unchanged_axial_foot':sum(r['all_counter_intersections'] for r in strict['surfaces']),
                  'strict_worktop_pairs_at_unchanged_axial_foot':sum(r['worktop_intersections'] for r in strict['surfaces'])}
    out=dict(snapshot_count=len(paths),same_donor_import_sha256=DONOR_HASH,recipe='actual native steering, sampled clips, no yaw overrides',
             support_contour=planning_contour(d,hh),measurements=measurements,analytic_same_foot_sideways_controls=shared_foot)
    print(json.dumps(out,indent=2,sort_keys=True))
