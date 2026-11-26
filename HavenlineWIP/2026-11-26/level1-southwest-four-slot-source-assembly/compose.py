from pathlib import Path
import hashlib,json,numpy as np
R=Path(__file__).resolve().parent;P=R.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={
 'hvn-l1-fence-33036-west1-hidden-cap-grade-v1':'6ee2751af33963320faba1a1b7db107ac5f5ee79d86b641409f6c0cd28390931',
 'hvn-l1-fence-33036-shared-perp-outward-seams-v1':'c31c1ccfaf2795be6743cf667dfab9411cd6b44b641582bf521d12fd66ef08f8',
 'hvn-l1-fence-33036-embossed-shared-perp-v1':'c71ccb5157f54aefaabb97411995d08ac649fa94c5b24a87dbe08f6e3b70c0b7'
}
for k,v in pins.items():assert sha(P/k/'SHA256SUMS')==v
f=P/'hvn-l1-fence-33036-west1-hidden-cap-grade-v1/grade.py'
a=f.read_text();c={'__file__':str(f)};exec(a[:a.index('ret={}')],c)
Q=dict(c['T']);B=c['B'];d=c['d'];C=c['V'];T=d['T'];A=d['A'];grp=d['new_assets'];stock=d['base'];mat=d['mat']; idx=d['post_idx']; logs=d['logs']
assert len(Q)>0
for g in ('SW0/post8','SW0/post8_icing','West2/post1','West2/post1_icing'):del Q[g]
Q.update(grp)
# Material-band ownership is preserved during replacement/subdivision.
for name,cutend in [('SW1',0),('West1',7)]:
 cut=logs&(idx==cutend);X=A[name][0];assert cut.sum()==360
 for k in sorted(set(mat)):
  selected=(mat==k)&~cut
  lf=stock[:,:,1].mean(1)<.50
  for lo in ['lower','upper','whole'] if k in ('front_rounded_rails','ivory_hemp_warm','ivory_hemp_cream') else ['whole']:
   if lo=='whole' and k in ('front_rounded_rails','ivory_hemp_warm','ivory_hemp_cream'):continue
   if name=='West1' and lo=='lower' and k in ('front_rounded_rails','ivory_hemp_warm'):
    Q[name+'/'+k+'/'+lo]=B['rail' if k=='front_rounded_rails' else 'warm']
   else:Q[name+'/'+k+'/'+lo]=X[selected&(lf if lo=='lower' else ~lf if lo=='upper' else np.ones_like(lf))]
bounds=[]
for k,T in sorted(Q.items()):
 if not any(w in k for w in ('rail','return','hemp','emboss','rear')):continue
 b=c['terrain'](T); bounds.append((k,b))
# All previous direct face bounds remain inspectable without owning root rig/gate side.
D=[]; known_sets=['SW0','West2','SW1','West1']
def union(parts):return np.concatenate(parts,axis=0)
# Exterior endpoints held where proof policy permits; known R17 as fixed visual control
# only. Not proposing that this stock boundary is correct. SW edge nearest gate handled
# as a separate held source, not relabeled tested.
stock_path=(P/'hvn-l1-fence-meshy-bold-material-native-preflight-v1/staged/HavenlineLevel1/previews/r17_fence/assets/fence_panel.obj')
S,SM=C['obj'](stock_path); G=C['panels'](S,False)
assert sha(stock_path)=='8b1890810e5734e5a2552098f762e7c72f8980b05be5d369ee3952521a97774f'
outer={}
for n,o in [('West1','West0')]:
 witness={}
 for k,v in sorted(Q.items()):
  if not k.startswith(n+'/'):continue
  hit=C['culled_intersections'](v,G[o][0],[k]*len(v),SM)
  if hit:witness.update(hit)
 outer[n+'/'+o]=witness
# Preserve approved authored atlas bytes but never describe an unbound normal as accepted.
ep=P/'hvn-l1-fence-33036-rooted-emboss-module-v1'
material={k:sha(ep/k) for k in ['RootedFence.mtl','RopeFiberBaseColor.png','RopeFiberNormal.png']}
protected=[]
for k,v in sorted(Q.items()):
 if any(q in k for q in ('_icing','soft_snow','/snow','shared_corner_cap')):
  g=c['terrain'](v)
  protected.append((k,'cap_min_indexed_ground_y_gap_mm',g['minimum_clearance_m']*1000))
 elif any(q in k for q in ('/post','/amber_logs','/timber','amber_front')) or k=='shared_corner':
  y=v[:,:,1]; yy=y.min()
  X=np.unique(np.round(v[y<=yy+.020],8).reshape(-1,3),axis=0)
  g=[float(p0[1]-C['height'](p0[[0,2]])) for p0 in X]
  protected.append((k,'indexed_lowest_root_vertex_probe_range_mm',[min(g)*1000,max(g)*1000]))
# Get verified boundary-pair audit: admitted shared structural seats not counted
# as hidden problems. CAD groups kept separated for independent review.
inner={}
for n,m in [('SW0','West2'),('SW0','SW1'),('West2','West1')]:
 X=sorted((k,v) for k,v in Q.items() if k.startswith(n+'/') and k not in ['SW1/timber','West1/timber','SW1/snow','West1/snow'])
 Y=sorted((k,v) for k,v in Q.items() if k.startswith(m+'/') and k not in ['SW1/timber','West1/timber','SW1/snow','West1/snow'])
 hit={}
 for a,v in X:
  for b,u in Y:
   hit.update(C['culled_intersections'](v,u,[a]*len(v),[b]*len(u)))
 inner[n+'/'+m]=hit
res={'scope':'offline full four SLOT visual geometry enumerated in exact signed world frame; not an admitted scene, shaders or importer','pins':pins,
 'source_group_count':len(Q),'total_faces':sum(len(x) for x in Q.values()),'triangles_per_group':{k:len(v) for k,v in sorted(Q.items())},
 'all_blades_band_terrain_except_intentionally_rooted_logs':dict(bounds),'remaining_exact_negative_terrain':{k:v for k,v in bounds if v['minimum_clearance_m']<0},
 'fixed_outer_visual_adjacency':'West0 still stock control; nearest gate side has not been admitted as same visual variant',
 'exact_internal_nonshared_low_and_upper_group_pair_contacts':inner,'root_and_cap_terrain_group_probes':protected,'unintended_external_boundary_contact':outer,'exact_bound_atlas_files_referenced_only':material,
 'material_binding_gate':'known held authored SW0 MTL has map_Kd only; exact native tangent/normal binding unavailable, no plastic replacement or fallback. Original donor wood UVs distinct from stroked fabric. Preserve rear originals. Need private content mapping and native exact import fixture after independent total source approval.'}
(R/'result.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
print('groups',len(Q),'tris',res['total_faces'],'negative_terrain',[(k,v['minimum_clearance_m']) for k,v in bounds if v['minimum_clearance_m']<0],'external',bool(any(outer.values())))

# Save complete local CAD source (review only, no owner media, UV or shaders). Never substitute for authored paint.
z=['# HOLD one four-slot full CAD source; no material, collider, or scene'];ind=1
for k,tri in sorted(Q.items()):
 z.append('o '+k.replace('/','_'))
 for f in tri:
  for q in f:z.append('v '+' '.join(f'{v:.9f}' for v in q))
  z.append(f'f {ind} {ind+1} {ind+2}');ind+=3
(R/'FourSlots_AllSource_HOLD.obj').write_text('\n'.join(z)+'\n')
