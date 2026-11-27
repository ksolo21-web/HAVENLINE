"""Propose an explicit source/review file manifest; never publish or freeze it.

Only named task documents and the actual file references reachable from those
documents are proposed. Existing baseline images and already captured native
generation artifacts are bound by exact hash instead of copied again.
"""
from pathlib import Path
from collections import defaultdict, deque
import importlib.util
import json
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
TEXT = {'.json', '.md', '.txt', '.py', '.svg'}
IMAGES = {'.png', '.jpg', '.jpeg'}
cache = {}

def metrics(path):
    path = path.resolve()
    if path not in cache:
        cache[path] = a.metrics(path.read_bytes())
    return cache[path]

baseline_by_blob = defaultdict(list)
for row in a.read(ROOT / 'archive-baseline-tree.json')['tree']:
    if row['type'] == 'blob':
        baseline_by_blob[row['sha']].append(row['path'])
automatic_by_sha = defaultdict(list)
automatic = []
for path in sorted(a.OUT.rglob('*')):
    if path.is_file():
        m = metrics(path)
        archive_path = str(path.relative_to(a.REPO))
        automatic_by_sha[m['sha256']].append(archive_path)
        automatic.append({'archive_path': archive_path, **m})

allowed_sources = {}
for name in ['archive-generation-input-allowlist.json', 'archive-derived-input-allowlist.json']:
    for row in a.read(ROOT / name)['allowed_inputs']:
        path = Path(row['local_path'])
        path = path if path.is_absolute() else ROOT / path
        allowed_sources[path.resolve()] = row['archive_relative_path']

public = {}
public_by_sha = defaultdict(list)
reasons = defaultdict(set)
baseline_bindings = {}
automatic_bindings = {}
proposed_bindings = {}
unresolved = {}
queue = deque()
queued = set()

def propose(path, reason, destination=None, force_public=False, preserve_markdown_navigation=False):
    path = Path(path).resolve()
    opaque_preflight_input = path.is_relative_to(ROOT / 'reviews/archive-preflight') and 'inputs' in path.parts
    if not path.is_file() or path.suffix.lower() not in TEXT | IMAGES:
        return
    if 'private-library-transfer' in path.parts:
        return
    if path.is_relative_to(ROOT / 'reviews/archive-blob-prefetch'):
        return
    m = metrics(path)
    if (path.suffix.lower() in IMAGES or not path.is_relative_to(ROOT)) and m['git_blob_sha'] in baseline_by_blob:
        candidates = sorted(baseline_by_blob[m['git_blob_sha']], key=lambda value: ('/selected/' not in value, len(value), value))
        baseline_bindings[str(path)] = {'original_local_path': str(path), **m,
            'source_commit': a.BASE, 'repository_path': candidates[0],
            'all_exact_baseline_alias_paths': candidates,
            'immutable_url': 'https://github.com/ksolo21-web/HAVENLINE/blob/' + a.BASE + '/' + quote(candidates[0], safe='/'),
            'local_bytes_verified_against_baseline_git_blob': True}
        return
    if m['sha256'] in automatic_by_sha and not force_public:
        automatic_bindings[str(path)] = {'original_local_path': str(path), **m,
                                        'archive_paths': automatic_by_sha[m['sha256']]}
        if path.suffix.lower() == '.json' and path.is_relative_to(ROOT) and path not in queued and not opaque_preflight_input:
            queue.append(path)
            queued.add(path)
        return
    if m['sha256'] in public_by_sha and not force_public:
        proposed_bindings[str(path)] = {'original_local_path': str(path), **m,
            'proposed_archive_paths': [a.PREFIX + '/' + name for name in public_by_sha[m['sha256']]],
            'publication_status': 'Draft only; these exact aliases have not been staged or published by this helper.'}
        return
    if not path.is_relative_to(ROOT):
        unresolved[str(path)] = {'path': str(path), **m, 'reason': 'Referenced external local file is not an exact baseline or current-task artifact; no copy proposed.'}
        return
    rel = path.relative_to(ROOT)
    if rel.parts[0] in {'archive-repo', 'renders', 'invocations', 'prompts', 'archive-exact-invoked-prompts'}:
        unresolved[str(path)] = {'path': str(path), **m, 'reason': 'Expected automatic capture has not yet staged these exact bytes; rerun registration before final freeze.'}
        return
    if destination is None:
        if path in allowed_sources:
            destination = allowed_sources[path]
        elif rel.parts[0] == 'archive-review-snapshots':
            destination = 'provenance/review-history/' + path.name
        elif rel.parts[0] == 'archive-preparation-reports':
            destination = 'provenance/preparation-reports/' + path.name
        elif rel.parts[0] == 'archive-prepared-invocation-snapshots':
            unresolved[str(path)] = {'path': str(path), **m, 'reason': 'Prepared record awaits automatic history capture.'}
            return
        elif rel.parts[0].startswith('archive-'):
            destination = 'provenance/archive-records/' + path.name
        else:
            destination = str(rel)
    # Historical Markdown is preserved as exact text so its original relative
    # links are not misrepresented as navigation within this new package.
    if path.suffix.lower() == '.md' and not preserve_markdown_navigation:
        destination += '.txt'
    assert not destination.startswith(('attempts/', 'selected/', 'prompts/', 'provenance/invocations/'))
    assert destination not in public or public[destination]['source_path'] == str(path)
    public[destination] = {'source_path': str(path), 'archive_path': destination, **m}
    if destination not in public_by_sha[m['sha256']]:
        public_by_sha[m['sha256']].append(destination)
    reasons[destination].add(reason)
    if path.suffix.lower() == '.json' and path not in queued and not opaque_preflight_input:
        queue.append(path)
        queued.add(path)

