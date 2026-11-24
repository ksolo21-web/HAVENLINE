"""Assemble the independently reviewed art expansion without altering its base set."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
from PIL import Image

ROOT = Path('/workspace/scratch/fc906e16b0fb')
SOURCE = ROOT / 'havenline-resource-expansion'
REPO = ROOT / 'havenline-resource-art-git'
REL = Path('Docs/Design/ResourceTurnarounds/2026-11-23-expansion')
OUT = REPO / REL
DOWNLOAD = ROOT / 'deliverables/Havenline-Animal-and-Processed-Resource-360-Renders'
ZIP = DOWNLOAD.with_suffix('.zip')
PARENT = 'ba6b00e5018b658730b3a127e8c9a7896ce5a3a4'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')


contract = json.loads((SOURCE / 'acceptance-contract.json').read_text())
order = [x['id'] for x in contract['animal_meat_concepts'] + contract['processed_and_byproduct_concepts']]
assert len(order) == len(set(order)) == 20
final_path = SOURCE / 'reviews/final-independent-visual-review.json'
final = json.loads(final_path.read_text())
assets = final['assets']
assert len(assets) == 20 and {x['asset'] for x in assets} == set(order)
assert all(x['score'] > 9.0 and not x['blocking_defects'] for x in assets)
assert all(x['actual_full_sheet_inspected'] and x['view_count'] == 8 for x in assets)
selected = {x['candidate_path']: x for x in assets}

baseline = json.loads((SOURCE / 'prior-package-preservation-baseline.json').read_text())
assert baseline['commit'] == PARENT
for f in baseline['files']:
    b = (REPO / f['path']).read_bytes()
    assert sha256(b) == f['sha256'] and git_sha(b) == f['git_blob_sha'], f['path']

receipts = json.loads((SOURCE / 'all-image-blob-receipts.json').read_text())['blobs']
by_path = {x['local_path']: x for x in receipts}
assert len(by_path) == len(receipts)
assert set(selected).issubset(by_path)
candidate_ids = {}
initial_paths = set()


def visit_records(value, initial=False):
    if isinstance(value, list):
        for x in value:
            visit_records(x, initial)
    elif isinstance(value, dict):
        path = value.get('candidate_path') or value.get('path') or value.get('local_path')
        asset = value.get('asset') or value.get('id') or value.get('key')
        if isinstance(path, str) and path.endswith('.png') and asset:
            candidate_ids[path] = asset
            if initial:
                initial_paths.add(path)
        for x in value.values():
            if isinstance(x, (dict, list)):
                visit_records(x, initial)


for folder in ['animal-build', 'processed-build']:
    for p in sorted((SOURCE / folder).glob('*results.json')):
        visit_records(json.loads(p.read_text()), p.name.startswith('batch-'))
for p in sorted((SOURCE / 'reviews').glob('*.json')):
    visit_records(json.loads(p.read_text()))

OUT.mkdir(parents=True, exist_ok=True)
DOWNLOAD.mkdir(parents=True, exist_ok=True)
(OUT / '.gitattributes').write_text('# Preserve these concept reference PNGs directly in Git.\n*.png -filter -diff -merge -text\n')
images = []
for path, receipt in sorted(by_path.items()):
    p = Path(path)
    data = p.read_bytes()
    assert sha256(data) == receipt['sha256']
    blob = receipt.get('blob_sha') or receipt.get('git_blob_sha')
    assert git_sha(data) == blob
    if path in selected:
        item = selected[path]
        asset = item['asset']
        assert sha256(data) == item['sha256']
        with Image.open(p) as im:
            assert list(im.size) == [1536, 1024]
            im.verify()
        rel = Path('reviewed-concepts') / f"{order.index(asset) + 1:02d}-{asset.replace('_', '-')}.png"
        disposition = 'selected-reviewed-concept'
        shutil.copy2(p, DOWNLOAD / rel.name)
    else:
        asset = candidate_ids.get(path, receipt.get('id') or receipt.get('key') or 'diagnostic-evidence')
        if '/reviews/inspection-crops/' in path:
            rel = Path('reviews/inspection-crops') / p.name
            disposition = 'inspection-evidence'
        else:
            original = receipt.get('archive_role') == 'original_candidate' or (path in initial_paths and 'repair' not in receipt.get('archive_role', ''))
            stage = 'initial' if original else 'superseded-repairs'
            rel = Path('archived-candidates') / stage / f"{asset.replace('_', '-')}-{p.name}"
            disposition = f'superseded-{stage}-not-current'
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
    images.append({'asset': asset, 'package_path': rel.as_posix(), 'repository_path': (REL / rel).as_posix(),
                   'source_filename': p.name, 'sha256': sha256(data), 'git_blob_sha': blob,
                   'bytes': len(data), 'disposition': disposition})

for name in ['acceptance-contract.json', 'source-equipment-coverage.json', 'wildlife-source-provenance.json', 'prior-package-preservation-baseline.json', 'common-prompt.txt', 'build_source_coverage.py', 'build_expansion_package.py', 'merge_blob_receipts.py']:
    if (SOURCE / name).is_file():
        shutil.copy2(SOURCE / name, OUT / name)
for folder in ['animal-build', 'processed-build', 'reviews']:
    for p in sorted((SOURCE / folder).glob('*.json')):
        target = OUT / folder / p.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)

index = {
    'title': 'Havenline Animal and Processed Resource 360 Concepts', 'date_utc': '2026-11-23',
    'new_sheet_count': 20, 'illustrated_view_count': 160, 'sheet_resolution': [1536, 1024],
    'prior_set_sheet_count': 13, 'prior_set_commit': PARENT, 'prior_set_preserved_unchanged': True,
    'concept_review_minimum': min(x['score'] for x in assets),
    'scope': '10 proposed wildlife meat cuts and 10 processed/byproduct concepts; illustrated eight-view sheets, not native shared-mesh renders.',
    'source_boundary': 'Reference-backed outputs and explicit proposals are distinguished in source-equipment-coverage.json. No complete implemented recipe or species-drop registry is claimed.',
    'production_approval': False, 'runtime_changes': False,
    'review_report_sha256': sha256(final_path.read_bytes()),
    'sheets': [{**{k: v for k, v in x.items() if k != 'candidate_path'}, 'source_image_filename': Path(x['candidate_path']).name,
                'filename': f"{order.index(x['asset']) + 1:02d}-{x['asset'].replace('_', '-')}.png"} for x in sorted(assets, key=lambda x: order.index(x['asset']))]
}
write_json(DOWNLOAD / 'Render-Index.json', index)
shutil.copy2(final_path, DOWNLOAD / 'Independent-Visual-Review.json')
shutil.copy2(SOURCE / 'source-equipment-coverage.json', DOWNLOAD / 'Source-Equipment-Coverage.json')
shutil.copy2(SOURCE / 'acceptance-contract.json', DOWNLOAD / 'Acceptance-Contract.json')
if (SOURCE / 'wildlife-source-provenance.json').is_file():
    shutil.copy2(SOURCE / 'wildlife-source-provenance.json', DOWNLOAD / 'Wildlife-Source-Provenance.json')
write_json(DOWNLOAD / 'Preservation-Checkpoint.json', {
    'title': 'Reviewed art payload and preserved base checkpoint',
    'prior_commit': PARENT, 'prior_package_files_verified_unchanged': len(baseline['files']),
    'prior_package_manifest': baseline['files'],
    'new_reviewed_png_count': 20, 'new_illustrated_view_count': 160,
    'new_selected_pngs': [{'filename': a['filename'], 'sha256': a['sha256']} for a in index['sheets']],
    'runtime_files_changed': False,
    'scope': 'Payload and base preservation checkpoint; remote commit receipt is maintained separately in the repository.'
})
minimum = index['concept_review_minimum']
(DOWNLOAD / 'Read-Me.txt').write_text(f'''HAVENLINE — ANIMAL AND PROCESSED RESOURCE CONCEPT TURNAROUNDS

20 new PNG sheets, 1536 × 1024 each, with eight illustrated directions each (160 views total).
The previous 13-sheet resource set is preserved separately, unchanged.

Animal concepts: deer, boar, rabbit, moose, squirrel, wild bear, wild wolf, wild fox, lynx and wolverine meat.
Processed/byproduct concepts: processed meat portion, cooked game meat, dried meat, prepared fish fillet, cooked whole fish, dried fish, timber planks, split firewood, hide and fur.

These are concept references for art planning and later modeling. They are not native 3D assets or proof of implemented recipes. The ten animal cuts do not establish species food eligibility, hunting drops or yields. Companions remain separate. Prepared fish fillet is an explicit proposed intermediate. Equipment mapping, rates, quantities, fuel use and timings remain unspecified where the source evidence does not define them.

The source map distinguishes actual runtime facts, required reference-video design, direct art evidence and new proposals. The previous steel and bread-like cooked-food sheets cover those reused output concepts. No flour, leather, refined fuel, steel plates or charcoal recipe is introduced.

All 20 selected sheets passed a separate independent concept-image review, with minimum score {minimum:.1f}/10 and no unresolved mandatory image defects. This does not grant production integration approval or certify exact shared geometry/camera calibration.

Render-Index.json records exact image hashes and review findings. Independent-Visual-Review.json preserves the final reviewer evidence. Source-Equipment-Coverage.json records equipment/source boundaries. Acceptance-Contract.json preserves the agreed scope.
''')

write_json(OUT / 'delivery-manifest.json', {**index, 'images': images})
write_json(OUT / 'blob-upload-receipts.json', {'repository': 'ksolo21-web/HAVENLINE', 'all_image_hashes_verified': True, 'images': images})
shutil.copy2(DOWNLOAD / 'Render-Index.json', OUT / 'download-render-index.json')

rows = []
for a in sorted(assets, key=lambda x: order.index(x['asset'])):
    path = next(i['package_path'] for i in images if i['sha256'] == a['sha256'])
    rows.append(f"| {a['asset'].replace('_', ' ').title()} | [{Path(path).name}]({path}) | {a['score']:.1f}/10 |")
archive_count = sum(i['disposition'].startswith('superseded-') for i in images)
crop_count = sum(i['disposition'] == 'inspection-evidence' for i in images)
(OUT / 'README.md').write_text('''# Havenline animal and processed resource concepts

20 new concept turnaround sheets, each with eight illustrated directions and a 1536 × 1024 canvas. This expansion adds 10 wildlife meat proposals and 10 processed/byproduct concepts to the [previous 13-sheet set](../2026-11-23/), which is preserved byte-for-byte at its original paths.

These images support art review and later modeling. They are AI-generated illustrations, not native shared-mesh renders, game-ready assets or evidence of implemented recipes. No runtime file is changed and no production integration approval is claimed.

## Reviewed sheets

| Concept | PNG | Independent concept review |
| --- | --- | --- |
''' + '\n'.join(rows) + f'''

Every selected sheet passed the separate critic above 9.0; the minimum score is {minimum:.1f}/10. No mandatory concept-image defects remain. The exact views, findings, source classification and hashes are retained in the [final review](reviews/final-independent-visual-review.json).

## Source and completeness boundaries

The [equipment/source map](source-equipment-coverage.json) distinguishes confirmed runtime behavior, locked reference-video chains, direct source-visible appearances and proposed output forms. Inspected runtime resource kinds are wood, stone, metal and fuel. Fish and wheat processing are required reference-design chains; their exact recipes are not supplied by the current resource registry.

The rectangular processed meat portion follows the visible cooker output. Cooked fish follows the whole-fish-shaped output in the locked reference. PLANK, HIDE and FUR are explicit atlas nouns. Saw-to-plank mapping, split firewood, cooked game meat, dried states and the prepared fish fillet are clearly marked proposals where the exact conversion is not frozen. The prior steel and bread-like cooked-food concepts are reused.

The ten wildlife meat forms do not establish that each species is edible, huntable or an implemented drop. Optional predator cuts retain their unfrozen food eligibility; companion characters remain separate. Quantities, timings, fuel requirements, yields, tier bindings and unshown intermediates remain undefined. This bounded package does not claim to cover an unspecified complete future recipe/drop registry.

## Preserved evidence

The current files are under `reviewed-concepts/`. {archive_count} superseded candidate images are retained under `archived-candidates/`, and {crop_count} inspection crops are retained with the review evidence. The prompts and generation results are in `animal-build/` and `processed-build/`; each repair and review remains separately recorded. Source reference images are identified by exact filenames/hashes instead of being duplicated here.

- [Acceptance contract](acceptance-contract.json)
- [Delivery and image-hash manifest](delivery-manifest.json)
- [Equipment and output source map](source-equipment-coverage.json)
- [Wildlife source provenance](wildlife-source-provenance.json)
- [Independent review records](reviews/)
- [Prior package preservation baseline](prior-package-preservation-baseline.json)

Stochastic generation is not expected to recreate identical pixels. Preserved PNG bytes and SHA256/Git blob hashes define the reviewed candidate. This branch remains separate from active gameplay production.
''')

expected_pngs = {x['filename']: x['sha256'] for x in index['sheets']}
actual_pngs = {p.name: sha256(p.read_bytes()) for p in DOWNLOAD.glob('*.png')}
assert actual_pngs == expected_pngs
with zipfile.ZipFile(ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for p in sorted(DOWNLOAD.iterdir()):
        if p.is_file():
            archive.write(p, arcname=DOWNLOAD.name + '/' + p.name)
with zipfile.ZipFile(ZIP) as archive:
    assert archive.testzip() is None
    archived_pngs = {Path(n).name: sha256(archive.read(n)) for n in archive.namelist() if n.endswith('.png')}
    assert archived_pngs == expected_pngs
verification = {
    'zip_filename': ZIP.name, 'zip_bytes': ZIP.stat().st_size, 'zip_sha256': sha256(ZIP.read_bytes()),
    'reviewed_pngs': 20, 'illustrated_views': 160, 'png_hash_matches': '20/20',
    'zip_integrity': 'PASS', 'prior_package_files_unchanged': len(baseline['files']),
    'independent_review_sha256': sha256(final_path.read_bytes()),
    'production_or_runtime_changes': False
}
write_json(SOURCE / 'delivery-verification.json', verification)
write_json(OUT / 'delivery-verification.json', verification)

files = []
for p in sorted(OUT.rglob('*')):
    if p.is_file():
        b = p.read_bytes()
        files.append({'path': p.relative_to(REPO).as_posix(), 'local_path': str(p), 'bytes': len(b),
                      'sha256': sha256(b), 'git_blob_sha': git_sha(b), 'kind': 'image' if p.suffix == '.png' else 'text'})
write_json(SOURCE / 'package-file-manifest.json', {'repository_root': str(REPO), 'package_path': REL.as_posix(), 'files': files})
assert len([f for f in files if f['kind'] == 'image']) == len(images)
print(json.dumps({'package_files': len(files), 'unique_pngs': len(images), 'reviewed_pngs': 20, 'archived_candidates': archive_count,
                  'inspection_crops': crop_count, 'zip_path': str(ZIP), 'verification': verification}))
