from pathlib import Path
import json, hashlib, subprocess, sys
from PIL import Image

base = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def binding(rel): return {'path': rel, 'sha256': sha(base / rel)}
def git_blob(p):
    data = Path(p).read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

requirements = json.loads((base / 'requirements.json').read_text())
review_path = 'reviews/critic-final-visual-acceptance.json'
review = json.loads((base / review_path).read_text())
assert review['requirements_sha256'] == sha(base / 'requirements.json')
assert review['all_mandatory_visual_checks_passed'] and not review['unresolved_visual_repairs']
assert review['score'] >= 9.5
assert all(x['status'] == 'PASS' for x in review['cross_sheet_checks'])
assert len(review['selected']) == requirements['required_selected_sheets'] == 9
assert review['horizontal_rotation_count'] == requirements['required_turnaround_angles'] == 24
expected_series = {s['id'] for a in requirements['assets'] for s in a['sheets']}
assert {x['series_id'] for x in review['selected']} == expected_series

selected = []
for entry in review['selected']:
    p = base / entry['source_path']
    rp = base / entry['per_sheet_review_path']
    r = json.loads(rp.read_text())
    assert sha(p) == entry['sha256'] == r['image_sha256']
    assert sha(rp) == entry['per_sheet_review_sha256']
    assert r['full_image_inspected'] and r['score'] >= 9.5
    assert r['status'].startswith('PASS') and not r['required_repairs']
    assert all(v == 'PASS' for v in r['checks'].values())
    assert r['requirements_sha256'] == sha(base / 'requirements.json')
    assert list(Image.open(p).size) == entry['native_size']
    assert sha(base / r['crop_provenance_path']) == r['crop_provenance_sha256']
    for crop in r['crop_evidence']:
        assert sha(base / crop['path']) == crop['sha256']
    selected.append({**entry, 'image_path': entry['source_path'], 'attempt_id': entry['image_id'], 'git_blob_sha': git_blob(p), 'bytes': p.stat().st_size})

all_reviews = {}
for e in review['attempt_review_bindings']:
    rp = base / e['path']
    assert sha(rp) == e['sha256']
    r = json.loads(rp.read_text())
    assert sha(base / r['image_path']) == r['image_sha256'] == e['image_sha256']
    all_reviews[Path(r['image_path']).stem] = (e, r)
assert len(all_reviews) == review['reviewed_attempt_count'] == 17

selected_ids = {x['image_id'] for x in selected}
gp = base / 'generation-index.json'
generation = json.loads(gp.read_text())
for e in generation['images']:
    meta, r = all_reviews[e['id']]
    e.update({'selected': e['id'] in selected_ids,
              'status': 'SELECTED_STATIC_VISUAL_PASS' if e['id'] in selected_ids else 'REJECTED_RETAINED_HISTORY',
              'independent_score': r['score'], 'review_path': meta['path'], 'review_sha256': meta['sha256']})
generation.update({'generation_frozen': True, 'status': 'FROZEN_STATIC_VISUAL_PASS',
                   'selected': {x['series_id']: x['image_id'] for x in selected if x['asset_id'] != 'customer-counter'},
                   'final_visual_review': binding(review_path)})
gp.write_text(json.dumps(generation, indent=2) + '\n')
subprocess.run([sys.executable, str(base / 'verify_inputs.py')], check=True)

root_review_path = base / 'root-visual-review.json'
root_review = json.loads(root_review_path.read_text())
root_review.update({'independent_visual_acceptance': binding(review_path),
                    'remaining_gates': ['Frozen archive package verification and GitHub remote proof']})
root_review_path.write_text(json.dumps(root_review, indent=2) + '\n')

index_names = ['generation-index.json', 'invocation-index.json',
               'counter-builder/generation-index.json', 'counter-builder/invocation-index.json']
freeze = {
    'schema_version': 1, 'date': '2026-11-25', 'task': requirements['task'],
    'generation_frozen': True, 'visual_status': 'PASS', 'delivery_status': 'PENDING_PACKAGE_AND_REMOTE',
    'requirements': binding('requirements.json'),
    'requirements_sha256': sha(base / 'requirements.json'),
    'repository': requirements['repository'], 'branch': requirements['branch'],
    'base_commit': requirements['base_commit'], 'prefix': requirements['prefix'],
    'generation_index_bindings': [binding(x) for x in index_names],
    'final_independent_visual_review': binding(review_path),
    'root_visual_review': binding('root-visual-review.json'),
    'root_input_verification': binding('root-input-verification.json'),
    'input_index': binding('input-index.json'),
    'counter_final_handoff': binding('counter-builder/final-handoff.json'),
    'generated_original_count': 17, 'selected_count': 9, 'rejected_retained_count': 8,
    'horizontal_rotation_count': 24, 'selected': selected,
    'all_attempt_reviews': review['attempt_review_bindings'],
    'visual_score': review['score'],
    'remaining_gates': ['Independent concrete package audit', 'Fresh exact-head remote publication verification'],
    'scope_boundary': review['scope_boundary'],
    'reopening_rule': 'Any changed image, invoked prompt/input, selected review, requirement or index hash reopens this freeze; no further generation after freeze without a new revision.'
}
out = base / 'final-freeze.json'
assert not out.exists(), 'Refusing to overwrite a frozen batch'
out.write_text(json.dumps(freeze, indent=2) + '\n')
print(json.dumps({'freeze': str(out), 'sha256': sha(out), 'selected': len(selected), 'originals': 17, 'visual_score': review['score']}, indent=2))
