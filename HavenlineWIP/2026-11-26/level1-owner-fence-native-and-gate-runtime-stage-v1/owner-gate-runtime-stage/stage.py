"""Stage only the detached owner gate assembly. No Godot, replay, or baseline writes."""
import json
import re
import shutil
import subprocess
from hashlib import sha256,md5
from pathlib import Path
root=Path(__file__).resolve().parent
src=root.parent
def read(p):return p.read_text()
def hash(p):return sha256(p.read_bytes()).hexdigest()
def pin(p,exp):assert hash(p)==exp,p
def verify(capsule,seal):
 pin(capsule/'SHA256SUMS',seal)
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=capsule,check=True)
def dump(path,data):path.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
def replace(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)
base=src/'hvn-l1-clearance-active-close-timeout-v3'
asset=src/'hvn-l1-owner-gate-v2-import-census-fix-v1'
verify(base,'c4ee66fcebf97bc1836b5c71e857dac8ea9faf6642ba0943b3902e98b73bc2b8')
verify(asset,'6676c4e4b37a24fda005659a283f2e85a7a8b09c38e5a1d2433a7a14a6883f29')
old=base/'staged/HavenlineLevel1'
subprocess.run(['sha256sum','-c','--status','../draw-source.sha256'],cwd=old,check=True)
old_report=json.loads(read(base/'graphics-evidence.t0YOq6Hx/active-close-evidence.json'))
assert old_report['active_close_checks']==11 and old_report['inherited_route_checks']==67
assert old_report['original_v2_bytes_unmodified'] and len(old_report['frames'])==4
proof=src/'hvn-l1-gate-art-admission-protocol/result.json'
census=asset/'evidence.tH5YO3DS/strict-census.json'
pin(census,'97499876091ce4797321af920e3a1c4c8226ab41ff6e27ca552b33601671ef32')
strict=json.loads(read(census))
assert strict['source_world_space_triangle_geometry_matches'] and strict['native_import_read_only']
prior=dict(post_minus_hinge_y_m={n:v['post_minus_hinge_height_m'] for n,v in json.loads(read(proof))['results'].items()},meshes=strict['meshes'])
assert set(prior['post_minus_hinge_y_m'])=={'south-left','south-right','east-left','east-right'}
project=root/'staged/HavenlineLevel1'
assert not project.parent.exists()
shutil.copytree(old,project)
p=project/'previews/clearance_gate'
a=p/'owner_assets';a.mkdir()
artdir='res://previews/clearance_gate/owner_assets/'
for f in sorted(prior['meshes']):
 row=prior['meshes'][f]
 pin(asset/'input/donors'/f,row['digest'])
 shutil.copyfile(asset/'input/donors'/f,a/f)
 # Change resource paths only, preserving the precise native-probe importer parameters.
 imp=read(asset/'input/donors'/(f+'.import'))
 oldpath='res://donors/'+f
 newpath=artdir+f
 sidecar=imp.replace(oldpath,newpath).replace(md5(oldpath.encode()).hexdigest(),md5(newpath.encode()).hexdigest())
 assert sidecar.count('force_disable_mesh_compression=true')==1
 (a/(f+'.import')).write_text(sidecar)
shutil.copyfile(asset/'input/donors/owner33035.mtl',a/'owner33035.mtl')
dump(p/'owner_runtime_census.json',prior)
shutil.copyfile(root/'owner_mesh.gd',p/'owner_mesh.gd')
g=p/'clearance_gate_view.gd'
s=read(g); pivot=s.index('const REPAIRED_LEFT:')
tail=s.index('func _terrain_custody()')
g.write_text(s[:pivot]+read(root/'graft.inc')+'\n'+s[tail:])

