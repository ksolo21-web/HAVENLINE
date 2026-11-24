"""Join uploader receipts and verify each exact PNG before final packaging."""
from pathlib import Path
import hashlib
import json

root = Path('/workspace/scratch/fc906e16b0fb/havenline-resource-expansion')
blobs = {}
for name in ['animal-image-blob-receipts.json', 'processed-image-blob-receipts.json', 'inspection-image-blob-receipts.json']:
    doc = json.loads((root / name).read_text())
    records = doc if isinstance(doc, list) else doc['blobs']
    for entry in records:
        path = entry['local_path']
        data = Path(path).read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        git_sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert sha == entry['sha256'] and git_sha == entry['blob_sha']
        if path in blobs:
            assert blobs[path]['blob_sha'] == git_sha
        blobs[path] = {**entry, 'git_blob_sha': git_sha, 'bytes': len(data), 'receipt_file': name}
output = {'repository': 'ksolo21-web/HAVENLINE', 'verified_blob_count': len(blobs), 'blobs': sorted(blobs.values(), key=lambda x: x['local_path'])}
(root / 'all-image-blob-receipts.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps({'verified_blob_count': len(blobs), 'output': str(root / 'all-image-blob-receipts.json')}))
