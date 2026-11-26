"""Read-only independent runtime census/position proof for all sixteen inherited camera captures."""
from hashlib import sha256
from itertools import chain
from pathlib import Path
import json, math, re, sys

def load(p):return json.loads(p.read_text())

out,here=map(Path,sys.argv[1:])
cfg=load(here/'staged/HavenlineLevel1/previews/clearance_gate/owner_runtime_census.json')
fg=load(out/'frame-evidence.json')
gate=load(out/'gate-evidence.json')
close=load(out/'active-close-evidence.json')
route=load(out/'functional.json')
assert route['phases']['write']['checks']==57 and route['phases']['cold']['checks']==10
assert route['controlled_checkpoint']['primary_sha256']=='832e3f09cb5718634de49d89e1e358b70cc5789464612b2ca48ec6dab43bc415'
assert close['active_close_checks']==11 and close['original_v2_bytes_unmodified']
frames={}
for d,prefix,png_field in ((fg['frames'],'','png_sha256'),(gate['swing_frames'],'swing-','png_sha256'),
                           ({r['tag']:r for r in close['frames']},'close-','packed_png_sha256')):
 for tag,r in d.items():
  assert tag not in frames
  image=out/(prefix+tag+'.png')
  assert sha256(image.read_bytes()).hexdigest()==r[png_field]
  frames[tag]=image.name
assert len(frames)==16 and set(frames.values())=={p.name for p in out.glob('*.png')}
seen={}
settled={}
def close_value(a,b,atol=1e-6):
 assert math.isclose(float(a),float(b),abs_tol=atol,rel_tol=0.0)
def near_vec(a,b,n):
 assert len(a)==len(b)==n
 for u,v in zip(a,b):close_value(u,v,1e-5)
def mesh(src,f):
 want=cfg['meshes'][f]
 assert src['source']=='res://previews/clearance_gate/owner_assets/'+f
 assert src['render_triangles']==want['triangles'] and src['surface_count']==want['exact_ordered_surface_count']
 near_vec(src['aabb_low'],want['aabb'][0],3)
 near_vec(src['aabb_high'],want['aabb'][1],3)
 assert len(src['ordered_surfaces'])==len(want['surfaces'])
 for a,b in zip(src['ordered_surfaces'],want['surfaces']):
  assert a['material']==b['label'] and a['class']==b['material_class'] and a['albedo_map'] is False
  assert all(a[x]==b[x] for x in ('index','primitive','triangles','indices','vertices'))
  near_vec(a['albedo_rgba'],b['albedo_rgba'],4)
for role in ('write','cold'):
 log=(out/(role+'.log')).read_text()
 assert log.count('OWNER33035_GATE_GRAFT mounted-four-leaves-four-posts')==1
 assert all(x not in log for x in ('OWNER33035_GATE_REJECT','CLEARANCE_GATE_FALLBACK'))
 for value in re.findall(r'^OWNER33035_DRAW_BOUND (.+)$',log,re.M):
  data=json.loads(value)
  phase=data['phase']
  assert [data[k] for k in ('panels','posts','tris','stock_daylight_degrees','stock_shadow_enabled')]==[12,4,28792,[-48,-28,0],True]
  assert set(data['gates'])=={'gate-south','gate-east'}
  reports={}
  for i,g in enumerate(('gate-south','gate-east')):
   row=data['gates'][g]
   assert row['technical_box_leaf_placeholder'] is False and len(row['mounts'])==len(row['stationary_owner_posts'])==2
   ids=[]
   axis=[1.,0.,0.] if i==0 else [0.,0.,-1.]
   front=[0.,0.,1.] if i==0 else [1.,0.,0.]
   for j,(leaf,post) in enumerate(zip(row['mounts'],row['stationary_owner_posts'])):
    side='left' if j==0 else 'right'
    sign=-1 if j==0 else 1
    suffix='_Right' if j else ''
    mesh(leaf,'GateLeaf'+suffix+'.obj')
    mesh(post,'ThresholdPost'+suffix+'.obj')
    assert leaf['owner_pivot']==('HingeLeft' if j==0 else 'HingeRight')
    assert leaf['stock_box_hidden'] and leaf['visual_global_basis_matches_pivot']
    assert leaf['leaf_name']=='DetachedArtLeafStudy'
    assert post['name']==f"OwnerThreshold_{i}"+('_L' if j==0 else '_R') and post['fixed_shell_owner']
    near_vec(post['basis_z'],front,3)
    pos=[x+sign*.19616*unit for x,unit in zip(leaf['pivot_world_origin'],axis)]
    pos[1]+=cfg['post_minus_hinge_y_m'][g[5:]+'-'+side]
    near_vec(post['world_origin'],pos,3)
    near_vec(post['expected_world_origin'],pos,3)
    ids.append({'post':post['name'],'post_resource':post['source'],'post_world_origin':post['world_origin'],
      'leaf':leaf['leaf_name'],'leaf_resource':leaf['source'],'leaf_pivot':leaf['owner_pivot'],'hinge_world_origin':leaf['pivot_world_origin'],
      'post_outward_basis_z':post['basis_z'],'ordered_import_surface_counts':[leaf['surface_count'],post['surface_count']]})
   reports[g]={'angle':row['angle'],'parts':ids}
  if phase.endswith('-settled'):
   assert phase not in settled and role=='write'
   settled[phase]=reports
  else:
   assert phase in frames and phase not in seen and ((phase=='cold-v2-no-replay')==(role=='cold'))
   seen[phase]={"image":frames[phase],"gates":reports}
assert set(seen)==set(frames)
assert set(settled)=={'gate-east-settled','gate-south-settled'}
# Verify the independently observed post and hinge positions did not rotate with either gate.
for g in ('gate-south','gate-east'):
 basis=seen['fresh-spawn']['gates'][g]['parts']
 for observed in seen.values():
  next_parts=observed['gates'][g]['parts']
  for a,b in zip(next_parts,basis):
   near_vec(a['post_world_origin'],b['post_world_origin'],3)
   near_vec(a['hinge_world_origin'],b['hinge_world_origin'],3)
print(json.dumps({'scope':'exact owner leaf/post native custody at 16 stock-camera draws; old fence remains comparison without approved seams',
 'gameplay_checks':78,'frame_count':16,'renders':seen,'ordinary_closing_settled_nonframe_witness':settled,
 'unchanged_save_sha256':route['controlled_checkpoint']['primary_sha256'],'art_device_enclosure_release_approval':False},sort_keys=True,indent=2))
