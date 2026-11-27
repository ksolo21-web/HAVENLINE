"""Read complete immutable GitHub file bodies and verify exact staged bytes.

Aliases share a Git blob: one full body is fetched for each distinct new blob,
while a separate recursive-tree check must verify every alias path and mode.
"""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
commit = sys.argv[1]
assert len(commit) == 40 and all(c in '0123456789abcdef' for c in commit)
manifest = json.loads((ROOT / 'archive-expected-paths.json').read_text())
unique = {}
for row in sorted(manifest['files'], key=lambda r: ('/selected/' not in r['path'], r['path'])):
    unique.setdefault(row['git_blob_sha'], []).append(row)


def verify(group):
    row = group[0]
    url = 'https://raw.githubusercontent.com/ksolo21-web/HAVENLINE/' + commit + '/' + urllib.parse.quote(row['path'], safe='/')
    with urllib.request.urlopen(url, timeout=45) as response:
        status = response.status
        data = response.read()
    sha = hashlib.sha256(data).hexdigest()
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert status == 200 and len(data) == row['bytes'] and sha == row['sha256'] and blob == row['git_blob_sha']
    assert data == (ROOT / 'archive-repo' / row['path']).read_bytes(), row['path']
    assert all(r['bytes'] == len(data) and r['sha256'] == sha for r in group)
    return {'body_path': row['path'], 'alias_paths': [r['path'] for r in group],
            'immutable_url': url, 'http_status': status, 'bytes': len(data),
            'sha256': sha, 'git_blob_sha': blob, 'complete_body_read': True,
            'exact_staged_bytes_match': True}


rows = []
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(verify, group) for group in unique.values()]
    for future in concurrent.futures.as_completed(futures):
        rows.append(future.result())
        if len(rows) % 10 == 0:
            print(json.dumps({'complete_distinct_bodies': len(rows), 'required_distinct_bodies': len(unique)}), flush=True)
result = {'schema_version': 1, 'status': 'PASS_ALL_COMPLETE_NEW_BODIES', 'commit': commit,
          'unique_new_blobs': len(rows), 'covered_archive_paths': sum(len(r['alias_paths']) for r in rows),
          'downloaded_bytes': sum(r['bytes'] for r in rows), 'files': sorted(rows, key=lambda r: r['body_path']),
          'scope': 'Every complete new distinct file body compared to exact staged bytes. The independent live tree gate must separately bind all paths/modes and unchanged baseline files.'}
(ROOT / 'archive-body-readback.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}))
