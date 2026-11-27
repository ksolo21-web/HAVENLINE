"""Plan unattached immutable blobs from the explicit public-file draft.

This does not stage a file, select artwork, create a tree/commit or publish a ref.
Only exact image bytes already named in the reviewed draft can be transferred.
Final assembly still depends on the root freeze and separate package approval.
"""
from pathlib import Path
import argparse
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--limit', type=int)
args = parser.parse_args()
assert args.limit is None or args.limit > 0
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
draft_path = ROOT / 'archive-public-files-draft.json'
draft = a.read(draft_path)
assert draft['status'] == 'DRAFT_FOR_ROOT_FINAL_FREEZE_REVIEW'
assert not draft['unresolved_referenced_files']
assert not (ROOT / 'archive-content-publication.json').exists()
receipts_path = ROOT / 'archive-blob-receipts.json'
receipts = a.read(receipts_path)['receipts'] if receipts_path.exists() else []
uploaded = {row['git_blob_sha']: row for row in receipts}
baseline = {row['sha'] for row in a.read(ROOT / 'archive-baseline-tree.json')['tree'] if row['type'] == 'blob'}
pending = {}
for row in draft['public_files']:
    source = Path(row['source_path']).resolve()
    if source.suffix.lower() not in {'.png', '.jpg', '.jpeg'}:
        continue
    assert source.is_relative_to(ROOT) and 'private-library-transfer' not in source.parts
    actual = a.metrics(source.read_bytes())
    assert all(actual[key] == row[key] for key in ['sha256', 'bytes', 'git_blob_sha']), str(source)
    if actual['git_blob_sha'] in baseline:
        continue
    if actual['git_blob_sha'] in uploaded:
        prior = uploaded[actual['git_blob_sha']]
        assert prior['remote_git_blob_sha'] == actual['git_blob_sha']
        assert prior['sha256'] == actual['sha256'] and prior['bytes'] == actual['bytes']
        continue
    intended = a.PREFIX + '/' + row['archive_path']
    if actual['git_blob_sha'] not in pending:
        pending[actual['git_blob_sha']] = {'local_path': str(source), 'path': intended, **actual,
            'planned_archive_aliases': [], 'publication_status': 'UNATTACHED_BLOB_ONLY_PENDING_ROOT_FREEZE',
            'explicit_public_draft_sha256': a.metrics(draft_path.read_bytes())['sha256']}
    pending[actual['git_blob_sha']]['planned_archive_aliases'].append(intended)
rows = list(pending.values())
print(json.dumps({'pending': rows[:args.limit] if args.limit else rows,
                  'pending_total_before_limit': len(rows), 'already_uploaded_distinct_blobs': len(uploaded),
                  'purpose': 'Early immutable blob transfer only; no file staging, tree, commit or branch write'}, indent=2))
