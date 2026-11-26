from pathlib import Path
from collections import Counter
import hashlib,json
sha='31f3c98df40d5986c806f12f0af333929cd61d1fd0dfaa14dc9b1292e5da58d4'
raw=Path('imported-probe.jsonl').read_bytes()
assert hashlib.sha256(raw).hexdigest()==sha
rows=[json.loads(line) for line in raw.splitlines()]
assert [x['surface_count'] for x in rows]==[38,38,39,39]
assert [x['path'] for x in rows]==['res://old/GateLeaf.obj','res://old/GateLeaf_Right.obj','res://new/GateLeaf.obj','res://new/GateLeaf_Right.obj']
for k in ('gate-config.json','authenticated-candidate.json'):
    p=Path(k); cfg=json.loads(p.read_text())
    cfg['import_probe_sha256']=sha
    for side,n,pin in [('left',2,[[.007,.074,-.066],[1.178,1.336,.069]]),('right',3,[[-1.178,.074,-.066],[-.007,1.336,.069]])]:
        g=rows[n]
        v=cfg['leaves'][side]
        assert g['triangles_combined']==v['material_triangles']
        assert len(g['surfaces'])==39 and sum(r['triangles'] for r in g['surfaces'])==3226
        assert all(r['index']==n and r['primitive']==3 and r['class']=='StandardMaterial3D' and not r['albedo_map'] for n,r in enumerate(g['surfaces']))
        assert all(abs(x-y)<1e-6 for a,b in zip(g['aabb'],pin) for x,y in zip(a,b))
        v['signed_aabb_m']=pin
        v['ordered_surfaces']=g['surfaces']
    p.write_text(json.dumps(cfg,indent=2)+'\n')
