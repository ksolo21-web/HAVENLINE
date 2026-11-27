"""Plan bounded, sequential unattached Git-tree construction from a frozen package.

Every intermediate tree identity is computed locally from all 4,955 baseline
leaves plus that exact cumulative set of additions. This creates no remote tree,
commit or ref. Remote construction must wait for independent package approval;
the one eventual content commit points only to the final verified candidate.
"""
from pathlib import Path
import argparse
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
parser = argparse.ArgumentParser()
parser.add_argument('--maximum-request-bytes', type=int, default=2_000_000)
parser.add_argument('--maximum-entries', type=int, default=150)
args = parser.parse_args()
assert 500_000 <= args.maximum_request_bytes <= 4_000_000
assert 1 <= args.maximum_entries <= 300
freeze_path = ROOT / 'final-freeze.json'
assert a.read(freeze_path)['generation_frozen'] is True
assert not (ROOT / 'archive-content-publication.json').exists()
manifest = a.read(ROOT / 'archive-expected-paths.json')
assert manifest['base_commit'] == a.BASE and manifest['base_tree'] == a.BASE_TREE
baseline = [row for row in a.read(ROOT / 'archive-baseline-tree.json')['tree'] if row['type'] != 'tree']
assert len(baseline) == 4955 and a.git_tree_identity(baseline) == a.BASE_TREE
entries = []
for row in manifest['files']:
    path = a.REPO / row['path']
    raw = path.read_bytes()
    assert all(a.metrics(raw)[key] == row[key] for key in ['bytes', 'sha256', 'git_blob_sha'])
    entry = {key: row[key] for key in ['path', 'mode', 'type']}
    if path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
        entry['sha'] = row['git_blob_sha']
    else:
        entry['content'] = raw.decode('utf-8')
    entries.append((entry, {'path': row['path'], 'mode': row['mode'], 'type': row['type'], 'sha': row['git_blob_sha']}))
groups, current, current_size = [], [], 0
for entry, leaf in entries:
    size = len(json.dumps(entry, ensure_ascii=False).encode('utf-8'))
    assert size < 4_000_000, 'Single text entry exceeds bounded request ceiling; upload it as a blob instead'
    if current and (current_size + size > args.maximum_request_bytes or len(current) >= args.maximum_entries):
        groups.append(current)
        current, current_size = [], 0
    current.append((entry, leaf))
    current_size += size
if current:
    groups.append(current)
folder = ROOT / 'archive-tree-batches'
folder.mkdir(exist_ok=True)
previous = a.BASE_TREE
leaves = list(baseline)
records = []
for number, group in enumerate(groups, 1):
    leaves.extend(leaf for _,leaf in group)
    expected = a.git_tree_identity(leaves)
    request = {'repository_full_name': 'ksolo21-web/HAVENLINE', 'base_tree_sha': previous,
               'tree_elements': [entry for entry,_ in group]}
    path = folder / ('batch-' + str(number).zfill(3) + '.json')
    raw = (json.dumps(request, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    assert not path.exists() or path.read_bytes() == raw
    path.write_bytes(raw)
    records.append({'number': number, 'request_path': str(path), **a.metrics(raw),
                    'base_tree': previous, 'expected_result_tree': expected,
                    'entries': len(group), 'cumulative_new_paths': len(leaves)-len(baseline)})
    previous = expected
assert previous == manifest['candidate_tree']
plan = {'schema_version': 1, 'status': 'PLAN_ONLY_AWAITING_INDEPENDENT_PACKAGE_GATE',
        'final_freeze_sha256': a.metrics(freeze_path.read_bytes())['sha256'],
        'expected_paths_sha256': a.metrics((ROOT / 'archive-expected-paths.json').read_bytes())['sha256'],
        'base_commit': a.BASE, 'base_tree': a.BASE_TREE, 'final_candidate_tree': previous,
        'baseline_leaves_unchanged': len(baseline), 'new_paths': len(entries), 'batches': records,
        'commit_plan': 'Only the final candidate is committed once; intermediate trees are unattached immutable objects.',
        'remote_mutations_performed': False}
a.write(ROOT / 'archive-tree-construction-plan.json', plan)
print(json.dumps({'batches': len(records), 'new_paths': len(entries), 'candidate_tree': previous,
                  'largest_request_bytes': max(row['bytes'] for row in records), 'remote_mutations_performed': False}, indent=2))
