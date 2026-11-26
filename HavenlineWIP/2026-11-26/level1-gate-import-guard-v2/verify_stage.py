from pathlib import Path
import hashlib,json,sys
old,new=map(Path,sys.argv[1:])
def filemap(p):
    assert not any(f.is_symlink() for f in p.rglob('*'))
    return {str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
a,b=filemap(old),filemap(new)
assert len(a)==143 and len(b)==144
changed={k for k in a if a[k]!=b[k]}
assert changed=={'previews/clearance_gate/clearance_gate_view.gd','tests/hvn_l1_combined_draw.gd','tests/hvn_l1_gate_config.json'}
new_only=set(b)-set(a)
assert new_only=={'previews/clearance_gate/import_census.json'}
for cfg in ('gate-config.json','authenticated-candidate.json'):
    policy=json.loads(Path(cfg).read_text())
    for ident,e in policy['leaves'].items():
        assert e['sha256']==b[e['resource'][6:]]
        assert len(e['ordered_surfaces'])==39 and sum(s['triangles'] for s in e['ordered_surfaces'])==3226
assert b['previews/clearance_gate/import_census.json']==b['tests/hvn_l1_gate_config.json']
data={'unchanged_prior_files':len(a)-len(changed),'changed_guards_or_observer_only':{k:[a[k],b[k]] for k in sorted(changed)},
      'new_census_only':{k:b[k] for k in new_only},
      'unchanged_donors_stock_validator_route_physics_r17_assets_daylight_and_shaders':True}
print(json.dumps(data,indent=2))
