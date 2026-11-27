"""Stage only the design author's explicit final and retained-history file list."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
source_root = ROOT / 'design'
manifest_path = source_root / 'PUBLIC-DESIGN-ARCHIVE-MANIFEST.json'
if not manifest_path.exists():
    print(json.dumps({'status': 'AWAITING_AUTHOR_FINAL_DESIGN_MANIFEST', 'expected': str(manifest_path)}))
    raise SystemExit(0)
manifest = a.read(manifest_path)
expected_sha = a.read(ROOT / 'archive-package-config.json').get('frozen_design_manifest_sha256')
assert expected_sha and a.metrics(manifest_path.read_bytes())['sha256'] == expected_sha, 'Explicit author-frozen manifest hash required'
base = manifest.get('base', 'design')
assert base in {'.', 'design'}, 'Unexpected design manifest base'
source_root = ROOT if base == '.' else ROOT / 'design'
rows = manifest.get('allowed_files', manifest.get('selected_files', manifest.get('files')))
assert isinstance(rows, list), 'Explicit design file list required'
records = []
for row in rows:
    relative = Path(row['relative_path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    if base == '.':
        assert relative.parts[0] in {'design', 'reviews'}, 'Unrelated task path in design manifest'
    source = (source_root / relative).resolve()
    assert source.is_relative_to(source_root.resolve())
    assert source.suffix.lower() in {'.json', '.md', '.txt', '.svg', '.png', '.jpg', '.jpeg', '.csv', '.py'}
    if row.get('local_path'):
        assert Path(row['local_path']).resolve() == source
    metrics = a.metrics(source.read_bytes())
    assert metrics['sha256'] == row['sha256'] and metrics['bytes'] == row['bytes'], str(source)
    destination = str(relative) if base == '.' else 'design/' + str(relative)
    saved = a.exact_copy(source, destination)
    records.append({**saved, 'role': row.get('classification', row.get('kind', row.get('role'))), 'source_manifest': str(manifest_path)})
saved_manifest = a.exact_copy(manifest_path, 'design/PUBLIC-DESIGN-ARCHIVE-MANIFEST.json')
records.append({**saved_manifest, 'role': 'Exact final design publication manifest'})
report = {'schema_version': 1, 'explicit_selection_only': True, 'files': records,
          'generated_render_count_policy': 'Design SVGs and preview PNGs are catalogued separately from imagegen original attempts; retained reviewed revisions remain historical.'}
a.write(ROOT / 'archive-design-snapshot.json', report)
a.write(a.OUT / 'provenance/design-artifacts.json', report)
print(json.dumps({'design_files_staged': len(records), 'design_bytes': sum(row['bytes'] for row in records)}))
