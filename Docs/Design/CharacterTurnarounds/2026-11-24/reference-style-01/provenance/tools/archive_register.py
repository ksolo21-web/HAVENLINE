"""Register immutable generated PNG/prompt pairs for the additive art archive.

Input is a JSON list, or {"images": [...]}, with id, local_path and
local_prompt_path. Every existing registered byte is protected; this command
only creates local staging files and never creates a GitHub commit/ref.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, re, shutil
from PIL import Image

ROOT = Path('/workspace/scratch/9c51da47f878/havenline-character-style-360')
REPO = ROOT / 'archive-repo'
PREFIX = Path('Docs/Design/CharacterTurnarounds/2026-11-24/reference-style-01')
OUT = REPO / PREFIX
SNAPSHOT = ROOT / 'archive-image-snapshot.json'
parser = argparse.ArgumentParser()
parser.add_argument('--batch', type=Path, required=True)
args = parser.parse_args()
batch = json.loads(args.batch.read_text())
batch = batch['images'] if isinstance(batch, dict) else batch
assert isinstance(batch, list)

def digest(data):
    return {'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
            'bytes': len(data)}

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)

ledger = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {
    'schema_version': 1, 'generation_frozen': False,
    'repository': 'ksolo21-web/HAVENLINE',
    'base_commit': 'f3f86e7695e7b68e0d16456dde66788e25291d98',
    'destination': str(PREFIX), 'images': []}
assert ledger.get('generation_frozen') is not True, 'Cannot append after generation freeze.'
known = {row['id']: row for row in ledger['images']}
prepared = []
for row in batch:
    identifier = row['id']
    assert re.fullmatch(r'[a-z0-9][a-z0-9_-]*', identifier), identifier
    image = Path(row['local_path']).resolve()
    prompt = Path(row['local_prompt_path']).resolve()
    assert image.is_relative_to(ROOT) and prompt.is_relative_to(ROOT), 'Use current-task immutable source copies.'
    assert image.suffix.lower() == '.png' and image.is_file() and prompt.is_file()
    data = image.read_bytes()
    assert data.startswith(b'\x89PNG\r\n\x1a\n'), image
    metrics = digest(data)
    if 'sha256' in row:
        assert row['sha256'] == metrics['sha256'], identifier
    if 'git_blob_sha' in row:
        assert row['git_blob_sha'] == metrics['git_blob_sha'], identifier
    if 'bytes' in row:
        assert row['bytes'] == metrics['bytes'], identifier
    prompt_data = prompt.read_bytes()
    prompt_text = prompt_data.decode('utf-8')
    assert not re.search(r'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|[?&](?:sig|signature|X-Amz-Signature|token)=', prompt_text), prompt
    prompt_metrics = digest(prompt_data)
    with Image.open(image) as opened:
        assert opened.format == 'PNG'
        dimensions = list(opened.size)
    record = {'id': identifier, 'local_path': str(image), 'local_prompt_path': str(prompt),
        'archive_path': str(PREFIX / 'attempts' / (identifier + '.png')),
        'prompt_archive_path': str(PREFIX / 'prompts' / (identifier + '.txt')),
        **metrics, 'dimensions': dimensions, 'prompt_sha256': prompt_metrics['sha256'],
        'prompt_git_blob_sha': prompt_metrics['git_blob_sha'], 'prompt_bytes': prompt_metrics['bytes']}
    if row.get('source_index'):
        record['source_index'] = row['source_index']
    if identifier in known:
        for key in ['sha256', 'git_blob_sha', 'bytes', 'prompt_sha256', 'prompt_bytes']:
            assert known[identifier][key] == record[key], 'Registered original changed: ' + identifier
    for source, relative, expected in [(image, record['archive_path'], metrics['sha256']),
                                        (prompt, record['prompt_archive_path'], prompt_metrics['sha256'])]:
        target = REPO / relative
        assert not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() == expected, 'Staged original changed: ' + str(target)
    prepared.append((record, image, prompt))

added = []
for record, image, prompt in prepared:
    for source, key in [(image, 'archive_path'), (prompt, 'prompt_archive_path')]:
        target = REPO / record[key]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
    if record['id'] not in known:
        ledger['images'].append(record)
        known[record['id']] = record
        added.append(record['id'])
ledger.update(registered_generated_pngs=len(ledger['images']),
              distinct_generated_blobs=len({row['git_blob_sha'] for row in ledger['images']}),
              generated_original_bytes=sum(row['bytes'] for row in ledger['images']),
              updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
write_json(SNAPSHOT, ledger)
checkpoint = json.loads((ROOT / 'archive-checkpoint.json').read_text())
checkpoint.update(stage='UPLOADING_IMMUTABLE_GENERATED_OUTPUTS_AWAITING_FREEZE',
                  registered_generated_pngs=ledger['registered_generated_pngs'],
                  next_action='Upload unreceipted generated blobs; retain all attempts and wait for the final independent selection/review freeze before committing.')
write_json(ROOT / 'archive-checkpoint.json', checkpoint)
print(json.dumps({'registered_generated_pngs': ledger['registered_generated_pngs'],
                  'distinct_generated_blobs': ledger['distinct_generated_blobs'],
                  'added': added, 'snapshot': str(SNAPSHOT), 'remote_branch_changed': False}))
