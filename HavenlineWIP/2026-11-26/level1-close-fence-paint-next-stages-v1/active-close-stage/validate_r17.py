import json, math, re, sys
from pathlib import Path
out=Path(sys.argv[1])
assert len(sys.argv)==4 and sys.argv[3]=='--active-close'
stock=json.loads(Path(sys.argv[2]).read_text())
actual=json.loads((out/'functional.json').read_text())
assert actual['controlled_checkpoint']==stock['controlled_checkpoint']
assert all(actual['phases'][k]['checkpoints']==stock['phases'][k]['checkpoints']
           and actual['phases'][k]['checks']==stock['phases'][k]['checks']
           for k in ('write','cold'))
frames={}
motion={}
inherited_motion={}
for role in ('write','cold'):
    text=(out/(role+'.log')).read_text()
    rows=[json.loads(s) for s in re.findall(r'^R17_NATIVE_DRAW_EVIDENCE (.+)$',text,re.M)]
    assert len(rows)==(5 if role=='write' else 1)
    ticks=[json.loads(s) for s in re.findall(r'^R17_MOTION_TICKS (.+)$',text,re.M)]
    assert len(ticks)==1 and ticks[0]==([82,82] if role=='write' else [0,0])
    inherited=[json.loads(s) for s in re.findall(r'^CLOSE_INHERITED_MOTION_COUNTS (.+)$',text,re.M)]
    assert inherited==([[41,41]] if role=='write' else [])
    inherited_motion[role]=inherited[0] if inherited else None
    motion[role]=ticks[0]
    for row in rows:
        phase=row['phase']
        assert [row[k] for k in ('panels','posts','tris','stock_daylight_degrees','stock_shadow_enabled')]==[12,4,8384,[-48,-28,0],True]
        assert set(row['gates'])=={'gate-south','gate-east'}
        for g,gate in row['gates'].items():
            active=phase in ('east-bidirectional','writer-v2') or phase=='south-bidirectional' and g=='gate-south'
            assert abs(gate['angle']-(math.pi/2 if active else 0))<.00001
            assert gate['technical_box_leaf_placeholder'] is False
            assert len(gate['projected_hinge_verticals_px'])==2
            for bx,by,tx,ty in gate['projected_hinge_verticals_px']:
                assert abs(tx-bx)<.001 and by-ty>1
        frames[phase]=row
assert set(frames)=={'fresh-spawn','paid-first-frame','south-bidirectional','east-bidirectional','writer-v2','cold-v2-no-replay'}
print(json.dumps({'scope':'native stock daylight & camera, visible wall/post shell with exact imported clearance-authored leaves; closure counters are separately verified; no device, appearance or performance acceptance',
  'exact_stock_checkpoint_and_save_digest_match':True,'gates_transition_ticks':motion,'inherited_open_motion_ticks':inherited_motion,'samples':frames},indent=2,sort_keys=True))