d=project/'tests/hvn_l1_combined_draw.gd'
s=read(d)
s=replace(s,'const WRITER :=','const Owner = preload("res://previews/clearance_gate/owner_mesh.gd")\nconst WRITER :=')
a0=s.index('\tvar totals := [7680,704]');a1=s.index('\tfor i in range(6):',a0)
s=s[:a0]+replace(s[a0:a1],'var totals := [7680,704]','var totals := [7680]').replace('["R17WallPanels","R17ThresholdPosts"]','["R17WallPanels"]').replace('for n in range(2):','for n in range(1):').replace('[12,4][n]','[12][n]').replace('[2,3][n]','[2][n]')+s[a1:]
s=replace(s,'\t\tvar mount_witness := []','\t\tvar mount_witness := []\n\t\tvar post_witness := []')
s=replace(s,'\t\t\tmount_witness.append(mount)', '''			mount_witness.append(mount)
			var post := admitted_post(gate,hinge,i,side<0)
			if post.is_empty():
				return {}
			post_witness.append(post)'''.replace(' 	','	'))
s=replace(s,'"mounts":mount_witness','"mounts":mount_witness,"stationary_owner_posts":post_witness')
old_return='\treturn {"phase":phase,"stock_daylight_degrees":[-48,-28,0],"stock_shadow_enabled":true,"gates":result,"panels":12,"posts":4,"tris":8384}'
s=replace(s,old_return,'''	var witness := {"phase":phase,"stock_daylight_degrees":[-48,-28,0],"stock_shadow_enabled":true,"gates":result,"panels":12,"posts":4,"tris":28792}
	print("OWNER33035_DRAW_BOUND ",JSON.stringify(witness))
	return witness''')
a0=s.index('\tvar source := art.mesh as ArrayMesh',s.index('func admitted_leaf'))
a1=s.index('func schedule_swing()',a0)
s=s[:a0]+'''	if art.material_override!=null or art.material_overlay!=null:
		return {}
	var file := Owner.file_for(side<0,false)
	var report := Owner.receipt(art.mesh,file)
	if report.is_empty() or art.mesh!=load(Owner.DIR+file):
		return {}
	report.merge({"owner_pivot":String(pivot.name),"stock_box_hidden":true,
		"visual_global_basis_matches_pivot":art.global_basis.is_equal_approx(pivot.global_basis),
		"leaf_name":String(art.name),"pivot_world_origin":[pivot.global_position.x,pivot.global_position.y,pivot.global_position.z]})
	return report

'''+read(root/'observer_posts.inc')+'\n'+s[a1:]
d.write_text(s)
config={'leaves':{},'source_import_census_sha256':hash(census),'script':'res://previews/clearance_gate/clearance_gate_view.gd',
        'mesh_node':'DetachedArtLeafStudy','scope':'owner geometry draft, old wall panel comparison, no seam or art approval'}
oldcfg=json.loads(read(old/'tests/hvn_l1_gate_config.json'))
config['mesh_node']=oldcfg['mesh_node']
for side,f in [('left','GateLeaf.obj'),('right','GateLeaf_Right.obj')]:
 row=prior['meshes'][f]
 ordered=[{'index':r['index'],'material':r['label'],'class':r['material_class'],'primitive':r['primitive'],'triangles':r['triangles'],
          'indices':r['indices'],'vertices':r['vertices'],'albedo_map':False,'albedo_rgba':r['albedo_rgba']} for r in row['surfaces']]
 from collections import Counter
 counts=Counter()
 for r in ordered: counts[r['material']]+=r['triangles']
 config['leaves'][side]=dict(resource=artdir+f,ordered_surfaces=ordered,material_triangles=dict(counts),signed_aabb_m=row['aabb'],
                             triangles=row['triangles'],surface_count=row['exact_ordered_surface_count'])
dump(project/'tests/hvn_l1_gate_config.json',config)
dump(root/'authenticated-candidate.json',config)
for f in ('stock-result.json','summarize.py','validate_draw.py'):
 shutil.copyfile(base/f,root/f)
