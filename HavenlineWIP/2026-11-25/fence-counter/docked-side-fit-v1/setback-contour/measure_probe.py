"""Strict posed mesh checks, exact donor worktop points and straight donor occlusion."""
from __future__ import annotations
import hashlib,json,multiprocessing,sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np

C_SHA='533edea2220e437f37f80350e7ac1404d0b740d741ed08e4c6fd6adf3793508b'
D_SHA='7825ba134e6b13ce6539e3cbab16899f64a2cd83de0e085a50e6443fc08d36b4'
A=None

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(p):return A['check_hero'](Path(p))
def xyz(v):return list(map(float,v))
def nearest_hit(origin,target,tri, ids):
    o=np.array(origin); d=np.array(target)-o
    dist=float(np.linalg.norm(d))
    if dist<=1e-8:raise ValueError('empty segment')
    ray=d/dist
    e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
    cross1=np.cross(ray,e2);det=np.einsum('ij,ij->i',e1,cross1)
    cancel=np.abs(det)<1e-12
    otr=o-tri[:,0]
    cross2=np.cross(otr,e1)
    div=np.divide(1.0,det,out=np.zeros(len(tri)),where=~cancel)
    u=np.einsum('ij,ij->i',otr,cross1)*div
    v=cross2@ray*div
    t=np.einsum('ij,ij->i',e2,cross2)*div
    ok=(~cancel)&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>1e-5)&(t<dist+5e-6)
    if not np.any(ok):return None
    k=int(np.argmin(np.where(ok,t,np.inf)))
    w=float(t[k])
    return {'surface':int(ids[k][0]),'triangle':int(ids[k][1]),'point':xyz(o+ray*w),'distance_m':w}

def endpoints(marker,all_board,board_ids):
    mapped={}
    for name in ('Stock','Payment'):
        ref=marker[name+'RestWitness']
        x,y,z=ref
        # Board-only projection locates the true worktop beneath the authored
        # rest-witness XZ without treating the marker itself as geometry.
        hit=nearest_hit([x,1.19,z],[x,.86,z],all_board,board_ids)
        assert hit is not None
        hit['original_rest_witness_local']=ref
        hit['original_handling_marker_local']=marker[name+'Handling']
        hit['board_height_minus_rest_witness_m']=hit['point'][1]-y
        mapped[name]=hit
    return mapped

def measure_lines(pose,targets,tri,ids):
    anatomy={'foot':pose['foot'],**pose['anatomy']}
    rows={}
    for role,where in targets.items():
        target=where['point']
        dist={}
        for b,origin in anatomy.items():
            d=float(np.linalg.norm(np.array(origin)-target))
            hit=nearest_hit(origin,target,tri,ids)
            dist[b]={'straight_line_to_real_worktop_m':d,
                     'straight_line_to_logical_marker_m':
                        float(np.linalg.norm(np.array(origin)-where['original_handling_marker_local'])),
                     'nearest_actual_donor_intersection':hit,
                     'clear_segment_to_target_before_endpoint':hit is None or d-hit['distance_m']<=.0005}
        rows[role]=dist
    return rows

if __name__=='__main__':
    path,src=map(Path,sys.argv[1:])
    assert digest(src)==C_SHA and digest(path/'counter.json')==D_SHA
    rows=[json.loads(x.removeprefix('PRISM_CPU ')) for x in (path/'route.log').read_text().splitlines() if x.startswith('PRISM_CPU ')]
    assert len(rows)==len(set(r['id'] for r in rows)) and len(rows)>0
    sys.argv=[str(src),str(path)]
    code=src.read_text()
    split="z={s:check_hero("
    assert code.count(split)==1
    # Only avoid the frozen checker's CLI iteration; execute all frozen
    # pair/part discrimination and geometry function code byte-for-byte.
    A={'__file__':str(src),'__name__':'__fuel_exact_functions__'}
    exec(compile(code[:code.index(split)],str(src),'exec'),A)
    allcounter=A['allcounter'];donor=A['donor']
    ids=np.array([x[:2] for x in allcounter])
    work=np.array([x[2] for x in allcounter],dtype=bool)
    t=endpoints(rows[0]['actual_unbound_markers'],donor[work],ids[work])
    assert all(r['actual_unbound_markers']==rows[0]['actual_unbound_markers'] for r in rows)
    files=[path/(r['id']+'.json') for r in rows];o={}
    with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('fork')) as pool:
       for r,pb,x in zip(rows,files,pool.map(check,map(str,files))):
         o[r['id']]={'native_pose':r,'real_readback_sha256':digest(pb),
                  'entire_donor_pairs':sum(y['all_counter_intersections'] for y in x['surfaces']),
                  'worktop_pairs':sum(y['worktop_intersections'] for y in x['surfaces']),
                  'strict_longest_worktop_segments':x['longest_worktop_hits_m_with_triangle_ids_and_contact_point'][:3],
                  'strict_longest_other_segments':x['longest_other_hits'][:3]}
         if r['kind']=='temporary-stance':
             o[r['id']]['donor_only_segment_lines_to_actual_stock_payment_surfaces']=measure_lines(r,t,donor,ids)
    print(json.dumps({
          'native_pose_count':len(rows),'all_six_immutable_surface_references':rows[0]['actual_unbound_markers'],
          'exact_actual_worktop_endpoints':t,'same_donor_sha256':D_SHA,
          'acceptance_scope':'hypothetical scene only; no service reach or actual interaction authorization',
          'sites':o},indent=2,sort_keys=True))
