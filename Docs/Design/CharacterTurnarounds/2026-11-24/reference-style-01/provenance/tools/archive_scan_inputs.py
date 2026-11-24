"""Normalize only the declared builder indexes for immutable registration."""
from pathlib import Path
import json, subprocess, sys

ROOT = Path('/workspace/scratch/9c51da47f878/havenline-character-style-360')
registry = json.loads((ROOT / 'archive-input-sources.json').read_text())
images, missing = [], []
for source in registry['sources']:
    index = Path(source['index_path'])
    if not index.exists():
        missing.append(str(index))
        continue
    data = json.loads(index.read_text())
    for row in data['images']:
        image = Path(row['path'])
        if not image.is_absolute():
            image = index.parent / image
        prompt = Path(row['prompt'])
        if not prompt.is_absolute():
            prompt = index.parent / prompt
        images.append({'id': row['id'], 'local_path': str(image), 'local_prompt_path': str(prompt),
                       'sha256': row['sha256'], 'git_blob_sha': row['git_blob_sha'],
                       'bytes': row['bytes'], 'source_index': str(index)})
assert len({row['id'] for row in images}) == len(images), 'Duplicate output IDs across builders.'
batch = ROOT / 'archive-import-batch.json'
batch.write_text(json.dumps({'images': images}, indent=2) + '\n')
if images:
    subprocess.run([sys.executable, str(ROOT / 'archive_register.py'), '--batch', str(batch)], check=True)
print(json.dumps({'declared_indexes': len(registry['sources']), 'registered_index_outputs': len(images),
                  'indexes_not_yet_created': missing}))
