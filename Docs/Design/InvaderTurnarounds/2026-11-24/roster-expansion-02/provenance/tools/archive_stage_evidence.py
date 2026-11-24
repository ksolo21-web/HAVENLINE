"""Preserve current-task QA images/provenance separately from generated renders."""
from pathlib import Path
import hashlib, json, re, shutil
from PIL import Image

ROOT = Path('/workspace/scratch/9c51da47f878/havenline-enemy-roster-02')
PREFIX = Path('Docs/Design/InvaderTurnarounds/2026-11-24/roster-expansion-02')
OUT = ROOT / 'archive-repo' / PREFIX
LEDGER = ROOT / 'archive-evidence-snapshot.json'
sources = {'reviews/evidence': 'review-evidence/critic',
           'animal-builds/evidence': 'review-evidence/animal-builder',
           'aerial-siege-builds/evidence': 'review-evidence/aerial-siege-builder'}
records = json.loads(LEDGER.read_text())['files'] if LEDGER.exists() else []

def metrics(data):
    return {'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
            'bytes': len(data)}

for source_root, target_root in sources.items():
    source_dir = ROOT / source_root
    if not source_dir.exists():
        continue
    for source in sorted(source_dir.rglob('*')):
        if not source.is_file() or source.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.json'}:
            continue
        data = source.read_bytes()
        info = metrics(data)
        if source.suffix == '.json':
            value = data.decode('utf-8')
            json.loads(value)
            assert not re.search(r'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|[?&](?:sig|signature|X-Amz-Signature|token)=', value), source
        relative = Path(target_root) / source.relative_to(source_dir)
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != data:
            old_data = target.read_bytes()
            old_sha = metrics(old_data)['sha256']
            historical = Path('review-evidence/history') / (old_sha + target.suffix)
            (OUT / historical).parent.mkdir(parents=True, exist_ok=True)
            (OUT / historical).write_bytes(old_data)
            for row in records:
                if row['archive_relative_path'] == str(relative):
                    row['archive_relative_path'] = str(historical)
                    row['archive_path'] = str(PREFIX / historical)
                    row['historical_version'] = True
        shutil.copy2(source, target)
        record = {'origin_task_relative_path': str(source.relative_to(ROOT)),
                  'archive_relative_path': str(relative), 'archive_path': str(PREFIX / relative),
                  'local_staged_path': str(target), 'kind': 'provenance_json' if source.suffix == '.json' else 'qa_image',
                  'generated_render': False, **info}
        if record['kind'] == 'qa_image':
            with Image.open(source) as image:
                record['dimensions'] = list(image.size)
        records = [row for row in records if not (row['archive_relative_path'] == str(relative) and row['sha256'] == info['sha256'])]
        records.append(record)
for row in records:
    path = OUT / row['archive_relative_path']
    assert metrics(path.read_bytes()) == {key: row[key] for key in ['sha256', 'git_blob_sha', 'bytes']}, path
    row['local_staged_path'] = str(path)
records.sort(key=lambda x: (x['origin_task_relative_path'], x['sha256']))
ledger = {'schema_version': 1, 'generated_render_count': 0,
          'qa_evidence_files': len(records), 'qa_image_files': sum(x['kind'] == 'qa_image' for x in records),
          'bytes': sum(x['bytes'] for x in records), 'files': records}
LEDGER.write_text(json.dumps(ledger, indent=2) + '\n')
public = {**ledger, 'files': [{key: value for key, value in row.items() if key != 'local_staged_path'} for row in records]}
(OUT / 'review-evidence').mkdir(parents=True, exist_ok=True)
(OUT / 'review-evidence/index.json').write_text(json.dumps(public, indent=2) + '\n')
print(json.dumps({key: value for key, value in ledger.items() if key != 'files'}))
