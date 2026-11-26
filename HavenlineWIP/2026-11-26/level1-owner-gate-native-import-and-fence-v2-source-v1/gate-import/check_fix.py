"""Source guard and synthetic controls; do not rewrite or certify the earlier native receipt."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
import sys
import tempfile
import validate

here=Path(__file__).resolve().parent
parent=here.parent
old=parent/'hvn-l1-owner-gate-v2-import-census-v1'
assert sha256((old/'SHA256SUMS').read_bytes()).hexdigest()=='d87eed4c2f3df5c200cce6de733c35cf00321cb7ad3fe1f5255a4b2e7d6b5402'
before=(old/'input/probe.gd').read_text()
after=(here/'input/probe.gd').read_text()
old_line='if key.ends_with("_texture") and mat.get(key) != null:'
new_line='if int(property.type) == TYPE_OBJECT and mat.get(key) is Texture:'
note='\t\t\t\t# Check the descriptor and actual resource; heightmap_flip_texture is bool.\n'
assert after.replace(note,'').replace(new_line,old_line)==before
for f in ("validate.py","expected.json","selftest.py","input/project.godot"):
 assert (here/f).read_bytes()==(old/f).read_bytes()
needle="""for name in GateLeaf GateLeaf_Right ThresholdPost ThresholdPost_Right; do
  grep -Fxq 'force_disable_mesh_compression=true' "$work/project/donors/$name.obj.import"
done
"""
assert (here/'run.sh').read_text().replace(needle,'')==(old/'run.sh').read_text()
for p in (here/'input/donors').iterdir():
 if p.suffix=='.import':
  assert p.read_text().count('force_disable_mesh_compression=true')==1
  assert 'scale_mesh=Vector3(1, 1, 1)' in p.read_text() and 'offset_mesh=Vector3(0, 0, 0)' in p.read_text()
 else:
  assert p.read_bytes()==(old/'input/donors'/p.name).read_bytes()
class Texture: pass
class Texture2D(Texture): pass
TYPE_BOOL=1
TYPE_OBJECT=24
fixture=[
 ("heightmap_flip_texture",TYPE_BOOL,False),
 ("heightmap_flip_texture",TYPE_BOOL,True),
 ("albedo_texture",TYPE_OBJECT,Texture2D()),
 ("detail_mask",TYPE_OBJECT,Texture2D()), # real map even without suffix
 ("normal_texture",TYPE_OBJECT,None),
 ("shader_nontexture_object",TYPE_OBJECT,object()),
]
found=[key for key,t,value in fixture if t==TYPE_OBJECT and isinstance(value,Texture)]
assert found==['albedo_texture','detail_mask']
replay=old/'evidence.K8K8d2Um'
original=[json.loads(l) for l in (replay/'result.jsonl').read_text().splitlines()]
all_rows=[x for r in original for x in r['surfaces']]
assert all(x['map_slots_bound']==['heightmap_flip_texture'] for x in all_rows)
# Hypothetical previous-native metadata correction in scratch ONLY: demonstrate all other strict guards.
with tempfile.TemporaryDirectory(prefix='fixture.',dir=here) as d:
 t=Path(d)
 for p in replay.glob('*.xyzf32'): (t/p.name).symlink_to(p.resolve())
 def run(rows):
  (t/'result.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
  return subprocess.run([sys.executable,str(here/'validate.py'),str(t)],capture_output=True,text=True)
 assert run(original).returncode
 for row in all_rows: row['map_slots_bound']=[]
 cleared=run(original)
 assert cleared.returncode and 'assert np.max(sep)<4e-7' in cleared.stderr
 all_rows[0]['map_slots_bound']=['albedo_texture']
 rejected=run(original)
 assert rejected.returncode and "got['map_slots_bound']==[]" in rejected.stderr
import numpy as np
from scipy.spatial import cKDTree
positions={}
for row in original:
 _,groups=validate.parse(validate.donors/row['file'])
 large=[]
 for g,got in zip(groups,row['surfaces']):
  src=np.unique(g['xyz'].reshape(-1,3),axis=0)
  actual=np.fromfile(replay/got['payload'],dtype='<f4').reshape(-1,3)
  dist,_=cKDTree(src).query(actual,k=1)
  large.append(float(dist.max()))
 positions[row['file']]=max(large)
print(json.dumps({"native_probe_invoked":False,"synthetic_true_texture_properties":found,
 "actual_prior_result_sha256":sha256((replay/'result.jsonl').read_bytes()).hexdigest(),"false_positive_rows":len(all_rows),
 "prior_geometry_over_0_4um_remains_rejected_with_false_texture_metadata_removed":True,
 "maximum_default_import_source_coordinate_difference_m":positions,
 "new_configuration":"disable OBJ mesh compression in all four disposable import sidecars; source triangle tolerance unchanged",
 "synthetic_actual_map_still_rejected_by_original_validator":True},indent=2))
