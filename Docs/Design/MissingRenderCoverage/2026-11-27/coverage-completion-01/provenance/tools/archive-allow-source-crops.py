"""Allow only individually named existing source crops after exact pixel checks."""
from pathlib import Path
from PIL import Image
import argparse
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
parser = argparse.ArgumentParser()
parser.add_argument('provenance_files', nargs='+')
parser.add_argument('--role', default='Exact recovered user-board crop used for a focused visual identity repair.')
args = parser.parse_args()
assert not (ROOT / 'archive-content-publication.json').exists()
allow_path = ROOT / 'archive-derived-input-allowlist.json'
allow = a.read(allow_path)
source_allow = a.read(ROOT / 'archive-generation-input-allowlist.json')
sources = {row['sha256']: row for row in source_allow['allowed_inputs']}
index_path = ROOT / 'archive-input-snapshot-index.json'
index = a.read(index_path)
results = []
for value in args.provenance_files:
    provenance_path = Path(value)
    if not provenance_path.is_absolute():
        provenance_path = ROOT / provenance_path
    provenance_path = provenance_path.resolve()
    assert provenance_path.is_relative_to(ROOT)
    provenance = a.read(provenance_path)
    if isinstance(provenance['source'], str) and 'native_crop' in provenance:
        source_metadata = {'path': provenance['source'], 'sha256': provenance['source_sha256'],
                           'bytes': provenance['source_bytes']}
        crop_metadata = provenance['native_crop']
        box = crop_metadata['bbox_xyxy']
        resize = crop_metadata['resize']
    else:
        source_metadata, crop_metadata = provenance['source'], provenance['output']
        box, resize = provenance['bbox'], provenance['resize']
    source = Path(source_metadata['path']).resolve()
    crop = Path(crop_metadata['path']).resolve()
    sm, cm = a.metrics(source.read_bytes()), a.metrics(crop.read_bytes())
    assert sm['sha256'] == source_metadata['sha256']
    if 'bytes' in source_metadata:
        assert sm['bytes'] == source_metadata['bytes']
    assert cm['sha256'] == crop_metadata['sha256'] and cm['bytes'] == crop_metadata['bytes']
    assert resize is False and sm['sha256'] in sources
    parent = sources[sm['sha256']]
    assert parent.get('source_kind') != 'AUTHOR_CREATED_MATHEMATICAL_GUIDE', 'An authored-guide derivative must not be mislabeled as a recovered user-board crop'
    assert all(sm[k] == parent[k] for k in ['sha256', 'git_blob_sha', 'bytes'])
    with Image.open(source) as original, Image.open(crop) as cut:
        assert cut.format == 'PNG'
        assert 0 <= box[0] < box[2] <= original.width and 0 <= box[1] < box[3] <= original.height
        assert cut.size == (box[2] - box[0], box[3] - box[1])
        assert original.convert('RGBA').crop(tuple(box)).tobytes() == cut.convert('RGBA').tobytes()
        dimensions = list(cut.size)
        source_format = original.format
    previous = next((row for row in allow['allowed_inputs'] if row['local_path'] == str(crop)), None)
    if previous:
        assert all(previous[k] == cm[k] for k in ['sha256', 'git_blob_sha', 'bytes'])
        disposition = 'EXISTING_EXACT_ALLOWLIST_REVERIFIED'
    else:
        allow['allowed_inputs'].append({
            'local_path': str(crop), **cm,
            'archive_relative_path': 'generation-inputs/board-crops/' + crop.name,
            'kind': 'EXACT_USER_SOURCE_BOARD_CROP', 'role': args.role,
            'derivation': {'source_image': {'local_path': str(source), **sm,
                'actual_format': source_format, 'archive_relative_path': parent['archive_relative_path']},
                'crop_box_xyxy': box, 'dimensions': dimensions, 'upscaled': False,
                'provenance_document_path': str(provenance_path),
                'provenance_document_sha256': a.metrics(provenance_path.read_bytes())['sha256'],
                'verification': 'Every decoded RGBA pixel exactly matches the recorded rectangle of the unchanged source image. Existing crop PNG bytes retained; no conversion or image generation performed.'}})
        disposition = 'EXACT_CROP_NEWLY_ALLOWLISTED'
    raw = provenance_path.read_bytes()
    pm = a.metrics(raw)
    snapshot = ROOT / 'archive-input-snapshots' / ('source-' + provenance_path.stem + '--' + pm['sha256'] + '.json')
    assert not snapshot.exists() or snapshot.read_bytes() == raw
    if not snapshot.exists():
        snapshot.write_bytes(raw)
    if not any(row['sha256'] == pm['sha256'] for row in index['snapshots']):
        index['snapshots'].append({'original_path': str(provenance_path.relative_to(ROOT)),
                                  'snapshot_path': str(snapshot.relative_to(ROOT)), **pm})
    results.append({'path': str(crop), 'sha256': cm['sha256'], 'dimensions': dimensions, 'status': disposition})
a.write(allow_path, allow)
a.write(index_path, index)
print(json.dumps({'checks': results, 'allowed_derived_input_count': len(allow['allowed_inputs'])}, indent=2))
