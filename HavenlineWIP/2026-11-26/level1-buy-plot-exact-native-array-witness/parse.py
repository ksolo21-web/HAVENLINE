from pathlib import Path
import hashlib,json,sys,subprocess
import numpy as np
from census import admit
root=Path(__file__).resolve().parent
parent=root.parent/'hvn-buy-plot-c1-stencil-native-preflight'
ref=parent/'graphics-evidence.mawe8Hs6/enabled'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(parent/'parse.py')=='0f9a853be1e649700405b2a662beb563827bca597f2d4f8421a25901d00c9849'
names=['funded-approach-moving','funded-near-moving']
expected=['cbcf2616fb77dcac0a835b6ff40035f5efaeef8b25fd45250552f730840c5a3e','6f2e7258515795f76018fa06bc59667511466f6d9fd25f74f840dc7cb53010e0']
assert [sha(ref/(i+'.pose.json')) for i in names]==expected
roles=json.loads((root/'ordered-roles.json').read_text())
assert len(roles)==10 and all(admit(roles,[[m['relative'],s['surface']] for m in json.loads((ref/(i+'.pose.json')).read_text())['surfaces'] for s in m['surfaces']]) for i in names)
if sys.argv[1:]==['--pins-only']:
 print(subprocess.check_output([sys.executable,str(parent/'parse.py'),'--pins-only'],text=True).strip())
 sys.exit(0)
assert len(sys.argv)==2
summary=json.loads(subprocess.check_output([sys.executable,str(parent/'parse.py'),sys.argv[1]],text=True))
p=Path(sys.argv[1])/'enabled'
out=[]; prev={}
expected_files=set()
for name,h in zip(names,expected):
 posef=p/(name+'.pose.json'); assert sha(posef)==h
 pose=json.loads(posef.read_text())
 arraysf=p/(name+'.arrays.json'); arrays=json.loads(arraysf.read_text())
 assert [arrays['tick'],arrays['physics']]==[pose['tick'],pose['physics']]
 assert arrays['frame_pose_digest']==h
 rows=[(m,s) for m in pose['surfaces'] for s in m['surfaces']]
 assert admit(roles,[[m['relative'],s['surface']] for m,s in rows]) and admit(roles,[[p['relative'],p['surface']] for p in arrays['parts']])
 for i,(r,(m,s)) in enumerate(zip(arrays['parts'],rows)):
  assert r['visible'] is True and r['relative']==m['relative'] and r['surface']==s['surface'] and r['mesh_world']==m['world'] and r['decl']==s
  counts=[s['vertices']*12,s['indices']*4,s['weights']*4,s['weights']*4]; payload=[]
  for j,(a,k) in enumerate(zip(r['arrays'],'pijw')):
   f=p/f'{name}.part{i:02d}.{k}.bin'; expected_files.add(f.name)
   assert f.name==a['file'] and f.is_file() and not f.is_symlink() and f.stat().st_size==a['bytes']==counts[j] and sha(f)==a['sha256']
   payload.append(np.fromfile(f,dtype=('<f4' if k in 'pw' else '<i4')))
  q,idx,b,w=payload
  assert np.isfinite(q).all() and len(idx)>0 and len(idx)%3==0 and idx.min()>=0 and idx.max()<s['vertices']
  if len(w):
   assert np.isfinite(w).all() and w.min()>=0 and b.min()>=0 and b.max()<66
   assert np.max(abs(w.reshape(s['vertices'],-1).sum(1)-1.))<.0002
  sig=[x['sha256'] for x in r['arrays']]
  if i in prev:assert sig==prev[i]
  prev[i]=sig
 for l in arrays['labels']:
  assert len(l['pixel_bounds_corners'])==8 and np.isfinite(np.asarray(l['pixel_bounds_corners'])).all()
 out.append({'tick':pose['tick'],'parts':len(roles),'receipt':sha(arraysf),'label_count':len(arrays['labels'])})
assert set(x.name for x in p.glob('*.bin'))==expected_files
print(json.dumps({'reference':summary,'arrays':out,'static_part_stream_hashes':prev,'bytes_admit_no_raster_approval':True},indent=2))