root_documents = [
    'requirements.json', 'selection-working.json', 'root-visual-selection-verification.json',
    'world-render-catalog.json', 'atlas-animal-render-catalog.json',
    'atlas-raider-render-catalog.json', 'archive-source-authority.json',
    'archive-fresh-remote-baseline.json', 'archive-baseline-tree.json',
    'archive-baseline-verification.json', 'archive-package-config.json',
    'archive-review-snapshot-index.json', 'CHECKPOINT.md',
    'source-records/current-AGENTS.md', 'source-records/HAVENLINE_BUILD_PLAN_V2.md',
    'source-records/ONE_CAMP_DESIGN.md', 'source-records/REFERENCE_STYLE_LOCK.json',
    'audit/world/root-catalog-approval.json', 'audit/world/source-equipment-coverage.json',
    'audit/world/inspected-input-provenance-v1-superseded.json', 'audit/world/source-selected-status.json',
    'audit/world/board-asset-census.json', 'audit/world/source-renderarchive-readme.md',
    'audit/world/source-stations-catalog.json', 'audit/world/build_world_audit_v2.py',
    'audit/world/world-gap-matrix.json', 'audit/world/world-gap-matrix-v1-superseded.json',
    'audit/world/inspected-input-provenance.json', 'audit/world/source-T05-frozen-scope.md',
    'audit/world/source-image-index.json', 'audit/world/world-gap-audit.md',
    'audit/world/world-gap-audit-v1-superseded.md', 'audit/world/source-asset-manifest.json',
    'audit/cast/source-npc-catalog.json', 'audit/cast/source-selected-status.json',
    'audit/cast/cast-coverage-matrix-v1-prior-roster-checkpoint.json',
    'audit/cast/cast-coverage-matrix-v1-prior-roster-checkpoint.md',
    'audit/cast/cast-coverage-matrix.json', 'audit/cast/atlas-cast-census-v2.json',
    'audit/cast/source-image-index.json', 'audit/cast/prior-selected-provenance.json',
    'audit/cast/local-recovered-image-matches.json', 'audit/cast/audit-integrity-check.json',
    'audit/cast/source-render-archive-readme.md', 'audit/cast/atlas-cast-census-v2.md',
    'audit/cast/cast-coverage-matrix.md', 'audit/cast/source-reference-register.json',
    'reviews/write_male01_r1_reviews.py', 'reviews/cast_review_utils.py',
    'reviews/write_male01_r2_reviews.py', 'reviews/write_world_review.py',
    'reviews/write_defense_world_reviews.py',
    'reviews/cast-critic-final-46-sheet-acceptance.json',
    'reviews/cast-review-evidence-integrity.json',
    'reviews/cast-review-evidence-integrity-42-selected.json',
    'reviews/archive-critic-preflight-draft.json',
    'reviews/archive_selected_integrity.py',
    'reviews/archive_package_integrity.py',
    'reviews/archive_prefetch_blobs.py',
    'reviews/archive-immutable-blob-prefetch-proof.json',
    'reviews/archive-critic-readback.py',
    'reviews/archive-selected-integrity-final-81.json',
    'reviews/critic-selected-world-evidence-integrity.json',
    'reviews/verify_selected_world_integrity.py',
    'reviews/selected-world-acceptance.md',
    'reviews/world-image-gate-checkpoint.json',
    'reviews/archive-selected-integrity-79-draft-v2.json',
    'reviews/archive-selected-integrity-parser-retest-note.json',
    'reviews/archive-selected-integrity-79-draft.json',
    'reviews/evidence/locked-raider-dorsal-hand-crops.json']
