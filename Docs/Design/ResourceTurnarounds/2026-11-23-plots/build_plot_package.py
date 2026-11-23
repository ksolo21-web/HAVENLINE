"""Package reviewed plot concepts, their source evidence, and the unchanged prior collection."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
from PIL import Image

ROOT = Path('/workspace/scratch/fc906e16b0fb')
SOURCE = ROOT / 'havenline-plot-renders'
REPO = ROOT / 'havenline-resource-art-git'
REL = Path('Docs/Design/ResourceTurnarounds/2026-11-23-plots')
OUT = REPO / REL
DOWNLOAD = ROOT / 'deliverables/Havenline-Storage-Buy-Activation-Plot-Renders'
ZIP = DOWNLOAD.with_suffix('.zip')
PARENT = '8bc2c7577be100fcb5a8fab11517374f71888208'


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def git_sha(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()


def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + '\n')


contract = json.loads((SOURCE / 'acceptance-contract.json').read_text())
addendum = json.loads((SOURCE / 'acceptance-addendum-extra-buy-plots.json').read_text())
assert len(contract['assets']) == 26 and len(addendum['assets']) == 3
contracts = {a['id']: a for a in contract['assets'] + addendum['assets']}
order = list(contracts)
assert len(order) == 29
core_path = SOURCE / 'reviews/final-independent-visual-review.json'
assert sha256(core_path.read_bytes()) == 'f19f0774cd45e136b7d7429ccec0566fe6b798bd5c5a7ce12f7e0d3e8616598b'
core = json.loads(core_path.read_text())
for reference in core['source_reference_inspection_ledger']:
    assert sha256(Path(reference['path']).read_bytes()) == reference['sha256'], reference['path']
final_path = SOURCE / 'reviews/final-combined-29-visual-review.json'
final = json.loads(final_path.read_text())
assets = final['assets']
assert len(assets) == 29 and {a['asset'] for a in assets} == set(order)
combined_by_id = {a['asset']: a for a in assets}
for a in core['assets']:
    b = combined_by_id[a['asset']]
    assert all(a[k] == b[k] for k in ['candidate_path', 'sha256', 'score', 'format', 'panel_count']), a['asset']
assert all(a['score'] > 9.0 and not a['blocking_defects'] for a in assets)
assert all(a['actual_full_sheet_inspected'] for a in assets)
expected_panels = {a: (8 if contracts[a]['format'] == '8_view_turnaround' else {'storage_use_states': 9, 'purchase_activation_states': 6, 'work_zone_states': 2}[a]) for a in order}
for a in assets:
    observed = a.get('panel_count', a.get('view_count'))
    assert observed == expected_panels[a['asset']], (a['asset'], observed)
    if a.get('format'):
        assert a['format'] == contracts[a['asset']]['format']
selected = {a['candidate_path']: a for a in assets}

baseline = json.loads((SOURCE / 'prior-package-preservation-baseline.json').read_text())
assert baseline['commit'] == PARENT and len(baseline['files']) == 136
for f in baseline['files']:
    b = (REPO / f['path']).read_bytes()
    assert sha256(b) == f['sha256'] and git_sha(b) == f['git_blob_sha'], f['path']

receipts = []
for name in ['preservation-image-blob-receipts.json', 'buy-image-blob-receipts.json']:
    d = json.loads((SOURCE / name).read_text())
    receipts.extend(d if isinstance(d, list) else d['blobs'])
by_path = {}
for r in receipts:
    if r['local_path'] in by_path:
        assert by_path[r['local_path']]['blob_sha'] == r['blob_sha']
    by_path[r['local_path']] = r
assert set(selected).issubset(by_path)

candidate_ids = {}
initial_paths = set()


def visit(value, initial=False):
    if isinstance(value, list):
        for x in value:
            visit(x, initial)
    elif isinstance(value, dict):
        path = value.get('candidate_path') or value.get('path') or value.get('local_path')
        asset = value.get('asset') or value.get('id') or value.get('key')
        if isinstance(path, str) and path.endswith('.png') and asset:
            candidate_ids[path] = asset
            if initial:
                initial_paths.add(path)
        for x in value.values():
            if isinstance(x, (dict, list)):
                visit(x, initial)


for folder in ['storage-build', 'buy-build', 'supplement-build']:
    for p in sorted((SOURCE / folder).glob('*results.json')):
        visit(json.loads(p.read_text()), (p.name.startswith('batch-') or folder == 'supplement-build') and 'repair' not in p.name)
for p in sorted((SOURCE / 'reviews').glob('*.json')):
    visit(json.loads(p.read_text()))

OUT.mkdir(parents=True, exist_ok=True)
DOWNLOAD.mkdir(parents=True, exist_ok=True)
(OUT / '.gitattributes').write_text('# Preserve these concept and source-evidence PNGs directly in Git.\n*.png -filter -diff -merge -text\n')
images = []
for path, receipt in sorted(by_path.items()):
    p = Path(path)
    b = p.read_bytes()
    assert sha256(b) == receipt['sha256'] and git_sha(b) == receipt['blob_sha'], path
    if path in selected:
        a = selected[path]
        asset = a['asset']
        assert sha256(b) == a['sha256']
        with Image.open(p) as im:
            assert list(im.size) == a['dimensions']
            im.verify()
        rel = Path('reviewed-concepts') / f"{order.index(asset)+1:02d}-{asset.replace('_', '-')}.png"
        disposition = 'selected-reviewed-concept'
        shutil.copy2(p, DOWNLOAD / rel.name)
    elif p.is_relative_to(SOURCE / 'sources') or p.is_relative_to(SOURCE / 'reviews'):
        asset = receipt.get('id', 'source-or-review-evidence')
        rel = p.relative_to(SOURCE)
        disposition = 'source-or-review-evidence'
    else:
        asset = candidate_ids.get(path, receipt.get('id') or receipt.get('key') or 'candidate')
        role = receipt.get('archive_role', '')
        original = role in ['original_candidate', 'initial-candidate'] or (path in initial_paths and 'repair' not in role)
        stage = 'initial' if original else 'superseded-repairs'
        rel = Path('archived-candidates') / stage / f"{asset.replace('_', '-')}-{p.name}"
        disposition = f'superseded-{stage}-not-current'
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
    images.append({'asset': asset, 'package_path': rel.as_posix(), 'repository_path': (REL / rel).as_posix(),
                   'source_filename': p.name, 'sha256': sha256(b), 'git_blob_sha': receipt['blob_sha'],
                   'bytes': len(b), 'disposition': disposition})

for name in ['acceptance-contract.json', 'acceptance-addendum-extra-buy-plots.json', 'common-prompt.txt', 'prior-package-preservation-baseline.json', 'execution-checkpoint.json', 'build_plot_package.py', 'build_complete_render_kit.py', 'prepare_preservation_uploads.py']:
    if (SOURCE / name).is_file():
        shutil.copy2(SOURCE / name, OUT / name)
for folder in ['sources', 'storage-build', 'buy-build', 'supplement-build', 'reviews']:
    for p in sorted((SOURCE / folder).rglob('*')):
        if not p.is_file() or p.suffix not in ['.json', '.txt', '.py', '.md']:
            continue
        content = p.read_text()
        assert 'data:image/png;base64,' not in content
        target = OUT / p.relative_to(SOURCE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)

index = {
    'title': 'Havenline Storage, Buy and Activation Plot Concepts', 'date_utc': '2026-11-23',
    'sheet_count': 29, 'core_sheet_count': 26, 'additional_buy_sheet_count': 3,
    'turnaround_count': 26, 'turnaround_views': 208,
    'state_plate_count': 3, 'state_panels': 17, 'total_illustrated_panels': 225,
    'prior_resource_sheet_count': 33, 'prior_resource_commit': PARENT, 'prior_files_preserved_unchanged': 136,
    'minimum_concept_review_score': min(a['score'] for a in assets),
    'scope': 'Static concept turnarounds and use-state plates. Ground plot forms follow actual supplied video pixels; unobserved resource storage variants are proposals.',
    'limits': ['No native mesh or exact camera calibration is certified.', 'Reference costs are display examples, not canonical Havenline prices.', 'Illustrated stock amounts do not establish storage capacity or shared inventory behavior.', 'Worker/hand/person-plus/counter glyph action bindings remain unspecified.', 'No runtime or gameplay approval is implied.'],
    'final_review_sha256': sha256(final_path.read_bytes()),
    'core_review_sha256': sha256(core_path.read_bytes()),
    'additive_contract_sha256': sha256((SOURCE / 'acceptance-addendum-extra-buy-plots.json').read_bytes()),
    'sheets': [{**{k: v for k, v in a.items() if k != 'candidate_path'}, 'source_image_filename': Path(a['candidate_path']).name,
                'filename': f"{order.index(a['asset'])+1:02d}-{a['asset'].replace('_', '-')}.png",
                'contract_format': contracts[a['asset']]['format'], 'illustrated_panels': expected_panels[a['asset']],
                'contract_source_status': contracts[a['asset']].get('source_status', 'reference_derived_use_state_concept')}
               for a in sorted(assets, key=lambda a: order.index(a['asset']))]
}
write_json(DOWNLOAD / 'Render-Index.json', index)
shutil.copy2(final_path, DOWNLOAD / 'Independent-Visual-Review.json')
shutil.copy2(core_path, DOWNLOAD / 'Core-26-Independent-Visual-Review.json')
shutil.copy2(SOURCE / 'acceptance-contract.json', DOWNLOAD / 'Acceptance-Contract.json')
shutil.copy2(SOURCE / 'acceptance-addendum-extra-buy-plots.json', DOWNLOAD / 'Acceptance-Addendum-Extra-Buy-Plots.json')
for src, name in [('buy-activation-source-notes.json', 'Buy-Activation-Source-Notes.json'), ('storage-source-notes.json', 'Storage-Source-Notes.json'), ('storage-resource-coverage-proposal.json', 'Storage-Resource-Coverage.json'), ('additional-buy-plot-source-notes.json', 'Additional-Buy-Plot-Source-Notes.json')]:
    shutil.copy2(SOURCE / 'sources' / src, DOWNLOAD / name)
write_json(DOWNLOAD / 'Preservation-Checkpoint.json', {'prior_commit': PARENT, 'prior_package_files_verified_unchanged': 136,
            'prior_resource_sheets': 33, 'new_plot_sheets': 29, 'core26_selection_preserved': True, 'runtime_files_changed': False,
            'new_selected_pngs': [{'filename': a['filename'], 'sha256': a['sha256']} for a in index['sheets']],
            'scope': 'Reviewed image payload checkpoint; remote publication is recorded separately in the repository.'})
(DOWNLOAD / 'Read-Me.txt').write_text('''HAVENLINE — STORAGE, BUY AND ACTIVATION PLOT CONCEPTS

29 PNG sheets: 26 eight-view turnarounds and 3 use-state plates. The turnarounds contain 208 illustrated views; the state plates contain 17 panels (storage 9, buy/activation 6, work zone 2). The original 26-sheet core remains unchanged; bow, person-plus and counter purchase variants are an additive source-observed supplement.

Storage plots use a nearly flush dark rounded rectangle with a thin continuous rim, resource pictogram and stock on the same footprint. The 16 storage sheets contain one empty template and 15 stocked examples. Wood/meat/cash plot types follow visible video references; other resource variants are clearly marked proposals using the same visual vocabulary. Related resource states may reuse a plot shape for art planning; this does not establish shared inventory or capacity rules.

Buy/action plots use four separated rounded corner brackets, a flat action glyph and a reference display cost. Payment activation uses green brackets/fill. A one-time marker can disappear when its installation appears; repeatable axe upgrades return to an available marker. Work zones instead use a segmented unfilled rectangle, white idle and green active, with no cost. No pedestal, freestanding billboard or permanent universal green completion pad is introduced.

All source prices are reference observations, not canonical Havenline economy. Worker, hand, person-plus and counter glyphs retain unspecified exact action bindings. Stock amounts are illustrative. These are AI-generated concept illustrations for art planning and later modeling, not native 3D models, motion captures or implemented gameplay.

Render-Index.json provides portable filenames, image hashes, classifications and review findings. The independent review and source maps preserve exact scope and limitations. The original 33 reviewed resource sheets and their existing packages remain unchanged and are supplied separately.
''')
write_json(OUT / 'delivery-manifest.json', {**index, 'images': images})
write_json(OUT / 'blob-upload-receipts.json', {'repository': 'ksolo21-web/HAVENLINE', 'all_image_hashes_verified': True, 'images': images})
shutil.copy2(DOWNLOAD / 'Render-Index.json', OUT / 'download-render-index.json')
rows = []
for a in sorted(assets, key=lambda a: order.index(a['asset'])):
    rel = next(i['package_path'] for i in images if i['sha256'] == a['sha256'])
    kind = '8-view turnaround' if contracts[a['asset']]['format'] == '8_view_turnaround' else f"{expected_panels[a['asset']]}-panel state plate"
    rows.append(f"| {contracts[a['asset']]['title'].title()} | [{Path(rel).name}]({rel}) | {kind} | {a['score']:.1f}/10 |")
archive_count = sum(i['disposition'].startswith('superseded-') for i in images)
evidence_count = sum(i['disposition'] == 'source-or-review-evidence' for i in images)
(OUT / 'README.md').write_text('''# Havenline storage, buy and activation plots

29 reviewed concept sheets: 16 storage turnarounds, 10 buy/work turnarounds and 3 use-state plates. The 26 turnarounds contain 208 illustrated directions, while the state plates contain 17 panels. The original 26-sheet core is preserved with three source-observed buy glyphs added separately. The [original resources](../2026-11-23/) and [animal/processed expansion](../2026-11-23-expansion/) remain byte-identical: 136 prior files and 33 selected resource sheets.

These are illustrated concepts for art review and later modeling. Unobserved reverse views are reconstructed concepts; no shared native mesh, runtime functionality or production integration approval is claimed.

## Reviewed sheets

| Concept | PNG | Format | Independent concept review |
| --- | --- | --- | --- |
''' + '\n'.join(rows) + f'''

Every selected sheet passed a separate independent critic above 9.0, minimum {index['minimum_concept_review_score']:.1f}/10, with no unresolved mandatory concept defects. The [combined final review](reviews/final-combined-29-visual-review.json) retains exact candidate hashes and findings; the [original core26 review](reviews/final-independent-visual-review.json) remains unchanged.

## Source form and state boundaries

Actual supplied video pixels define the plot forms. Storage uses a nearly ground-flush dark rounded rectangle, thin continuous rim and resource pictogram. The 12 unobserved resource-specific storage variants are proposals; using shared shape language does not assert shared inventory, custody or capacity behavior.

Buy/action markers use four separate rounded corner brackets with grounded icons and source-style cost fields. Idle cash pads are brown; initial construction on snow is gray. Active contribution uses green brackets and progressing green fill. One-shot construction/fishing activation removes its marker; the repeatable axe offer returns for a next tier. The work zone is a segmented unfilled rectangle, white idle and green active, with no cost. Older raised-deck generators and abstract runtime fixtures do not override these direct visual references.

Source display values are examples only. The construction 200 label remains visible during the inspected fill sequence, so the art does not fabricate a decrementing remaining-price counter. Exact worker/hand/person-plus/counter action semantics, canonical economy, storage capacities, contribution rates and game timings remain undefined.

## Evidence and resumption

- [Acceptance contract](acceptance-contract.json)
- [Three-glyph additive contract](acceptance-addendum-extra-buy-plots.json)
- [Buy/activation source map](sources/buy-activation-source-notes.json)
- [Additional buy-glyph source map](sources/additional-buy-plot-source-notes.json)
- [Storage source map](sources/storage-source-notes.json)
- [Resource coverage proposals](sources/storage-resource-coverage-proposal.json)
- [Image manifest](delivery-manifest.json)
- [Independent reviews](reviews/)
- [Source gameplay crops and sequences](sources/)
- [Prior-file preservation baseline](prior-package-preservation-baseline.json)

`reviewed-concepts/` holds the 29 current sheets. {archive_count} superseded images remain under `archived-candidates/`, and {evidence_count} source/review PNGs retain visual evidence. Exact generation and repair prompts/results are under `storage-build/`, `buy-build/` and `supplement-build/`. Original recordings are identified by cryptographic hashes and extraction records; relevant gameplay crops/sequences are preserved here. Stochastic regeneration is not expected to reproduce identical pixels, so the stored PNG bytes and hashes define the reviewed assets.

This commit adds this art/documentation folder only. No active gameplay files are changed.
''')

expected = {a['filename']: a['sha256'] for a in index['sheets']}
assert {p.name: sha256(p.read_bytes()) for p in DOWNLOAD.glob('*.png')} == expected
with zipfile.ZipFile(ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(DOWNLOAD.iterdir()):
        if p.is_file():
            z.write(p, arcname=DOWNLOAD.name + '/' + p.name)
with zipfile.ZipFile(ZIP) as z:
    assert z.testzip() is None
    assert {Path(n).name: sha256(z.read(n)) for n in z.namelist() if n.endswith('.png')} == expected
verification = {'zip_filename': ZIP.name, 'zip_bytes': ZIP.stat().st_size, 'zip_sha256': sha256(ZIP.read_bytes()),
                 'reviewed_pngs': 29, 'turnaround_sheets': 26, 'state_plates': 3, 'illustrated_turnaround_views': 208,
                 'state_panels': 17, 'png_hash_matches': '29/29', 'zip_integrity': 'PASS',
                 'prior_package_files_unchanged': 136, 'prior_resource_sheets_unchanged': 33,
                 'independent_review_sha256': sha256(final_path.read_bytes()), 'runtime_files_changed': False}
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
print(json.dumps({'package_files': len(files), 'unique_pngs': len(images), 'reviewed_pngs': 29,
                  'archived_pngs': archive_count, 'evidence_pngs': evidence_count, 'zip_path': str(ZIP), 'verification': verification}))