for f in ('validate_r17.py','validate_gate.py','validate_close.py'):
 script=read(base/f).replace('8384','28792')
 if f=='validate_gate.py':
  script=script.replace('CLEARANCE_GATE_GRAFT mounted-four-clearance-authored','OWNER33035_GATE_GRAFT mounted-four-leaves-four-posts')
  script=script.replace("'CLEARANCE_GATE_FALLBACK' not in log","'OWNER33035_GATE_REJECT' not in log and 'CLEARANCE_GATE_FALLBACK' not in log")
  script=script.replace("r['surface_count']==39","r['surface_count']==pinned['surface_count']").replace("==3226","==pinned['triangles']")
  script=script.replace('normalized original R17 posts/soil/shader; no pending fill/rope variant','owner posts + both moving owner leaves; old R17 walls deliberately retained; seams not approved')
 if f=='validate_close.py':
  script=script.replace("obj['surface_count']==39","obj['surface_count']==expected['surface_count']").replace('==3226',"==expected['triangles']")
 (root/f).write_text(script)
r=read(base/'tty_capture.sh')
r=r.replace('/tmp/hvn-l1-gate-active-close.','/tmp/hvn-l1-owner-gate-active-close.')
r=replace(r,'|| deadline=360','|| deadline=480')
r=r.replace('explicit clearance-authored gate visual-only scene','explicit owner leaf/post visual-only scene with old R17 wall comparison')
target='(cd "$w/project"; sha256sum -c --status "$here/staged/draw-source.sha256")'
assert r.count(target)==2
first=r.index(target)+len(target)
# Godot may regenerate sidecar resource mapping/UID; only those exact four renderer-copy
# outputs are not byte-compared after import. Params are independently checked.
r=r[:first]+r[first:].replace(target,r'''(cd "$w/project"; grep -vE '/owner_assets/(GateLeaf(_Right)?|ThresholdPost(_Right)?)\.obj\.import$' "$here/staged/draw-source.sha256" | sha256sum -c --status)''',1)
key='exec_phase import --headless --editor --import --quit'
r=replace(r,key,key+'''
for name in GateLeaf GateLeaf_Right ThresholdPost ThresholdPost_Right; do
  p="$w/project/previews/clearance_gate/owner_assets/$name.obj.import"
  grep -Fxq 'force_disable_mesh_compression=true' "$p"
  grep -Fxq 'scale_mesh=Vector3(1, 1, 1)' "$p"
  grep -Fxq 'offset_mesh=Vector3(0, 0, 0)' "$p"
done''')
r=replace(r,'printf \'%s\\n\' "$out"','python3 "$here/validate_owner.py" "$out" "$here" > "$out/owner-all-four-each-16-frames.json"\n'+ 'printf \'%s\\n\' "$out"')
(root/'tty_capture.sh').write_text(r)
def scan(p):return {x.relative_to(p).as_posix():hash(x) for x in p.rglob('*') if x.is_file()}
before,after=scan(old),scan(project)
changed=sorted(k for k,v in before.items() if after[k]!=v)
assert changed==['previews/clearance_gate/clearance_gate_view.gd','tests/hvn_l1_combined_draw.gd','tests/hvn_l1_gate_config.json']
new=sorted(after.keys()-before.keys())
assert len(new)==11 and all(n.startswith('previews/clearance_gate/owner_') for n in new)
(project.parent/'draw-source.sha256').write_text(''.join(f'{h}  ./{n}\n' for n,h in sorted(after.items())))
dump(root/'staged-delta.json',{'old_source_count':len(before),'new_source_count':len(after),'byte_exact_inherited':len(before)-len(changed),
 'modified':{n:after[n] for n in changed},'added':{n:after[n] for n in new},'prior_active_close_evidence_sha256':hash(base/'graphics-evidence.t0YOq6Hx/active-close-evidence.json'),
 'exact_strict_import_receipt_sha256':hash(census),'new_engine_run':False})
