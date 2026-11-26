from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(sys.argv[1])
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
seal=sha(p/'SHA256SUMS')
assert seal=='bb361fbf66f8e89dd0b8d1f8caea7b7fc4d3bdfeb5a1018771f6d98de44b51bd'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
d=json.loads((p/'delta.json').read_text())
assert d['old_obj']=='54a98353986b7138b1c2ef7d8bc61719f69455ae08b9455c56072764668e89ab'
assert d['new_obj']=='137446d82b7c679c88f85069958b0eaacb85ca38dc8d1e7f73be5bef89b7ec53'
assert d['mtl']=='c606aaf113f042e22146e199f7308d9b604e5075ba62b5b8a27ffb139ecbc3f0'
assert d['all_other_lines_exact']
static=json.loads((p/'static.json').read_text())
assert static['sha256']==d['new_obj'] and static['shared_protected_aabb_and_snow_bounds']
assert sum(m['closed_parts'] for m in static['material_closed_shells'].values())==60
assert sum(m['faces'] for m in static['material_closed_shells'].values())==8840
pairs=json.loads((p/'pairs.json').read_text())
assert len(pairs)==20 and all(x['strict_pairs_per_face']==[12,12] and x['wood_strict_pairs_unchanged']>0 for x in pairs)
print(json.dumps({'source_admission':'exact corrected asset to one native capture only','independent_manifest_sha256':seal,'exact_repair':d,
                  'verified_manifold_closed_shells':60,'verified_triangles':8840,'no_art_or_native_result_claim':True},indent=2))
