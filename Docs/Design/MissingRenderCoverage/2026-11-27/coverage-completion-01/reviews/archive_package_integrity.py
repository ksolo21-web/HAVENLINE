"""Independent read-only verification of an assembled frozen Havenline package.

No builder module is imported and no archive file, Git object or ref is written.
The resulting evidence report still requires the independent critic's decision.
"""
from pathlib import Path
from collections import defaultdict
from urllib.parse import unquote
import argparse
import datetime
import hashlib
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'archive-repo'
BASE = 'd70fbfac21a852f99cc46b06b1944faf11ec7901'
BASE_TREE = '18c5641935b9cfaa7c1c82022bdbcbd5ad55ab77'
BRANCH = 'art/missing-renders-2026-11-27'
PREFIX = 'Docs/Design/MissingRenderCoverage/2026-11-27/coverage-completion-01'
OUT = REPO / PREFIX


def metric(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}


def read(path):
    return json.loads(Path(path).read_text())


def tree_hash(rows):
    root = {}
    for row in rows:
        branch = root
        names = row['path'].split('/')
        for name in names[:-1]:
            branch = branch.setdefault(name, {})
        if names[-1] in branch:
            raise ValueError('Duplicate or conflicting Git path: ' + row['path'])
        branch[names[-1]] = (row['mode'], row.get('sha') or row['git_blob_sha'])
    def rec(node):
        payload = bytearray()
        for name, value in sorted(node.items(), key=lambda item: (item[0] + ('/' if isinstance(item[1], dict) else '')).encode()):
            mode, digest = ('40000', rec(value)) if isinstance(value, dict) else value
            payload += mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(digest)
        return hashlib.sha1(b'tree ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
    return rec(root)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='reviews/archive-package-integrity-evidence.json')
    args = parser.parse_args()
    issues, counts = [], defaultdict(int)
    def need(value, message):
        if not value:
            issues.append(message)
    def bind(path):
        p = Path(path)
        return {'path': str(p), **metric(p.read_bytes())}
    freeze = read(ROOT / 'final-freeze.json')
    expected = read(ROOT / 'archive-expected-paths.json')
    baseline = read(ROOT / 'archive-baseline-tree.json')
    capture = read(OUT / 'generation-manifest.json')
    requirements = read(ROOT / 'requirements.json')
    old = {r['path']: r for r in baseline['tree'] if r['type'] != 'tree'}
    manifest_rows = expected['files']
    wanted = {r['path']: r for r in manifest_rows}
    files = {str(p.relative_to(REPO)): p for p in OUT.rglob('*') if p.is_file()}
    need(len(wanted) == len(manifest_rows), 'Duplicate expected file paths')
    need(set(files) == set(wanted), 'Staged paths differ from expected package paths')
    need(len(old) == 4955, 'Baseline leaf count differs from 4,955')
    need(sum(p.lower().endswith('.png') for p in old) == 1169, 'Baseline PNG-path count differs from 1,169')
    need(baseline.get('truncated') is False, 'Baseline tree is truncated or unknown')
    need(tree_hash(old.values()) == BASE_TREE, 'Reconstructed baseline tree differs')
    need(not set(files) & set(old), 'Package overwrites baseline paths')
    need(not any(p == '.github' or p.startswith('.github/') for p in old), 'Baseline unexpectedly contains operational workflow paths')
    need(all(p.startswith(PREFIX + '/') for p in files), 'New path outside dedicated prefix')
    for key, value in [('base_commit', BASE), ('base_tree', BASE_TREE), ('branch', BRANCH), ('prefix', PREFIX)]:
        need(freeze.get(key) == value and expected.get(key) == value, 'Freeze/expected boundary differs: ' + key)
    need(freeze.get('generation_frozen') is True, 'Generation not explicitly frozen')

    observed_metrics = {}
    sensitive = re.compile(rb'(?i)(?:[?&](?:X-Amz-Signature|X-Goog-Signature|sig|signature|access_token|oauth_token|api_key)=[^\s&"<>]{8,}|\bgh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bBearer [A-Za-z0-9._~+/=-]{20,})')
    forbidden = {'.mp4', '.mkv', '.mov', '.webm', '.mp3', '.wav', '.m4a', '.html', '.htm'}
    for path, local in sorted(files.items()):
        data = local.read_bytes()
        observed = metric(data)
        observed_metrics[path] = observed
        need(all(observed.get(k) == wanted[path].get(k) for k in observed), 'Expected metrics differ: ' + path)
        need(wanted[path].get('mode') == '100644' and wanted[path].get('type') == 'blob', 'Unexpected new-file mode/type: ' + path)
        need(not any(part == 'private-library-transfer' for part in Path(path).parts), 'Private transfer path included: ' + path)
        need(local.suffix.lower() not in forbidden, 'Full video/audio/web-page file included: ' + path)
        if local.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            need(not data.startswith(b'version https://git-lfs.github.com/spec/'), 'LFS pointer substituted for image: ' + path)
            with Image.open(local) as im:
                if local.suffix.lower() == '.png':
                    need(im.format == 'PNG' and data.startswith(b'\x89PNG\r\n\x1a\n'), 'Invalid native PNG: ' + path)
                im.verify()
            counts['actual_image_files'] += 1
        else:
            data.decode('utf-8')
            need(sensitive.search(data) is None, 'Potential credential or signed-transfer value: ' + path)
            counts['utf8_text_files'] += 1
            if local.suffix.lower() == '.json':
                json.loads(data)
        counts['package_bytes'] += len(data)
    candidate = tree_hash(list(old.values()) + manifest_rows)
    need(candidate == expected['candidate_tree'], 'Independent complete candidate tree differs')

    required = {sheet for family in requirements['families'] for sheet in family['required_sheets']}
    selected = freeze['selected']
    selected_ids = [r.get('deliverable_id', r['id']) for r in selected]
    need(len(required) == 81 and len(requirements['families']) == 60, 'Unexpected required source scope')
    need(len(selected_ids) == len(set(selected_ids)) == 81 and set(selected_ids) == required, 'Frozen selection does not uniquely cover 81 required sheets')
    need(capture.get('generation_frozen') is True, 'Archived generation manifest not frozen')
    need(capture.get('selection_freeze_sha256') == metric((ROOT / 'final-freeze.json').read_bytes())['sha256'], 'Archived manifest does not bind exact freeze')
    need(not capture.get('pending_invocations') and not capture.get('unresolved_new_input_scope'), 'Pending invocations or unresolved input scope remain')
    calls = {r['id']: r for r in capture['actual_invocations']}
    need(len(calls) == capture['generated_original_count'], 'Actual native invocation count differs')
    capture_selected = {r['deliverable_id']: r for r in capture['selected']}
    need(set(capture_selected) == required, 'Archived selected aliases differ from required set')
    for selected_row in selected:
        rid = selected_row['id']
        deliverable = selected_row.get('deliverable_id', rid)
        output = calls[rid]['output']
        alias = capture_selected[deliverable]
        need(alias['id'] == rid, 'Archived selected render identity differs: ' + deliverable)
        need(all(alias[k] == output[k] == selected_row[k] for k in ['bytes', 'sha256']), 'Selected/native metrics differ: ' + rid)
        need(observed_metrics.get(alias['path']) == {k: output[k] for k in ['bytes', 'sha256', 'git_blob_sha']}, 'Selected alias is not byte-identical: ' + rid)
        report_path = alias['review_path']
        review = read(REPO / report_path)
        need(observed_metrics[report_path]['sha256'] == selected_row['review_sha256'], 'Retained selected review differs: ' + rid)
        need(review.get('independent') is True and review.get('reviewer') not in {None, '/root', '/root/missing_archive'}, 'Review not independent: ' + rid)
        need(str(review.get('status', '')).startswith('PASS') and review.get('score', 0) > 9.0, 'Selected review not above-nine PASS: ' + rid)
        need(review.get('all_mandatory_visual_checks_passed') is True and not review.get('mandatory_defects_remaining'), 'Selected mandatory checks failed: ' + rid)
        need(not review.get('approval_reopened') and not review.get('approval_invalidated'), 'Selected approval reopened: ' + rid)
        need(all(a.get('score', 0) > 9 and str(a.get('status', '')).startswith('PASS') for a in review.get('areas', [])) and bool(review.get('areas')), 'Individual mandatory review area failed: ' + rid)

    for rid, call in calls.items():
        output = call['output']
        need(observed_metrics.get(output['path']) == {k: output[k] for k in ['bytes', 'sha256', 'git_blob_sha']}, 'Native original absent or altered: ' + rid)
        need(metric(Path(output['native_returned_locator']).read_bytes()) == {k: output[k] for k in ['bytes', 'sha256', 'git_blob_sha']}, 'Tool-returned native original differs: ' + rid)
        for key in ['exact_invocation', 'exact_invoked_prompt', 'source_prompt_document', 'requirements']:
            row = call[key]
            need(observed_metrics.get(row['path']) == {k: row[k] for k in ['bytes', 'sha256', 'git_blob_sha']}, 'Invocation/provenance file absent or altered: ' + rid + '/' + key)
        counts['native_originals'] += 1
    for failed in capture['failed_no_image_invocations']:
        need(failed.get('output') is None and failed.get('generated_image_count') == 0, 'No-image failure falsely claims output')
        for key in ['exact_invocation', 'exact_attempted_prompt', 'source_prompt_document', 'requirements', 'exact_original_error_record']:
            row = failed[key]
            need(observed_metrics.get(row['path']) == {k: row[k] for k in ['bytes', 'sha256', 'git_blob_sha']}, 'Failed request evidence absent or altered: ' + failed['id'] + '/' + key)
    need(len(freeze['public_files']) == len({r['archive_path'] for r in freeze['public_files']}), 'Duplicate public-file destinations')
    for row in freeze['public_files']:
        path = row['archive_path']
        path = path if path.startswith(PREFIX + '/') else PREFIX + '/' + path
        need(observed_metrics.get(path, {}).get('sha256') == row['sha256'], 'Frozen public file absent or altered: ' + path)
    review_binding = freeze['content_review']
    content_review = read(review_binding.get('source_path') or review_binding['path'])
    need(metric(Path(review_binding.get('source_path') or review_binding['path']).read_bytes())['sha256'] == review_binding['sha256'], 'Content-gate binding differs')
    need(content_review.get('independent') is True and content_review.get('reviewer') not in {None, '/root', '/root/missing_archive'}, 'Content gate is not independent')
    need(str(content_review.get('status', '')).startswith('PASS') and content_review.get('score', 0) > 9, 'Content gate is not above-nine PASS')

    resolver_path = PREFIX + '/provenance/hash-resolver.json'
    resolver = read(REPO / resolver_path)
    resolved_paths = set()
    for row in resolver['archive_files']:
        for path in row['archive_paths']:
            need(path not in resolved_paths, 'Duplicate hash-resolver path: ' + path)
            resolved_paths.add(path)
            need(observed_metrics.get(path) == {k: row[k] for k in ['bytes', 'sha256', 'git_blob_sha']}, 'Hash-resolver bytes differ: ' + path)
    need(resolved_paths == set(files) - {resolver_path}, 'Hash resolver does not cover exact package minus itself')
    published_paths = set(old) | set(files)
    for path in list(published_paths):
        published_paths.update(str(p) for p in Path(path).parents if str(p) != '.')
    for local in OUT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', local.read_text()):
            scheme = re.match(r'^([a-zA-Z][a-zA-Z0-9+.-]*):', target)
            if scheme:
                need(scheme.group(1).lower() in {'http', 'https', 'mailto'}, 'Unsupported public Markdown URI scheme')
                continue
            if target.startswith('#'):
                continue
            target_path = (local.parent / unquote(target.split('#')[0].split(' "')[0])).resolve()
            need(target_path.is_relative_to(REPO), 'Markdown link escapes repository')
            if target_path.is_relative_to(REPO):
                need(str(target_path.relative_to(REPO)) in published_paths, 'Broken final Markdown target: ' + str(local.relative_to(REPO)) + ' -> ' + target)
            counts['relative_markdown_links'] += 1
    result = {'schema_version': 1, 'reviewer': '/root/missing_cast_critic', 'independent': True,
              'reviewed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'PASS_EXACT_PACKAGE_EVIDENCE_ONLY' if not issues else 'FAIL_EXACT_PACKAGE_EVIDENCE',
              'scope': 'Independent local byte, path, complete-tree, baseline-preservation, review-binding, native-custody, hash-index, link and public-exclusion verification. Does not claim remote publication.',
              'input_bindings': [bind(ROOT / name) for name in ['final-freeze.json', 'archive-expected-paths.json', 'archive-baseline-tree.json', 'requirements.json']],
              'package_generation_binding': bind(OUT / 'generation-manifest.json'),
              'candidate_tree': candidate, 'base_tree': BASE_TREE, 'baseline_files_preserved': len(old),
              'baseline_png_paths_preserved': 1169, 'required_families': 60, 'required_selected_sheets': 81,
              'selected_count': len(selected), 'new_package_paths': len(files),
              'failed_no_image_requests_preserved': len(capture['failed_no_image_invocations']),
              'checks': dict(counts), 'issues': issues, 'remote_publication_verified': False}
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
