from pathlib import Path
import hashlib,json,numpy as np
R=Path(__file__).resolve().parent;P=R.parent
src=P/'hvn-l1-fence-33036-rooted-emboss-module-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src/'SHA256SUMS')=='cfe4449f40ff684aafe5565490d19de17684f9b2ebcd7e55180a291b66365c1d'
# Reconstruct exact complete source fixture without writes, data custodial receipt.
text=(src/'module.py').read_text(); N={'__file__':str(src/'module.py')}
exec(text[:text.index('# Atlas is physically')],N)
T=N['T']; C=N['ctx']; B=N['bound']
p=P/'hvn-l1-fence-meshy-bold-material-native-preflight-v1/staged/HavenlineLevel1/previews/r17_fence/assets/fence_panel.obj'
assert sha(p)=='8b1890810e5734e5a2552098f762e7c72f8980b05be5d369ee3952521a97774f'
stock,M=C['obj'](p)
A=C['panels'](stock,False)
holds={}
for name,key in [('left','West2'),('right','SW1')]:
 old=A[key][0];found={}
 for k,t in T.items():
  y=C['culled_intersections'](t,old,[k]*len(t),M)
  if y:found.update(y)
 holds[name]={'control_tile':key,'adjacent_slot_anchor_xz_m':A[key][2].tolist(),'neighbor_root_y_m':A[key][3],
  'actual_triangle_intersections_with_unmodified_neighbor':found,'nontermination_overlap_count':sum(v['pairs'] for key,v in found.items() if key.startswith(('body /','caps /')))}
# Exact extremal same source end vertices (signed world positions).
root=N['anchor']; width=.29484/2
L=float(root[1]-width);U=float(root[1]+width)
world={k:[t.min((0,1)).tolist(),t.max((0,1)).tolist()] for k,t in T.items()}
from scipy.spatial import ConvexHull
H=ConvexHull(np.unique(T['body'].reshape(-1,3),axis=0)).equations
for lab,s in [('left',-8.349),('right',-6.408)]:
 discs={}
 for k,F in T.items():
  if not k.startswith(('rail_','rear_')):continue
  t=F[(abs(F[:,:,0]-s)<=1e-8).all(1)]
  co=t.reshape(-1,3)
  assert len(t)>0
  signed=co@H[:,:3].T+H[:,3]
  discs[k]={'signed_x_m':s,'cap_triangles':len(t),
            'outside_even_global_timbers_convex_hull_vertex_number':int(np.sum(np.max(signed,axis=1)>1e-9)),
            'total_cap_triangle_vertex_instances':len(co),
            'outermost_hull_excess_mm':float(np.max(signed)*1000)}
 holds[lab]['existing_full_discs_even_global_convex_scoped']=discs
facts={'material_private_and_local_generated_only':{name:sha(src/name) for name in ('RopeFiberBaseColor.png','RopeFiberNormal.png','RootedFence.mtl','RootedEmbossedFence_SourceOnly.obj')},
 'admitted_root_visual_depth_interval_m':[L,U],'bindings':['emboss_atlas uses local base-color map_Kd','RootedFence.mtl contains no bound tangent normal slot; normal map proof cannot be inferred from file existence'],
 'actual_rear_lower_margin_to_root_visual_limit_mm':(world['rear_0'][0][2]-L)*1000, 'exact_preserved_crown_outside_root_limit_mm':(L-world['caps'][0][2])*1000,'immutable_source_post_crown_groups':world,'neighbor_hold':holds,'unfixed':'Neither preserved post/crown neighbor overlap can be repaired by shifting/shortening only two front and two rear discs. Need scope to replace terminal timbers at both local mates; do not move any approved world anchor.'}
(R/'result.json').write_text(json.dumps(facts,indent=2,sort_keys=True)+'\n')
print({k:(v['nontermination_overlap_count'],len(v['actual_triangle_intersections_with_unmodified_neighbor'])) for k,v in holds.items()})
