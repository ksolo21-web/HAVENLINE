"""Prepare the approved closed-gate dependency without invoking generation."""
from pathlib import Path
import copy
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

assert len(sys.argv) == 2, 'Pass the exact independently approved closed render ID'
closed_id = sys.argv[1]
assert closed_id.startswith('world-fortress-gates-closed-r')
catalog_path = ROOT / 'world-render-catalog.json'
catalog = a.read(catalog_path)
approval = a.read(ROOT / 'audit/world/root-catalog-approval.json')
catalog_metrics = a.metrics(catalog_path.read_bytes())
assert catalog_metrics['sha256'] in json.dumps(approval)
entry = next(row for row in catalog['sheets'] if row['id'] == 'world-fortress-gates-open')
assert entry['draft_arguments'] is None
required = entry['required_additional_reference']
assert required['order'] == 3 and required['approved_sheet_id'] == 'world-fortress-gates-closed'
closed_invocation = a.read(ROOT / 'invocations' / (closed_id + '.json'))
assert closed_invocation['deliverable_id'] == required['approved_sheet_id']
closed_path = Path(closed_invocation['output']['local_path']).resolve()
closed_metrics = a.metrics(closed_path.read_bytes())
assert all(closed_metrics[k] == closed_invocation['output'][k] for k in ['sha256', 'bytes', 'git_blob_sha'])
review_path = ROOT / 'reviews' / ('critic-' + closed_id + '.json')
review = a.read(review_path)
assert review.get('independent') is True
assert review.get('reviewer') not in {None, '/root', '/root/missing_archive'}
assert str(review.get('status', '')).startswith('PASS') and review['score'] > 9.0
assert review.get('all_mandatory_visual_checks_passed') is True
assert not review.get('mandatory_defects_remaining')
assert not review.get('approval_reopened') and not review.get('approval_invalidated')
assert review.get('actual_full_png_inspected') is True or review.get('actual_full_native_png_inspected') is True
reviewed = review['reviewed_image']
assert reviewed.get('sha256', reviewed.get('source_sha256')) == closed_metrics['sha256']
assert reviewed.get('bytes', reviewed.get('source_bytes')) == closed_metrics['bytes']
reviewed_path = reviewed.get('path', reviewed.get('local_path', reviewed.get('local_render_path')))
assert Path(reviewed_path).resolve() == closed_path

arguments = copy.deepcopy(entry['deferred_argument_template'])
assert len(arguments['referenced_image_paths']) == 2
for expected, actual in zip(entry['ordered_reference_inputs'], arguments['referenced_image_paths']):
    assert Path(actual).resolve() == Path(expected['local_path']).resolve()
    metrics = a.metrics(Path(actual).read_bytes())
    assert all(metrics[k] == expected[k] for k in ['sha256', 'bytes', 'git_blob_sha'])
arguments['referenced_image_paths'].append(str(closed_path))
assert arguments['prompt'] == entry['deferred_argument_template']['prompt']
render_id = 'world-fortress-gates-open-r1'
requirements = a.read(ROOT / 'requirements.json')
assert any(f['id'] == entry['family_id'] and entry['id'] in f['required_sheets'] for f in requirements['families'])
dependency = {'order': 3, 'deliverable_id': required['approved_sheet_id'], 'render_id': closed_id,
              'local_path': str(closed_path), **closed_metrics,
              'review_path': str(review_path.resolve()),
              'review_sha256': a.metrics(review_path.read_bytes())['sha256'],
              'review_status': review['status'], 'review_score': review['score'],
              'reviewer': review['reviewer'], 'all_mandatory_checks_passed': True}
invocation = {'id': render_id, 'deliverable_id': entry['id'], 'family_id': entry['family_id'],
              'tool': 'image_gen__imagegen', 'arguments': arguments, 'status': 'PREPARED',
              'reason': 'Root-authorized deferred gate-open preparation using the exact independently passed closed-state sheet in declared reference position 3; no generation invoked by this helper.',
              'prepared_from_catalog': {'path': catalog_path.name, 'sha256': catalog_metrics['sha256'],
                                        'entry_id': entry['id'], 'argument_source': 'deferred_argument_template'},
              'required_additional_reference_template': required,
              'resolved_approved_dependencies': [dependency]}
raw = (json.dumps(invocation, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
invocation_path = ROOT / 'invocations' / (render_id + '.json')
prompt_path = ROOT / 'prompts' / (render_id + '.txt')
assert not invocation_path.exists(), 'Existing invocation preserved; no overwrite allowed'
actual_prompt = arguments['prompt'].encode('utf-8')
document = actual_prompt + b'\n'
assert not prompt_path.exists() or prompt_path.read_bytes() in {actual_prompt, document}
if not prompt_path.exists():
    with prompt_path.open('xb') as output:
        output.write(document)
with invocation_path.open('xb') as output:
    output.write(raw)
preparation_snapshot = ROOT / 'archive-prepared-invocation-snapshots' / (render_id + '--' + a.metrics(raw)['sha256'] + '.json')
preparation_snapshot.parent.mkdir(exist_ok=True)
assert not preparation_snapshot.exists() or preparation_snapshot.read_bytes() == raw
if not preparation_snapshot.exists():
    preparation_snapshot.write_bytes(raw)
report = {'status': 'PREPARED_EXACT_APPROVED_DEPENDENCY_NO_GENERATION', 'id': render_id,
          'invocation_sha256': a.metrics(raw)['sha256'],
          'prompt_argument_sha256': a.metrics(actual_prompt)['sha256'],
          'prompt_argument_unchanged': True, 'resolved_approved_dependency': dependency,
          'actual_ordered_reference_inputs': arguments['referenced_image_paths'],
          'generation_invoked': False, 'requirements_modified': False}
a.write(ROOT / 'archive-preparation-reports/gates-open-approved-dependency.json', report)
print(json.dumps(report, indent=2))
