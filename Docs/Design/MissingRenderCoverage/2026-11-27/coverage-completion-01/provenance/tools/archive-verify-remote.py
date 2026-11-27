"""Verify fresh saved GitHub content readbacks against the frozen package.

The caller fetches ref, commit and recursive tree through GitHub, then saves
the unmodified JSON objects to the three named archive-published files.
"""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

manifest = a.read(ROOT / 'archive-expected-paths.json')
ref = a.read(ROOT / 'archive-published-ref.json')
commit = a.read(ROOT / 'archive-published-commit.json')
tree = a.read(ROOT / 'archive-published-tree.json')
baseline = a.read(ROOT / 'archive-baseline-tree.json')
body = a.read(ROOT / 'archive-body-readback.json')
assert ref['ref'] == 'refs/heads/' + a.BRANCH
assert ref['object']['sha'] == commit['sha'] == body['commit']
assert [row['sha'] for row in commit['parents']] == [a.BASE]
assert commit['tree']['sha'] == tree['sha'] == manifest['candidate_tree']
assert tree['truncated'] is False
remote = {row['path']: row for row in tree['tree'] if row['type'] != 'tree'}
old = {row['path']: row for row in baseline['tree'] if row['type'] != 'tree'}
expected = {row['path']: row for row in manifest['files']}
assert len(old) == 4955 and not set(old) & set(expected)
assert set(remote) == set(old) | set(expected)
for path, row in old.items():
    assert all(remote[path].get(k) == row.get(k) for k in ['sha', 'mode', 'type', 'size']), path
for path, row in expected.items():
    observed = remote[path]
    assert observed['sha'] == row['git_blob_sha'] and observed['size'] == row['bytes'], path
    assert observed['type'] == row['type'] and observed['mode'] == row['mode'], path
assert a.git_tree_identity(list(remote.values())) == tree['sha']
assert body['status'] == 'PASS_ALL_COMPLETE_NEW_BODIES'
seen = set()
for row in body['files']:
    assert row['complete_body_read'] and row['exact_staged_bytes_match']
    for path in row['alias_paths']:
        assert path not in seen
        seen.add(path)
        assert all(row[k] == expected[path][k] for k in ['bytes', 'sha256', 'git_blob_sha']), path
assert seen == set(expected)
assert len(body['files']) == len({row['git_blob_sha'] for row in expected.values()})
result = {'schema_version': 1, 'status': 'PASS_VERIFIED_CONTENT_PUBLICATION', 'score': 10,
          'repository': 'ksolo21-web/HAVENLINE', 'branch': a.BRANCH, 'prefix': a.PREFIX,
          'content_commit': commit['sha'], 'content_tree': tree['sha'], 'sole_parent': a.BASE,
          'recursive_tree_truncated': False, 'baseline_files_unchanged': len(old),
          'baseline_png_paths_unchanged': sum(path.lower().endswith('.png') for path in old),
          'new_archive_files': len(expected), 'published_total_files': len(remote),
          'complete_new_blob_bodies': len(body['files']), 'complete_body_paths': len(seen),
          'unexpected_paths': [], 'mismatches': [],
          'mutation_scope': 'Only the dedicated art branch and additive reference prefix; no baseline file changes.'}
a.write(ROOT / 'archive-content-readback.json', result)
print(json.dumps(result))
