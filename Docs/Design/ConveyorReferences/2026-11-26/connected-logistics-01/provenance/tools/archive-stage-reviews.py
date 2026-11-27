"""Preserve exact critic reports and generated-art QA; link baseline source art."""
from pathlib import Path
import importlib.util
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
index_path = ROOT / 'archive-review-snapshot.json'
index = a.read(index_path) if index_path.exists() else {'schema_version': 1, 'captured_versions': [], 'baseline_source_bindings': []}
baseline = {}
for row in a.read(ROOT / 'archive-baseline-tree.json')['tree']:
    if row['type'] == 'blob':
        baseline.setdefault(row['sha'], []).append(row['path'])
by_origin = {}
for row in index['captured_versions']:
    by_origin.setdefault(row['original_locator'], []).append(row)
sources = list((ROOT / 'reviews').glob('*.json')) + list((ROOT / 'reviews').glob('*.md'))
sources += [p for p in (ROOT / 'reviews/evidence').rglob('*') if p.is_file()] if (ROOT / 'reviews/evidence').exists() else []
for source in sorted(sources):
    assert source.suffix.lower() in {'.json', '.md', '.txt', '.png', '.jpg', '.jpeg'}
    rel = source.relative_to(ROOT / 'reviews')
    dest = a.OUT / 'reviews' / rel
    data = source.read_bytes()
    m = a.metrics(data)
    if source.suffix.lower() == '.json':
        json.loads(data)
    if source.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
        with Image.open(source) as image:
            image.verify()
    if dest.exists() and dest.read_bytes() != data:
        old = a.metrics(dest.read_bytes())
        history = dest.parent / 'history' / (dest.stem + '--' + old['sha256'] + dest.suffix)
        history.parent.mkdir(parents=True, exist_ok=True)
        if history.exists():
            assert history.read_bytes() == dest.read_bytes()
            dest.unlink()
        else:
            dest.rename(history)
        for row in by_origin.get(str(source), []):
            if row['sha256'] == old['sha256']:
                row['archive_path'] = str(history.relative_to(a.REPO))
                row['disposition'] = 'RETAINED_EARLIER_CAPTURE'
    saved = a.exact_copy(source, 'reviews/' + str(rel))
    assert saved['sha256'] == m['sha256']
    if not any(row['sha256'] == m['sha256'] for row in by_origin.setdefault(str(source), [])):
        row = {'original_locator': str(source), 'archive_path': saved['path'], **m, 'disposition': 'CURRENT_CAPTURE'}
        index['captured_versions'].append(row)
        by_origin[str(source)].append(row)
# Full existing source PNGs are already committed; preserve their exact baseline bindings.
source_dir = ROOT / 'reviews/source-inspection'
for source in sorted(source_dir.glob('*')) if source_dir.exists() else []:
    if not source.is_file() or source.suffix.lower() not in {'.png', '.jpg', '.jpeg'}:
        continue
    m = a.metrics(source.read_bytes())
    assert m['git_blob_sha'] in baseline, 'Unrecognized source-inspection image; explicit scope required: ' + str(source)
    paths = sorted(baseline[m['git_blob_sha']], key=lambda p: ('/selected/' not in p, len(p), p))
    row = {'original_locator': str(source), **m, 'source_commit': a.BASE,
           'repository_path': paths[0], 'immutable_url': 'https://github.com/ksolo21-web/HAVENLINE/blob/' + a.BASE + '/' + paths[0],
           'disposition': 'LINK_EXISTING_BASELINE_ART_NO_DUPLICATE_COPY'}
    if not any(old['original_locator'] == row['original_locator'] and old['sha256'] == row['sha256'] for old in index['baseline_source_bindings']):
        index['baseline_source_bindings'].append(row)
a.write(index_path, index)
a.write(a.OUT / 'provenance/review-evidence.json', index)
print(json.dumps({'captured_report_and_qa_versions': len(index['captured_versions']), 'baseline_source_bindings': len(index['baseline_source_bindings'])}))