custody_path = ROOT / 'archive-native-cache-custody-working.json'
if custody_path.exists() and a.read(custody_path)['status'] == 'PASS_CURRENT_NATIVE_CACHE_BINDINGS':
    root_documents.append(custody_path.name)
for name in root_documents:
    path = ROOT / name
    if path.exists():
        propose(path, 'Explicit current task source, requirement, audit, or review-process record', force_public=True)
for path in sorted((ROOT / 'reviews').glob('critic-*.json')):
    propose(path, 'Exact completed independent selected-or-rejected review; status remains unchanged', force_public=True)
for path in sorted((ROOT / 'archive-review-snapshots').glob('*.json')):
    name = path.name.split('--')[0] + '.json'
    canonical = ROOT / 'reviews' / name
    if not canonical.exists() or metrics(path)['sha256'] != metrics(canonical)['sha256']:
        propose(path, 'Earlier exact review version retained as history')
for path in sorted((ROOT / 'archive-preparation-reports').glob('*.json')):
    propose(path, 'Exact authorized preparation report; not proof of generation')
for path in sorted((ROOT / 'reviews/builder-decisions').glob('*.json')):
    propose(path, 'Explicit builder decision retained separately from independent acceptance')
for path in sorted((ROOT / 'root-refinements').glob('*.json')):
    propose(path, 'Exact original preparation retained before root refined the actual invocation')
for path in sorted((ROOT / 'reviews/checkpoint-history').glob('*.json')):
    propose(path, 'Exact earlier task review checkpoint retained as history')
authored_guide_index = ROOT / 'author-guides/index.json'
if authored_guide_index.exists():
    authored_guides = a.read(authored_guide_index)
    propose(authored_guide_index, 'Explicit inventory of author-created guide revisions, separate from recovered sources and final art', force_public=True)
    for guide in authored_guides['guides']:
        for row in guide['files']:
            path = Path(row['source_path'])
            assert metrics(path)['sha256'] == row['sha256']
            propose(path, 'Exact author-created guide artifact; preserve each revision and its source code',
                    destination=row['archive_path'], force_public=True)
gallery_manifest_path = ROOT / 'gallery-drafts/gallery-manifest.json'
if gallery_manifest_path.exists():
    gallery_manifest = a.read(gallery_manifest_path)
    for row in gallery_manifest['public_files']:
        path = Path(row['source_path'])
        assert metrics(path)['sha256'] == row['sha256']
        propose(path, 'Newly authored category gallery or complete native/invocation/source index',
                destination=row['archive_path'], force_public=True, preserve_markdown_navigation=True)
    propose(gallery_manifest_path, 'Exact gallery build and proposed stable selected-alias bindings',
            destination='provenance/gallery-build.json')
for path in allowed_sources:
    propose(path, 'Explicit generation input allowlist; preserve original bytes and declared alias')

# Build an index of individual derivation records without copying the directory.
# A record is proposed only when a selected report actually references its crop.
derivation_index = defaultdict(list)
evidence_jsons = list((ROOT / 'reviews/evidence').glob('*.json'))
evidence_jsons += list((ROOT / 'audit/cast/atlas-evidence').glob('*.json'))

def strings(value):
    if isinstance(value, dict):
        # A dated preflight record binds its preserved snapshot, not the later
        # mutable file at source_path. Keep its exact raw inputs as opaque audit
        # evidence rather than recursively reinterpreting old draft manifests.
        skipped = set()
        if 'snapshot_path' in value and 'source_path' in value and 'sha256' in value:
            snapshot = Path(value['snapshot_path'])
            assert snapshot.is_file() and metrics(snapshot)['sha256'] == value['sha256']
            if 'bytes' in value:
                assert metrics(snapshot)['bytes'] == value['bytes']
            skipped.add('source_path')
        for key, child in value.items():
            if key in skipped:
                continue
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, str):
        yield value

