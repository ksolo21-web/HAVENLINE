from pathlib import Path
from hashlib import sha256
import shutil, json, sys
here=Path(__file__).resolve().parent
base=here.parent/'hvn-l1-owner-gate-33035-material-native-preflight-v1'
design=here.parent/'hvn-l1-owner-gate-33035-snow-hardware-v3'
probe=here/'import_probe'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def seal(dir,expected):
 assert sha(dir/'SHA256SUMS')==expected
 for ln in (dir/'SHA256SUMS').read_text().splitlines():
  h,f=ln.split(maxsplit=1);assert sha(dir/f.removeprefix('*'))==h
seal(base,'dea45f285ab3723bad5a08dd18e3b22919e07d5be6e12a65e8c628e88f19f5cf')
seal(design,'dad738959886cd00cb07d0a1ac29ff7fb7ca16c945dab24899cc7103159f7dbe')
seal(probe,'50a9f2b10eca2a6095af9288a4414f6c4d3b3355ca2ff6b55481172eae28df8f')
control=Path(sys.argv[1]).resolve(); imp=Path(sys.argv[2]).resolve()
assert control.parent==base and control.name.startswith('graphics-evidence.')
assert imp.parent==probe and imp.name.startswith('evidence.')
base_receipt=read(control/'owner-all-four-each-16-frames.json')
assert (base_receipt['gameplay_checks'],base_receipt['frame_count'],base_receipt['unchanged_save_sha256'])==(78,16,'832e3f09cb5718634de49d89e1e358b70cc5789464612b2ca48ec6dab43bc415')
old_finish=read(control/'owner-finish-effective.json')
assert len(old_finish['exact_native_roles'])==18 and set(old_finish['exact_native_roles'].values())=={126}
controls=['owner-all-four-each-16-frames.json','owner-finish-effective.json','functional.json','frame-evidence.json','r17-evidence.json','gate-evidence.json','active-close-evidence.json','owner-finish-ab.json','write.log','cold.log','exec-phase-status.jsonl']
from pair import images
fr=images(control);controls+=list(fr.values())
census=read(imp/'strict-census.json')
assert census['native_import_read_only'] and census['source_world_space_triangle_geometry_matches'] and census['digest_of_observed_jsonl']==sha(imp/'result.jsonl')
assert len(census['meshes'])==4
for name,m in census['meshes'].items():
 assert sha(design/'candidate'/name)==m['digest']
 assert all(r['exact_triangle_coordinate_multiset'] and r['winding']=='consistent_reversal' and r['max_position_error']<=4e-7 and sha(imp/r['payload'])==r['geometry_payload_sha256'] for r in m['surfaces'])
assert not (here/'staged').exists() and not (here/'SHA256SUMS').exists()
save(here/'painted-control-pins.json',{'folder':str(control.relative_to(here.parent)),'files':{n:sha(control/n) for n in sorted(controls)}})
save(here/'strict-import-pins.json',{'folder':str(imp.relative_to(here)),'files':{f.name:sha(f) for f in sorted(imp.iterdir()) if f.is_file()}})
shutil.copytree(base/'staged',here/'staged')
for n in ('stock-result.json','summarize.py','validate_draw.py','validate_r17.py','validate_gate.py','validate_close.py','validate_owner.py','validate_finish.py','metrics.py'):
 shutil.copyfile(base/n,here/n)
proj=here/'staged/HavenlineLevel1'; gp=proj/'previews/clearance_gate'
original={str(f.relative_to(proj)):sha(f) for f in proj.rglob('*') if f.is_file()}
cfg=read(gp/'owner_runtime_census.json')
for name,value in census['meshes'].items():
 src=design/'candidate'/name
 if name.startswith('ThresholdPost'):
  assert sha(src)==sha(gp/'owner_assets'/name)
  old=cfg['meshes'][name]
  assert [x['geometry_payload_sha256'] for x in old['surfaces']]==[x['geometry_payload_sha256'] for x in value['surfaces']]
 else:
  assert sha(src)!=sha(gp/'owner_assets'/name)
  shutil.copyfile(src,gp/'owner_assets'/name)
cfg['meshes']=census['meshes'];save(gp/'owner_runtime_census.json',cfg)
p=gp/'owner_mesh.gd'; source=p.read_text()
anchor='\tvar rows: Array[Dictionary] = []'
assert source.count(anchor)==1
source=source.replace(anchor,'\tvar payloads := verified_payloads(mesh,expected)\n\tif payloads.size()!=expected.size():\n\t\treturn {}\n'+anchor)
anchor='"render_triangles":tris}'
assert source.count(anchor)==1
p.write_text(source.replace(anchor,'"render_triangles":tris,"ordered_float32_triangle_stream_sha256s":Array(payloads)}')+'\n'+(here/'hash_insert.inc').read_text())
auth=read(base/'authenticated-candidate.json')
for side,file in [('left','GateLeaf.obj'),('right','GateLeaf_Right.obj')]:
 a=auth['leaves'][side]; c=census['meshes'][file]
 a['signed_aabb_m']=c['aabb']
 # Strict same original primitive/material/order/counters remain enforced; reject any importer drift.
 for row,ref in zip(a['ordered_surfaces'],c['surfaces']):
  assert row['material']==ref['label'] and row['class']==ref['material_class'] and row['albedo_rgba']==ref['albedo_rgba']
  assert all(row[k]==ref[k] for k in ['index','primitive','triangles','indices','vertices'])
save(here/'authenticated-candidate.json',auth)
save(proj/'tests/hvn_l1_gate_config.json',auth)
current={str(f.relative_to(proj)):sha(f) for f in proj.rglob('*') if f.is_file()}
assert set(original)==set(current)
assert {k for k in original if original[k]!=current[k]}=={'tests/hvn_l1_gate_config.json'}|{'previews/clearance_gate/'+n for n in ('owner_assets/GateLeaf.obj','owner_assets/GateLeaf_Right.obj','owner_mesh.gd','owner_runtime_census.json')}
(here/'staged/draw-source.sha256').write_text(''.join(f'{v}  ./{k}\n' for k,v in sorted(current.items())))
shell=(base/'tty_capture.sh').read_text()
marker='python3 "$here/verify_control.py" "$here" "$out" > "$out/owner-finish-ab.json"'
assert shell.count(marker)==1
(here/'tty_capture.sh').write_text(shell.replace(marker,'python3 "$here/pair.py" "$here" "$out" > "$out/v3-painted-control-paired-16.json"'))
files=sorted(f for f in here.rglob('*') if f.is_file() and '__pycache__' not in f.parts and 'evidence.' not in f.as_posix() and 'graphics-evidence.' not in f.as_posix())
(here/'SHA256SUMS').write_text(''.join(f'{sha(f)}  ./{f.relative_to(here)}\n' for f in files))
