"""Register exact native output and actual invocation inputs without image edits."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
render_id, native_path = sys.argv[1:3]
assert re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', render_id), 'Unsafe render identifier'
native = Path(native_path).resolve()
inv = ROOT / 'invocations' / (render_id + '.json')
record = json.loads(inv.read_text())
assert record['id'] == render_id
assert record['tool'] == 'image_gen__imagegen'
arguments = record['arguments']
references = arguments.get('referenced_image_paths', []) or []
assert len(references) <= 5, 'The actual tool accepts at most five reference images'
assert not arguments.get('num_last_images_to_include'), 'Use local input paths for exact archive custody'
prompt_path = ROOT / 'prompts' / (render_id + '.txt')
prompt_bytes = arguments['prompt'].encode('utf-8')
assert prompt_path.read_bytes() in {prompt_bytes, prompt_bytes + b'\n'}, 'Prompt document differs from actual invocation'
native_bytes = native.read_bytes()
assert native_bytes.startswith(b'\x89PNG\r\n\x1a\n'), 'Expected original native PNG'
with Image.open(native) as img:
    assert img.format == 'PNG'
    img.verify()
destination = ROOT / 'renders' / (render_id + '.png')
destination.parent.mkdir(parents=True, exist_ok=True)
assert not destination.exists() or destination.read_bytes() == native_bytes, 'A prior original must never be overwritten'
if not destination.exists():
    shutil.copy2(native, destination)

def fact(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    result = {'local_path': str(path), 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(),
              'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}
    try:
        with Image.open(path) as img:
            result.update(dimensions=list(img.size), actual_format=img.format)
    except (OSError, ValueError):
        pass
    return result

requirements_path = ROOT / 'requirements.json'
requirements = fact(requirements_path)
snapshot = ROOT / 'archive-input-snapshots' / ('requirements--' + requirements['sha256'] + '.json')
snapshot.parent.mkdir(parents=True, exist_ok=True)
assert not snapshot.exists() or snapshot.read_bytes() == requirements_path.read_bytes()
if not snapshot.exists():
    shutil.copyfile(requirements_path, snapshot)
actual_prompt = ROOT / 'archive-exact-invoked-prompts' / (render_id + '.txt')
actual_prompt.parent.mkdir(parents=True, exist_ok=True)
assert not actual_prompt.exists() or actual_prompt.read_bytes() == prompt_bytes
actual_prompt.write_bytes(prompt_bytes)

record['prompt_file'] = fact(prompt_path)
record['exact_actual_prompt_file'] = fact(actual_prompt)
record['ordered_reference_inputs'] = [dict(order=i + 1, **fact(p)) for i, p in enumerate(references)]
record['requirements_at_generation'] = requirements
record['requirements_snapshot_path'] = str(snapshot)
record['output'] = dict(native_returned_locator=str(native), **fact(destination))
record['status'] = 'GENERATED_AWAITING_REVIEW'
inv.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'id': render_id, 'output': record['output'], 'ordered_reference_count': len(references),
                  'requirements_snapshot_path': str(snapshot)}, indent=2))
