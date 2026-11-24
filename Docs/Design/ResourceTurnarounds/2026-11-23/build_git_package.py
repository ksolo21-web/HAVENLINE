"""Package reviewed resource concepts and their unmodified review provenance."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path('/workspace/scratch/fc906e16b0fb')
SOURCE = ROOT / 'havenline-resource-renders'
REPO = ROOT / 'havenline-resource-art-git'
REL = Path('Docs/Design/ResourceTurnarounds/2026-11-23')
OUT = REPO / REL
SOURCE_COMMIT = '08ec81f4668e5285d09172d790554b2f0ae009a5'
ORDER = ['wood','stone','slate','steel','metal_ore','fuel','meat','fish','wheat','cooked_food','money','cargo','coal']
final = json.loads((SOURCE / 'reviews/final-independent-visual-review.json').read_text())
originals = json.loads((SOURCE / 'original-image-blob-receipts.json').read_text())
receipts = json.loads((SOURCE / 'all-image-blob-receipts.json').read_text())['blobs']
by_local = {x['local_path']: x for x in receipts}
selected = {x['candidate_path']: x for x in final['assets']}
original_by_local = {x['local_path']: x for x in originals}
assert len(final['assets']) == 13 and len(receipts) == 25
assert {a['asset'] for a in final['assets']} == set(ORDER)
assert min(a['score'] for a in final['assets']) > 9.0
assert all(not a['blocking_defects'] for a in final['assets'])
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'.gitattributes').write_text('# Preserve these small concept reference PNGs directly in Git.\n*.png -filter -diff -merge -text\n')

def digest(b):
    return hashlib.sha256(b).hexdigest()

def git_digest(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

images = []
for local, receipt in sorted(by_local.items()):
    p = Path(local)
    b = p.read_bytes()
    assert digest(b) == receipt['sha256']
    assert git_digest(b) == receipt['blob_sha']
    if local in selected:
        a = selected[local]
        assert digest(b) == a['sha256']
        rel = Path('reviewed-concepts') / f"{ORDER.index(a['asset'])+1:02d}-{a['asset'].replace('_','-')}.png"
        disposition = 'selected-reviewed-concept'
        asset = a['asset']
    elif local in original_by_local:
        r = original_by_local[local]
        rel = Path('archived-candidates/initial') / (r['key'].replace('_','-') + '.png')
        disposition = 'superseded-initial-candidate-not-current'
        asset = r['key'][3:]
    else:
        rel = Path('archived-candidates/superseded-repairs') / p.name
        disposition = 'superseded-repair-not-current'
        asset = 'wheat'
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
    images.append({'asset': asset, 'package_path': rel.as_posix(), 'repository_path': (REL / rel).as_posix(), 'source_filename': p.name, 'sha256': digest(b), 'git_blob_sha': receipt['blob_sha'], 'bytes': len(b), 'disposition': disposition})

for name in ['acceptance-contract.json','scope-addendum.json']:
    shutil.copy2(SOURCE / name, OUT / name)
if (SOURCE/'delivery-verification.json').exists():
    shutil.copy2(SOURCE/'delivery-verification.json', OUT/'delivery-verification.json')
download_index=ROOT/'deliverables/Havenline-Resource-360-Renders/Render-Index.json'
if download_index.exists():
    shutil.copy2(download_index,OUT/'download-render-index.json')
for p in sorted(SOURCE.glob('prompts-*.json')):
    (OUT/'prompts').mkdir(exist_ok=True)
    shutil.copy2(p, OUT/'prompts'/p.name)
for folder in ['repairs','reviews']:
    (OUT/folder).mkdir(exist_ok=True)
    for p in sorted((SOURCE/folder).glob('*.json')):
        shutil.copy2(p,OUT/folder/p.name)
shutil.copy2(SOURCE/'build_git_package.py',OUT/'build_git_package.py')

reference_files = [
    (ROOT/'havenline-primary-reference-source/18607.png','Primary Havenline early-camp art board'),
    (ROOT/'havenline-primary-reference-source/18600.png','Primary Havenline camp utility art board'),
    (ROOT/'references/Whiteout Survival Asset Reference Guide.png','Secondary resource and style reference guide')
]
reference_files += [(p,'Original locked video reference frame') for p in sorted((ROOT/'havenline-resource-reference-source').glob('*.png'))]
references = {
    'source_commit': SOURCE_COMMIT,
    'authority_record': f'https://github.com/ksolo21-web/HAVENLINE/blob/{SOURCE_COMMIT}/Docs/Production/T05/R12-20261004/REFERENCE-AUTHORITY.json',
    'resource_registry': f'https://github.com/ksolo21-web/HAVENLINE/blob/{SOURCE_COMMIT}/Docs/Production/RESOURCE_ACTION_REGISTRY.json',
    'video_reference_contract': f'https://github.com/ksolo21-web/HAVENLINE/blob/{SOURCE_COMMIT}/Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md',
    'images': [{'filename':p.name,'role':role,'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p,role in reference_files],
    'note':'Reference source images are identified by hash and are not duplicated in this concept package. New concepts do not replace source reference authority.'
}
(OUT/'source-reference-provenance.json').write_text(json.dumps(references,indent=2)+'\n')

manifest = {
    'title':'Havenline Resource 360 Concept Turnarounds',
    'date':'2026-11-23',
    'source_commit':SOURCE_COMMIT,
    'branch':'art/resource-turnarounds-2026-11-23',
    'scope':'13 AI-generated concept reference sheets with eight illustrated directions each. No production, native-mesh or runtime approval.',
    'reviewed_count':13,
    'illustrated_view_count':104,
    'resolution':[1536,1024],
    'minimum_concept_review_score':final['minimum_score'],
    'review_report':'reviews/final-independent-visual-review.json',
    'review_report_sha256':digest((SOURCE/'reviews/final-independent-visual-review.json').read_bytes()),
    'user_visual_approval':False,
    'production_approval':False,
    'native_mesh_approval':False,
    'coal_status':'Supplementary reference concept, not a claim of registered gameplay content',
    'cooked_food_status':'Bread-like visual concept, not a canonical recipe claim',
    'images':images,
    'selected':[{**a, 'package_path':next(x['package_path'] for x in images if x['sha256']==a['sha256'])} for a in final['assets']]
}
(OUT/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'blob-upload-receipts.json').write_text(json.dumps({'repository':'ksolo21-web/HAVENLINE','image_count':25,'all_image_hashes_verified':True,'images':images},indent=2)+'\n')

rows=[]
for a in final['assets']:
    rel=next(x['package_path'] for x in images if x['sha256']==a['sha256'])
    rows.append(f"| {a['asset'].replace('_',' ').title()} | [{Path(rel).name}]({rel}) | {a['score']:.1f} / 10 |")
readme='''# Havenline resource turnaround concepts

13 separate resource and support-prop sheets, each with eight illustrated directions around the item. Every PNG is 1536 × 1024. Open the selected files below for the current reviewed set.

These are AI-generated concept references for art review and later modeling. They are not native engine renders of shared 3D geometry, exact camera-angle measurements, game-ready meshes, or proof of gameplay integration. No existing gameplay asset or approval record is changed by this branch. User art approval remains separate.

## Reviewed sheets

| Resource | PNG | Independent concept review |
| --- | --- | --- |
'''+ '\n'.join(rows)+'''

The direction sequence is front, front right, right, rear right, rear, rear left, left, and front left. The printed degrees describe the intended illustrated orbit. Exact metric camera rotation and microscopic surface identity are not proven by the images.

Coal is a supplementary reference concept. Cooked food is represented by a bread-like concept and does not establish a canonical recipe. Money and cargo are support props included from the recovered resource-prop inventory.

## Review and provenance

The separate critic inspected all 13 final sheets and their relevant references, corrected view-direction defects through targeted repair iterations, and passed the set at concept-reference scope. The minimum final score is 9.2/10, with no remaining blocking concept-image defects. Minor illustrative surface variation is explicitly recorded in the reports. This is not a claim of 10/10 production style equivalence.

- [Final independent review](reviews/final-independent-visual-review.json)
- [Delivery and image-hash manifest](delivery-manifest.json)
- [Reference provenance](source-reference-provenance.json)
- [Original acceptance contract](acceptance-contract.json)
- [Scope addendum](scope-addendum.json)
- [Exact generation prompts](prompts/)
- [Repair prompts and results](repairs/)
- [All independent review reports](reviews/)

## Preserved candidates

`reviewed-concepts/` contains the 13 selected current sheets. `archived-candidates/initial/` preserves the 11 initial images superseded by repairs, and `archived-candidates/superseded-repairs/` preserves one earlier wheat repair. The two initial images selected without replacement are already present in `reviewed-concepts/`; their bytes are not duplicated. All 25 unique generated PNGs are preserved and hash-indexed.

The generation and repair process used the built-in image-generation tool. The saved prompts and provenance support resumption, but stochastic regeneration is not expected to recreate identical pixels; the preserved PNGs and hashes are authoritative for this review.

This branch adds design-reference files only under `Docs/Design/ResourceTurnarounds/2026-11-23/`. It does not merge into or activate Havenline runtime work.
'''
(OUT/'README.md').write_text(readme)

files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file():
        b=p.read_bytes()
        files.append({'path':p.relative_to(REPO).as_posix(),'local_path':str(p),'bytes':len(b),'sha256':digest(b),'git_blob_sha':git_digest(b),'kind':'image' if p.suffix=='.png' else 'text'})
(SOURCE/'package-file-manifest.json').write_text(json.dumps({'repository_root':str(REPO),'package_path':REL.as_posix(),'files':files},indent=2)+'\n')
assert len([f for f in files if f['kind']=='image'])==25
print(json.dumps({'package_files':len(files),'unique_pngs':25,'reviewed_pngs':13,'archived_pngs':12,'package_path':str(OUT),'manifest':str(SOURCE/'package-file-manifest.json')}))
