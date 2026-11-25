"""Run the frozen strict-triangle checker on actual route CPU mesh dumps.
Good measured clearances are not gameplay captures or dynamic/LOD guarantees.
"""
import contextlib
import hashlib
import io
import json
import runpy
import sys
from pathlib import Path
import numpy as np

RAW_CHECKER_SHA = '533edea2220e437f37f80350e7ac1404d0b740d741ed08e4c6fd6adf3793508b'
STEP=.020
MIN_PLANNED_GAP=.010
TAGS = (
    "center-inboard-hard-stop", "center-outboard-hard-stop",
    "center-inboard-stance", "center-outboard-stance",
    "shoulder-inboard-left", "shoulder-inboard-right",
    "shoulder-outboard-left", "shoulder-outboard-right",
)
def digest(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()
def surfaces(p):
    return np.concatenate([np.array(q['positions'], dtype=np.float64)[np.array(q['triangles']).reshape(-1,3)]
                           for q in json.loads(p.read_text())])
def y_slab_gap(d,h,s):
    # Retain all donor faces that could share an x and a 20 mm height interval
    # with the actor. Exact triangle Z extrema (vertices) over these supersets
    # give a conservative lower bound, not a nearest-point distance.
    lo,hi = h.min((0,1)),h.max((0,1))
    dx = d[(d[:,:,0].max(1)>=lo[0])&(d[:,:,0].min(1)<=hi[0])]
    out=[]
    for slab in range(int(np.floor(lo[1]/STEP)),int(np.floor(hi[1]/STEP))+1):
        y=slab*STEP
        within=lambda t:t[(t[:,:,1].max(1)>=y)&(t[:,:,1].min(1)<=y+STEP)]
        a,b=within(dx),within(h)
        if len(a) and len(b):
            dz=(a[:,:,2]*s).max()
            hz=(b[:,:,2]*s).min()
            out.append((float(hz-dz),slab, float(hz),float(dz)))
    return min(out) if out else None

if __name__=="__main__":
    original_argv=sys.argv[:]
    assert len(original_argv)==3, "script requires native-dump-path pinned-checker-path"
    p,checker=map(Path,original_argv[1:])
    assert digest(checker)==RAW_CHECKER_SHA
    sys.argv=[str(checker),str(p)]
    # Preserve checker byte-for-byte; the initial top-level run computes both stops.
    with contextlib.redirect_stdout(io.StringIO()):
        ns=runpy.run_path(str(checker))
    results={tag:ns['z'][tag.split('-')[1]] for tag in TAGS[:2]}
    tags=(*TAGS, *(f"seam-{side}-{end}" for side in ("inboard","outboard") for end in ("left","right")))
    if not (p/(tags[-1]+".json")).is_file():
        tags=TAGS
    for tag in tags[2:]:
        results[tag]=ns['check_hero'](p/(tag+'.json'))
    donor=surfaces(p/'counter.json')
    summary={}
    for key,x in results.items():
        p0=p/(key+".json")
        gap=y_slab_gap(donor,surfaces(p0),1 if 'inboard' in key else -1)
        summary[key]={'surfaces':x['surfaces'],
            'longest_strict_worktop_segments':x['longest_worktop_hits_m_with_triangle_ids_and_contact_point'],
            'longest_other_strict_segments':x['longest_other_hits'],
            'field_of_view_checked':False,
            'signed_z_conservative_gap_m_in_20mm_y_slabs': None if gap is None else gap[0],
            'limiting_slab':gap,
            'native_dump_sha256':digest(p0)}
    strict={k:sum(x['all_counter_intersections'] for x in r['surfaces']) for k,r in summary.items()}
    centers=all(summary[k]['signed_z_conservative_gap_m_in_20mm_y_slabs'] is not None and
                summary[k]['signed_z_conservative_gap_m_in_20mm_y_slabs']>=MIN_PLANNED_GAP for k in TAGS[:4])
    print(json.dumps({'actual_donor_dump_sha256':digest(p/'counter.json'),'native_poses':summary,
            'strict_pair_count_by_site':strict,'centers_and_service_stances_conservative_gap_at_least_10mm': centers,
            'tested_geometry_clear':centers and not any(strict.values())},indent=2,sort_keys=True))
    raise SystemExit(0 if centers and not any(strict.values()) else 1)
