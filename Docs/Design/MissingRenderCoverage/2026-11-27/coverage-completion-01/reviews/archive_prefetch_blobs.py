"""Read complete already-uploaded immutable Git blobs without publishing a ref.

This critic-owned cache is not a public-package input. Git blob identity is
immutable; final branch/tree verification must bind each eventual alias path.
No credentials are read and no uploader receipt or builder file is modified.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import base64
import datetime
import hashlib
import json
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'reviews/archive-blob-prefetch'
REPOSITORY = 'ksolo21-web/HAVENLINE'


def metric(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_once(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, 'Immutable critic cache changed: ' + str(path)
    else:
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_bytes(data)
        temporary.replace(path)


def verify(row):
    sha = row['git_blob_sha']
    assert len(sha) == 40 and all(c in '0123456789abcdef' for c in sha)
    assert row['remote_git_blob_sha'] == sha and row['status'] == 'IMMUTABLE_BLOB_UPLOADED_UNATTACHED'
    staged = Path(row['local_path']).read_bytes()
    assert all(metric(staged)[k] == row[k] for k in ['bytes', 'sha256', 'git_blob_sha'])
    object_path = CACHE / 'objects' / sha
    response_path = CACHE / 'api-responses' / (sha + '.json')
    receipt_path = CACHE / 'receipts' / (sha + '.json')
    url = 'https://api.github.com/repos/' + REPOSITORY + '/git/blobs/' + sha
    headers = {}
    retrieved = None
    if response_path.exists():
        response_body = response_path.read_bytes()
        status = 200
        origin = 'Retained complete prior immutable Git blob API response; exact decoded bytes reverified'
    else:
        request = urllib.request.Request(url, headers={
            'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'Havenline-independent-archive-critic'})
        with urllib.request.urlopen(request, timeout=45) as response:
            status = response.status
            response_body = response.read()
            headers = {k.lower(): v for k, v in response.headers.items()
                       if k.lower() in {'content-type', 'content-length', 'date', 'etag',
                                        'x-github-request-id', 'x-ratelimit-limit',
                                        'x-ratelimit-remaining', 'x-ratelimit-reset'}}
        retrieved = stamp()
        origin = 'Complete immutable Git blob API response fetched during this independent critic run'
    response_json = json.loads(response_body)
    assert status == 200 and response_json['encoding'] == 'base64'
    raw = base64.b64decode(''.join(response_json['content'].split()), validate=True)
    observed = metric(raw)
    assert response_json['sha'] == observed['git_blob_sha'] == sha
    assert response_json['size'] == len(raw) and raw == staged
    assert all(observed[k] == row[k] for k in observed)
    write_once(response_path, response_body)
    write_once(object_path, raw)
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text())
        assert prior['complete_body_read'] is True and prior['exact_staged_bytes_match'] is True
        assert all(prior[k] == observed[k] for k in observed)
        assert prior['api_response']['sha256'] == metric(response_body)['sha256']
        return prior
    receipt = {
        'schema_version': 1, 'reviewer': '/root/missing_cast_critic', 'independent': True,
        'status': 'PASS_IMMUTABLE_OBJECT_BODY_ONLY', 'repository': REPOSITORY,
        'http_status': status, 'immutable_api_url': url, 'origin': origin,
        'retrieved_at_utc': retrieved, 'verified_at_utc': stamp(), 'response_headers': headers,
        **observed, 'complete_body_read': True, 'exact_staged_bytes_match': True,
        'input_upload_receipt': row, 'decoded_body_path': str(object_path),
        'api_response': {'path': str(response_path), **metric(response_body)},
        'final_tree_or_branch_verified': False,
        'boundary': 'Proof of exact stored immutable blob bytes only. Final published tree must independently bind every path/mode and preserve the baseline.'}
    write_once(receipt_path, (json.dumps(receipt, indent=2) + '\n').encode())
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-new-requests', type=int, default=50)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    assert 0 <= args.max_new_requests <= 50 and 1 <= args.workers <= 4
    raw = (ROOT / 'archive-blob-receipts.json').read_bytes()
    source = json.loads(raw)
    rows = {row['git_blob_sha']: row for row in source['receipts']}
    snapshot_sha = metric(raw)['sha256']
    snapshot_path = CACHE / 'input-receipts' / (snapshot_sha + '.json')
    write_once(snapshot_path, raw)
    cached, pending = [], []
    for row in sorted(rows.values(), key=lambda r: (-r['bytes'], r['git_blob_sha'])):
        if (CACHE / 'api-responses' / (row['git_blob_sha'] + '.json')).exists():
            cached.append(row)
        else:
            pending.append(row)
    targets = cached + pending[:args.max_new_requests]
    verified, errors = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(verify, row): row for row in targets}
        for future in as_completed(futures):
            row = futures[future]
            try:
                verified.append(future.result())
            except Exception as exc:
                error = {'git_blob_sha': row['git_blob_sha'], 'error_type': type(exc).__name__, 'message': str(exc)}
                if isinstance(exc, urllib.error.HTTPError):
                    error.update(http_status=exc.code, rate_limit_headers={k: v for k, v in exc.headers.items() if k.lower().startswith('x-ratelimit')})
                errors.append(error)
            if (len(verified) + len(errors)) % 5 == 0:
                print(json.dumps({'verified_complete_object_bodies': len(verified), 'batch_targets': len(targets), 'errors': len(errors)}), flush=True)
    result = {
        'schema_version': 1, 'reviewer': '/root/missing_cast_critic', 'independent': True,
        'status': 'PASS_BOUNDED_IMMUTABLE_OBJECT_PREFETCH' if not errors else 'PARTIAL_IMMUTABLE_OBJECT_PREFETCH',
        'completed_at_utc': stamp(), 'input_receipt_snapshot': {'path': str(snapshot_path), **metric(raw)},
        'snapshot_uploaded_objects': len(rows), 'new_request_budget': args.max_new_requests,
        'verified_complete_objects': len(verified), 'verified_body_bytes': sum(r['bytes'] for r in verified),
        'unread_snapshot_objects': sorted(set(rows) - {r['git_blob_sha'] for r in verified}),
        'object_receipts': [{'path': str(CACHE / 'receipts' / (r['git_blob_sha'] + '.json')), **metric((CACHE / 'receipts' / (r['git_blob_sha'] + '.json')).read_bytes())} for r in sorted(verified, key=lambda r: r['git_blob_sha'])],
        'errors': errors, 'publication_approved': False,
        'scope': 'Complete immutable Git blob API bodies, decoded and compared byte-for-byte to staged files. Bounded prepublication object proof; not a branch, tree, path, alias, availability or whole-package approval.'}
    report_path = CACHE / ('batch-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
    write_once(report_path, (json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({k: v for k, v in result.items() if k not in {'unread_snapshot_objects', 'object_receipts'}}), flush=True)


if __name__ == '__main__':
    main()
