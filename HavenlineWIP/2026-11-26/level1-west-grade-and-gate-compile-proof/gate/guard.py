"""Exact local compilation admission, no generalized importer normalization."""
import json,runpy,sys
from pathlib import Path
base=Path(__file__).resolve().parent.parent
prov=base/'hvn-l1-gate-import-exact-provenance-v1'
require_pin='22a139a7f09baba7f9a90223fe6d08a280e7e2ea898acbb1bc5921d659b3ba86'
from hashlib import sha256
def sha(data):return sha256(data).hexdigest()
assert sha((prov/'SHA256SUMS').read_bytes())==require_pin
for line in (prov/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1);assert sha((prov/n).read_bytes())==h
v=runpy.run_path(str(prov/'inspect_guard.py'))
require=v['require']
raw=base/'hvn-l1-gate-import-byte-recorder-v1/import-only.pt99CUoE'
require(sha((raw/'SHA256SUMS').read_bytes())=='4539682dcb491076c296dd60b81541298b41a4473461b5c05afdb1250e32028d','raw archive manifest')
for line in (raw/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1)
 require(Path(n).name==n.removeprefix('./') and sha((raw/n).read_bytes())==h,'archive bytes')
arc=json.loads((raw/'changes.json').read_bytes())
require(arc['diagnostic_only'] and not arc['tracked_non_sidecar_changes'] and not arc['unexpected_extracted_path_delta'],'unexpected tracked or texture changes')
pinned={}
uids=set()
for row in arc['sidecars']:
 p=Path(row['path'])
 require(p in v['sidecars'] and p not in pinned,'four precise remap paths')
 before=(v['src']/p).read_bytes(); after=(raw/p.name).read_bytes()
 require(sha(before)==v['original'][p]==row['original_sha256'] and sha(after)==row['actual_sha256'],'archived sidecar bytes')
 h=row['unique_uid'].encode()
 require(h not in uids,'duplicate UID')
 uids.add(h)
 uid_line=b'uid="'+h+b'"\n'
 type_line=b'type="Mesh"\n'
 dep_line=b'\nsource_file="res://'+p.as_posix().removesuffix('.import').encode()+b'"\n'
 require(before.count(type_line)==before.count(dep_line)==1,'ambiguous original insertion anchors')
 rebuilt=before.replace(type_line,type_line+uid_line,1).replace(dep_line,b'\n'+dep_line,1)
 require(rebuilt==after and set(row['semantic_diff']['key_diffs'])=={'remap.uid'},'not exact observed additive transform')
 pinned[p]={'before':sha(before),'after':sha(after),'uid':h.decode()}
require(pinned.keys()==v['sidecars'],'sidecar set incomplete')
expected=v['textures']()
require(len(arc['images'])==25 and {Path(r['path']) for r in arc['images']}==expected.keys(),'texture set mismatch')
for r in arc['images']:
 x=expected[Path(r['path'])]
 require(r['actual_sha256']==r['embedded_sha256']==x['embedded_sha256'] and r['same_as_embedded'] is True,'unverified texture bytes')
def check_tree(project):
 for p,h in v['original'].items():
  q=project/p
  require(q.is_file() and q.resolve()==q and not q.is_symlink(),f'invalid tracked path {p}')
  require(sha(q.read_bytes())==(pinned[p]['after'] if p in pinned else h),f'nonpinned postimport SHA {p}')
 for p,entry in expected.items():
  q=project/p
  require(q.is_file() and q.resolve()==q and not q.is_symlink() and sha(q.read_bytes())==entry['embedded_sha256'],f'texture extract mismatch {p}')
 for q in project.rglob('*'):
  require(not q.is_symlink(),'symlink')
  if q.is_dir():continue
  p=q.relative_to(project)
  require(q.is_file() and (p in v['original'] or p in expected or p.parts[0]=='.godot' or p.suffix in ('.import','.uid')),f'unexpected file {p}')
if __name__=='__main__':
 if len(sys.argv)==1:print(json.dumps({'observed_exact_pairs':{str(p):x for p,x in pinned.items()},'observed_exact_asset_extracts':len(expected),'compile_run':False},indent=2))
 else:
  p=Path(sys.argv[1])
  require(len(sys.argv)==2 and p.name=='project' and p.parent.parent==Path('/tmp') and p.parent.name.startswith('hvn-gate-latch-compile.') and p.resolve()==p,'isolated compile workspace only')
  check_tree(p)
  print('Exact observed postimport state matched; compile-only boundary, no gameplay result.')
