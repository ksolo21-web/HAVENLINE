from pathlib import Path
import hashlib,json,re,subprocess,sys
p=Path(sys.argv[1]); cfg=json.loads(Path(sys.argv[2]).read_text()); w=(p/'write.log').read_text(); c=(p/'cold.log').read_text()
assert len(re.findall(r'^CLOSE_ASSERT_OK ',w,re.M))==11
assert re.findall(r'^CLOSE_INHERITED_MOTION_COUNTS (.+)$',w,re.M)==['[41,41]']
assert re.findall(r'^R17_MOTION_TICKS (.+)$',w,re.M)==['[82,82]']
assert re.findall(r'^R17_MOTION_TICKS (.+)$',c,re.M)==['[0,0]']
assert re.findall(r'^ACTIVE_CLOSE_RESULT checks=(\d+) failures=(\d+)$',w,re.M)==[('11','0')]
assert not re.search(r'^ACTIVE_CLOSE_(RESULT|FRAME)|^CLOSE_ASSERT_OK',c,re.M)
rs=[json.loads(s) for s in re.findall(r'^ACTIVE_CLOSE_FRAME (.+)$',w,re.M)]
assert [r['tag'] for r in rs]==['gate-east-mid','gate-east-closed','gate-south-mid','gate-south-closed']
assert len({r['native_sha256'] for r in rs})==4
for r in rs:
    assert r['tick']>r['e_tick']>1156 and r['draw_physics_delta'] in (0,1)
    if r['tag'].endswith('-mid'):
        assert 40.6<r['drawn_deg']<=r['queued_deg']<=45.0
    else:
        assert abs(r['queued_deg'])+abs(r['drawn_deg'])<1e-5
    assert r['target_open'] is False and r['camera_zoom_m']==13.0
    g=r['gate_mount_witness']
    assert g['phase']==r['tag']
    assert [g[k] for k in ('panels','posts','tris','stock_daylight_degrees','stock_shadow_enabled')]==[12,4,8384,[-48,-28,0],True]
    assert set(g['gates'])=={'gate-south','gate-east'}
    gate_id=r['tag'].rsplit('-',1)[0]
    assert abs(g['gates'][gate_id]['angle']*180/3.141592653589793-r['drawn_deg']) < 1e-8
    other='gate-east' if gate_id=='gate-south' else 'gate-south'
    assert abs(g['gates'][other]['angle']-(0 if gate_id=='gate-south' else 3.141592653589793*.5)) < 1e-5
    for gate in g['gates'].values():
        assert gate['technical_box_leaf_placeholder'] is False and len(gate['mounts'])==2
        for side,obj in zip(('left','right'),gate['mounts']):
            expected=cfg['leaves'][side]
            assert obj['owner_pivot']==('HingeLeft' if side=='left' else 'HingeRight')
            assert obj['source']==expected['resource'] and obj['material_triangles']==expected['material_triangles']
            assert obj['stock_box_hidden'] and obj['visual_global_basis_matches_pivot']
            assert obj['surface_count']==39 and obj['ordered_surfaces']==expected['ordered_surfaces']
            assert sum(row['triangles'] for row in obj['ordered_surfaces'])==3226
            assert all(abs(x-y)<1e-6 for us,vs in zip((obj['aabb_low'],obj['aabb_high']),expected['signed_aabb_m']) for x,y in zip(us,vs))
    img=p/('close-'+r['tag']+'.png'); b=img.read_bytes()
    assert b[:8]==b'\x89PNG\r\n\x1a\n' and b[16:24]==bytes.fromhex('00000500000002d0')
    got=[]
    for pix,n in [('rgba',4),('rgb24',3)]:
        a=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-protocol_whitelist','file,pipe','-i',str(img),'-pix_fmt',pix,'-f','rawvideo','-'])
        assert len(a)==1280*720*n
        got.append(hashlib.sha256(a).hexdigest())
    assert r['native_sha256'] in got
    r['packed_png_sha256']=hashlib.sha256(b).hexdigest()
assert {q.stem for q in p.glob('close-*.png')}=={'close-'+r['tag'] for r in rs}
assert rs[0]['e_tick']==rs[1]['e_tick']<rs[2]['e_tick']==rs[3]['e_tick']
assert [r['tick'] for r in rs]==sorted(set(r['tick'] for r in rs))
blocks=[json.loads(s) for s in re.findall(r'^CLOSE_TRAVERSAL_BLOCK (.+)$',w,re.M)]
assert [(b['gate'],b['attempt_side']) for b in blocks]==[('gate-east','inside'),('gate-south','outside')]
for b in blocks:
    assert b['active_closed'] and b['aborted'] and b['grounded'] and .30<=b['still_correct_side_distance_m']<=.54
assert (p/'disposable.before').read_bytes()==(p/'disposable.after').read_bytes()
assert json.loads((p/'writer-digest.json').read_text())['primary_sha256']=='832e3f09cb5718634de49d89e1e358b70cc5789464612b2ca48ec6dab43bc415'
print(json.dumps({'scope':'post-original writer candidate only; ordinary E and movement, stock camera; cold is an independent read and not closing',
 'active_close_checks':11,'inherited_route_checks':67,'both_close_from_real_open':True,'stock_pre_close_moving_ticks':[41,41],'actual_close_delta_ticks':[41,41],'full_writer_moving_ticks':[82,82],'cold_moving_ticks':[0,0],'blocked_probes':blocks,
 'original_v2_bytes_unmodified':True,'frames':rs,'visual_device_release_claim':False},indent=2))
