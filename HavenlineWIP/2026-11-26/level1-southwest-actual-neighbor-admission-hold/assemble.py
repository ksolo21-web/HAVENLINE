from pathlib import Path
import json,hashlib,numpy as np
from collections import defaultdict
r=Path(__file__).resolve().parent;P=r.parent
passd=P/'hvn-l1-fence-33036-sw-south-warm-cap-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(passd/'SHA256SUMS')=='364ca201200c9963b904ac7967981a3273a029017e6f15639a73319e6ba34d36'
src=(passd/'warm.py').read_text(); d={'__file__':str(passd/'warm.py')}
exec(src[:src.index("D['R']=R")],d)
O=d['O']; origin=d['corner']; ctx=d['n']['V']; bound=ctx['culled_intersections']
assert sum(len(t) for t in O.values())==25968
assert len(O)==42
root_a=P/'hvn-l1-fence-meshy-bold-material-native-preflight-v1'
assert sha(root_a/'SHA256SUMS')=='25be22d2dc288ff5e8a012846a5d4dd3f6b146e82952ded65a457ce35adf2d4b'
stage=root_a/'staged/HavenlineLevel1'
oldwall=stage/'previews/r17_fence/assets/fence_panel.obj'
assert sha(oldwall)=='8b1890810e5734e5a2552098f762e7c72f8980b05be5d369ee3952521a97774f'
stock,stockmat=ctx['obj'](oldwall)
official,offmat=ctx['tr'],ctx['labels']
neighbors={}
for geometries,labels,art in [(stock,stockmat,'current_control'),(official,offmat,'owner_if_repeated')]:
 A=ctx['panels'](geometries,art!='current_control')
 for n,run in [('SW1','SW0'),('West1','West2')]:
  Y=A[n][0]; hits={}
  for key,T in sorted(O.items()):
   if not key.startswith(run+'/'):continue
   hit=bound(T,Y,[key]*len(T),labels)
   if hit:hits.update(hit)
  neighbors[art+'_'+n]={'pair_total':sum(x['pairs'] for x in hits.values()),'all_strict_pair_categories':hits}
print(json.dumps(neighbors,indent=2,sort_keys=True))
(r/'neighbor-evidence.json').write_text(json.dumps(neighbors,indent=2,sort_keys=True)+'\n')
