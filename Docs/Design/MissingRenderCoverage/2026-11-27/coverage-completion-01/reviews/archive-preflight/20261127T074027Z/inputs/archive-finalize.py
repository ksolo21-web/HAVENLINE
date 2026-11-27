"""Assemble only the exact root-frozen missing-render package; never publish refs."""
from pathlib import Path
import importlib.util
import json
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

def source(value):
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()

def relative(value):
    text = str(value)
    if text.startswith(a.PREFIX + '/'):
        text = text[len(a.PREFIX) + 1:]
    path = Path(text)
    assert not path.is_absolute() and '..' not in path.parts, text
    return str(path)

def main():
    assert not (ROOT / 'archive-content-publication.json').exists(), 'Published content is immutable; do not reassemble it'
    freeze_path = ROOT / 'final-freeze.json'
    freeze = a.read(freeze_path)
    assert freeze['generation_frozen'] is True
    assert freeze['base_commit'] == a.BASE and freeze['base_tree'] == a.BASE_TREE
    assert freeze['branch'] == a.BRANCH and freeze['prefix'] == a.PREFIX
    assert freeze.get('baseline_leaves_to_preserve', 4955) == 4955
    manifest = a.read(ROOT / 'archive-generation-snapshot.json')
    assert not manifest['pending_invocations'] and not manifest['unresolved_new_input_scope']
    calls = {row['id']: row for row in manifest['actual_invocations']}
    assert len(calls) == manifest['generated_original_count']
    assert freeze['generation_history']['generated_original_pngs'] == len(calls)
    assert freeze['generation_history']['failed_requests_without_images'] == len(manifest['failed_no_image_invocations'])
    actual = {str(path.resolve()) for path in (ROOT / 'renders').glob('*.png')}
    registered = {str(Path(row['output']['source_path']).resolve()) for row in calls.values()}
    assert actual == registered, 'Unregistered native originals remain'
    baseline_blobs = {row['sha'] for row in a.read(ROOT / 'archive-baseline-tree.json')['tree'] if row['type'] == 'blob'}
    original_hashes = {row['output']['sha256'] for row in calls.values()}
    native_cache_count = 0
    for cached in sorted((ROOT.parent / 'generated_images').glob('*.png')):
        cm = a.metrics(cached.read_bytes())
        assert cm['sha256'] in original_hashes or cm['git_blob_sha'] in baseline_blobs, 'Native cache output still lacks real tool-outcome custody: ' + str(cached)
        native_cache_count += 1
    assert freeze['selected'], 'A selected deliverable is required'
    config = a.read(ROOT / 'archive-package-config.json')
    if config.get('required_selected_studies') is not None:
        assert len(freeze['selected']) == config['required_selected_studies']
    if config.get('render_deliverable_ids'):
        selected_ids = [row.get('deliverable_id', row['id']) for row in freeze['selected']]
        assert len(selected_ids) == len(set(selected_ids))
        assert set(selected_ids) == set(config['render_deliverable_ids']), 'Frozen selection does not cover every required sheet identity'
    if 'required_selected_studies' in freeze:
        assert len(freeze['selected']) == freeze['required_selected_studies']

    # The root manifest is the explicit positive allowlist for public documents,
    # reports and narrow native-art QA evidence. No recursive research copy.
    imported = []
    public_by_source = {}
    destinations = set()
    for row in freeze['public_files']:
        src = source(row.get('source_path') or row['path'])
        dest = relative(row['archive_path'])
        assert src.is_relative_to(ROOT), 'Public file must be within this task root'
        assert 'private-library-transfer' not in src.relative_to(ROOT).parts, 'Private transfer descriptors are never public inputs'
        assert src.suffix.lower() in {'.json', '.md', '.txt', '.py', '.svg', '.png', '.jpg', '.jpeg'}
        assert not dest.startswith(('attempts/', 'selected/', 'prompts/', 'provenance/invocations/'))
        assert dest not in destinations, 'Duplicate explicit destination'
        destinations.add(dest)
        source_metrics = a.metrics(src.read_bytes())
        assert source_metrics['sha256'] == row['sha256'], 'Root-frozen public source changed before assembly'
        for key in ['bytes', 'git_blob_sha']:
            if key in row:
                assert source_metrics[key] == row[key]
        saved = a.exact_copy(src, dest)
        assert saved['sha256'] == row['sha256']
        for key in ['bytes', 'git_blob_sha']:
            if key in row:
                assert saved[key] == row[key]
        imported.append(saved)
        public_by_source[str(src)] = saved

    content_review = freeze['content_review']
    review_source = source(content_review.get('source_path') or content_review['path'])
    assert str(review_source) in public_by_source
    assert a.metrics(review_source.read_bytes())['sha256'] == content_review['sha256']
    assert content_review['score'] > 9.0
    assert str(content_review['status']).startswith('PASS')
    actual_content_review = a.read(review_source)
    assert actual_content_review['score'] == content_review['score']
    assert actual_content_review['status'] == content_review['status']
    assert actual_content_review.get('independent') is True
    assert actual_content_review.get('reviewer') not in {None, '/root', '/root/missing_archive'}
    assert not actual_content_review.get('approval_reopened')
    assert not actual_content_review.get('approval_invalidated')

    selected = []
    for row in freeze['selected']:
        original = calls[row['id']]['output']
        assert original['sha256'] == row['sha256'] and original['bytes'] == row['bytes']
        assert row['score'] > 9.0
        dest = relative(row.get('selected_path') or row.get('archive_path') or row['path'])
        assert dest.startswith('selected/') and dest.endswith('.png')
        saved = a.exact_copy(original['source_path'], dest)
        assert all(saved[k] == original[k] for k in ['bytes', 'sha256', 'git_blob_sha'])
        critic = source(row.get('review_path') or row['review'])
        assert str(critic) in public_by_source, 'Selected review must be explicitly retained'
        critic_bytes = critic.read_bytes()
        assert a.metrics(critic_bytes)['sha256'] == row['review_sha256']
        actual_review = json.loads(critic_bytes)
        assert actual_review.get('independent') is True
        assert actual_review.get('reviewer') not in {None, '/root', '/root/missing_archive'}
        assert str(actual_review.get('status', '')).startswith('PASS')
        assert actual_review.get('score') == row['score']
        assert actual_review.get('all_mandatory_visual_checks_passed') is True
        assert not actual_review.get('mandatory_defects_remaining')
        assert not actual_review.get('approval_reopened')
        assert not actual_review.get('approval_invalidated')
        assert (actual_review.get('actual_full_native_png_inspected') is True or
                actual_review.get('actual_full_png_inspected') is True)
        reviewed_image = actual_review['reviewed_image']
        assert reviewed_image.get('sha256', reviewed_image.get('source_sha256')) == original['sha256']
        assert reviewed_image.get('bytes', reviewed_image.get('source_bytes')) == original['bytes']
        if 'git_blob_sha' in reviewed_image:
            assert reviewed_image['git_blob_sha'] == original['git_blob_sha']
        selected.append({'id': row['id'], 'deliverable_id': row.get('deliverable_id', row['id']),
                         'path': saved['path'], 'original_path': original['path'],
                         **{k: original[k] for k in ['bytes', 'sha256', 'git_blob_sha', 'dimensions']},
                         'score': row['score'], 'review_path': public_by_source[str(critic)]['path'],
                         'review_sha256': row['review_sha256']})
    assert len({row['path'] for row in selected}) == len(selected)
    imported.append(a.exact_copy(freeze_path, 'final-freeze.json'))
    manifest.update(generation_frozen=True, selected=selected,
                    selection_freeze_sha256=a.metrics(freeze_path.read_bytes())['sha256'])
    a.write(a.OUT / 'generation-manifest.json', manifest)
    a.write(a.OUT / 'provenance/root-public-files.json', {'files': imported})

    tools = ['register_render.py', 'register_failed_call.py', 'archive-tools.py', 'archive-register.py',
             'archive-finalize.py', 'archive-readback-bodies.py', 'archive-verify-remote.py',
             'archive-allow-source-crops.py', 'archive-prepare-approved-raider-hands.py',
             'archive-allow-atlas-source-chain.py',
             'archive-allow-generated-reference-crops.py',
             'archive-prepare-approved-gates-open.py',
             'archive-draft-public-files.py',
             'archive-uploader-runtime.js',
             'archive-native-cache-custody.py',
             'archive-build-galleries.py',
             'build_world_render_catalog.py']
    for name in tools:
        a.exact_copy(ROOT / name, 'provenance/tools/' + name)
    mapping = '''# Archive paths and exact provenance

This additive package preserves exact native images and exact author/critic records.
Session paths inside frozen records are provenance locators. The hash resolver
maps those bytes to retained archive paths or immutable baseline source bindings.

| Source | Retained location |
| --- | --- |
| Every native generated PNG | `attempts/<id>.png` |
| Selected approved native PNG | Byte-identical alias under `selected/` |
| Saved prompt document | `prompts/<id>.txt` |
| Exact actual invoked UTF-8 prompt | `prompts/actual-arguments/<id>.txt` |
| Exact invocation record | Versioned under `provenance/invocations/` |
| Requirements/checkpoint versions | `provenance/input-history/` |
| Explicitly frozen author and critic records | Exact public-file manifest locations |
| Existing Havenline source artwork | Immutable baseline commit/blob binding |

Saved prompt documents may add a single final newline; the actual argument is
retained separately. Failed requests without an image have zero generated output.
All produced images, including rejected revisions, remain available. Selection
approval applies to static concept images, not native meshes, rigs, animation,
runtime integration, dimensions, capacities, recipes or game balance.

Public source copies require an explicit individual file allowlist. Full external
videos, full web pages, broad frame collections and audio are not republished.
Earlier stage records remain historical; their words are not new approvals.

[Exact hash resolver](provenance/hash-resolver.json) ·
[Generation and selection manifest](generation-manifest.json) ·
[Root public-file allowlist](provenance/root-public-files.json)
'''
    mapping_path = a.OUT / 'ARCHIVE-MAPPING.md'
    assert not mapping_path.exists() or mapping_path.read_text() == mapping
    mapping_path.write_text(mapping)
    by_hash = {}
    for path in sorted(a.OUT.rglob('*')):
        if not path.is_file() or path == a.OUT / 'provenance/hash-resolver.json':
            continue
        metrics = a.metrics(path.read_bytes())
        row = by_hash.setdefault(metrics['sha256'], {**metrics, 'archive_paths': []})
        row['archive_paths'].append(str(path.relative_to(a.REPO)))
    a.write(a.OUT / 'provenance/hash-resolver.json', {
        'schema_version': 1, 'scope': 'Exact package bytes and immutable preexisting source-art bindings; independently checked full tree binds the resolver itself.',
        'archive_files': list(by_hash.values()), 'existing_baseline_inputs': manifest['existing_baseline_inputs']})
    published_paths = {row['path'] for row in a.read(ROOT / 'archive-baseline-tree.json')['tree']}
    for staged_file in a.OUT.rglob('*'):
        if staged_file.is_file():
            published_paths.add(str(staged_file.relative_to(a.REPO)))
            for directory in staged_file.parents:
                if directory == a.REPO:
                    break
                if directory.is_relative_to(a.REPO):
                    published_paths.add(str(directory.relative_to(a.REPO)))
    link_count = 0
    for path in sorted(a.OUT.rglob('*.md')):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            scheme = re.match(r'^([a-zA-Z][a-zA-Z0-9+.-]*):', target)
            if scheme:
                assert scheme.group(1).lower() in {'http', 'https', 'mailto'}, 'Non-GitHub-resolvable link scheme: ' + target
                continue
            if target.startswith('#'):
                continue
            local = target.split('#')[0].split(' "')[0]
            resolved = (path.parent / unquote(local)).resolve()
            assert resolved.is_relative_to(a.REPO), 'Relative link escapes the published repository: ' + target
            assert str(resolved.relative_to(a.REPO)) in published_paths, 'Broken relative Markdown link: ' + str(path) + ' -> ' + target
            link_count += 1
    result = a.inventory()
    report = {'status': 'ASSEMBLED_FOR_INDEPENDENT_PACKAGE_REVIEW', 'score': None,
              'generated_originals': len(calls), 'selected_studies': len(selected),
              'failed_no_image_invocations': len(manifest['failed_no_image_invocations']),
              'root_public_files': len(imported), 'relative_markdown_links': link_count,
              'native_cached_pngs_bound_to_task_or_baseline': native_cache_count,
              'unbound_native_cache_outputs': [],
              **result, 'publication': 'No branch publication yet; exact-package independent approval remains required.'}
    a.write(ROOT / 'archive-assembly-report.json', report)
    print(json.dumps(report))

if __name__ == '__main__':
    main()
