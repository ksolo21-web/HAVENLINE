"""Validate the documented whole-rig audit coverage using the actual exported GLB."""
from pathlib import Path
import json,sys,struct,hashlib
ledger=Path(sys.argv[1]); a=json.loads(ledger.read_text()); p=Path(a['candidate']['path']); p=p if p.is_file() else (ledger.parent/a['candidate']['relative_path']).resolve(); b=p.read_bytes()
size=struct.unpack_from('<I',b,12)[0]; g=json.loads(b[20:20+size]); test=[]; missing=[]
def require(ok,label):
 test.append((bool(ok),label))
 if not ok: missing.append(label)
require(hashlib.sha256(b).hexdigest()==a['candidate']['sha256'],'Exact candidate SHA-256')
actual_joints={g['nodes'][idx]['name'] for skin in g['skins'] for idx in skin['joints']}
listed_joints={j for part in a['parts'] for j in part['joints']};require(actual_joints==listed_joints,'Every skin joint mapped')
clips={c['name'] for c in g['animations']};require(clips==set(a['clips']),'Every supplied clip identified')
rows={(r['part'],r['clip'],r['check']):r for r in a['checks']}
required={(p['id'],c,k) for p in a['parts'] for c in clips for k in ('transforms','deformation','clearance','temporal')}
required|={('*',c,k) for c in clips for k in ('loop_continuity','contact','motion_intent')}
required|={('*','*',k) for k in ('preservation','skeleton_integrity','animation_integrity','export_integrity')}
require(required<=rows.keys(),'Every required part, clip and check is present')
require(len(a['checks'])==len(rows),'No duplicate rows')
for key,r in rows.items():
 require(r['status']=='PASS','Pass '+str(key))
 require(bool(r['evidence']) and all((ledger.parent/s).is_file() for s in r['evidence']),'Evidence '+str(key))
scores=[r['score'] for r in a.get('reviewers',[])]
require(bool(scores) and a['score']==min(scores) and all(9<=s<=10 for s in scores),'Each independent score >=9 and reported score is the lowest')
require(9<=a['score']<=10,'Independent score >=9 and <=10')
print('Documented-format verifier; local implementation. Official skill script was unavailable.')
print('GLB:',p);print('SHA-256:',a['candidate']['sha256']);print('Joints:',len(actual_joints),'clips:',len(clips),'required rows:',len(required),'checked rows:',len(rows))
for msg in missing:print('FAIL:',msg)
print('Result:','FAIL' if missing else 'PASS','| score',a['score']);sys.exit(int(bool(missing)))
