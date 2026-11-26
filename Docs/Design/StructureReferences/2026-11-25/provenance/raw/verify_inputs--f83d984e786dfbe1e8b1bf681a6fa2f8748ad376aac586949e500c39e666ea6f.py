from pathlib import Path
import json, hashlib
from PIL import Image

base = Path(__file__).resolve().parent

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def blob(p):
    data = Path(p).read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

root_gen = json.loads((base / 'generation-index.json').read_text())
counter_gen = json.loads((base / 'counter-builder/generation-index.json').read_text())
root_inv = json.loads((base / 'invocation-index.json').read_text())
counter_inv = json.loads((base / 'counter-builder/invocation-index.json').read_text())
images = {}
issues = []
for entry in root_gen['images'] + counter_gen['generations']:
    ident = entry.get('id', entry.get('generation_id'))
    p = Path(entry.get('path', entry.get('local_path')))
    original = Path(entry.get('source_file', entry.get('native_original_path')))
    if ident in images:
        issues.append('Duplicate generated ID: ' + ident)
    try:
        im = Image.open(p)
        dimensions, fmt = list(im.size), im.format
        im.verify()
        assert fmt == 'PNG', 'Not a real PNG'
        assert digest(p) == entry['sha256'], 'Generated hash mismatch'
        assert dimensions == entry['dimensions'], 'Native dimensions mismatch'
        assert p.stat().st_size == entry['bytes'], 'Byte count mismatch'
        assert p.read_bytes() == original.read_bytes(), 'Generated original was changed'
        if 'git_blob_sha' in entry:
            assert blob(p) == entry['git_blob_sha'], 'Git blob identity mismatch'
        images[ident] = {'path': str(p.relative_to(base)), 'sha256': digest(p), 'git_blob_sha': blob(p), 'bytes': p.stat().st_size, 'dimensions': dimensions, 'native_original_unchanged': True}
    except Exception as exc:
        issues.append(ident + ': ' + str(exc))

invocations = {}
for entry in root_inv['invocations'] + counter_inv['invocations']:
    ident = entry.get('id', entry.get('invocation_id'))
    try:
        assert ident not in invocations, 'Duplicate invocation ID'
        assert ident in images, 'Invocation has no generated output yet'
        p = Path(entry['prompt_path'])
        assert digest(p) == entry['prompt_sha256'], 'Actual prompt hash mismatch'
        if 'prompt' in entry:
            assert p.read_text() == entry['prompt'], 'Inline exact prompt differs from file'
        if 'referenced_image_paths' in entry:
            refs = list(zip(entry['referenced_image_paths'], entry['reference_sha256']))
        else:
            refs = [(x['local_path'], x['sha256']) for x in entry['ordered_reference_inputs']]
        assert refs, 'Missing actual ordered reference inputs'
        for path, expected in refs:
            assert digest(path) == expected, 'Reference changed: ' + path
        output_hash = entry.get('output_sha256', entry.get('output', {}).get('sha256'))
        assert output_hash == images[ident]['sha256'], 'Invocation output mismatch'
        invocations[ident] = {'prompt_path': str(p.relative_to(base)), 'prompt_sha256': digest(p), 'ordered_references': [{'path': str(Path(x).relative_to(base)), 'sha256': h} for x, h in refs]}
    except Exception as exc:
        issues.append(ident + ': ' + str(exc))

all_render_files = {p.resolve() for d in [base / 'renders', base / 'counter-builder/renders'] for p in d.glob('*.png')}
registered_files = {(base / x['path']).resolve() for x in images.values()}
if all_render_files != registered_files:
    issues.append('Unregistered or missing render files: ' + repr(sorted(str(x) for x in all_render_files ^ registered_files)))
if set(images) != set(invocations):
    issues.append('Image/invocation ID sets differ')

report = {'schema_version': 1, 'reviewer': 'root independent archive-input verification', 'requirements_sha256': digest(base / 'requirements.json'), 'status': 'PASS' if not issues else 'BLOCKED', 'generated_original_count': len(images), 'actual_invocation_count': len(invocations), 'images': images, 'invocations': invocations, 'issues': issues, 'claim_boundary': 'Exact local original, prompt and reference integrity only; not visual approval or remote publication proof'}
(base / 'root-input-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in {'images', 'invocations'}}, indent=2))
raise SystemExit(0 if not issues else 1)
