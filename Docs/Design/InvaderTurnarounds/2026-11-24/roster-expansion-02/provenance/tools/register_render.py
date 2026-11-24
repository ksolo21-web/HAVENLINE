from pathlib import Path
import sys, shutil, json, hashlib
from PIL import Image

base = Path(__file__).resolve().parent
ident, source = sys.argv[1:3]
src = Path(source)
dst = base / 'renders' / (ident + '.png')
if dst.exists() and dst.read_bytes() != src.read_bytes():
    raise SystemExit('Refusing to replace a prior revision')
shutil.copy2(src, dst)
data = dst.read_bytes()
im = Image.open(dst)
dims = list(im.size)
im.verify()
entry = {'id': ident, 'filename': dst.name, 'source_file': str(src), 'path': str(dst),
         'sha256': hashlib.sha256(data).hexdigest(),
         'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
         'bytes': len(data), 'dimensions': dims, 'prompt': 'prompts/' + ident + '.txt',
         'status': 'PENDING_INDEPENDENT_REVIEW'}
mp = base / 'generation-index.json'
manifest = json.loads(mp.read_text()) if mp.exists() else {'schema_version': 1, 'date': '2026-11-24', 'images': []}
manifest['images'] = [x for x in manifest['images'] if x['id'] != ident] + [entry]
mp.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(entry))
