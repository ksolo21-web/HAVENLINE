from pathlib import Path
import hashlib,json,re,sys
out=Path(sys.argv[1])
package=Path(sys.argv[2])
control=json.loads((package/'control-frames.json').read_text())['frames']
live=json.loads((out/'frame-evidence.json').read_text())['frames']
assert set(control)==set(live)
comparable=('queued_tick','wood','renewals','paid','south_open','east_open')
assert all(all(control[k][v]==live[k][v] for v in comparable) for k in live)
control_r17=json.loads((package/'control-r17.json').read_text())
now_r17=json.loads((out/'r17-evidence.json').read_text())
assert now_r17['gates_transition_ticks']==control_r17['gates_transition_ticks']
for key in live:
    x=now_r17['samples'][key]; y=control_r17['samples'][key]
    assert all(x[k]==y[k] for k in ('panels','posts','stock_daylight_degrees','stock_shadow_enabled'))
    for gate in x['gates']:
        assert x['gates'][gate]['angle']==y['gates'][gate]['angle']
rows={}
for phase in ('write','cold'):
    log=(out/(phase+'.log')).read_text()
    assert log.count('REFERENCE_PANEL_MOUNT one authored panel replaces one stock transform')==1
    assert 'REFERENCE_PANEL_FALLBACK' not in log
    for l in re.findall(r'^REFERENCE_PANEL_BOUNDS (.+)$',log,re.M):
        row=json.loads(l); key=row['phase']
        assert key not in rows and row['stock_neighbors']==11
        assert row['paid_visible'] is live[key]['paid']
        rows[key]={**row,'control_native_sha256':control[key]['matching_native_buffer_sha256'],
            'detail_native_sha256':live[key]['matching_native_buffer_sha256']}
assert set(rows)==set(live)
x0,y0,x1,y1=rows['paid-first-frame']['rectangle_px']
assert 300<x0<x1<560 and 170<y0<y1<420 and (x1-x0)>60 and (y1-y0)>40
print(json.dumps({'stock_authority_and_daylight_unchanged':True,
 'exact_one_replacement_no_fallback':True,'review_primary':'paid-first-frame.png',
 'wall_neighbor_readability_and_roi_are_not_artist_approval':True,'frames':rows},indent=2,sort_keys=True))