def local_file(value, referring_path):
    if len(value) > 1024 or '\n' in value or '://' in value:
        return None
    candidate = Path(value)
    if candidate.suffix.lower() not in TEXT | IMAGES:
        return None
    candidates = [candidate] if candidate.is_absolute() else [
        referring_path.parent / candidate, ROOT / candidate, ROOT.parent / candidate,
        ROOT / 'reviews/evidence' / candidate, ROOT / 'audit/cast/atlas-evidence' / candidate,
        ROOT / 'source-records/original-boards' / candidate]
    for path in candidates:
        if path.is_file():
            return path.resolve()
    return None

for path in evidence_jsons:
    for value in strings(a.read(path)):
        image = local_file(value, path)
        if image is not None and image.suffix.lower() in IMAGES and image.is_relative_to(ROOT):
            derivation_index[image].append(path.resolve())

while queue:
    path = queue.popleft()
    for value in strings(a.read(path)):
        referenced = local_file(value, path)
        if referenced is None:
            continue
        propose(referenced, 'Actual file dependency of ' + str(path.relative_to(ROOT)))
        for provenance in derivation_index.get(referenced, []):
            propose(provenance, 'Exact native-crop/comparison provenance for referenced image ' + referenced.name)

for dest, row in public.items():
    row['draft_inclusion_reasons'] = sorted(reasons[dest])
source_mapping = {'schema_version': 1, 'status': 'DRAFT_EXACT_SOURCE_BINDINGS_NO_PUBLICATION',
    'baseline_commit': a.BASE, 'baseline_tree': a.BASE_TREE,
    'baseline_source_bindings': list(baseline_bindings.values()),
    'already_staged_exact_artifact_bindings': list(automatic_bindings.values()),
    'proposed_exact_artifact_bindings': list(proposed_bindings.values()),
    'unresolved_referenced_files': list(unresolved.values()),
    'policy': 'No new baseline binary duplicates. Exact original bytes remain accessible through immutable baseline paths or this task\'s already staged artifact paths.'}
mapping_path = ROOT / 'archive-draft-source-bindings.json'
a.write(mapping_path, source_mapping)
propose(mapping_path, 'Self-contained exact hash mapping for this draft', 'provenance/source-and-artifact-bindings.json')
manifest = a.read(ROOT / 'archive-generation-snapshot.json')
draft = {'schema_version': 1, 'status': 'DRAFT_FOR_ROOT_FINAL_FREEZE_REVIEW',
    'generation_frozen': False, 'branch_publication_authorized_by_this_draft': False,
    'exclusions': ['private-library-transfer/', 'reviews/archive-blob-prefetch/ mutable transfer cache and progress',
                   'Unrelated media', 'Full third-party video/HTML/audio collections',
                   'Unnecessary baseline binary duplicates', 'Unregistered or pending generations'],
    'generation_capture': {'generated_originals': manifest['generated_original_count'],
        'actual_invocations': len(manifest['actual_invocations']),
        'failed_no_image_calls': len(manifest['failed_no_image_invocations']),
        'prepared_records_pending': len(manifest['pending_invocations']),
        'exact_source_input_versions': len(manifest['source_input_snapshots']),
        'already_staged_paths': len(automatic), 'automatic_staging_includes_every_original_and_actual_prompt': True},
    'public_files': sorted(public.values(), key=lambda row: row['archive_path']),
    'already_staged_files': automatic,
    'baseline_source_binding_count': len(baseline_bindings),
    'unresolved_referenced_files': list(unresolved.values()),
    'next_step': 'Root must review and refresh the exact list after generation/review completion, add final gallery/acceptance/content-critic records, freeze exact selected revisions, then obtain independent exact-package approval. This draft does not stage its proposed public_files.'}
a.write(ROOT / 'archive-public-files-draft.json', draft)
print(json.dumps({'status': draft['status'], 'proposed_explicit_public_files': len(public),
    'already_staged_paths': len(automatic), 'generated_originals': manifest['generated_original_count'],
    'baseline_source_bindings': len(baseline_bindings), 'unresolved_referenced_files': len(unresolved),
    'proposed_public_bytes': sum(row['bytes'] for row in public.values()), 'branch_written': False}, indent=2))
