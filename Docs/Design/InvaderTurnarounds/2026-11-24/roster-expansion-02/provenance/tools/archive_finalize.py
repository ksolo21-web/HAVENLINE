"""Assemble the frozen authored-concept package; no GitHub ref mutation."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, sys

ROOT = Path('/workspace/scratch/9c51da47f878/havenline-enemy-roster-02')
REPO = ROOT / 'archive-repo'
PREFIX = Path('Docs/Design/InvaderTurnarounds/2026-11-24/roster-expansion-02')
OUT = REPO / PREFIX
BASE = 'bb54c582916b3dbc5d542309f290e5101ab9e218'
BASE_TREE = 'edb050ca01bf19cee9bac69b3922e5fb76fb6946'

def digest(data):
    return {'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
            'bytes': len(data)}

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

freeze_path = ROOT / 'final-freeze.json'
freeze = json.loads(freeze_path.read_text())
assert freeze['generation_frozen'] is True
assert freeze['parent_commit'] == BASE
assert freeze['destination'] == str(PREFIX)
subprocess.run([sys.executable, str(ROOT / 'archive_stage_evidence.py')], check=True)
qa_evidence = json.loads((ROOT / 'archive-evidence-snapshot.json').read_text())
snapshot = json.loads((ROOT / 'archive-image-snapshot.json').read_text())
requirements = json.loads((ROOT / 'requirements.json').read_text())
status = json.loads((ROOT / 'reviews/latest-independent-status.json').read_text())
baseline = json.loads((ROOT / 'archive-baseline-tree.json').read_text())
attempts = {x['id']: x for x in snapshot['images']}
selected = freeze['selected']
supplementary = freeze.get('supplementary', [])
assert len(selected) == 16 and requirements['required_subject_count'] == 8
assert status['approved_required_count'] == 16 and status['all_required_visuals_passed'] is True
assert {x['id'] for x in freeze['all_generated_attempts']} == set(attempts)
assert freeze['generated_png_count'] == len(attempts)
slots = {x.get('asset_id'): x for x in status['required_slots'] if x.get('asset_id')}
documents = {}

def import_exact(source, relative):
    source = Path(source)
    relative = Path(relative)
    data = source.read_bytes()
    value = data.decode('utf-8')
    assert not re.search(r'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|[?&](?:sig|signature|X-Amz-Signature|token)=', value), source
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != data:
        old = target.read_bytes()
        old_sha = digest(old)['sha256']
        history = Path('evidence/input-history') / (target.stem + '-' + old_sha + target.suffix)
        (OUT / history).parent.mkdir(parents=True, exist_ok=True)
        (OUT / history).write_bytes(old)
        documents[str(history)] = {'archive_path': str(history), 'original_sha256': old_sha,
            'archived_sha256': old_sha, 'bytes': len(old), 'byte_identical': True,
            'role': 'Earlier exact task-input version retained when current metadata advanced.'}
    target.write_bytes(data)
    metrics = digest(data)
    documents[str(relative)] = {'archive_path': str(relative), 'original_sha256': metrics['sha256'],
        'archived_sha256': metrics['sha256'], 'bytes': metrics['bytes'], 'byte_identical': True,
        'role': 'Unmodified task document or exact generation prompt; non-secret original evidence locators retained.'}
    return metrics

for row in snapshot['images']:
    data = Path(row['local_path']).read_bytes()
    assert digest(data) == {key: row[key] for key in ['sha256', 'git_blob_sha', 'bytes']}
    target = REPO / row['archive_path']
    assert target.is_relative_to(OUT / 'attempts')
    assert target.read_bytes() == data
    prompt = import_exact(Path(row['local_prompt_path']), Path('prompts') / (row['id'] + '.txt'))
    assert prompt['sha256'] == row['prompt_sha256']

for row in selected + supplementary:
    original = attempts[row['id']]
    for key in ['sha256', 'git_blob_sha', 'bytes']:
        assert row[key] == original[key]
    assert row['score'] >= 9.5 and str(row['status']).startswith('PASS')
    if row in selected:
        reviewed = slots[row['id']]
        assert reviewed['sha256'] == row['sha256'] and reviewed['all_mandatory_checks_passed'] is True
        assert reviewed['score'] == row['score']
    raw = Path(row['raw_review_path'])
    assert digest(raw.read_bytes())['sha256'] == row['raw_review_sha256']
    target = REPO / row['archive_path']
    assert target.is_relative_to(OUT / ('selected' if row in selected else 'supplementary'))
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists() or target.read_bytes() == Path(original['local_path']).read_bytes()
    shutil.copy2(Path(original['local_path']), target)

frozen_inputs = json.loads((ROOT / 'archive-frozen-inputs.json').read_text())
for row in frozen_inputs['documents']:
    target = OUT / row['archive_relative_path']
    assert digest(target.read_bytes())['sha256'] == row['sha256']
    documents[row['archive_relative_path']] = {'archive_path': row['archive_relative_path'],
        'original_sha256': row['sha256'], 'archived_sha256': row['sha256'], 'bytes': row['bytes'],
        'byte_identical': True, 'role': 'Exact earlier review-bound input.'}
for path in sorted((ROOT / 'reviews').glob('*.json')):
    import_exact(path, Path('reviews') / path.name)
for name in ['final-freeze.json', 'requirements.json', 'archive-requirements.json', 'archive-checkpoint.json']:
    import_exact(ROOT / name, Path(name))
for name in ['register_render.py', 'freeze_roster.py', 'archive_register.py', 'archive_scan_inputs.py',
             'archive_stage_evidence.py', 'archive_finalize.py']:
    assert (ROOT / name).exists(), name
    import_exact(ROOT / name, Path('provenance/tools') / name)
for row in qa_evidence['files']:
    if row['kind'] == 'provenance_json':
        documents[row['archive_relative_path']] = {'archive_path': row['archive_relative_path'],
            'original_sha256': row['sha256'], 'archived_sha256': row['sha256'],
            'bytes': row['bytes'], 'byte_identical': True, 'role': 'Exact QA crop/contact provenance input.'}
for source, target in [
    ('generation-index.json', 'inputs/root-generation-index.json'),
    ('animal-builds/generation-index.json', 'inputs/animal-generation-index.json'),
    ('aerial-siege-builds/generation-index.json', 'inputs/aerial-siege-generation-index.json'),
    ('references/style-anchors.json', 'inputs/root-style-anchors.json'),
    ('animal-builds/style-anchors.json', 'inputs/animal-style-anchors.json'),
    ('reference-inputs.json', 'inputs/root-reference-inputs.json'),
    ('references/reference-inputs.json', 'inputs/root-reference-inputs.json'),
    ('animal-builds/reference-inputs.json', 'inputs/animal-reference-inputs.json'),
    ('aerial-siege-builds/reference-inputs.json', 'inputs/aerial-siege-reference-inputs.json'),
    ('aerial-siege-builds/style-anchors.json', 'inputs/aerial-siege-style-anchors.json'),
    ('animal-builds/roster-design-notes.md', 'roster-design-notes.md'),
    ('archive-baseline-verification.json', 'evidence/prior-archive-verification.json')]:
    if (ROOT / source).exists():
        import_exact(ROOT / source, Path(target))
if (ROOT / 'archive-input-corrections.json').exists():
    import_exact(ROOT / 'archive-input-corrections.json', Path('provenance/prompt-record-corrections.json'))

review_results = {}
for path in sorted((ROOT / 'reviews').glob('*.json')):
    data = json.loads(path.read_text())
    for key in ['results', 'items', 'reviews']:
        for item in data.get(key, []) if isinstance(data.get(key), list) else []:
            if isinstance(item, dict) and item.get('id', item.get('asset_id')):
                review_results[item.get('id', item.get('asset_id'))] = (path.name, item)
selected_ids = {x['id'] for x in selected}
supplementary_ids = {x['id'] for x in supplementary}
public_images = []
for row in snapshot['images']:
    item = {key: row[key] for key in ['id', 'sha256', 'git_blob_sha', 'bytes', 'dimensions', 'prompt_sha256']}
    item.update(path='attempts/' + row['id'] + '.png', prompt='prompts/' + row['id'] + '.txt',
        selected_required=row['id'] in selected_ids, selected_supplementary=row['id'] in supplementary_ids)
    if row['id'] in review_results:
        report, result = review_results[row['id']]
        item.update(status=result.get('status'), score=result.get('score'), review='reviews/' + report)
    public_images.append(item)
write_json(OUT / 'image-index.json', {'schema_version': 1, 'authorship': 'Original authored enemy proposals; not newly source-observed enemies.',
    'produced_pngs': len(attempts), 'unique_generated_blobs': len({x['git_blob_sha'] for x in attempts.values()}),
    'required_selected': 16, 'supplementary_selected': len(supplementary),
    'generated_original_bytes': sum(x['bytes'] for x in attempts.values()),
    'qa_evidence_files': qa_evidence['qa_evidence_files'], 'qa_images': qa_evidence['qa_image_files'],
    'qa_evidence_generated_render_count': 0, 'qa_evidence_index': 'review-evidence/index.json',
    'alias_policy': 'Selected aliases reuse exact original PNG blobs; existing style-reference images are linked, not duplicated or counted as new renders.',
    'images': public_images})
public_selected = []
for row in selected + supplementary:
    public_selected.append({**{key: row[key] for key in ['id', 'sha256', 'git_blob_sha', 'bytes', 'status', 'score']},
        'path': str(Path(row['archive_path']).relative_to(PREFIX)),
        'review': 'reviews/' + Path(row['raw_review_path']).name, 'raw_review_sha256': row['raw_review_sha256'],
        'supplementary': row['id'] in supplementary_ids})
write_json(OUT / 'selected-status.json', {'required_subjects': 8, 'required_sheets': 16,
    'supplementary_references': len(supplementary), 'authored_additions': True,
    'source_roster_exhaustiveness_claimed': False, 'selections': public_selected})

# Stable existing reference blobs get portable links without extra copied imagery.
by_blob = {}
for row in baseline['entries']:
    by_blob.setdefault(row['sha'], []).append(row['path'])
prior_originals = json.loads((ROOT / 'archive-prior-originals.json').read_text())['originals']
prior_sha = {x['sha256']: x for x in prior_originals}
reference_links = []
for name in ['references/style-anchors.json', 'animal-builds/style-anchors.json']:
    if not (ROOT / name).exists():
        continue
    anchors = json.loads((ROOT / name).read_text())
    for anchor in anchors:
        blob = anchor.get('git_blob_sha') or prior_sha[anchor['sha256']]['git_blob_sha']
        paths = sorted(by_blob[blob], key=lambda x: ('/selected/' not in x, len(x), x))
        reference_links.append({'sha256': anchor['sha256'], 'git_blob_sha': blob, 'source_commit': BASE,
            'preferred_repository_path': paths[0], 'matching_repository_paths': paths,
            'url': 'https://github.com/ksolo21-web/HAVENLINE/blob/' + BASE + '/' + paths[0],
            'role': 'Existing material/board style anchor, not evidence that this authored enemy exists in the original footage.'})
write_json(OUT / 'reference-links.json', {'schema_version': 1, 'style_anchors': reference_links})

write_json(OUT / 'document-provenance.json', {'schema_version': 1,
    'policy': 'All imported prompts, raw reviews and review-bound inputs are byte-identical. Portable navigation is separate.',
    'documents': list(documents.values())})
resolver = {sha: sorted({x['archive_path'] for x in documents.values() if x['original_sha256'] == sha})
            for sha in sorted({x['original_sha256'] for x in documents.values()})}
for sha, paths in resolver.items():
    for path in paths:
        assert digest((OUT / path).read_bytes())['sha256'] == sha
for path in (ROOT / 'reviews').glob('*.json'):
    data = json.loads(path.read_text())
    bound = data.get('requirements_sha256', data.get('requirements_sha256_at_review_start'))
    if bound:
        assert bound in resolver, 'Missing exact requirements input: ' + str(path)
image_resolver = {}
for row in snapshot['images']:
    image_resolver.setdefault(row['sha256'], []).append('attempts/' + row['id'] + '.png')
for row in selected + supplementary:
    image_resolver[row['sha256']].append(str(Path(row['archive_path']).relative_to(PREFIX)))
external_resolver = {}
for row in prior_originals:
    external_resolver.setdefault(row['sha256'], []).append('https://github.com/ksolo21-web/HAVENLINE/blob/' + BASE + '/' + row['archive_path'])
for row in reference_links:
    external_resolver.setdefault(row['sha256'], []).append(row['url'])
qa_resolver, locator_resolver = {}, {}
for row in qa_evidence['files']:
    qa_resolver.setdefault(row['sha256'], []).append(row['archive_relative_path'])
    locator_resolver.setdefault(row['origin_task_relative_path'], []).append(row['archive_relative_path'])
write_json(OUT / 'review-input-resolver.json', {'schema_version': 1, 'sha256_to_archive_paths': resolver,
    'generated_image_sha256_to_archive_paths': image_resolver,
    'qa_evidence_sha256_to_archive_paths': qa_resolver,
    'qa_original_task_relative_locator_to_archive_paths': locator_resolver,
    'existing_reference_image_sha256_to_urls': {key: sorted(set(value)) for key, value in external_resolver.items()},
    'style_reference_links': 'reference-links.json',
    'policy': 'Frozen inputs keep original locators; use these exact hash-to-path bindings for durable resolution. Diagnostic review crops are identified by the retained source PNG hashes and crop provenance.'})

rows = []
for subject in requirements['subjects']:
    sid = subject['id']
    rows.append('| ' + subject['name'] + ' | ' + subject['role'] + ' | [Turnaround](selected/' + sid + '-turnaround.png) | [Details / static poses](selected/' + sid + '-details.png) |')
readme = '''# Havenline — additional authored enemy concepts

**Eight new enemy proposals, with 16 independently approved static reference sheets.** These are authored additions in the established Havenline visual style. They are not newly observed source enemies or approved runtime canon.

## Reviewed gallery

| Concept | Proposed role | Eight-angle turnaround | Details and static poses |
| --- | --- | --- | --- |
''' + '\n'.join(rows) + '''

## What is preserved

All ''' + str(len(attempts)) + ''' generated PNG originals are retained, including every repair or rejected revision. The 16 selected sheet aliases''' + (' and ' + str(len(supplementary)) + ' supplementary aliases' if supplementary else '') + ''' reuse those exact image blobs. Original prompt text, raw independent reviews and frozen input hashes remain unchanged. Existing style-reference PNGs are linked through provenance rather than duplicated as new renders.

- [All generated originals and revisions](attempts/)
- [Exact image inventory and hashes](image-index.json)
- [Reviewed selection status](selected-status.json)
- [Exact prompts](prompts/) and [independent findings/retests](reviews/)
- [Exact QA closeups, contact sheets and crop provenance](review-evidence/index.json), kept separate from generated-render counts
- [Style reference links](reference-links.json)
- [Authored roster design notes](roster-design-notes.md)
- [Frozen output selection](final-freeze.json) and [creative requirements](requirements.json)
- [Original document provenance](document-provenance.json) and [hash resolver](review-input-resolver.json)
- [Prior 44-original archive verification](evidence/prior-archive-verification.json)
- [Archive requirements](archive-requirements.json) and [prepublication checkpoint](archive-checkpoint.json)
- [Session-path audit and resumption helpers](provenance/tools/) for this static render archive

## Relationship to the earlier renders

The [earlier invader batch](../README.md) and [nine-subject reference expansion](../expansion/README.md) remain intact. All 2,150 pre-existing repository files are preserved; this batch adds only its own directory. The earlier 44 invader originals remain available.

The [existing source coverage matrix](../expansion/coverage-matrix.md) keeps its original limits. YT13 identity and inaccessible footage remain unresolved. These creative additions do not change those findings or establish an exhaustive source roster.

These are static concept boards. They do not certify native meshes, rigs, continuous animation, gameplay behavior or device performance. Imported checkpoint/review inputs retain the exact stage at which they were recorded; final remote integrity is reported separately after publication.
'''
(OUT / 'README.md').write_text(readme)
(OUT / '.gitattributes').write_text('*.png -filter -diff -merge -text\n*.jpg -filter -diff -merge -text\n')
for subject in requirements['subjects']:
    for kind in ['turnaround', 'details']:
        assert (OUT / 'selected' / (subject['id'] + '-' + kind + '.png')).exists()
subprocess.run(['git', 'add', '--sparse', '--', str(PREFIX)], cwd=REPO, check=True)
raw = subprocess.check_output(['git', 'diff', '--cached', '--name-status', '-z'], cwd=REPO).decode().split('\0')
changes = list(zip(raw[:-1:2], raw[1:-1:2]))
assert all(kind == 'A' and path.startswith(str(PREFIX) + '/') for kind, path in changes), changes
files = [{'path': str(path.relative_to(REPO)), **digest(path.read_bytes())} for path in sorted(OUT.rglob('*')) if path.is_file()]
assert {path for _, path in changes} == {row['path'] for row in files}
tree = subprocess.check_output(['git', 'write-tree'], cwd=REPO).decode().strip()
write_json(ROOT / 'archive-expected-paths.json', {'base_commit': BASE, 'base_tree': BASE_TREE,
    'prefix': str(PREFIX), 'allowed_preexisting_changes': [], 'candidate_tree': tree, 'files': files})
print(json.dumps({'new_package_files': len(files), 'generated_originals': len(attempts),
    'selected_aliases': len(selected), 'supplementary_aliases': len(supplementary),
    'preexisting_files_changed': 0, 'candidate_tree': tree,
    'manifest': str(ROOT / 'archive-expected-paths.json')}))
