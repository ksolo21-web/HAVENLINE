from pathlib import Path
import json, hashlib, itertools
import numpy as np
root=Path(__file__).resolve().parent
full=root.parent/'hvn-l1-fence-33036-full-perimeter-repair-bound-v1'
assert hashlib.sha256((full/'SHA256SUMS').read_bytes()).hexdigest()=='45c8b73f0463f8158b1985b58ae0fa8f852799c0d57911de41f2e9e0e8a8c845'
ns={'__file__':str(full/'verify.py')}
exec((full/'verify.py').read_text().split('seams=')[0],ns)
sha=ns['sha']; p=root.parent/'hvn-l1-fence-33036-neutral-corner-socket-v1'
assert sha(p/'SHA256SUMS')=='7569dfc50f343e4611b5752a635df872121863f00403d98654fd918a66d4c8ea'
T=ns['tr']; labels=np.array(ns['labels']); obj=ns['obj']; height=ns['height']; intersect=ns['culled_intersections']
seats=ns['panels'](T,True)
assert seats['SW0'][1]==seats['West2'][1]==1
world=np.array([-8.25,9.8])
tile_y=min(height(world+np.array([dx,dz])) for dx in np.linspace(-.14484,.14484,17) for dz in np.linspace(-.14484,.14484,17) if np.hypot(dx,dz)<=.14484)
# Author neutral shared log already starts at -40mm; its transform is based on actual source terrain, not a dummy flat plane.
corner_origin=np.array([world[0],tile_y,world[1]])
corner_path=p/'candidate/Corner.obj'
with corner_path.open() as f:
 v=[]; groups={}; group=None
 for row in f:
  s=row.split()
  if not s: continue
  if s[0]=='o': group=s[1]; groups[group]=[]
  if s[0]=='v': v.append(list(map(float,s[1:])))
  if s[0]=='f':groups[group].append([int(z.split('/')[0])-1 for z in s[1:]])
v=np.asarray(v)
groups={k:v[q]+corner_origin for k,q in groups.items()}
centers=np.array([i['log_x_center_m'] for i in json.loads((root.parent/'hvn-l1-fence-33036-bold-wrap-v3/build-result.json').read_text())['modules']])
post=np.isin(labels,['amber_logs','meshy_bold_amber_front','soft_snow'])
post_idx=np.argmin(abs(T[:,:,0].mean(1)[:,None]-centers),axis=1)
def bbox(t):return [t.min((0,1)).tolist(),t.max((0,1)).tolist()]
result={}
for name,sign,typ in [('SW0',1,'south'),('West2',-1,'west')]:
 S,_,at,Y=seats[name]
 near=0 if sign==1 else 7
 to_keep=post&(post_idx!=near)
 neighbor=1 if sign==1 else 6
 next_post=post&(post_idx==neighbor)
 assert (post&(post_idx==near)).sum()==360
 row={}
 for g in ('shared_corner','shared_corner_cap',typ+'_middle',typ+'_middle_cap',typ+'_outer',typ+'_outer_cap'):
  other=groups[g]
  bound=intersect(other,S[to_keep],[g]*len(other),labels[to_keep])
  if bound:row[g]=bound
 rail_global=[]
 for band,cy in enumerate([.191,.883]):
  R=S[(labels=='front_rounded_rails')&(abs(T[:,:,1].mean(1)-cy)<.15)]
  rail_global.append({'donor_global_rail_height_m':bbox(R), 'neutral_same_band_height_m':bbox(groups[typ+'_rail_'+str(band)])})
 result[name]={'protected_anchor_xz_m':at.tolist(),'donor_seat_y_m':Y,
 'removed_terminal_post_and_cap_faces':int((post&(post_idx==near)).sum()),
 'other_7_posts_and_caps_retained_exact_in_screen':int(to_keep.sum()),
 'first_remaining_authored_post_bbox':bbox(S[next_post]),
 'fixture_wood_or_cap_collisions_vs_only_protected_remaining_posts':row, 'strict_pairs_from_adding_neutral_wood_cap_vs_retained_posts':sum(item['pairs'] for m in row.values() for item in m.values()),
 'rail_height_bands':rail_global}
print(json.dumps(dict(status='HOLD: no actual SW mate under exact retain-only duplicate terminal cut',chosen_corner_xz_m=world.tolist(),candidate_math_root_y_m=tile_y,
 each_donor_triangles=11904,original_two_donor_triangles=23808,neutral_fixture_triangles=int(sum(len(g) for g in groups.values())),
 retained_after_two_post_cap_removals_count=23808-720, shared_wood_and_cap_only_triangles=len(groups['shared_corner'])+len(groups['shared_corner_cap']), naive_sum_if_adding_old_fixture_after_removals=23808-720+sum(len(g) for g in groups.values()),
 denial='existing neutral arms cannot be appended: wood/cap collides even after the exact two terminal posts are removed; current donor end rail in lower nominal Y band does not align with unchanged neutral socket. Need a shared-post-only junction and two independently re-authored face-continuous short end rails/rope terminations with genuine seated contacts, not stretching or deleting retained neighbor posts.',
 runs=result),indent=2))
