#!/usr/bin/env python3
"""Mechanical T01 evidence checks, separate from visual criticism and final release."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
root=Path(sys.argv[1] if len(sys.argv)>1 else 'task01-evidence')
repo=Path(__file__).resolve().parents[2]
hash_file=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})

tests=[]
for p in sorted(root.glob('test_*.log')):
    text=p.read_text();check('No runtime errors: '+p.stem,not any(x in text for x in ('SCRIPT ERROR','Parse Error','ERROR:','ObjectDB instances were leaked')))
    rows=[json.loads(l) for l in text.splitlines() if l.startswith('{')]
    check('Actual result exists: '+p.stem,bool(rows))
    if not rows:continue
    r=rows[-1];tests.extend(r['checks']);check('All assertions: '+p.stem,bool(r['checks']) and all(c['passed'] for c in r['checks']) and not r.get('failures'))
check('Eleven suites and 676 engine assertions',len(list(root.glob('test_*.log')))==11 and len(tests)==676)
geometry=json.loads((root/'geometry-audit.json').read_text())
check('Nine closed-edge/manifold/budget checks',geometry['passed'] and geometry['geometry_checks']==9)
before=json.loads((root/'protected-before.json').read_text())
check('All 30 earlier GLBs preserved',len(before)==30 and all(hash_file(repo/p)==h for p,h in before.items()))
report=json.loads((root/'gallery/capture.json').read_text())
check('Actual Mobile renderer',report['renderer']=='mobile')
check('Dense forest preserves all 586 instances',report['forest']['instances']==586)
check('Spatial batch count remains 96',report['forest']['spatial_batches']==96)
required=['gameplay-integration','forest-boundary-gameplay']
required += [f'v{i:02d}-{angle}' for i in (1,2,3) for angle in ('front','rear','side','three-quarter')]
required += [f'orbit-{i:02d}' for i in range(24)]+[f'integration-{i:02d}' for i in range(12)]
check('All 50 required tree/integration frames exist',all((root/'gallery'/f'{n}.png').is_file() for n in required))
clear=json.loads((root/'clearance/clearance.json').read_text())
check('Actual depletion hides resource and restores quantity',clear['depleted_tree_hidden'] and clear['original_units_restored'])
check('Clearance uses actual Mobile renderer',clear['renderer']=='mobile')
images={name:np.asarray(Image.open(root/'clearance'/f'clearance-{name}.png').convert('RGB')).astype(float) for name in ('baseline','disabled','enabled')}
x,y=clear['focus_screen'];x,y=int(x),int(y)
# Crop covers the actual player, whose focus coordinate is supplied by the renderer.
roi=(max(0,x-45),max(0,y-40),min(clear['image_size'][0],x+45),min(clear['image_size'][1],y+110))
a,b,c,d=roi
error_disabled=float(np.abs(images['disabled'][b:d,a:c]-images['baseline'][b:d,a:c]).mean())
error_enabled=float(np.abs(images['enabled'][b:d,a:c]-images['baseline'][b:d,a:c]).mean())
check('Fixture really obstructs player before clearance',error_disabled>25)
check('Player-region obstruction reduced at least 65 percent',error_enabled<error_disabled*.35)
check('Resource fading has six distinct actual frames',len({hash_file(root/'clearance'/f'resource-clearance-{i:02d}.png') for i in range(6)})==6)
# Render scale/dimensions are measured; fixed-step capture deliberately cannot certify FPS.
native=json.loads((root/'native4k/render-evidence.json').read_text())
check('Actual native dimensions meet both minimums',native['internal_render'][0]>=3840 and native['internal_render'][1]>=2160)
check('No resolution scaling',native['render_scale']==1)
check('Native image dimensions match renderer',list(Image.open(root/'native4k/native-scene.png').size)==native['internal_render'])
check('Native capture uses Mobile renderer',native['renderer']=='mobile')
for log in ('mobile-gallery.log','clearance.log','native4k.log'):
    text=(root/log).read_text();check('Clean capture log: '+log,not any(x in text for x in ('SCRIPT ERROR','Parse Error','ERROR:')))
result={'task':'T01','source':(root/'SOURCE.txt').read_text().strip(),'engine_checks':len(tests),'mechanical_checks':checks,'passed':all(c['passed'] for c in checks),'player_roi':roi,'obstruction_error_disabled':error_disabled,'obstruction_error_enabled':error_enabled,'obstruction_error_reduction_fraction':1-error_enabled/error_disabled,'native_render_record':native,'independent_critic_executed_by_this_tool':False,'task_approved':False,'physical_phone_tablet_4k60_verified':False}
(root/'mechanical-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'task':'T01','engine_checks':len(tests),'mechanical_checks':len(checks),'passed':result['passed'],'failed':[x['name'] for x in checks if not x['passed']]},indent=2))
sys.exit(0 if result['passed'] else 1)
