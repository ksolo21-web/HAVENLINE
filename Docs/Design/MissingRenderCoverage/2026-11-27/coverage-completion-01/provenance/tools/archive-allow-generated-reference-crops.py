"""Capture exact native evidence crops used or explicitly authorized as inputs.

Completed invocation inputs are discovered automatically. Optional command-line
paths must be expressly authorized by root for upcoming calls. Registered source
PNGs and explicit crop provenance are required; this creates no new imagery.
"""
from pathlib import Path
import importlib.util
import json
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
assert not (ROOT / 'archive-content-publication.json').exists()
invocations = [a.read(path) for path in sorted((ROOT / 'invocations').glob('*.json'))]
completed = [row for row in invocations if row.get('output')]
originals = {Path(row['output']['local_path']).resolve(): row for row in completed}
allowlist_path = ROOT / 'archive-derived-input-allowlist.json'
allowlist = a.read(allowlist_path)
already = {Path(row['local_path']).resolve() for row in allowlist['allowed_inputs']}
needed = {}
for invocation in completed:
    for ref in invocation['ordered_reference_inputs']:
        path = Path(ref['local_path']).resolve()
        if path.is_relative_to(ROOT / 'reviews/evidence') and path not in already:
            needed.setdefault(path, []).append({'invocation_id': invocation['id'], 'order': ref['order'],
                                               'recorded_sha256': ref['sha256'], 'basis': 'COMPLETED_INVOCATION_INPUT'})
for locator in sys.argv[1:]:
    path = (ROOT / locator).resolve()
    assert path.is_relative_to(ROOT / 'reviews/evidence') and path.is_file()
    if path not in already:
        needed.setdefault(path, []).append({'invocation_id': None, 'order': None,
            'recorded_sha256': a.metrics(path.read_bytes())['sha256'],
            'basis': 'EXPLICIT_ROOT_AUTHORIZATION_FOR_UPCOMING_REFERENCE',
            'execution_boundary': 'Preparation authority only; no invocation is claimed by this binding.'})

candidates = {}
def capture(row, provenance, inherited_source=None):
    if not isinstance(row, dict):
        return
    if 'output' in row and 'source' in row and 'bbox' in row:
        out, source, box = row['output'], row['source'], row['bbox']
        candidate = {'path': out['path'], 'sha256': out['sha256'], 'source_path': source['path'],
                     'source_sha256': source['sha256'], 'box': box, 'native_pixels': row.get('resize') is False}
    elif inherited_source and 'path' in row and ('box' in row or 'bbox_xyxy' in row):
        candidate = {**row, **inherited_source,
                     'box': row.get('box', row.get('bbox_xyxy')),
                     'native_pixels': row.get('native_pixels', row.get('transform') == 'native crop only')}
    elif 'source_path' in row and ('box' in row or 'bbox_xyxy' in row) and ('crop_path' in row or 'path' in row):
        candidate = {'path': row.get('crop_path', row.get('path')),
                     'sha256': row.get('crop_sha256', row.get('sha256')),
                     'source_path': row['source_path'], 'source_sha256': row['source_sha256'],
                     'box': row.get('box', row.get('bbox_xyxy')),
                     'native_pixels': row.get('native_pixels', row.get('resize') is False or row.get('transform') == 'native crop only')}
    else:
        candidate = None
    if candidate:
        path = Path(candidate['path']).resolve()
        source = Path(candidate['source_path']).resolve()
        if path in needed and source in originals:
            candidates.setdefault(path, []).append({**candidate, 'provenance': provenance})
    if 'source_path' in row and 'source_sha256' in row and isinstance(row.get('crops'), list):
        inherited = {'source_path': row['source_path'], 'source_sha256': row['source_sha256']}
        for child in row['crops']:
            capture(child, provenance, inherited)
    elif isinstance(row.get('source'), dict) and isinstance(row.get('crops'), list):
        inherited = {'source_path': row['source']['path'], 'source_sha256': row['source']['sha256']}
        for child in row['crops']:
            capture(child, provenance, inherited)
    for key, value in row.items():
        if key == 'crops':
            continue
        if isinstance(value, list):
            for child in value:
                capture(child, provenance)
        elif isinstance(value, dict):
            capture(value, provenance)

