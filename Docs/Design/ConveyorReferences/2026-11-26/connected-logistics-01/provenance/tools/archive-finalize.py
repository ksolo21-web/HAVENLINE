"""Assemble the root-frozen conveyor package without publishing a Git ref.

Run once after the final selection and root public-file list are frozen. Raw
author/review documents remain byte-identical; navigation is derived separately.
"""
from pathlib import Path
import importlib.util
import json
import re

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def source(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def relative(value):
    text = str(value)
    if text.startswith(a.PREFIX + '/'):
        text = text[len(a.PREFIX) + 1:]
    path = Path(text)
    assert not path.is_absolute() and '..' not in path.parts, text
    return str(path)


def main():
    freeze_path = ROOT / 'final-freeze.json'
    freeze = a.read(freeze_path)
    assert freeze['generation_frozen'] is True
    assert freeze['base_commit'] == a.BASE and freeze['base_tree'] == a.BASE_TREE
    assert freeze['branch'] == a.BRANCH and freeze['prefix'] == a.PREFIX
    m = a.read(ROOT / 'archive-generation-snapshot.json')
    assert not m['pending_invocations'] and not m['unresolved_new_input_scope']
    assert m['generated_original_count'] == len(m['actual_invocations'])
    assert freeze['generation_history']['generated_original_pngs'] == len(m['actual_invocations'])
    assert freeze['generation_history']['failed_requests_without_images'] == len(m['failed_no_image_invocations'])
    for name in ['content_review', 'full_upgrade_design_manifest']:
        bound = freeze[name]
        assert a.metrics((ROOT / bound['path']).read_bytes())['sha256'] == bound['sha256']
        assert (a.OUT / bound['path']).read_bytes() == (ROOT / bound['path']).read_bytes()
    assert len(freeze['selected']) == 7
    calls = {row['id']: row for row in m['actual_invocations']}
    actual = {str(path.resolve()) for path in (ROOT / 'renders').glob('*.png')}
    registered = {str(Path(row['output']['source_path']).resolve()) for row in calls.values()}
    assert actual == registered
    if 'generated_original_count' in freeze:
        assert freeze['generated_original_count'] == len(calls)
    selected = []
    for row in freeze['selected']:
        call = calls[row['id']]
        original = call['output']
        assert original['sha256'] == row['sha256']
        assert row['score'] >= 9.5
        dest = relative(row.get('selected_path') or row.get('archive_path') or row['path'])
        assert dest.startswith('selected/') and dest.endswith('.png')
        saved = a.exact_copy(original['source_path'], dest)
        assert all(saved[k] == original[k] for k in ['bytes', 'sha256', 'git_blob_sha'])
        review_value = row.get('review_path') or row.get('review')
        review_source = source(review_value)
        review_dest = relative(str(review_source.relative_to(ROOT)))
        review_data = review_source.read_bytes()
        review_sha = a.metrics(review_data)['sha256']
        assert review_sha == row['review_sha256']
        assert original['sha256'] in review_data.decode('utf-8')
        assert (a.OUT / review_dest).read_bytes() == review_data
        selected.append({'id': row['id'], 'path': saved['path'],
                         'original_path': original['path'],
                         **{k: original[k] for k in ['bytes', 'sha256', 'git_blob_sha', 'dimensions']},
                         'score': row['score'], 'review_path': a.PREFIX + '/' + review_dest,
                         'review_sha256': review_sha})
    assert len({row['path'] for row in selected}) == 7
    imported = []
    for row in freeze['public_files']:
        src = source(row.get('source_path') or row['path'])
        dest = relative(row['archive_path'])
        assert src.suffix.lower() in {'.json', '.md', '.txt', '.py', '.svg'}
        saved = a.exact_copy(src, dest)
        assert saved['sha256'] == row['sha256']
        for key in ['bytes', 'git_blob_sha']:
            if key in row:
                assert saved[key] == row[key]
        imported.append(saved)
    imported.append(a.exact_copy(freeze_path, 'final-freeze.json'))
    m.update(generation_frozen=True, selected=selected,
             selection_freeze_sha256=a.metrics(freeze_path.read_bytes())['sha256'])
    a.write(a.OUT / 'generation-manifest.json', m)
    a.write(a.OUT / 'provenance/root-public-files.json', {'files': imported})

    # Audit/resumption helpers are task-local tools, not game/runtime code.
    for name in ['archive-tools.py', 'archive-register.py', 'archive-stage-research.py',
                 'archive-stage-design.py', 'archive-stage-reviews.py',
                 'archive-finalize.py', 'archive-readback-bodies.py', 'archive-verify-remote.py']:
        a.exact_copy(ROOT / name, 'provenance/tools/' + name)

    mapping_text = '''# Archive paths and exact provenance

This package preserves the original author and critic document bytes. Session
paths inside those frozen records are evidence locators, not live GitHub links.
Use the SHA-256 resolver below to find the exact retained version.

| Session source | Published location |
| --- | --- |
| `renders/<id>.png` | `attempts/<id>.png`; approved versions also have `selected/` aliases |
| `prompts/<id>.txt` | `prompts/<id>.txt`, preserving the saved document bytes |
| Actual invocation prompt argument | `prompts/actual-arguments/<id>.txt`, preserving the exact invoked UTF-8 string |
| `invocations/<id>.json` | `provenance/invocations/<id>--<sha256>.json` |
| `references/existing/` | `research/existing/`, positive manifest selection only |
| `references/new/` | `research/new/`, positive manifest selection only |
| Authored design and retained draft versions | `design/`, as selected by its frozen design manifest |
| Critic reports and native review crops | `reviews/`, with earlier changed versions retained in `history/` subfolders |
| Existing approved Havenline reference art | Exact immutable baseline URLs in the provenance indexes; no duplicate source artwork required |

The saved prompt documents contain one final newline absent from the actual
argument strings. Both exact versions are retained and distinguished in
`generation-manifest.json`. The failed camp r1 tool call produced no image and
is counted separately from the generated originals.

The limited primary-A frames and internal review/layout inputs have explicit
hash-bound allowlists in `generation-inputs/`. Full source videos, full web
pages, broad frame collections and audio are not republished. Their hashes and
source URLs remain provenance records; their absence from this image package
is intentional.

The original requirement/checkpoint and preflight inputs preserve their stage
statuses. Current content acceptance is in the root acceptance document and
the frozen selection; later publication evidence attests a specific immutable
content commit. These are static concepts and design proposals, not runtime,
animation, mechanical fit, capacity, recipe or economy approval.

Review-bound earlier root prose is retained as exact raw UTF-8 `.md.txt` input
snapshots under `provenance/root-document-history/`. Use the canonical root
README and gallery for current navigation; the snapshots preserve earlier
wording without pretending their stage-specific links are the current gallery.

[Exact hash resolver](provenance/hash-resolver.json) ·
[Review evidence index](provenance/review-evidence.json) ·
[Historical preflight inputs](provenance/preflight-inputs/index.json)
'''
    mapping_path = a.OUT / 'ARCHIVE-MAPPING.md'
    assert not mapping_path.exists() or mapping_path.read_text() == mapping_text
    mapping_path.write_text(mapping_text)

    files = []
    for path in sorted(a.OUT.rglob('*')):
        if path.is_file() and path != a.OUT / 'provenance/hash-resolver.json':
            files.append({'path': str(path.relative_to(a.REPO)), **a.metrics(path.read_bytes())})
    by_hash = {}
    for row in files:
        entry = by_hash.setdefault(row['sha256'], {
            **{k: row[k] for k in ['sha256', 'git_blob_sha', 'bytes']}, 'archive_paths': []})
        entry['archive_paths'].append(row['path'])
    baseline_inputs = m['existing_baseline_inputs'] + a.read(ROOT / 'archive-review-snapshot.json')['baseline_source_bindings']
    a.write(a.OUT / 'provenance/hash-resolver.json', {
        'schema_version': 1,
        'scope': 'Exact frozen package bytes and immutable existing reference artwork. The resolver is not self-hashed; the independently checked whole-tree manifest binds it.',
        'archive_files': list(by_hash.values()),
        'existing_baseline_inputs': baseline_inputs,
        'full_source_media_policy': 'Source-video and full-page hashes in research remain provenance-only. Only explicit public manifests and generation-input allowlists authorize media copies.'})
    link_count = 0
    for path in sorted(a.OUT.rglob('*.md')):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            local = target.split('#')[0].split(' "')[0]
            assert (path.parent / local).exists(), 'Broken relative Markdown link: ' + str(path) + ' -> ' + target
            link_count += 1
    result = a.inventory()
    report = {'status': 'ASSEMBLED_FOR_INDEPENDENT_PACKAGE_REVIEW',
              'score': None, 'generated_originals': len(calls), 'selected_studies': 7,
              'failed_no_image_invocations': len(m['failed_no_image_invocations']),
              'root_public_files': len(imported), 'resolved_distinct_package_hashes': len(by_hash),
              'relative_markdown_links': link_count, **result,
              'publication': 'Not yet committed or available through a branch; remote gates remain pending.'}
    a.write(ROOT / 'archive-assembly-report.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
