"""Verify and allow one explicitly requested nested crop from the user Atlas.

This verifies existing bytes only; it never renders, edits, resizes or rewrites
the images. A comparison document's other generated-image crops are not added.
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
assert len(sys.argv) == 3, 'Pass exact comparison JSON and exact requested crop path'
comparison_path = (ROOT / sys.argv[1]).resolve()
target = (ROOT / sys.argv[2]).resolve()
assert comparison_path.is_relative_to(ROOT) and target.is_relative_to(ROOT)
comparison = a.read(comparison_path)
rows = comparison.get('native_pixel_crops', comparison.get('images', []))
matches = [row for row in rows if Path(row.get('crop_path', row.get('path', ''))).resolve() == target]
assert len(matches) == 1
step = matches[0]
middle = Path(step['source_path']).resolve()
middle_metrics, target_metrics = a.metrics(middle.read_bytes()), a.metrics(target.read_bytes())
assert middle_metrics['sha256'] == step['source_sha256']
assert target_metrics['sha256'] == step.get('crop_sha256', step.get('sha256'))
assert step.get('native_pixels', True) is True
census_path = ROOT / 'audit/cast/atlas-cast-census-v2.json'
census = a.read(census_path)
source_matches = [row for row in census['subjects'] if Path(row['source_crop']).resolve() == middle]
assert len(source_matches) == 1
subject = source_matches[0]
assert subject['source_crop_sha256'] == middle_metrics['sha256']
atlas = Path(census['source']['path']).resolve()
atlas_metrics = a.metrics(atlas.read_bytes())
assert census['source']['sha256'] == atlas_metrics['sha256']
atlas_allow = next(row for row in a.read(ROOT / 'archive-generation-input-allowlist.json')['allowed_inputs']
                   if Path(row['local_path']).resolve() == atlas)
assert all(atlas_metrics[k] == atlas_allow[k] for k in ['sha256', 'bytes', 'git_blob_sha'])
outer = subject['source_box']
inner = step['box']
assert len(outer) == len(inner) == 4
composed = [outer[0] + inner[0], outer[1] + inner[1], outer[0] + inner[2], outer[1] + inner[3]]
with Image.open(atlas) as source_image, Image.open(middle) as middle_image, Image.open(target) as target_image:
    assert middle_image.format == target_image.format == 'PNG'
    assert 0 <= outer[0] < outer[2] <= source_image.width and 0 <= outer[1] < outer[3] <= source_image.height
    assert 0 <= inner[0] < inner[2] <= middle_image.width and 0 <= inner[1] < inner[3] <= middle_image.height
    assert middle_image.size == (outer[2] - outer[0], outer[3] - outer[1])
    assert target_image.size == (inner[2] - inner[0], inner[3] - inner[1])
    assert source_image.crop(outer).convert('RGBA').tobytes() == middle_image.convert('RGBA').tobytes()
    assert middle_image.crop(inner).convert('RGBA').tobytes() == target_image.convert('RGBA').tobytes()
    assert source_image.crop(composed).convert('RGBA').tobytes() == target_image.convert('RGBA').tobytes()
    dimensions = {middle: list(middle_image.size), target: list(target_image.size)}

index_path = ROOT / 'archive-input-snapshot-index.json'
index = a.read(index_path)
for path in [comparison_path, census_path]:
    raw = path.read_bytes()
    m = a.metrics(raw)
    snapshot = ROOT / 'archive-input-snapshots' / (path.stem + '--' + m['sha256'] + path.suffix)
    assert not snapshot.exists() or snapshot.read_bytes() == raw
    if not snapshot.exists():
        snapshot.write_bytes(raw)
    if not any(row['sha256'] == m['sha256'] for row in index['snapshots']):
        index['snapshots'].append({'original_path': str(path.relative_to(ROOT)),
                                  'snapshot_path': str(snapshot.relative_to(ROOT)), **m})
a.write(index_path, index)

allowlist_path = ROOT / 'archive-derived-input-allowlist.json'
allowlist = a.read(allowlist_path)
existing = {Path(row['local_path']).resolve(): row for row in allowlist['allowed_inputs']}
source_binding = {'local_path': str(atlas), **atlas_metrics,
                  'archive_relative_path': atlas_allow['archive_relative_path']}
results = []
for path, box, steps, alias, role in [
    (middle, outer, [outer], subject['source_subject_id'] + '-native.png',
     'Exact intermediate user-Atlas source crop retained as provenance for the explicitly requested focused repair input.'),
    (target, composed, [outer, inner], target.name,
     'Explicitly requested exact source-visible detail crop used as a focused image-generation repair reference.')]:
    m = a.metrics(path.read_bytes())
    row = {'local_path': str(path), **m,
           'archive_relative_path': 'generation-inputs/atlas-crops/' + alias,
           'kind': 'EXACT_USER_SOURCE_BOARD_CROP', 'role': role,
           'derivation': {'source_image': source_binding, 'crop_box_xyxy': box,
               'dimensions': dimensions[path], 'upscaled': False,
               'original_two_step_crop_boxes': steps,
               'source_census_path': str(census_path),
               'source_census_sha256': a.metrics(census_path.read_bytes())['sha256'],
               'source_comparison_provenance_path': str(comparison_path),
               'source_comparison_provenance_sha256': a.metrics(comparison_path.read_bytes())['sha256'],
               'verification': 'Whole decoded RGBA pixel equality verified at each original crop step and against the directly composed rectangle in the full recovered Atlas. Exact existing crop PNG bytes retained unchanged.'}}
    if path in existing:
        assert all(existing[path][key] == m[key] for key in ['sha256', 'bytes', 'git_blob_sha'])
        saved = a.exact_copy(path, existing[path]['archive_relative_path'])
        status = 'EXISTING_EXACT_ENTRY_REVERIFIED'
    else:
        allowlist['allowed_inputs'].append(row)
        saved = a.exact_copy(path, row['archive_relative_path'])
        status = 'EXACT_SOURCE_CHAIN_NEWLY_ALLOWLISTED'
    results.append({'local_path': str(path), **m, 'dimensions': dimensions[path],
                    'full_atlas_box': box, 'archive_path': saved['path'], 'status': status})
a.write(allowlist_path, allowlist)
print(json.dumps({'checks': results, 'allowed_derived_input_count': len(allowlist['allowed_inputs']),
                  'other_comparison_crops_added': False, 'image_bytes_modified': False}, indent=2))
