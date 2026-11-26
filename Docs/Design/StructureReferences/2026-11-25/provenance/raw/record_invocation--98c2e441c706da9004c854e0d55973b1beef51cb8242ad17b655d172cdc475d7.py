from pathlib import Path
import sys, json, hashlib

base = Path(__file__).resolve().parent
ident, *paths = sys.argv[1:]
prompt = base / 'prompts' / (ident + '.txt')
if not prompt.is_file() or not paths:
    raise SystemExit('Need existing exact prompt and ordered reference paths')
refs = [Path(x).resolve(strict=True) for x in paths]
entry = {
    'id': ident, 'tool': 'image_gen.imagegen',
    'prompt_path': str(prompt),
    'prompt_sha256': hashlib.sha256(prompt.read_bytes()).hexdigest(),
    'referenced_image_paths': [str(x) for x in refs],
    'reference_sha256': [hashlib.sha256(x.read_bytes()).hexdigest() for x in refs],
    'transparent_background': False, 'status': 'READY_TO_INVOKE'
}
path = base / 'invocation-index.json'
index = json.loads(path.read_text()) if path.exists() else {'schema_version': 1, 'invocations': []}
if any(x['id'] == ident for x in index['invocations']):
    raise SystemExit('Refusing to rewrite an invocation: use a new revision ID')
index['invocations'].append(entry)
path.write_text(json.dumps(index, indent=2) + '\n')
print(json.dumps(entry))
