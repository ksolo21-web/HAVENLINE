from pathlib import Path
import hashlib,json,math,re,subprocess,sys
out=Path(sys.argv[1]); cfg=json.loads(Path(sys.argv[2]).read_text())
stat=json.loads((out/'r17-evidence.json').read_text())
assert stat['exact_stock_checkpoint_and_save_digest_match']
wanted=['gate-south','gate-east']
records={}
for role in ('write','cold'):
    log=(out/(role+'.log')).read_text()
    assert log.count('CLEARANCE_GATE_GRAFT mounted-four-clearance-authored')==1
    assert 'CLEARANCE_GATE_FALLBACK' not in log
    swing=[json.loads(l) for l in re.findall(r'^CLEARANCE_SWING_FRAME (.+)$',log,re.M)]
    assert [v['label'] for v in swing]==([f'{g}-{i}' for g in wanted for i in (225,450,675)] if role=='write' else [])
    for r in swing:
        label=r['label']
        assert label.startswith(r['gate']+'-')
        assert r['target_deg']<=r['queue_deg']<=r['draw_deg']<r['target_deg']+4.4
        assert r['physics_delta'] in (0,1) and (r['width'],r['height'])==(1280,720)
        path=out/f'swing-{label}.png'
        data=path.read_bytes()
        assert data[:8]==b'\x89PNG\r\n\x1a\n' and data[16:24]==bytes.fromhex('00000500000002d0')
        candidates=[]
        for pix_fmt,count in [('rgba',4),('rgb24',3)]:
            raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-protocol_whitelist','file,pipe','-i',str(path),'-pix_fmt',pix_fmt,'-f','rawvideo','-'])
            assert len(raw)==1280*720*count
            candidates.append(hashlib.sha256(raw).hexdigest())
        assert r['native_buffer_sha256'] in candidates
        records[label]={**r,'png_sha256':hashlib.sha256(data).hexdigest()}
assert sorted(p.stem for p in out.glob('swing-*.png'))==sorted('swing-'+label for label in records)
assert len({r['native_buffer_sha256'] for r in records.values()})==6
for name,frame in stat['samples'].items():
    for gate,data in frame['gates'].items():
        mounts=data['mounts']; assert len(mounts)==2
        for pos,side in enumerate(('left','right')):
            r=mounts[pos]; pinned=cfg['leaves'][side]
            assert r['owner_pivot']==('HingeLeft' if side=='left' else 'HingeRight')
            assert r['source']==pinned['resource'] and r['material_triangles']==pinned['material_triangles']
            assert r['stock_box_hidden'] and r['visual_global_basis_matches_pivot']
            assert r['surface_count']==39 and r['ordered_surfaces']==pinned['ordered_surfaces']
            assert sum(s['triangles'] for s in r['ordered_surfaces'])==3226
            assert all(abs(a-b)<1e-6 for x,y in zip((r['aabb_low'],r['aabb_high']),pinned['signed_aabb_m']) for a,b in zip(x,y))
print(json.dumps({'scope':'six inherited full frames and six intermediate natural-opening full frames; no angle/camera forcing or art/device acceptance',
 'control':'normalized original R17 posts/soil/shader; no pending fill/rope variant',
 'candidate':cfg,'swing_frames':records,'stock_gate_and_save_controls':stat['gates_transition_ticks'],
 'review':'closed paid and cold, both fully open route checkpoints, three intermediate angle windows per gate; invisible surfaces remain unverified'},indent=2,sort_keys=True))
