from pathlib import Path
import hashlib,json,numpy as np,itertools
from collections import Counter
R=Path(__file__).resolve().parent;P=R.parent
S=P/'hvn-l1-fence-33036-sw-south-warm-cap-v1'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(S/'SHA256SUMS')=='364ca201200c9963b904ac7967981a3273a029017e6f15639a73319e6ba34d36'
M=P/'hvn-l1-fence-33036-embossed-rooted-terminal-compat-v1'
assert sha(M/'SHA256SUMS')=='55ea5eff7576833fbbb68cc9ef4d17019951af8e0f53b1b5b35264d979000b71'
f=S/'warm.py'
D={'__file__':str(f)}; txt=f.read_text();exec(txt[:txt.index("D['R']=R")],D)
T=dict(D['O']);N=D['D'];coord=D['corner']; b=N['bound'];terrain=N['terrain']
r=P/'hvn-l1-fence-33036-rooted-emboss-module-v1/module.py'
E={'__file__':str(r)}
src=r.read_text()
# Exact mechanism, scoped emission uses true original materials; no imports or asset serving.
exec(src[:src.index('# Exact owner tolerance')],E)
orig=E['T']; E['X0']=-8.207
U=E['uvs']; aobb=E['aobb'];hold=E['hold'];frame=E['frame']
# Physically opposite old decorations superseded as one shared post. Rest same
# measured 14 rooted post/cap pairs in T. Preserve outer donor beyond these bands.
for k in [k for k in T if k.startswith('SW0/') and ('rail_' in k or 'distinct_return' in k)]:
 del T[k]
Y=E['yfull']; zc=9.8; xEnd=-6.408
# Keep the exact exterior contour until the concealed cap transitions.
s=np.linspace(-8.207,xEnd,81)
for j,band in enumerate([0,.692]):
 D1=[];D2=[]
 for x in s:
  u=(x-s[0])/(s[-1]-s[0]); old_u=(x+8.349)/1.941
  c=np.cos(8*np.pi*old_u); g=float(E['ground'](x))+band
  ny= .066885+.05655*np.sqrt(np.maximum(0,1-(Y/.064)**2))
  strength=np.clip((x-s[0])/.105,0,1)
  # Two exact round full front source bands; make cap depth margin
  # robust inside rooted shared timber by recessing through 22mm blend.
  z1=ny-.023*(1-strength)
  shade=np.maximum(np.maximum(0,1-((Y-.039*c)/.024)**2),.72*np.maximum(0,1-((Y+.039*c)/.024)**2))
  shape=.009*strength*shade*np.clip((.064-abs(Y))/.012,0,1)
  front=[frame(x,g+y,z+v) for y,z,v in zip(Y,z1,shape)]
  front.extend(frame(x,g+y,.066885-.05655*np.sqrt(max(0,1-(y/.064)**2))-.023*(1-strength)) for y in Y[-2:0:-1])
  D1.append(front)
  # Rear course end both moves inward by 25mm and shortens axially.
  ds=-.126+.025*(1-strength)+.0015*np.cos(u*16*np.pi)*strength
  rr=np.arange(8)*np.pi/4
  D2.append(np.array([frame(x,g+.010*np.cos(t),ds+.009*np.sin(t)) for t in rr]))
 for name,rings,uv in [('front',D1,True),('rear',D2,False)]:
  K=f'SW0/emboss_{name}_{j}';T[K],U[K]=aobb(np.array(rings),uv)
  assert hold(T[K])
# Recess each West rear-side segment into the central seated pin; unchanged cut
# opposite arm and upper profile outside 220mm local window. Signed deformation
# is shared by all identical vertices, so it cannot open indexed edges.
westchange={}
for k,t in list(T.items()):
 if not k.startswith('West2/') or 'distinct_return' not in k:continue
 u=np.clip((t[:,:,2]-9.58)/.14,0,1); w=np.clip((t[:,:,0]+8.245)/.035,0,1)
 a0=u*u*(3-2*u)*w*w*(3-2*w)
 q=t.copy();q[:,:,0]-=.014*a0
 T[k]=q
 westchange[k]={'exact_vertex_instances_changed':int(np.sum(a0>0)),'new_minimum_terrain_clearance_mm':float(terrain(q)['minimum_clearance_m']*1000),'shared_post_seat':b(q,T['shared_corner'],[k]*len(q),['shared_corner']*len(T['shared_corner']))}
