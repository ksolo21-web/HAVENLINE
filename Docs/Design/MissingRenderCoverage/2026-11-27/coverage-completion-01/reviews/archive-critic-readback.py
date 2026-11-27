"""Independent complete-body verification of one frozen additive archive commit.

Read-only network/source access. Output is limited to archive-critic-* files.
The expected-path file must be independently computed from frozen staged bytes.
An optional hash-bound independent-critic prefetch can avoid duplicate downloads.
Its complete original API responses are decoded and reverified here; all other
objects receive fresh immutable raw-commit GETs. These sources stay distinct.
"""
import base64
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / 'archive-repo'
PREFIX = 'Docs/Design/MissingRenderCoverage/2026-11-27/coverage-completion-01/'
COMMIT = sys.argv[1]
EXPECTED = ROOT / 'reviews' / (sys.argv[2] if len(sys.argv) > 2 else 'archive-critic-frozen-paths.json')
OUTPUT = ROOT / 'reviews' / (sys.argv[3] if len(sys.argv) > 3 else 'archive-critic-final-body-readback.json')
assert len(COMMIT) == 40 and all(c in '0123456789abcdef' for c in COMMIT)
assert EXPECTED.name.startswith('archive-critic-') and OUTPUT.name.startswith('archive-critic-')
assert EXPECTED.parent == ROOT / 'reviews' and OUTPUT.parent == ROOT / 'reviews'

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def git_blob(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

PREFETCH = ROOT / 'reviews/archive-blob-prefetch/batch-20261127T075802Z.json'
PREFETCH_SHA256 = '4c1c13c2fb8bc56913a2ddb18e8b2b62d6fb829faa2634586fa433e089f36dc8'
cache = {}
prefetch_summary = None
if PREFETCH.exists():
    prefetch_bytes = PREFETCH.read_bytes()
    assert sha256(prefetch_bytes) == PREFETCH_SHA256
    prefetch = json.loads(prefetch_bytes)
    assert prefetch['reviewer'] == '/root/missing_cast_critic' and prefetch['independent'] is True
    assert prefetch['status'] == 'PASS_BOUNDED_IMMUTABLE_OBJECT_PREFETCH' and not prefetch['errors']
    for bound_receipt in prefetch['object_receipts']:
        receipt_bytes = pathlib.Path(bound_receipt['path']).read_bytes()
        assert len(receipt_bytes) == bound_receipt['bytes'] and sha256(receipt_bytes) == bound_receipt['sha256']
        assert git_blob(receipt_bytes) == bound_receipt['git_blob_sha']
        receipt = json.loads(receipt_bytes)
        oid = receipt['git_blob_sha']
        assert oid not in cache
        assert receipt['reviewer'] == '/root/missing_cast_critic' and receipt['independent'] is True
        assert receipt['status'] == 'PASS_IMMUTABLE_OBJECT_BODY_ONLY' and receipt['http_status'] == 200
        assert receipt['complete_body_read'] is True and receipt['repository'] == 'ksolo21-web/HAVENLINE'
        assert receipt['immutable_api_url'] == 'https://api.github.com/repos/ksolo21-web/HAVENLINE/git/blobs/' + oid
        cache[oid] = (receipt, bound_receipt)
    assert len(cache) == prefetch['verified_complete_objects'] == 51
    prefetch_summary = {'path': str(PREFETCH), 'sha256': PREFETCH_SHA256,
                        'independent_fetch_reviewer': prefetch['reviewer'],
                        'available_cached_objects': len(cache),
                        'scope': 'Original complete immutable API responses re-decoded and reverified here; no new request for a reused body.'}

snapshot_bytes = EXPECTED.read_bytes()
snapshot = json.loads(snapshot_bytes)
assert snapshot.get('frozen') is True
rows = snapshot['files']
assert rows and all(row['path'].startswith(PREFIX) for row in rows)
groups = {}
for row in rows:
    groups.setdefault(row['git_blob_sha'], []).append(row)

def fetch_group(pair):
    oid, aliases = pair
    row = next((x for x in aliases if '/selected/' in x['path']), aliases[0])
    rel = row['path']
    url = 'https://raw.githubusercontent.com/ksolo21-web/HAVENLINE/' + COMMIT + '/' + urllib.parse.quote(rel, safe='/')
    result = {'path': rel, 'aliases': [x['path'] for x in aliases], 'immutable_commit_url': url,
              'expected_git_blob_sha': oid, 'expected_sha256': row['sha256'],
              'expected_bytes': row['bytes']}
    try:
        assert all(x['sha256'] == row['sha256'] and x['bytes'] == row['bytes'] for x in aliases)
        if oid in cache:
            receipt, bound_receipt = cache[oid]
            api_identity = receipt['api_response']
            api_bytes = pathlib.Path(api_identity['path']).read_bytes()
            assert len(api_bytes) == api_identity['bytes'] and sha256(api_bytes) == api_identity['sha256']
            assert git_blob(api_bytes) == api_identity['git_blob_sha']
            api = json.loads(api_bytes)
            assert api['encoding'] == 'base64' and api['sha'] == oid
            assert api['url'] == receipt['immutable_api_url'] and api['size'] == row['bytes']
            body = base64.b64decode(''.join(api['content'].split()), validate=True)
            assert pathlib.Path(receipt['decoded_body_path']).read_bytes() == body
            assert len(body) == receipt['bytes'] and sha256(body) == receipt['sha256'] and git_blob(body) == oid
            result.update({'body_evidence_source': 'REVERIFIED_COMPLETE_CACHED_INDEPENDENT_CRITIC_API_RESPONSE',
                           'fresh_request_made_by_this_critic': False,
                           'url': receipt['immutable_api_url'], 'response_url': api['url'],
                           'http_status': receipt['http_status'],
                           'prefetch_receipt': bound_receipt,
                           'prefetch_origin': receipt['origin'],
                           'prefetch_retrieved_at_utc': receipt['retrieved_at_utc'],
                           'prefetch_verified_at_utc': receipt['verified_at_utc'],
                           'complete_api_response': api_identity,
                           'complete_api_response_redecoded_here': True,
                           'decoded_cache_file_equal_api_body': True})
        else:
            request = urllib.request.Request(url, headers={'User-Agent': 'Havenline-Missing-Archive-Independent-Critic/1.0', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read()
                result['http_status'] = response.status
                result['response_url'] = response.geturl()
            result.update({'body_evidence_source': 'FRESH_IMMUTABLE_RAW_COMMIT_DOWNLOAD',
                           'fresh_request_made_by_this_critic': True, 'url': url})
        result['observed_bytes'] = len(body)
        result['observed_sha256'] = sha256(body)
        result['observed_git_blob_sha'] = git_blob(body)
        result['whole_body_read'] = True
        result['all_local_alias_bytes_equal_remote'] = all((STAGE / x['path']).read_bytes() == body for x in aliases)
        result['pass'] = (result['http_status'] == 200 and len(body) == row['bytes']
                          and result['observed_sha256'] == row['sha256']
                          and result['observed_git_blob_sha'] == oid
                          and result['all_local_alias_bytes_equal_remote'])
    except Exception as error:
        result['pass'] = False
        result['error'] = type(error).__name__ + ': ' + str(error)
    return result

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    futures = [pool.submit(fetch_group, pair) for pair in groups.items()]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        results.append(result)
        if not result['pass']:
            print(json.dumps({'completed': len(results), 'of': len(groups), 'failed_path': result['path'], 'error': result.get('error', 'BODY_MISMATCH')}), flush=True)
        elif len(results) % 25 == 0:
            print(json.dumps({'completed': len(results), 'of': len(groups), 'failures': sum(not x['pass'] for x in results)}), flush=True)

report = {'schema_version': 2, 'reviewer': '/root/missing_world_audit',
          'method': 'Complete-body verification: hash-bound independent-critic immutable API responses are re-decoded/rehashed locally; every other object receives a fresh immutable raw-commit GET. Every body is compared by SHA256, Git blob SHA1, length and exact frozen alias bytes. No builder body-verification receipt is substituted.',
          'commit': COMMIT, 'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'expected_path_snapshot_sha256': sha256(snapshot_bytes),
          'independent': True, 'script_sha256': sha256(pathlib.Path(__file__).read_bytes()),
          'prefetch': prefetch_summary,
          'reverified_cached_api_body_count': sum(x.get('body_evidence_source') == 'REVERIFIED_COMPLETE_CACHED_INDEPENDENT_CRITIC_API_RESPONSE' for x in results),
          'fresh_raw_commit_body_count': sum(x.get('body_evidence_source') == 'FRESH_IMMUTABLE_RAW_COMMIT_DOWNLOAD' for x in results),
          'expected_path_count': len(rows), 'distinct_new_blob_count': len(groups),
          'whole_body_reads_passed': sum(x['pass'] for x in results),
          'unique_body_bytes': sum(x.get('observed_bytes', 0) for x in results),
          'snapshot_unchanged': EXPECTED.read_bytes() == snapshot_bytes,
          'checks': sorted(results, key=lambda x: x['path']),
          'boundary': 'Complete body evidence only. Final package/tree/branch/receipt verification is separately owned by /root/missing_cast_critic; cached objects become path evidence only through the verified final immutable tree.',
          'status': 'PASS_FULL_BODY_READBACK' if len(results) == len(groups) and all(x['pass'] for x in results) and EXPECTED.read_bytes() == snapshot_bytes else 'FAIL_OR_INCOMPLETE'}
OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['status', 'commit', 'expected_path_count', 'distinct_new_blob_count', 'whole_body_reads_passed', 'reverified_cached_api_body_count', 'fresh_raw_commit_body_count', 'unique_body_bytes', 'snapshot_unchanged']}, indent=2), flush=True)
