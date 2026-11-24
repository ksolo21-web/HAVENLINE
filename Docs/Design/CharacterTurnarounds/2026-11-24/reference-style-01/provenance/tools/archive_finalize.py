"""Assemble exact frozen character reference artwork; never mutate a remote ref.

This is a session-path archival/resumption helper, not Havenline runtime code.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path('/workspace/scratch/9c51da47f878/havenline-character-style-360')
REPO = ROOT / 'archive-repo'
PREFIX = Path('Docs/Design/CharacterTurnarounds/2026-11-24/reference-style-01')
OUT = REPO / PREFIX
BASE = 'f3f86e7695e7b68e0d16456dde66788e25291d98'
BASE_TREE = '7311e511183ae0a14d25f0a65ff76d0fdf9fdad2'
ACTIVE_REQUIREMENTS_SHA = 'a5253f143633b6b60e99ab527d562a5f33c657f88d772349c366a774becebadf'


def metrics(data):
    return {'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
            'bytes': len(data)}


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


freeze = read_json(ROOT / 'final-freeze.json')
assert freeze['generation_frozen'] is True and freeze['parent_commit'] == BASE
assert freeze['destination'] == str(PREFIX)
assert freeze['required_subject_count'] == 4 and freeze['required_sheet_count'] == 12
assert freeze['required_body_view_count'] == 32 and freeze['required_hand_view_count'] == 16
assert freeze['all_selected_mandatory_checks_passed'] is True
assert freeze['all_cross_sheet_consistency_passed'] is True
assert freeze['requirements']['sha256'] == ACTIVE_REQUIREMENTS_SHA
subprocess.run([sys.executable, str(ROOT / 'archive_scan_inputs.py')], check=True)
subprocess.run([sys.executable, str(ROOT / 'archive_stage_evidence.py')], check=True)
snapshot = read_json(ROOT / 'archive-image-snapshot.json')
qa = read_json(ROOT / 'archive-evidence-snapshot.json')
requirements = read_json(ROOT / 'requirements-v2.json')
status = read_json(ROOT / 'reviews/latest-independent-status.json')
baseline = read_json(ROOT / 'archive-baseline-tree.json')
user_reference = read_json(ROOT / 'archive-user-reference.json')
assert status['requirements_sha256'] == ACTIVE_REQUIREMENTS_SHA
assert status['complete_visual_set'] is True and status['approved_sheet_count'] == 12
assert status['visual_selection_frozen'] is True
assert metrics((ROOT / 'requirements-v2.json').read_bytes())['sha256'] == ACTIVE_REQUIREMENTS_SHA
assert metrics((ROOT / 'reviews/latest-independent-status.json').read_bytes()) == {
    k: freeze['independent_status'][k] for k in ['sha256', 'git_blob_sha', 'bytes']}
assert metrics((ROOT / 'reviews/final-character-set-visual-audit.json').read_bytes()) == {
    k: freeze['final_visual_set_audit'][k] for k in ['sha256', 'git_blob_sha', 'bytes']}

attempts = {x['id']: x for x in snapshot['images']}
frozen_attempts = {x['id']: x for x in freeze['all_generated_attempts']}
assert set(attempts) == set(frozen_attempts)
assert len(attempts) == freeze['generated_png_count']
assert {tuple(x['dimensions']) for x in attempts.values()} == {(1254, 1254)}
for image_id, row in attempts.items():
    bound = frozen_attempts[image_id]
    for key in ['sha256', 'git_blob_sha', 'bytes', 'dimensions', 'prompt_sha256', 'archive_path', 'prompt_archive_path']:
        assert row[key] == bound[key], (image_id, key)
    assert metrics((REPO / row['archive_path']).read_bytes()) == {
        k: row[k] for k in ['sha256', 'git_blob_sha', 'bytes']}
    assert metrics((REPO / row['prompt_archive_path']).read_bytes())['sha256'] == row['prompt_sha256']

selected = freeze['selected']
assert len(selected) == 12 and len({x['series_id'] for x in selected}) == 12
assert {x['series_id'] for x in selected} == {
    s['id'] + '-' + kind for s in requirements['subjects'] for kind in ['cardinal', 'diagonal', 'hands']}
for row in selected:
    source = attempts[row['id']]
    assert row['sha256'] == source['sha256'] and row['all_mandatory_checks_passed'] is True
    assert row['score'] >= 9.5
    target = REPO / row['archive_path']
    assert target.is_relative_to(OUT / 'selected')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((REPO / source['archive_path']).read_bytes())
    assert metrics(target.read_bytes()) == {k: row[k] for k in ['sha256', 'git_blob_sha', 'bytes']}

# Existing exact snapshots are authoritative even if their original source paths advanced.
documents = {}
prior_provenance = OUT / 'document-provenance.json'
if prior_provenance.exists():
    for old in read_json(prior_provenance)['documents']:
        if metrics((OUT / old['archive_path']).read_bytes())['sha256'] == old['archived_sha256']:
            documents[old['archive_path']] = old
for row in read_json(ROOT / 'archive-frozen-inputs.json')['documents']:
    relative = row['archive_relative_path']
    target = OUT / relative
    if metrics(target.read_bytes())['sha256'] != row['sha256']:
        history = Path('evidence/input-history') / (target.stem + '-' + row['sha256'] + target.suffix)
        assert (OUT / history).exists(), row
        relative, target = str(history), OUT / history
    m = metrics(target.read_bytes())
    assert m['sha256'] == row['sha256'] and m['bytes'] == row['bytes'], row
    documents[relative] = {
        'archive_path': relative, 'original_sha256': m['sha256'],
        'archived_sha256': m['sha256'], 'bytes': m['bytes'], 'byte_identical': True,
        'original_locator': row['origin'], 'role': row.get('role', 'Exact frozen original input snapshot.')}


def import_exact(source, relative, role='Exact current-task source document; original locators are retained.'):
    source = Path(source)
    relative = Path(relative)
    data = source.read_bytes()
    text = data.decode('utf-8')
    assert not re.search(r'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|[?&](?:sig|signature|X-Amz-Signature|token)=', text), source
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != data:
        old = target.read_bytes()
        old_metrics = metrics(old)
        history = Path('evidence/input-history') / (target.stem + '-' + old_metrics['sha256'] + target.suffix)
        (OUT / history).parent.mkdir(parents=True, exist_ok=True)
        (OUT / history).write_bytes(old)
        old_record = documents.pop(str(relative), {})
        documents[str(history)] = {
            **old_record, 'archive_path': str(history), 'original_sha256': old_metrics['sha256'],
            'archived_sha256': old_metrics['sha256'], 'bytes': old_metrics['bytes'], 'byte_identical': True,
            'role': 'Earlier exact input version preserved when source metadata advanced.'}
    target.write_bytes(data)
    m = metrics(data)
    documents[str(relative)] = {
        'archive_path': str(relative), 'original_sha256': m['sha256'], 'archived_sha256': m['sha256'],
        'bytes': m['bytes'], 'byte_identical': True, 'original_locator': str(source), 'role': role}


config = read_json(ROOT / 'archive-input-sources.json')
config['expected_required_sheets'] = 12
write_json(ROOT / 'archive-input-sources.json', config)
checkpoint = read_json(ROOT / 'archive-checkpoint.json')
checkpoint.update(stage='ASSEMBLED_FROZEN_CANDIDATE_PENDING_PACKAGE_AND_REMOTE_GATES',
                  milestones_passed=2, milestones_required=4, new_selected_approved=12,
                  generation_frozen=True, final_selection_approved=True,
                  required_total_views=48, required_body_views=32, required_hand_views=16,
                  registered_generated_originals=len(attempts), registered_generated_pngs=len(attempts),
                  next_action='Approve the exact local candidate, publish with a base-head lease, then verify the remote committed tree. Completion receipts are separate additive files.')
write_json(ROOT / 'archive-checkpoint.json', checkpoint)

for name in ['final-freeze.json', 'requirements-v2.json', 'scope-change-01.json',
             'CHARACTER_STYLE_REFERENCE.md', 'root-checkpoint.json', 'archive-requirements.json', 'archive-checkpoint.json']:
    import_exact(ROOT / name, name)
for name in ['generation-index.json', 'reference-inputs.json']:
    import_exact(ROOT / name, Path('provenance/root') / name)
for name in ['archive-input-sources.json', 'archive-evidence-sources.json']:
    import_exact(ROOT / name, Path('provenance/archive') / name)
import_exact(ROOT / 'archive-baseline-verification.json', 'evidence/baseline-verification.json')
import_exact(ROOT / 'archive-user-reference.json', 'inputs/user-style-reference.json')
builder = ROOT / 'builder-characters-2-4'
for path in sorted(builder.glob('*.json')):
    import_exact(path, Path('provenance/character-builder') / path.name)
import_exact(builder / 'identity-notes.md', 'identity/character-2-4-notes.md')
import_exact(builder / 'approved-reference-provenance.json', 'identity/character-2-4-reference-provenance.json')
for path in sorted((builder / 'drafts').glob('*.txt')):
    import_exact(path, Path('provenance/unexecuted-prompt-drafts') / path.name,
                 'Unexecuted draft retained for history. This file is not an actual generation prompt and has zero outputs.')
for row in freeze.get('prepared_not_invoked_prompts', []):
    assert row['generated_image_count'] == 0 and row['id'] not in attempts
    assert metrics(Path(row['local_path']).read_bytes())['sha256'] == row['sha256']
    import_exact(row['local_path'], Path(row['archive_path']).relative_to(PREFIX),
                 'PREPARED_NOT_INVOKED: exact unused prompt, zero generated images.')
for path in sorted((ROOT / 'reviews').glob('*.json')):
    assert 'package' not in path.name and 'remote' not in path.name, 'Add later package/remote receipts only in the evidence child.'
    import_exact(path, Path('reviews') / path.name)
for row in snapshot['images']:
    import_exact(row['local_prompt_path'], Path(row['prompt_archive_path']).relative_to(PREFIX),
                 'Exact prompt text used for this registered generated PNG.')
for row in qa['files']:
    if row['kind'] == 'provenance_json':
        import_exact(OUT / row['archive_relative_path'], row['archive_relative_path'],
                     'Exact QA crop/contact-sheet provenance; not a generated artwork.')
for name in ['register_render.py', 'freeze_characters.py', 'archive_register.py',
             'archive_scan_inputs.py', 'archive_stage_evidence.py', 'archive_finalize.py']:
    import_exact(ROOT / name, Path('provenance/tools') / name,
                 'Session-path audit/resumption helper for static art archival; not runtime code.')
import_exact(builder / 'register_render.py', 'provenance/tools/builder-register-render.py',
             'Session-path builder output registration helper; not runtime code.')

# Durable mappings supplement, never rewrite, the local locators in frozen originals.
image_resolver = {}
for row in snapshot['images']:
    image_resolver.setdefault(row['sha256'], []).append('attempts/' + row['id'] + '.png')
for row in selected:
    image_resolver[row['sha256']].append(str(Path(row['archive_path']).relative_to(PREFIX)))
input_resolver = {user_reference['sha256']: [user_reference['archive_relative_path']]}
assert metrics((OUT / user_reference['archive_relative_path']).read_bytes()) == {
    k: user_reference[k] for k in ['sha256', 'git_blob_sha', 'bytes']}
baseline_entries = baseline['entries']
by_blob = {}
for row in baseline_entries:
    by_blob.setdefault(row['sha'], []).append(row['path'])
reference_records = []
reference_links = {}
for ref_record in freeze['exact_reference_input_records']:
    source = Path(ref_record['path'])
    assert metrics(source.read_bytes()) == {k: ref_record[k] for k in ['sha256', 'git_blob_sha', 'bytes']}
    outputs = read_json(source)['outputs']
    if isinstance(outputs, dict):
        outputs = [{'id': key, 'actual_referenced_image_paths': value} for key, value in outputs.items()]
    for output in outputs:
        portable_inputs = []
        for i, ref in enumerate(output['actual_referenced_image_paths']):
            source_path = Path(ref.get('local_path', ref.get('path')))
            m = metrics(source_path.read_bytes())
            assert m['sha256'] == ref['sha256']
            item = {'order': ref.get('order', i + 1), **m}
            if m['sha256'] in image_resolver:
                item['archive_paths'] = image_resolver[m['sha256']]
            elif m['sha256'] in input_resolver:
                item['archive_paths'] = input_resolver[m['sha256']]
            else:
                paths = sorted(by_blob[m['git_blob_sha']], key=lambda x: ('/selected/' not in x, len(x), x))
                item['url'] = 'https://github.com/ksolo21-web/HAVENLINE/blob/' + BASE + '/' + paths[0]
                reference_links[m['sha256']] = {**m, 'source_commit': BASE,
                    'repository_path': paths[0], 'url': item['url'],
                    'role': 'Existing character identity reference actually used for generation; retained unchanged in the prior archive.'}
            portable_inputs.append(item)
        reference_records.append({'id': output['id'], 'actual_inputs_in_order': portable_inputs})
assert {r['id'] for r in reference_records} == set(attempts)
write_json(OUT / 'reference-links.json', {'schema_version': 1,
    'user_style_input': user_reference,
    'existing_identity_references': list(reference_links.values()),
    'actual_generation_inputs': reference_records,
    'policy': 'Actual generator input order is recorded. Existing source PNGs remain in their immutable prior archive; they are not counted as new renders.'})

raw_reviews = {}
for path in sorted((ROOT / 'reviews').glob('*.json')):
    report = read_json(path)
    for entry in report.get('entries', []):
        if isinstance(entry, dict) and entry.get('sha256'):
            raw_reviews.setdefault(entry['sha256'], []).append({
                'path': 'reviews/' + path.name, 'sha256': metrics(path.read_bytes())['sha256'],
                'status': entry.get('status'), 'score': entry.get('score')})
selected_ids = {x['id'] for x in selected}
generation_rows = {}
for source in freeze['declared_output_indexes']:
    path = Path(source['path'])
    assert metrics(path.read_bytes()) == {k: source[k] for k in ['sha256', 'git_blob_sha', 'bytes']}
    generation_rows.update({x['id']: x for x in read_json(path)['images']})
public_images = []
for row in snapshot['images']:
    original = generation_rows[row['id']]
    public_images.append({**{k: row[k] for k in ['id', 'sha256', 'git_blob_sha', 'bytes', 'dimensions', 'prompt_sha256']},
        'path': 'attempts/' + row['id'] + '.png', 'prompt': 'prompts/' + row['id'] + '.txt',
        'selected_current_v2': row['id'] in selected_ids,
        'source_status': original.get('status'), 'requirement_scope': original.get('requirement_scope'),
        'review_entries': raw_reviews.get(row['sha256'], [])})
write_json(OUT / 'image-index.json', {'schema_version': 2,
    'produced_pngs': len(attempts), 'unique_generated_blobs': len({x['git_blob_sha'] for x in attempts.values()}),
    'generated_original_bytes': sum(x['bytes'] for x in attempts.values()),
    'required_selected_sheets': 12, 'required_body_views': 32, 'required_hand_views': 16,
    'actual_native_dimensions': sorted({tuple(x['dimensions']) for x in attempts.values()}),
    'qa_evidence_files': qa['qa_evidence_files'], 'qa_image_files': qa['qa_image_files'],
    'qa_evidence_generated_render_count': 0, 'user_supplied_input_images': 1,
    'prepared_not_invoked_prompt_count': len(freeze.get('prepared_not_invoked_prompts', [])),
    'prepared_not_invoked_generated_images': 0,
    'alias_policy': 'Selected aliases reuse original PNG bytes. Historical images, QA images and the user input are separate categories.',
    'images': public_images})
public_selected = [{**{k: row[k] for k in ['id', 'series_id', 'subject_id', 'sheet_type', 'sha256', 'git_blob_sha', 'bytes', 'dimensions', 'status', 'score']},
    'path': str(Path(row['archive_path']).relative_to(PREFIX)), 'original': 'attempts/' + row['id'] + '.png',
    'raw_review': 'reviews/' + Path(row['raw_review_path']).name,
    'raw_review_sha256': row['raw_review_sha256']} for row in selected]
write_json(OUT / 'selected-status.json', {'active_requirements_version': 2, 'required_subjects': 4,
    'required_sheets': 12, 'required_body_views': 32, 'required_hand_views': 16,
    'minimum_selected_score': freeze['minimum_selected_score'], 'all_mandatory_static_checks_passed': True,
    'native_mesh_rig_animation_runtime_approval': False, 'selections': public_selected})

resolver = {}
for row in documents.values():
    resolver.setdefault(row['original_sha256'], []).append(row['archive_path'])
for sha, paths in resolver.items():
    for path in paths:
        assert metrics((OUT / path).read_bytes())['sha256'] == sha
for path in (ROOT / 'reviews').glob('*.json'):
    bound = read_json(path).get('requirements_sha256')
    if bound:
        assert bound in resolver, 'Missing original requirements version for ' + str(path)
for row in selected:
    assert row['raw_review_sha256'] in resolver
qa_resolver, locator_resolver = {}, {}
for row in qa['files']:
    qa_resolver.setdefault(row['sha256'], []).append(row['archive_relative_path'])
    locator_resolver.setdefault(row['origin_task_relative_path'], []).append(row['archive_relative_path'])
for row in documents.values():
    source = row.get('original_locator')
    if source and Path(source).is_relative_to(ROOT):
        locator_resolver.setdefault(str(Path(source).relative_to(ROOT)), []).append(row['archive_path'])
for row in snapshot['images']:
    locator_resolver.setdefault(str(Path(row['local_path']).relative_to(ROOT)), []).append('attempts/' + row['id'] + '.png')
write_json(OUT / 'document-provenance.json', {'schema_version': 1,
    'policy': 'Imported prompts, raw reviews and frozen input versions retain exact original bytes. Navigation and completion status are separate derived records.',
    'documents': sorted(documents.values(), key=lambda r: r['archive_path'])})
write_json(OUT / 'review-input-resolver.json', {'schema_version': 2,
    'sha256_to_archive_paths': {k: sorted(set(v)) for k, v in resolver.items()},
    'generated_image_sha256_to_archive_paths': image_resolver,
    'user_input_image_sha256_to_archive_paths': input_resolver,
    'qa_evidence_sha256_to_archive_paths': qa_resolver,
    'original_task_relative_locator_to_archive_paths': {k: sorted(set(v)) for k, v in locator_resolver.items()},
    'qa_original_task_relative_locator_to_archive_paths': {r['origin_task_relative_path']: [r['archive_relative_path']] for r in qa['files']},
    'existing_reference_image_sha256_to_urls': {k: [r['url']] for k, r in reference_links.items()},
    'policy': 'Keep original local locators in frozen documents; resolve exact content hashes and task-relative locations through this separate portable index.'})

rows = []
for subject in requirements['subjects']:
    sid = subject['id']
    label = 'Character ' + sid.split('-')[-1]
    rows.append('| ' + label + ' | [Cardinal views](selected/' + sid + '-cardinal.png) | [Diagonal views](selected/' + sid + '-diagonal.png) | [Spread-finger hands](selected/' + sid + '-hands.png) |')
readme = '''# Havenline — Characters 1–4 in the supplied studio style

**Four characters, 12 independently approved reference sheets: 32 body views and 16 explicit hand closeups.** The final selection follows the user's polished gray studio style and visible, spread-finger direction. Character 1 follows the attached identity and outfit; Characters 2–4 preserve their existing identities, clothing and gear.

## Reviewed gallery

| Character | Front / left / back / right | Four diagonal views | Left / right palms and backs |
| --- | --- | --- | --- |
''' + '\n'.join(rows) + '''

Each body pair supplies eight ordered angles around the character. The hand sheets make all five digits and left/right palm/back construction explicit. Body sheets passed at 9.7/10 and hand sheets at 9.8/10; the separate character comparisons and four-character style comparison also passed. These are static reference images for later modeling and rigging; no native mesh, rig or animation validation is claimed.

The generated images are **1254 × 1254 pixels at their actual native output size**. The original requests specified 2048 × 2048; the returned originals are retained without upscaling or a higher-resolution claim.

## Originals, revisions and exact evidence

All ''' + str(len(attempts)) + ''' generated PNG originals remain available. The 12 selected aliases reuse the exact approved image bytes. Seven earlier images were produced under the original hand specification; they remain historical alongside subsequent repairs. The unused Character 4 diagonal r1 prompt was prepared but never invoked and has zero generated images. QA crops/contact sheets and the supplied reference are catalogued separately from generated renders.

- [All original PNGs and revisions](attempts/), [exact image hashes and dimensions](image-index.json), and [current selection status](selected-status.json)
- [Exact prompts actually used](prompts/) and [prepared but unused request](provenance/prepared-not-invoked/character-4-diagonal-r1.txt)
- [Independent visual findings and repair retests](reviews/) and [final cross-sheet/style audit](reviews/final-character-set-visual-audit.json)
- [QA closeups, comparison sheets and crop provenance](review-evidence/index.json)
- [Current character style standard](CHARACTER_STYLE_REFERENCE.md), [v2 acceptance requirements](requirements-v2.json), and [frozen selection](final-freeze.json)
- [Original user reference](inputs/user-style-reference.jpg), [actual reference inputs and immutable identity links](reference-links.json), and [identity notes](identity/character-2-4-notes.md)
- [Historical v1 requirements and reviews](history/v1/), [scope change](scope-change-01.json), and [builder invocation record](provenance/character-builder/execution-log.json)
- [Byte-identical document provenance](document-provenance.json), [hash and locator resolver](review-input-resolver.json), and [generation records](provenance/)
- [Frozen root checkpoint](root-checkpoint.json), [archive requirements](archive-requirements.json), and [prepublication archive checkpoint](archive-checkpoint.json)
- [Session-path audit/resumption helpers](provenance/tools/) for this static reference archive

## Preservation and delivery status

This package adds only its own directory on the existing art branch. All 2,291 prior repository files, including 628 PNG paths, are protected unchanged. The previous enemy, equipment, companion and character artwork remains in its earlier locations.

Imported requirements, checkpoints and raw reviews preserve the exact stage at which they were written. They may describe archive checks as pending. Publication is verified separately against an immutable content commit; its completion receipt is stored as an additive `delivery-status/summary.json` after remote readback. The generated images and frozen review inputs are not rewritten when delivery status advances.
'''
(OUT / 'README.md').write_text(readme)
(OUT / '.gitattributes').write_text('*.png -filter -diff -merge -text\n*.jpg -filter -diff -merge -text\n*.jpeg -filter -diff -merge -text\n')
subprocess.run(['git', 'add', '--sparse', '--', str(PREFIX)], cwd=REPO, check=True)
raw = subprocess.check_output(['git', 'diff', '--cached', '--name-status', '-z'], cwd=REPO).decode().split('\0')
changes = list(zip(raw[:-1:2], raw[1:-1:2]))
assert all(kind == 'A' and path.startswith(str(PREFIX) + '/') for kind, path in changes), changes
files = [{'path': str(path.relative_to(REPO)), **metrics(path.read_bytes())}
         for path in sorted(OUT.rglob('*')) if path.is_file()]
assert {path for _, path in changes} == {row['path'] for row in files}
tree = subprocess.check_output(['git', 'write-tree'], cwd=REPO).decode().strip()
write_json(ROOT / 'archive-expected-paths.json', {'base_commit': BASE, 'base_tree': BASE_TREE,
    'prefix': str(PREFIX), 'allowed_preexisting_changes': [], 'candidate_tree': tree, 'files': files})
print(json.dumps({'new_package_files': len(files), 'generated_originals': len(attempts),
    'selected_aliases': len(selected), 'qa_images': qa['qa_image_files'], 'qa_files': qa['qa_evidence_files'],
    'preexisting_files_changed': 0, 'candidate_tree': tree,
    'manifest': str(ROOT / 'archive-expected-paths.json')}))