# More robust left point control: directed faces plus positive enclosed margins.
sel={k:v for k,v in T.items() if k.startswith('SW0/emboss_')}
capcheck={}
for k,v in sel.items():
 cap=v[(abs(v[:,:,0]-s[0])<1e-9).all(1)].reshape(-1,3)
 rr=np.linalg.norm(cap[:,[0,2]]-coord[[0,2]],axis=1)
 inscribed=.142*np.cos(np.pi/20)
 capcheck[k]={'outer_radius_guard_mm':float((inscribed-rr.max())*1000),'body_base_grade_relative_range_y_m':(cap[:,1].min()-coord[1],cap[:,1].max()-coord[1]),'actual_terrain':terrain(v)}
# Exact selected bands vs all opposite-arm geometry and the shared crown.
hits={};ground={};seat={}
for k,t in sel.items():
 for h,v in T.items():
  if k==h:continue
  if h.startswith('SW0/') and 'icing' not in h:continue
  ws=b(t,v,[k]*len(t),[h]*len(v))
  if not ws:continue
  dest=seat if h=='shared_corner' else hits
  dest.update(ws)
# Verify all cross-arm component pairs, not only new rails. Rooted shared timber
# is the only intentionally shared body contact, and its crown is checked separately.
complete={}
for a0,ta in T.items():
 if not a0.startswith('SW0/'):continue
 for a1,tb in T.items():
  if not a1.startswith('West2/'):continue
  h=b(ta,tb,[a0]*len(ta),[a1]*len(tb))
  if h:complete.update(h)
# Actual still-protected nonlocal neighbors, not only empty geometry scene.
ctx=N['n']['V'];base=ctx['panels'](ctx['tr'],True)
neighbors={}
for u,k in [('SW1','SW0'),('West1','West2')]:
 c=base[u][0]; labels=ctx['labels'];act={}
 for g,t in T.items():
  if not g.startswith(k+'/'):continue
  act.update(b(t,c,[g]*len(t),labels))
 neighbors[u]={'pairs':sum(q['pairs'] for q in act.values()),'categories':act}
out=dict(status='HOLD: matched share-root geometry in source only; exact source intersections/tree caps and neighboring contacts must pass',cap_check=capcheck,
 all_new_embroidered_vs_other_arm_and_caps=hits,complete_lower_and_upper_arm_vs_other_arm=complete,actual_shared_seats=seat,real_fixed_neighbors=neighbors,
 total_composite_triangles=sum(len(t) for t in T.values()), retained_west_scope='unchanged prior signed West2, includes closed separate rear returns physically local, no claim bare stock artifact',
 width_data={k:[float((t[:,:,2]-9.8).min()),float((t[:,:,2]-9.8).max())] for k,t in sel.items()},
 west_matched_rear_buried_path_recess=westchange, material_scope='Source generation uses exact prior authored embossed base map alignment, original bark colors; no unproven tangent normal binding or copied paid maps.')
(R/'result.json').write_text(json.dumps(out,indent=2)+'\n')
rows=['# Held detached geometry, no materials or scene install'];i=1
for k,t in sel.items():
 rows.append('o '+k.replace('/','_'))
 for f in t:
  for p in f:rows.append('v '+' '.join(f'{z:.9f}' for z in p))
  rows.append(f'f {i} {i+1} {i+2}');i+=3
(R/'PerpendicularBeds_HOLD.obj').write_text('\n'.join(rows)+'\n')
print('left gaps', {k:round(v['outer_radius_guard_mm'],3) for k,v in capcheck.items()})
print('pairs',len(hits),{k:v['pairs'] for k,v in neighbors.items()},'mesh total',out['total_composite_triangles'])
