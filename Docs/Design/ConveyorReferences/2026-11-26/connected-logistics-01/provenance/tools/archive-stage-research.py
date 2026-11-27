"""Stage only the two explicit public research allowlists; no recursive import."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
groups = ['existing', 'new']
records, pending = [], []
permitted = set()
for group in groups:
    research_root = ROOT / 'references' / group
    manifest_path = research_root / 'PUBLIC-ARCHIVE-MANIFEST.json'
    if not manifest_path.exists():
        pending.append(str(manifest_path.relative_to(ROOT)))
        continue
    manifest = a.read(manifest_path)
    assert manifest.get('archive_this_manifest', True)
    selected = []
    selected_rows = manifest.get('allowed_files', manifest.get('selected_files'))
    assert isinstance(selected_rows, list), 'Missing explicit positive file selection'
    for row in selected_rows:
        relative = Path(row['relative_path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        source = (research_root / relative).resolve()
        assert source.is_relative_to(research_root.resolve())
        if row.get('local_path'):
            assert Path(row['local_path']).resolve() == source
        assert source.suffix.lower() in {'.json', '.md', '.txt', '.png', '.jpg', '.jpeg', '.svg', '.csv'}, 'Disallowed full media/HTML type'
        data = source.read_bytes()
        m = a.metrics(data)
        assert m['sha256'] == row['sha256'] and m['bytes'] == row['bytes'], 'Allowlist drift: ' + str(source)
        selected.append((source, relative, m, row.get('kind')))
    selected.append((manifest_path, Path('PUBLIC-ARCHIVE-MANIFEST.json'), a.metrics(manifest_path.read_bytes()), 'Exact positive publication allowlist'))
    for source, relative, m, kind in selected:
        archive_relative = Path('research') / group / relative
        target = a.OUT / archive_relative
        permitted.add(str(archive_relative))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != source.read_bytes():
            cache = ROOT / 'archive-research-stage-history' / group / (target.stem + '--' + a.metrics(target.read_bytes())['sha256'] + target.suffix)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(target.read_bytes())
        target.write_bytes(source.read_bytes())
        records.append({'group': group, 'original_locator': str(source), 'path': str(target.relative_to(a.REPO)), **m, 'kind': kind})
# A previous staging copy removed from an updated allowlist must not leak into publication.
for group in groups:
    if str(Path('references') / group / 'PUBLIC-ARCHIVE-MANIFEST.json') in pending:
        continue
    destination = a.OUT / 'research' / group
    if not destination.exists():
        continue
    for target in sorted(destination.rglob('*')):
        if target.is_file() and str(target.relative_to(a.OUT)) not in permitted:
            cache = ROOT / 'archive-research-stage-history' / group / (target.stem + '--' + a.metrics(target.read_bytes())['sha256'] + target.suffix)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(target.read_bytes())
            target.unlink()
report = {'schema_version': 1, 'positive_allowlist_only': True,
    'public_research_files': records, 'pending_manifests': pending,
    'excluded': 'All unlisted research inputs, full third-party videos/HTML and broad timeline/storyboard collections remain outside this public archive.'}
a.write(ROOT / 'archive-research-snapshot.json', report)
a.write(a.OUT / 'provenance/public-research.json', report)
print(json.dumps({'allowed_files_staged': len(records), 'pending_manifests': pending, 'public_research_bytes': sum(x['bytes'] for x in records)}))
