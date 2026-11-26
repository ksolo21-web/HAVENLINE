"""Verify the complete frozen project file list before and after recording."""
import hashlib
import json
import sys
from pathlib import Path

project, manifest, destination = (Path(x) for x in sys.argv[1:4])
source = sys.argv[4]
receipt = json.loads(manifest.read_text())
assert receipt['commit'] == source, (receipt['commit'], source)
files = receipt['files']
for name, expected in files.items():
    path = project / name
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open('rb') as stream:
        observed = hashlib.file_digest(stream, 'sha256').hexdigest()
    if observed != expected:
        raise RuntimeError(f'{name}: expected {expected}, observed {observed}')
result = {'commit': source, 'project_files_checked': len(files),
          'source_manifest': manifest.name,
          'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
          'entry': 'res://field_opening.tscn'}
destination.write_text(json.dumps(result, indent=2)+'\n')
print(result)
