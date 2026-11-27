"""Independent read-only draft archive audit; writes only critic-owned evidence."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit
from collections import defaultdict
from PIL import Image
import hashlib, json, posixpath, re

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / 'archive-repo'
STAMP = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT = ROOT / 'reviews/archive-preflight' / STAMP
OUT.mkdir(parents=True, exist_ok=True)
inputs = []

def metrics(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}

def snapshot(rel):
    source = ROOT / rel
    raw = source.read_bytes()
    target = OUT / 'inputs' / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    inputs.append({'source_path': str(source), 'snapshot_path': str(target), **metrics(raw)})
    return json.loads(raw) if source.suffix == '.json' else raw.decode('utf-8')

public = snapshot('archive-public-files-draft.json')
bindings = snapshot('archive-draft-source-bindings.json')
capture = snapshot('archive-generation-snapshot.json')
config = snapshot('archive-package-config.json')
baseline = snapshot('archive-baseline-tree.json')
requirements = snapshot('requirements.json')
selection = snapshot('selection-working.json')
gallery = snapshot('gallery-drafts/gallery-manifest.json')
for name in ['archive-finalize.py', 'archive-register.py', 'archive-tools.py', 'archive-draft-public-files.py', 'archive-build-galleries.py']:
    snapshot(name)

findings = []
def issue(code, item, detail):
    findings.append({'code': code, 'item': item, 'detail': detail})

def bound_file(row, path_key='path'):
    path = REPO / row[path_key]
    raw = path.read_bytes()
    m = metrics(raw)
    for key in ['bytes', 'sha256', 'git_blob_sha']:
        if key in row and m[key] != row[key]:
            raise AssertionError(f'{path_key} {key} mismatch for {row[path_key]}')
    return raw

# Reconstruct every baseline subtree independently from the downloaded rows.
children = defaultdict(list)
seen = set()
for entry in baseline['tree']:
    path = PurePosixPath(entry['path'])
    parent = '' if str(path.parent) == '.' else str(path.parent)
    assert entry['path'] not in seen
    seen.add(entry['path']); children[parent].append(entry)
computed = {}; subtree_issues = []
for parent in sorted(children, key=lambda p: p.count('/') + bool(p), reverse=True):
    body = bytearray()
    for entry in sorted(children[parent], key=lambda e: (PurePosixPath(e['path']).name + ('/' if e['type'] == 'tree' else '')).encode()):
        identity = computed.get(entry['path'], entry['sha'])
        if entry['type'] == 'tree' and identity != entry['sha']:
            subtree_issues.append(entry['path'])
        body.extend(entry['mode'].lstrip('0').encode() + b' ' + PurePosixPath(entry['path']).name.encode() + b'\0' + bytes.fromhex(identity))
    computed[parent] = hashlib.sha1(b'tree ' + str(len(body)).encode() + b'\0' + body).hexdigest()
leaves = {e['path']: e for e in baseline['tree'] if e['type'] != 'tree'}
baseline_blobs = {e['sha'] for e in leaves.values() if e['type'] == 'blob'}
baseline_result = {'root': computed[''], 'expected_root': config['base_tree'],
                   'leaf_count': len(leaves), 'png_paths': sum(p.lower().endswith('.png') for p in leaves),
                   'subtree_mismatches': subtree_issues,
                   'truncated': baseline.get('truncated'),
                   'operational_workflow_paths': [p for p in leaves if p == '.github' or p.startswith('.github/')]}
assert computed[''] == config['base_tree'] and not subtree_issues and baseline.get('truncated') is False

# Native custody, immutable invocation/prompt bytes, input order and requirements.
calls = capture['actual_invocations']
call_results = []; input_count = 0; actual_hashes = set()
assert len(calls) == capture['generated_original_count'] == len({c['id'] for c in calls})
for call in calls:
    errors = []; ident = call['id']
    try:
        native = bound_file(call['output'])
        actual_hashes.add(metrics(native)['sha256'])
        source = Path(call['output']['source_path']).read_bytes()
        returned = Path(call['output']['native_returned_locator']).read_bytes()
        assert native == source == returned, 'registered/staged/native-returned bytes differ'
        assert native.startswith(b'\x89PNG\r\n\x1a\n'), 'native PNG signature missing'
        with Image.open(Path(call['output']['source_path'])) as im:
            assert list(im.size) == call['output']['dimensions'] and im.format == 'PNG'
            im.verify()
        inv = json.loads(bound_file(call['exact_invocation']))
        prompt = bound_file(call['exact_invoked_prompt'])
        assert prompt == inv['arguments']['prompt'].encode('utf-8'), 'actual argument differs from preserved prompt'
        document = bound_file(call['source_prompt_document'])
        assert document == prompt or document == prompt + b'\n', 'source prompt differs beyond declared terminal newline'
        refs = inv['arguments'].get('referenced_image_paths', [])
        assert len(refs) == len(call['ordered_reference_inputs'])
        assert not inv['arguments'].get('num_last_images_to_include'), 'unbound conversation-image reference'
        for order, (locator, ref) in enumerate(zip(refs, call['ordered_reference_inputs']), 1):
            input_count += 1
            assert order == ref['order'] and Path(locator).resolve() == Path(ref['original_locator']).resolve(), 'input order/locator mismatch'
            raw = Path(locator).read_bytes(); m = metrics(raw)
            assert all(m[k] == ref[k] for k in ['bytes', 'sha256', 'git_blob_sha']), 'input bytes mismatch'
            if ref['disposition'] == 'IMMUTABLE_BASELINE_IMAGE':
                assert leaves[ref['repository_path']]['sha'] == ref['git_blob_sha']
                assert ref['source_commit'] == config['base_commit']
            elif ref['disposition'] == 'PENDING_EXPLICIT_INPUT_SCOPE':
                issue('PENDING_SOURCE_BINDING', ident, {'order': order, 'input_path': locator, 'sha256': ref['sha256']})
            else:
                assert bound_file({'path': ref['archive_path'], **m}) == raw
        requirement_raw = bound_file(call['requirements'])
        assert metrics(requirement_raw)['sha256'] == inv['requirements_at_generation']['sha256'], 'requirements snapshot mismatch'
    except Exception as exc:
        errors.append(str(exc)); issue('GENERATION_CUSTODY_OR_PROVENANCE', ident, str(exc))
    call_results.append({'id': ident, 'status': 'PASS' if not errors else 'FAIL', 'errors': errors})

failure_results = []
for call in capture['failed_no_image_invocations']:
    errors = []
    try:
        inv = json.loads(bound_file(call['exact_invocation']))
        prompt = bound_file(call['exact_attempted_prompt'])
        assert prompt == inv['arguments']['prompt'].encode('utf-8')
        assert call.get('output') is None and call['generated_image_count'] == 0 and not inv.get('output')
        bound_file(call['exact_original_error_record'])
        assert call['recorded_status'] == 'TOOL_FAILED_NO_IMAGE'
        refs = inv['arguments'].get('referenced_image_paths', [])
        assert len(refs) == len(call['attempted_ordered_reference_inputs'])
        for order, (locator, ref) in enumerate(zip(refs, call['attempted_ordered_reference_inputs']), 1):
            assert order == ref['order'] and Path(locator).resolve() == Path(ref['original_locator']).resolve()
            m = metrics(Path(locator).read_bytes())
            assert all(m[k] == ref[k] for k in m)
    except Exception as exc:
        errors.append(str(exc)); issue('NO_IMAGE_RECORD', call['id'], str(exc))
    failure_results.append({'id': call['id'], 'status': 'PASS' if not errors else 'FAIL', 'errors': errors})

prepared_errors = []
for row in capture['prepared_invocation_history']:
    inv = json.loads(bound_file(row['exact_prepared_record']))
    if inv.get('status') != 'PREPARED' or inv.get('output'):
        prepared_errors.append(row['id'])

# Check proposed/staged bytes and explicit exclusion boundary, redacting any match.
entries = [(Path(r['source_path']), r['archive_path'], 'proposed', r) for r in public['public_files']]
entries += [(REPO / r['archive_path'], r['archive_path'], 'staged', r) for r in public['already_staged_files']]
manifest_byte_drift = []; excluded = []; credential_hits = []; scanned_text = 0
secret_patterns = {
    'signed_url_parameter': re.compile(r'https?://[^\s"<>]+[?&](?:X-Amz-Signature|X-Goog-Signature|sig|signature|access_token|oauth_token|api_key)=[^\s"<>]{8,}', re.I),
    'github_secret': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'private_key_block': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'literal_bearer_token': re.compile(r'Bearer\s+[A-Za-z0-9._~+/=-]{24,}')}
prefix = config['prefix']; published = set(leaves); destinations = {}
for path, dest, kind, row in entries:
    full_dest = dest if dest.startswith(prefix + '/') else prefix + '/' + dest
    if 'private-library-transfer' in path.parts or 'private-library-transfer' in PurePosixPath(dest).parts:
        excluded.append({'path': dest, 'reason': 'private transfer descriptor included'})
    if path.suffix.lower() in {'.mp4','.webm','.mov','.mp3','.wav','.m4a','.ogg','.html','.htm','.mhtml'}:
        excluded.append({'path': dest, 'reason': 'full excluded media extension'})
    if full_dest in leaves:
        excluded.append({'path': dest, 'reason': 'baseline path would be overwritten'})
    if full_dest in destinations and destinations[full_dest] != row['sha256']:
        excluded.append({'path': dest, 'reason': 'destination collision with different bytes'})
    destinations[full_dest] = row['sha256']; published.add(full_dest)
    raw = path.read_bytes(); current = metrics(raw)
    if any(current[k] != row[k] for k in ['bytes','sha256','git_blob_sha']):
        manifest_byte_drift.append({'path': dest, 'source_kind': kind, 'expected_sha256': row['sha256'], 'current_sha256': current['sha256']})
    if path.suffix.lower() in {'.json','.md','.txt','.py','.js','.svg'}:
        scanned_text += 1; text = raw.decode('utf-8')
        for label, pattern in secret_patterns.items():
            count = len(pattern.findall(text))
            if count: credential_hits.append({'path': dest, 'pattern': label, 'match_count': count, 'secret_values_printed': False})
# Tools automatically added by final assembly also undergo the same credential check.
for name in ['archive-uploader-runtime.js','archive-prepare-delivery.py','archive-readback-bodies.py','archive-verify-remote.py']:
    text = (ROOT / name).read_text(); scanned_text += 1
    for label, pattern in secret_patterns.items():
        count = len(pattern.findall(text))
        if count: credential_hits.append({'path': name, 'pattern': label, 'match_count': count, 'secret_values_printed': False})

baseline_binding_errors = []
for row in bindings['baseline_source_bindings']:
    try:
        m = metrics(Path(row['original_local_path']).read_bytes())
        assert all(m[k] == row[k] for k in m)
        assert row['source_commit'] == config['base_commit']
        for alias in row['all_exact_baseline_alias_paths']:
            assert leaves[alias]['sha'] == row['git_blob_sha']
    except Exception as exc:
        baseline_binding_errors.append({'path': row['original_local_path'], 'error': str(exc)})

# Independent gallery resolution against its explicit proposed aliases.
for row in gallery['proposed_selected_aliases']:
    published.add(prefix + '/' + row['selected_path'])
for path in list(published):
    p = PurePosixPath(path)
    for parent in p.parents:
        if str(parent) != '.': published.add(str(parent))
link_results = []; gallery_sources = []
planned_finalizer_targets = {prefix + '/provenance/hash-resolver.json'}
for page in gallery['public_files']:
    rel = Path(page['source_path']).relative_to(ROOT)
    content = snapshot(str(rel)); gallery_sources.append({'archive_path': page['archive_path'], 'sha256': metrics(content.encode())['sha256']})
    for target in re.findall(r'\]\(([^)]+)\)', content):
        target = target.split(' "')[0]
        scheme = urlsplit(target).scheme
        if scheme:
            ok = scheme in {'http','https','mailto'}; resolved = target
        elif target.startswith('#'):
            ok = True; resolved = target
        else:
            resolved = posixpath.normpath(posixpath.join(prefix, posixpath.dirname(page['archive_path']), unquote(target.split('#')[0])))
            ok = resolved in published
        link_results.append({'page': page['archive_path'], 'target': target, 'resolved': resolved,
                             'pass': ok, 'planned_finalizer_target': resolved in planned_finalizer_targets})

# Required identity counts are structural; unfrozen pending rows are not failures.
required = [sheet if isinstance(sheet, str) else sheet['id']
            for family in requirements['families'] for sheet in family['required_sheets']]
assert len(required) == len(set(required)) == 81
assert len(requirements['families']) == 60
assert set(config['render_deliverable_ids']) == set(required)

native_cache_unbound = []
for path in sorted((ROOT.parent / 'generated_images').glob('*.png')):
    m = metrics(path.read_bytes())
    if m['sha256'] not in actual_hashes and m['git_blob_sha'] not in baseline_blobs:
        native_cache_unbound.append({'path': str(path), **m})

aggregate_paths = ['reviews/cast-critic-final-46-sheet-acceptance.json', 'reviews/cast-review-evidence-integrity.json', 'reviews/cast-review-evidence-integrity-42-selected.json']
public_sources = {str(Path(r['source_path']).resolve()) for r in public['public_files']}
missing_aggregates = [p for p in aggregate_paths if str((ROOT / p).resolve()) not in public_sources]

report = {
    'schema_version': 1, 'reviewer': '/root/missing_cast_critic', 'independent': True,
    'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'DRAFT_ONLY_PREFLIGHT_NOT_A_FINAL_ARCHIVE_APPROVAL',
    'scope': 'Independent structural, byte-custody, input-order, reference-link and exclusion audit of the named mutable draft snapshots. Pending visual work is not relabeled as an archive failure or approval.',
    'final_archive_gate': {'status': 'NOT_RUN_FINAL_SELECTION_AND_PACKAGE_NOT_FROZEN', 'score': 0, 'publication_approved': False},
    'snapshot_directory': str(OUT), 'inputs': inputs,
    'baseline_reconstruction': baseline_result,
    'required_coverage': {'families': 60, 'sheets': 81, 'unique_required_sheet_ids': 81},
    'draft_snapshot_counts': {'native_originals': len(calls), 'ordered_image_inputs_checked': input_count,
                              'no_image_attempts': len(failure_results), 'prepared_histories': len(capture['prepared_invocation_history']),
                              'gallery_selected': gallery['selected_sheets'], 'working_selected': selection['selected_count'],
                              'proposed_public_files': len(public['public_files']), 'already_staged_paths': len(public['already_staged_files'])},
    'native_original_invocation_prompt_requirements_checks': call_results,
    'no_image_attempt_checks': failure_results, 'invalid_prepared_history_ids': prepared_errors,
    'baseline_source_bindings_checked': len(bindings['baseline_source_bindings']), 'baseline_source_binding_errors': baseline_binding_errors,
    'mutable_draft_source_byte_drift': manifest_byte_drift,
    'excluded_path_media_or_collision_findings': excluded,
    'credential_scan': {'text_files_checked': scanned_text, 'findings': credential_hits, 'secret_values_printed': False},
    'gallery_links_checked': len(link_results),
    'broken_gallery_links': [r for r in link_results if not r['pass'] and not r['planned_finalizer_target']],
    'pending_final_assembly_gallery_links': [r for r in link_results if not r['pass'] and r['planned_finalizer_target']],
    'gallery_link_evidence': str(OUT / 'gallery-link-evidence.json'),
    'unbound_native_cache_at_this_unfrozen_snapshot': native_cache_unbound,
    'missing_explicit_cast_aggregate_documents': missing_aggregates,
    'actionable_findings': findings,
    'final_gate_requirements': [
        'Freeze one exact81-sheet selection covering every required identity in the60 families, after all mandatory visual checks pass strictly above9.',
        'Refresh all generation/source bindings, galleries, public files and native-cache custody to the same settled tool-outcome boundary.',
        'Retain all native attempts, rejected reviews, exact prompts/input order and zero-image failure records with resolvable archived hashes.',
        'Include the final cast acceptance and integrity aggregate records explicitly.',
        'Independently review the exact assembled candidate tree preserving all4955 baseline leaves and all1169 prior PNG paths.',
        'After authorized publication, verify the full remote tree and every added blob body before delivery approval.'
    ],
    'builder_separation': 'missing_archive builds the package; this critic does not modify builder artifacts or publish GitHub objects/refs.'
}
(OUT / 'gallery-link-evidence.json').write_text(json.dumps(link_results, indent=2) + '\n')
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
(ROOT / 'reviews/archive-critic-preflight-draft.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'report': str(OUT / 'report.json'), 'draft_counts': report['draft_snapshot_counts'],
                  'custody_errors': sum(bool(r['errors']) for r in call_results),
                  'no_image_errors': sum(bool(r['errors']) for r in failure_results),
                  'actionable_findings': findings, 'draft_byte_drift_count': len(manifest_byte_drift),
                  'excluded_findings': excluded, 'credential_findings': credential_hits,
                  'broken_gallery_link_count': len(report['broken_gallery_links']),
                  'baseline_binding_errors': baseline_binding_errors,
                  'native_cache_unbound_count': len(native_cache_unbound),
                  'missing_cast_aggregate_documents': missing_aggregates}, indent=2))
