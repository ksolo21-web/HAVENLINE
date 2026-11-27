"""Read complete immutable GitHub file bodies and verify exact staged bytes.

Aliases share a Git blob: one full body is fetched for each distinct new blob,
while a separate recursive-tree check must verify every alias path and mode.
"""
from pathlib import Path
import concurrent.futures
import base64
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
    cache = ROOT / 'reviews/archive-blob-prefetch'
    cached_receipt = cache / 'receipts' / (row['git_blob_sha'] + '.json')
    cache_proof = None
    if cached_receipt.exists():
        receipt_raw = cached_receipt.read_bytes()
        receipt = json.loads(receipt_raw)
        assert receipt['independent'] is True and receipt['reviewer'] == '/root/missing_cast_critic'
        assert receipt['status'] == 'PASS_IMMUTABLE_OBJECT_BODY_ONLY'
        assert receipt['complete_body_read'] is True and receipt['exact_staged_bytes_match'] is True
        retrieval_url = 'https://api.github.com/repos/ksolo21-web/HAVENLINE/git/blobs/' + row['git_blob_sha']
        assert receipt['immutable_api_url'] == retrieval_url and receipt['http_status'] == 200
        response_path = Path(receipt['api_response']['path']).resolve()
        object_path = Path(receipt['decoded_body_path']).resolve()
        assert response_path == (cache / 'api-responses' / (row['git_blob_sha'] + '.json')).resolve()
        assert object_path == (cache / 'objects' / row['git_blob_sha']).resolve()
        response_raw = response_path.read_bytes()
        assert len(response_raw) == receipt['api_response']['bytes']
        assert hashlib.sha256(response_raw).hexdigest() == receipt['api_response']['sha256']
        response_json = json.loads(response_raw)
        assert response_json['sha'] == row['git_blob_sha'] and response_json['encoding'] == 'base64'
        data = base64.b64decode(''.join(response_json['content'].split()), validate=True)
        assert response_json['size'] == len(data) and data == object_path.read_bytes()
        assert all(receipt[key] == row[key] for key in ['sha256', 'bytes', 'git_blob_sha'])
        status = 200
        body_source = 'REVERIFIED_COMPLETE_IMMUTABLE_BLOB_API_BODY_FROM_INDEPENDENT_CRITIC_CACHE'
        cache_proof = {'receipt_path': str(cached_receipt), 'receipt_bytes': len(receipt_raw),
                       'receipt_sha256': hashlib.sha256(receipt_raw).hexdigest(),
                       'api_response_sha256': receipt['api_response']['sha256'],
                       'retrieved_at_utc': receipt['retrieved_at_utc'],
                       'independent_reviewer': receipt['reviewer']}
    else:
        with urllib.request.urlopen(url, timeout=45) as response:
            status = response.status
            data = response.read()
        retrieval_url = url
        body_source = 'COMPLETE_BODY_FROM_IMMUTABLE_COMMIT_URL'
    sha = hashlib.sha256(data).hexdigest()
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert status == 200 and len(data) == row['bytes'] and sha == row['sha256'] and blob == row['git_blob_sha']
    assert data == (ROOT / 'archive-repo' / row['path']).read_bytes(), row['path']
    assert all(r['bytes'] == len(data) and r['sha256'] == sha for r in group)
    return {'body_path': row['path'], 'alias_paths': [r['path'] for r in group],
            'immutable_url': url, 'http_status': status, 'bytes': len(data),
            'body_retrieval_url': retrieval_url, 'http_status_applies_to': retrieval_url,
            'body_source': body_source, 'reused_immutable_object_cache': cache_proof,
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
          'verified_complete_body_bytes': sum(r['bytes'] for r in rows),
          'downloaded_bytes_in_this_phase': sum(r['bytes'] for r in rows if r['reused_immutable_object_cache'] is None),
          'reverified_independent_cached_object_count': sum(r['reused_immutable_object_cache'] is not None for r in rows),
          'files': sorted(rows, key=lambda r: r['body_path']),
          'scope': 'Every complete new distinct file body compared to exact staged bytes. The independent live tree gate must separately bind all paths/modes and unchanged baseline files.'}
(ROOT / 'archive-body-readback.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}))
