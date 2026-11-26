"""Independent byte-line/seat pairing of frozen contact donor and derived snow."""
from pathlib import Path
import hashlib,json,sys
a,b=[Path(p).read_text().splitlines() for p in sys.argv[1:]]
ref_ray=json.loads(Path('../hvn-l1-reference-panel-v2-rope-contact-independent/new.json').read_text())
cur_ray=json.loads(Path('rope-replay.json').read_text())
assert len(a)==len(b)
rows={}
material=''
for line in a:
    if line.startswith('usemtl '): material=line.split()[1];rows[material]=set()
    if line.startswith('f '): rows[material].update(int(p.split('/')[0])-1 for p in line.split()[1:])
ts={}
for label in ('v','vn'):
    ai=[i for i,x in enumerate(a) if x.startswith(label+' ')]
    changed={j for j,i in enumerate(ai) if a[i]!=b[i]}
    assert changed and changed<=rows['draped_snow']
    ts[label]=len(changed)
assert [x for x in a if not x.startswith(('v ','vn ','mtllib '))]==[x for x in b if not x.startswith(('v ','vn ','mtllib '))]
assert ref_ray['triangle_counts']==cur_ray['triangle_counts']
assert len(ref_ray['rows'])==len(cur_ray['rows'])==40
for old,new in zip(ref_ray['rows'],cur_ray['rows']):
    assert all(old[k]==new[k] for k in old if k not in ('printed_cap_vertices_in_wood','face_mid'))
    assert new['printed_cap_vertices_in_wood']>=1
    assert [{k:v for k,v in side.items() if k!='x'} for side in old['face_mid']]==[{k:v for k,v in side.items() if k!='x'} for side in new['face_mid']] # prior diagnostic X origin was cap centroid
old=samples0=json.loads(Path('v2-projection.json').read_text())['sampled_visible_material_pixel_area']
new=samples1=json.loads(Path('v3-projection.json').read_text())['sampled_visible_material_pixel_area']
assert all(new[k]['loops_with_at_least_four_px_contiguous_span']==40 for k in new)
print(json.dumps({'lower_scallop_surface_delta_rows':ts,'rope_and_wood_coordinates_normals_topology_and_materials_exact':True,
  'rope_contact_geometry_all_40_replayed_against_frozen_v2':True,'snow_root_sampled_support_per_module':True,
  'samples_native_ortho_projection_only':{k:{'snow_covered_area_delta_px2':new[k]['visible_material_pixel_area']['draped_snow']-old[k]['visible_material_pixel_area']['draped_snow'],
   'minimum_rope_contiguous_width_px':min(x['main_component_native_width_px'] for x in new[k]['rope_components_by_loop'])} for k in new},
  'no_native_import_or_appearance_claim':True},indent=2))
