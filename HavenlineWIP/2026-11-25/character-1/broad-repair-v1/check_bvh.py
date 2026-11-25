from pathlib import Path
import json, numpy as np
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parent
D=np.load(p/'pose-inputs.npz'); P=np.load(p/'diagnostic-corrected-arrays.npz'); rest=D['rest']
_,weld=np.unique(np.rint(rest/1e-6).astype('int64'),axis=0,return_inverse=True)
changed=P['edited']; out=[]
def cross(x, a,b):
 tree=lambda tri:BVHTree.FromPolygons(x.tolist(),tri.tolist(),all_triangles=True,epsilon=0.)
 return len(tree(a).overlap(tree(b)))
def self_nonadj(x,tri):
 t=BVHTree.FromPolygons(x.tolist(),tri.tolist(),all_triangles=True,epsilon=0.)
 pairs=t.overlap(t); ids=weld[tri]
 return {(a,b) for a,b in pairs if a<b and not np.isin(ids[a],ids[b]).any()}
def sdist(a,b):return float(np.linalg.norm(a-b,axis=-1).max())
for i,(raw,edit) in enumerate(zip(D['xyz'],P['xyz'])):
 assert np.array_equal(raw[~changed],edit[~changed])
 side={}
 for s,k in [('L','lboot'),('R','rboot')]:
  T=D[k]; boot=D['boot'+s]; site=D['phase'+s]; fixed=boot[rest[boot,2]<rest[boot,2].min()+.030]
  assert np.array_equal(raw[fixed],edit[fixed]) and np.array_equal(raw[site],edit[site])
  orig=self_nonadj(raw,T); test=self_nonadj(edit,T)
  side[s]={'outer_lower_mask_fixed_verts':len(fixed),'phase_pin_max_delta_mm':sdist(raw[site],edit[site])*1e3,
   'boot_lowest_raw_vs_corrected_mm':[float(v[boot,2].min()*1e3) for v in (raw,edit)],
   'within_boot_nonadj_before':len(orig),'within_boot_nonadj_after':len(test),'new_within_boot_nonadj':len(test-orig),
   'first_new_face_vertex_tris':[T[j].tolist() for j in sorted(test-orig)[0]] if test-orig else None}
 out.append({'key_s':[0,.075,.15][i],'sides':side,'boot_and_coat_before_after':[[cross(v,D[a],D[b]) for a,b in [('lboot','rboot'),('lboot','coat'),('rboot','coat')]] for v in (raw,edit)]})
(p/'bvh-result.json').write_text(json.dumps(out,indent=2)+'\n')
