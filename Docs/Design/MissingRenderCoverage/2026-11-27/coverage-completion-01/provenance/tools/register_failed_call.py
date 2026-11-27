"""Register one observed no-image tool failure without inventing an output."""
from pathlib import Path
import importlib.util
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
assert not (ROOT / 'archive-content-publication.json').exists()
assert len(sys.argv) == 3, 'Pass exact render ID and observed failure JSON path'
render_id, error_locator = sys.argv[1:]
assert re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', render_id)
invocation_path = ROOT / 'invocations' / (render_id + '.json')
original_bytes = invocation_path.read_bytes()
record = json.loads(original_bytes)
error_path = (ROOT / error_locator).resolve()
error_bytes = error_path.read_bytes()
error = json.loads(error_bytes)
assert record['id'] == error['render_id'] == render_id
assert record['tool'] == error['tool'] == 'image_gen__imagegen'
assert error['status'] == 'FAILED_NO_IMAGE' and error['native_image'] is None
assert isinstance(error['error'], str) and error['error']
assert (ROOT / error['actual_invocation']).resolve() == invocation_path.resolve()
assert not record.get('output') and not (ROOT / 'renders' / (render_id + '.png')).exists()
assert record['status'] == 'PREPARED', 'Do not overwrite an earlier registration'
arguments = record['arguments']
references = arguments.get('referenced_image_paths', [])
assert len(references) <= 5 and not arguments.get('num_last_images_to_include')
prompt = arguments['prompt'].encode('utf-8')
prompt_path = ROOT / 'prompts' / (render_id + '.txt')
assert prompt_path.read_bytes() in {prompt, prompt + b'\n'}
prepared = ROOT / 'archive-prepared-invocation-snapshots' / (render_id + '--' + a.metrics(original_bytes)['sha256'] + '.json')
prepared.parent.mkdir(exist_ok=True)
assert not prepared.exists() or prepared.read_bytes() == original_bytes
if not prepared.exists():
    prepared.write_bytes(original_bytes)

def fact(path):
    path = Path(path).resolve()
    return {'local_path': str(path), **a.metrics(path.read_bytes())}

requirements_path = ROOT / 'requirements.json'
requirements = fact(requirements_path)
index_path = ROOT / 'archive-input-snapshot-index.json'
index = a.read(index_path)
for path in [requirements_path, error_path]:
    raw = path.read_bytes()
    m = a.metrics(raw)
    snapshot = ROOT / 'archive-input-snapshots' / (path.stem + '--' + m['sha256'] + path.suffix)
    assert not snapshot.exists() or snapshot.read_bytes() == raw
    if not snapshot.exists():
        snapshot.write_bytes(raw)
    if not any(row['sha256'] == m['sha256'] for row in index['snapshots']):
        index['snapshots'].append({'original_path': str(path.relative_to(ROOT)),
                                  'snapshot_path': str(snapshot.relative_to(ROOT)), **m})
a.write(index_path, index)
exact_prompt = ROOT / 'archive-exact-invoked-prompts' / (render_id + '.txt')
assert not exact_prompt.exists() or exact_prompt.read_bytes() == prompt
exact_prompt.write_bytes(prompt)
record.update(status='TOOL_FAILED_NO_IMAGE', output=None,
              tool_error=error['error'], tool_error_record=fact(error_path),
              observed_tool_error_status=error['status'],
              prompt_file=fact(prompt_path), exact_actual_prompt_file=fact(exact_prompt),
              ordered_reference_inputs=[{'order': order, **fact(path)} for order, path in enumerate(references, 1)],
              requirements_at_generation=requirements,
              requirements_snapshot_path=str(ROOT / 'archive-input-snapshots' / ('requirements--' + requirements['sha256'] + '.json')),
              execution_boundary='Observed tool invocation failed without a native image. Preserved argument/input and requirements bytes do not represent a generated original or visual approval.')
invocation_path.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'id': render_id, 'status': record['status'], 'output': None,
                  'exact_error_record': record['tool_error_record'],
                  'requirements': requirements, 'ordered_input_count': len(references)}, indent=2))
