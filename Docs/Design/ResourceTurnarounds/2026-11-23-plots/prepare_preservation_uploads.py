"""List storage candidates and source/review image evidence for immutable blob upload."""
from pathlib import Path
import hashlib
import json

ROOT = Path('/workspace/scratch/fc906e16b0fb')
SOURCE = ROOT / 'havenline-plot-renders'
items = {}


def record(path, asset, role):
    p = Path(path)
    if not p.is_file() or p.suffix.lower() != '.png':
        return
    b = p.read_bytes()
    items[str(p)] = {'id': asset, 'local_path': str(p), 'role': role, 'bytes': len(b),
                     'sha256': hashlib.sha256(b).hexdigest(),
                     'git_blob_sha': hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()}


def walk(value):
    if isinstance(value, list):
        for x in value:
            walk(x)
    elif isinstance(value, dict):
        path = value.get('path') or value.get('candidate_path')
        asset = value.get('id') or value.get('asset') or value.get('key')
        if path and asset:
            record(path, asset, 'storage-generated-candidate')
        for x in value.values():
            if isinstance(x, (dict, list)):
                walk(x)


for folder in ['storage-build', 'supplement-build']:
    for p in sorted((SOURCE / folder).glob('*results.json')):
        walk(json.loads(p.read_text()))
for p in sorted((SOURCE / 'sources').rglob('*.png')):
    record(p, 'source-evidence', 'source-gameplay-crop-or-sequence')
omitted = []
for p in sorted((SOURCE / 'reviews').rglob('*.png')):
    if p.parent.name == 'B-activation-sequence' and p.name.startswith('frame-'):
        b = p.read_bytes()
        omitted.append({'source_filename': p.name, 'source_relative_path': p.relative_to(SOURCE).as_posix(),
                        'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b),
                        'retention': 'Original recording hash and extraction records preserve source identity. Published gameplay contact/detail sheets retain review pixels without duplicating full phone-screen frames.'})
    else:
        record(p, 'review-evidence', 'review-inspection-evidence')
(SOURCE / 'sources/source-evidence-retention.json').write_text(json.dumps({'full_recording_frames_identified': omitted, 'source_videos_duplicated_in_git': False, 'original_recording_identity': 'buy-activation-source-notes.json', 'published_evidence': 'Gameplay source crops, exact transition detail sheets and independent review contact sheets.'}, indent=2) + '\n')
receipts_path = SOURCE / 'preservation-image-blob-receipts.json'
receipts = json.loads(receipts_path.read_text())['blobs'] if receipts_path.is_file() else []
known = {x['local_path']: x['sha256'] for x in receipts}
queue = [v for k, v in items.items() if known.get(k) != v['sha256']]
(SOURCE / 'preservation-upload-queue.json').write_text(json.dumps({'pending': queue}, indent=2) + '\n')
print(json.dumps({'pending': len(queue), 'storage_candidates': sum(x['role'] == 'storage-generated-candidate' for x in queue),
                  'source_or_review_evidence': sum(x['role'] != 'storage-generated-candidate' for x in queue),
                  'already_uploaded': len(receipts)}))
