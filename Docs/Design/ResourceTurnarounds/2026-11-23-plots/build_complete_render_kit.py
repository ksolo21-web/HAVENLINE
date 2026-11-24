"""Combine immutable resource and plot downloads, preserving every source member byte."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path('/workspace/scratch/fc906e16b0fb')
SOURCE = ROOT / 'havenline-plot-renders'
BASE = ROOT / 'deliverables/Havenline-Complete-Resource-360-Renders.zip'
PLOTS = ROOT / 'deliverables/Havenline-Storage-Buy-Activation-Plot-Renders.zip'
COMPLETE = ROOT / 'deliverables/Havenline-Resources-and-Plots-Complete-Render-Kit.zip'
BASE_HASH = '38b1fb7527982832ede44da48165746468f5cc8534a7631dfdcdf5327d5361ee'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


base_hash = sha256(BASE.read_bytes())
plot_hash = sha256(PLOTS.read_bytes())
assert base_hash == BASE_HASH
plot_verification = json.loads((SOURCE / 'delivery-verification.json').read_text())
assert plot_hash == plot_verification['zip_sha256']
assert plot_verification['png_hash_matches'] == '29/29'
with zipfile.ZipFile(BASE) as archive:
    base_index_name = next(n for n in archive.namelist() if n.endswith('/Complete-Render-Index.json'))
    base_index = json.loads(archive.read(base_index_name))
with zipfile.ZipFile(PLOTS) as archive:
    plot_index_name = next(n for n in archive.namelist() if n.endswith('/Render-Index.json'))
    plot_index = json.loads(archive.read(plot_index_name))
assert len(base_index['images']) == 33 and len(plot_index['sheets']) == 29
assert plot_index['turnaround_count'] == 26 and plot_index['state_plate_count'] == 3
images = [{'path': 'Resources-33-Sheets/' + a['path'], 'sha256': a['sha256'], 'format': '8_view_turnaround', 'illustrated_panels': 8} for a in base_index['images']]
images.extend({'path': 'Storage-Buy-Activation-Plots-29-Sheets/' + a['filename'], 'sha256': a['sha256'],
               'asset': a['asset'], 'format': a['contract_format'], 'illustrated_panels': a['illustrated_panels']}
              for a in plot_index['sheets'])
expected = {a['path']: a['sha256'] for a in images}
assert len(expected) == 62
assert sum(a['format'] == '8_view_turnaround' for a in images) == 59
assert sum(a['illustrated_panels'] for a in images) == 489
index = {
    'title': 'Havenline Resources and Plots Complete Render Kit', 'sheet_count': 62,
    'resource_sheets': 33, 'plot_sheets': 29, 'eight_view_turnarounds': 59, 'turnaround_views': 472,
    'state_plates': 3, 'state_panels': 17, 'total_illustrated_panels': 489,
    'scope': 'Static reviewed concept illustrations. Exact source/proposal classifications and limits remain in each original index and source map.',
    'limits': ['Three sheets are use-state plates with9,6 and2panels; only59sheets are eight-view turnarounds.', 'No native mesh or runtime gameplay approval.', 'Reference costs and illustrated stock amounts do not establish Havenline economy or storage capacities.'],
    'source_packages': [{'filename': BASE.name, 'sha256': base_hash}, {'filename': PLOTS.name, 'sha256': plot_hash}],
    'images': images,
}
readme = '''HAVENLINE — RESOURCES AND PLOTS COMPLETE RENDER KIT

62 reviewed sheets: 33 resource sheets plus 29 storage/buy/activation plot sheets.

59 sheets are eight-view concept turnarounds (472 illustrated directions). Three are use-state plates with 9, 6 and 2 panels (17 state panels). The complete kit contains 489 illustrated views/state panels.

Resources-33-Sheets contains the unchanged prior collection, including its Base-Resources and Animal-and-Processed-Resources folders, indexes and review/source evidence.

Storage-Buy-Activation-Plots-29-Sheets contains 16 storage turnarounds, 10 buy/work turnarounds and 3 use-state plates, along with the portable index, source maps, acceptance contract and additive glyph contract, independent visual reviews and preservation checkpoint. All 26 core plot sheets remain unchanged; three observed buy-glyph variants form the supplement.

All source package members retain their original bytes. Both separate ZIP downloads and the earlier 13/20-sheet packages remain unchanged.

These are static illustrated concepts for art planning and later modeling. They are not native 3D models or proof of implemented gameplay. Source-backed forms, new proposals, species/drop eligibility, unknown recipe bindings and the plot state distinctions are documented in the existing source maps. Reference display prices and stock amounts do not establish canonical Havenline costs, capacities or timing. Exact worker/hand/person-plus/counter action bindings remain unspecified. No active gameplay files were changed.

Complete-Kit-Index.json lists all 62 image paths, hashes, formats and panel counts. Each source collection retains its detailed index and review evidence.
'''
prefix = 'Havenline-Resources-and-Plots-Complete-Render-Kit/'
source_members = {}
with zipfile.ZipFile(COMPLETE, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
    for path, folder in [(BASE, 'Resources-33-Sheets'), (PLOTS, 'Storage-Buy-Activation-Plots-29-Sheets')]:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith('/'):
                    continue
                relative = name.split('/', 1)[1]
                assert '..' not in Path(relative).parts
                target = folder + '/' + relative
                data = archive.read(name)
                source_members[target] = sha256(data)
                output.writestr(prefix + target, data)
    output.writestr(prefix + 'Read-Me.txt', readme)
    output.writestr(prefix + 'Complete-Kit-Index.json', json.dumps(index, indent=2) + '\n')
with zipfile.ZipFile(COMPLETE) as archive:
    assert archive.testzip() is None
    actual_images = {n[len(prefix):]: sha256(archive.read(n)) for n in archive.namelist() if n.endswith('.png')}
    assert actual_images == expected
    for name, digest in source_members.items():
        assert sha256(archive.read(prefix + name)) == digest
    members = len(archive.namelist())
assert sha256(BASE.read_bytes()) == base_hash and sha256(PLOTS.read_bytes()) == plot_hash
verification = {
    'zip_filename': COMPLETE.name, 'zip_path': str(COMPLETE), 'zip_bytes': COMPLETE.stat().st_size,
    'zip_sha256': sha256(COMPLETE.read_bytes()), 'sheet_count': 62, 'eight_view_turnarounds': 59,
    'turnaround_views': 472, 'state_plates': 3, 'state_panels': 17, 'total_illustrated_panels': 489,
    'png_hash_matches': '62/62', 'all_source_members_preserved': len(source_members), 'files_in_zip': members,
    'zip_integrity': 'PASS', 'prior_33_zip_unchanged': True, 'plot_29_zip_unchanged': True, 'images': images,
}
(SOURCE / 'complete-kit-verification.json').write_text(json.dumps(verification, indent=2) + '\n')
(ROOT / 'deliverables/Havenline-Resources-and-Plots-Complete-Render-Kit-verification.json').write_text(json.dumps(verification, indent=2) + '\n')
repo = ROOT / 'havenline-resource-art-git'
package = repo / 'Docs/Design/ResourceTurnarounds/2026-11-23-plots'
assert package.is_dir()
(package / 'complete-kit-verification.json').write_text(json.dumps(verification, indent=2) + '\n')
(package / 'complete-kit-index.json').write_text(json.dumps(index, indent=2) + '\n')
files = []
for p in sorted(package.rglob('*')):
    if p.is_file():
        b = p.read_bytes()
        files.append({'path': p.relative_to(repo).as_posix(), 'local_path': str(p), 'bytes': len(b),
                      'sha256': sha256(b), 'git_blob_sha': hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest(),
                      'kind': 'image' if p.suffix == '.png' else 'text'})
(SOURCE / 'package-file-manifest.json').write_text(json.dumps({'repository_root': str(repo),
    'package_path': package.relative_to(repo).as_posix(), 'files': files}, indent=2) + '\n')
print(json.dumps({k: v for k, v in verification.items() if k != 'images'}))