for provenance in sorted((ROOT / 'reviews/evidence').glob('*.json')):
    obj = a.read(provenance)
    for row in obj if isinstance(obj, list) else [obj]:
        capture(row, provenance)
index_path = ROOT / 'archive-input-snapshot-index.json'
index = a.read(index_path)
results = []
unmatched = []
for path, uses in needed.items():
    if path not in candidates:
        unmatched.append(str(path))
        continue
    options = candidates[path]
    assert len({(row['source_path'], tuple(row['box']), row['sha256'], row['source_sha256']) for row in options}) == 1
    chosen = options[0]
    source = Path(chosen['source_path']).resolve()
    original = originals[source]
    source_metrics = a.metrics(source.read_bytes())
    crop_metrics = a.metrics(path.read_bytes())
    assert all(source_metrics[k] == original['output'][k] for k in ['bytes', 'sha256', 'git_blob_sha'])
    assert chosen['source_sha256'] == source_metrics['sha256']
    assert chosen['sha256'] == crop_metrics['sha256']
    assert all(use['recorded_sha256'] == crop_metrics['sha256'] for use in uses)
    assert chosen['native_pixels'] is True
    box = chosen['box']
    with Image.open(source) as source_image, Image.open(path) as crop_image:
        assert source_image.format == crop_image.format == 'PNG'
        assert 0 <= box[0] < box[2] <= source_image.width and 0 <= box[1] < box[3] <= source_image.height
        assert crop_image.size == (box[2] - box[0], box[3] - box[1])
        assert source_image.crop(box).convert('RGBA').tobytes() == crop_image.convert('RGBA').tobytes()
        dimensions = list(crop_image.size)
    provenance = chosen['provenance']
    raw = provenance.read_bytes()
    pm = a.metrics(raw)
    snapshot = ROOT / 'archive-input-snapshots' / (provenance.stem + '--' + pm['sha256'] + provenance.suffix)
    assert not snapshot.exists() or snapshot.read_bytes() == raw
    if not snapshot.exists():
        snapshot.write_bytes(raw)
    if not any(row['sha256'] == pm['sha256'] for row in index['snapshots']):
        index['snapshots'].append({'original_path': str(provenance.relative_to(ROOT)),
                                  'snapshot_path': str(snapshot.relative_to(ROOT)), **pm})
    row = {'local_path': str(path), **crop_metrics,
           'archive_relative_path': 'generation-inputs/generated-reference-crops/' + path.name,
           'kind': 'EXACT_NATIVE_GENERATED_REFERENCE_CROP',
           'role': 'Native unresampled detail crop actually used or explicitly authorized for an upcoming generation reference; individual bindings distinguish those states. The source image review remains the authority on visual approval.',
           'derivation': {'source_image': {'local_path': str(source), **source_metrics,
                             'render_id': original['id'], 'archive_path': a.PREFIX + '/attempts/' + original['id'] + '.png'},
               'crop_box_xyxy': box, 'dimensions': dimensions, 'upscaled': False,
               'provenance_path': str(provenance), 'provenance_sha256': pm['sha256'],
               'authorized_reference_bindings': uses,
               'verification': 'Complete decoded RGBA pixel equality between the exact source rectangle and the existing crop PNG; original compressed crop bytes retained unchanged.'}}
    allowlist['allowed_inputs'].append(row)
    a.exact_copy(path, row['archive_relative_path'])
    results.append({'path': str(path), **crop_metrics, 'source_render': original['id'], 'authorized_reference_bindings': uses})
a.write(index_path, index)
a.write(allowlist_path, allowlist)
print(json.dumps({'newly_allowlisted_generated_reference_crops': results,
                  'unmatched_inputs_require_explicit_source_scope': unmatched,
                  'image_bytes_modified': False}, indent=2))
