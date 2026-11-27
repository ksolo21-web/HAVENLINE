"""Lean exact-byte archive helpers for Havenline conveyor reference concepts.

This helper stages local files and computes Git identities. It never publishes
remote refs and never copies prior artwork into this additive archive package.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT / 'archive-repo'
PREFIX = 'Docs/Design/ConveyorReferences/2026-11-26/connected-logistics-01'
OUT = REPO / PREFIX
BASE = 'e3c787a4ecfffa7ae2013227d2db553f2e2829ef'
BASE_TREE = '62a12cbf7c564b2ba7eebafdaebd3fec27ed42db'
BRANCH = 'art/conveyors-2026-11-26'
SECRET_PATTERN = re.compile(rb'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|[?&](?:sig|signature|X-Amz-Signature|token)=')

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if path.exists() and path.read_bytes() != data:
        old = path.read_bytes()
        old_sha = hashlib.sha256(old).hexdigest()
        history = ROOT / 'archive-stage-snapshot-history' / (path.stem + '--' + old_sha + path.suffix)
        history.parent.mkdir(parents=True, exist_ok=True)
        assert not history.exists() or history.read_bytes() == old
        if not history.exists():
            history.write_bytes(old)
    path.write_bytes(data)

def metrics(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}

def exact_copy(source, relative):
    source = Path(source).resolve()
    target = (OUT / relative).resolve()
    assert target.is_relative_to(OUT), 'Destination escaped archive prefix'
    data = source.read_bytes()
    if source.suffix.lower() not in {'.png', '.jpg', '.jpeg'}:
        data.decode('utf-8')
        assert not SECRET_PATTERN.search(data), source
    assert not target.exists() or target.read_bytes() == data, 'Preserved file bytes changed: ' + str(target)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return {'source_path': str(source), 'path': str(target.relative_to(REPO)), **metrics(data)}

def git_tree_identity(entries):
    root = {}
    for row in entries:
        if row['type'] == 'tree':
            continue
        parts = row['path'].split('/')
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            assert isinstance(node, dict), 'File/directory collision'
        assert parts[-1] not in node, 'Duplicate path: ' + row['path']
        node[parts[-1]] = (row['mode'].lstrip('0'), row['sha'])
    def subtree(node):
        body = bytearray()
        for name, value in sorted(node.items(), key=lambda kv: (kv[0] + ('/' if isinstance(kv[1], dict) else '')).encode()):
            mode, sha = ('40000', subtree(value)) if isinstance(value, dict) else value
            body.extend(mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(sha))
        return hashlib.sha1(b'tree ' + str(len(body)).encode() + b'\0' + body).hexdigest()
    return subtree(root)

def baseline_check():
    tree = read(ROOT / 'archive-baseline-tree.json')
    assert tree['sha'] == BASE_TREE and tree['truncated'] is False
    leaves = [r for r in tree['tree'] if r['type'] != 'tree']
    assert len(leaves) == 4618
    assert git_tree_identity(leaves) == BASE_TREE
    assert not any(r['path'].startswith(PREFIX + '/') or r['path'] == PREFIX for r in leaves)
    assert not any(r['path'] == '.github' or r['path'].startswith('.github/') for r in leaves)
    report = {'status': 'PASS', 'base_commit': BASE, 'base_tree': BASE_TREE,
              'baseline_leaf_count': len(leaves), 'baseline_png_paths': sum(r['path'].lower().endswith('.png') for r in leaves),
              'recursive_tree_truncated': False, 'full_tree_reconstructed': BASE_TREE,
              'archive_destination_unused': True, 'operational_github_absent': True,
              'preexisting_changes_allowed': [], 'branch': BRANCH, 'prefix': PREFIX}
    write(ROOT / 'archive-baseline-verification.json', report)
    return report

def inventory():
    baseline_check()
    baseline = [r for r in read(ROOT / 'archive-baseline-tree.json')['tree'] if r['type'] != 'tree']
    existing_paths = {r['path'] for r in baseline}
    files = []
    for path in sorted(OUT.rglob('*')):
        if not path.is_file():
            continue
        relative = str(path.relative_to(REPO))
        assert relative.startswith(PREFIX + '/') and relative not in existing_paths
        data = path.read_bytes()
        row = {'path': relative, 'mode': '100644', 'type': 'blob', **metrics(data)}
        if path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            assert not data.startswith(b'version https://git-lfs.github.com/spec/')
            with Image.open(path) as im:
                row.update(dimensions=list(im.size), image_format=im.format)
                im.verify()
            if path.suffix.lower() == '.png':
                assert data.startswith(b'\x89PNG\r\n\x1a\n') and row['image_format'] == 'PNG'
        else:
            data.decode('utf-8')
            assert not SECRET_PATTERN.search(data), path
            if path.suffix.lower() == '.json':
                json.loads(data)
        files.append(row)
    leaves = baseline + [{'path': r['path'], 'mode': r['mode'], 'type': r['type'], 'sha': r['git_blob_sha']} for r in files]
    report = {'schema_version': 1, 'base_commit': BASE, 'base_tree': BASE_TREE, 'branch': BRANCH,
              'prefix': PREFIX, 'baseline_files_unchanged': len(baseline),
              'candidate_tree': git_tree_identity(leaves), 'files': files}
    write(ROOT / 'archive-expected-paths.json', report)
    return {'package_paths': len(files), 'package_bytes': sum(r['bytes'] for r in files),
            'candidate_tree': report['candidate_tree'], 'baseline_files_unchanged': len(baseline)}

def upload_plan():
    baseline_shas = {r['sha'] for r in read(ROOT / 'archive-baseline-tree.json')['tree'] if r['type'] == 'blob'}
    receipt_path = ROOT / 'archive-blob-receipts.json'
    receipts = read(receipt_path)['receipts'] if receipt_path.exists() else []
    uploaded = {r['git_blob_sha'] for r in receipts}
    unique = {}
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            row = {'local_path': str(path), 'path': str(path.relative_to(REPO)), **metrics(path.read_bytes())}
            if row['git_blob_sha'] not in baseline_shas | uploaded:
                unique[row['git_blob_sha']] = row
    return {'pending': list(unique.values()), 'already_uploaded_distinct_blobs': len(uploaded)}

def tree_request():
    inventory()
    manifest = read(ROOT / 'archive-expected-paths.json')
    pending = upload_plan()['pending']
    assert not pending, 'Upload binary blobs before creating tree'
    entries = []
    for row in manifest['files']:
        path = REPO / row['path']
        entry = {k: row[k] for k in ('path', 'mode', 'type')}
        if path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            entry['sha'] = row['git_blob_sha']
        else:
            entry['content'] = path.read_bytes().decode('utf-8')
        entries.append(entry)
    request = {'repository_full_name': 'ksolo21-web/HAVENLINE', 'base_tree_sha': BASE_TREE, 'tree_elements': entries}
    write(ROOT / 'archive-tree-request.json', request)
    return {'entries': len(entries), 'base_tree_sha': BASE_TREE, 'expected_tree_sha': manifest['candidate_tree']}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['baseline', 'inventory', 'upload-plan', 'tree-request'])
    args = parser.parse_args()
    print(json.dumps({'baseline': baseline_check, 'inventory': inventory, 'upload-plan': upload_plan, 'tree-request': tree_request}[args.command](), indent=2))
