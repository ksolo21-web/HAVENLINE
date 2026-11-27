"""Resolve approved pose dependencies and prepare exact hand/gear calls only.

This helper never generates images and never overwrites an existing invocation.
"""
from pathlib import Path
import copy
import importlib.util
import json
import re

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
catalog_path = ROOT / 'atlas-raider-render-catalog.json'
catalog = a.read(catalog_path)
assert catalog['status'] == 'ROOT_REVIEWED_SOURCE_BOUND'
catalog_metrics = a.metrics(catalog_path.read_bytes())
requirements = a.read(ROOT / 'requirements.json')
family_for = {ident: family['id'] for family in requirements['families'] for ident in family['required_sheets']}

def latest_approved(deliverable):
    candidates = []
    for path in (ROOT / 'invocations').glob(deliverable + '-r*.json'):
        match = re.fullmatch(re.escape(deliverable) + r'-r(\d+)', path.stem)
        if not match:
            continue
        invocation = a.read(path)
        if invocation.get('deliverable_id') != deliverable or not invocation.get('output'):
            continue
        report_path = ROOT / 'reviews' / ('critic-' + path.stem + '.json')
        if not report_path.exists():
            continue
        report = a.read(report_path)
        if not str(report.get('status', '')).upper().startswith('PASS'):
            continue
        if not isinstance(report.get('score'), (int, float)) or report['score'] <= 9.0:
            continue
        if report.get('independent') is not True or report.get('reviewer') in {None, '/root', '/root/missing_archive'}:
            continue
        if report.get('all_mandatory_visual_checks_passed') is not True or report.get('mandatory_defects_remaining'):
            continue
        if report.get('actual_full_native_png_inspected') is not True:
            continue
        if report.get('approval_reopened') or report.get('approval_invalidated'):
            continue
        image = Path(invocation['output']['local_path']).resolve()
        metrics = a.metrics(image.read_bytes())
        reviewed = report.get('reviewed_image', {})
        if not all(metrics[key] == invocation['output'][key] == reviewed.get(key) for key in ['bytes', 'sha256', 'git_blob_sha']):
            continue
        if Path(reviewed.get('local_path', '')).resolve() != image:
            continue
        candidates.append({'revision': int(match.group(1)), 'deliverable_id': deliverable,
                           'render_id': path.stem, 'local_path': str(image), **metrics,
                           'review_path': str(report_path.resolve()),
                           'review_sha256': a.metrics(report_path.read_bytes())['sha256'],
                           'review_status': report['status'], 'review_score': report['score'],
                           'reviewer': report['reviewer'], 'all_mandatory_checks_passed': True})
    return max(candidates, key=lambda row: row['revision']) if candidates else None

prepared = []
already = []
waiting = []
conflicts = []
newer_source_available = []
for entry in catalog['entries']:
    dependencies = entry.get('depends_on_approved', [])
    if not entry['id'].endswith('-hands-gear'):
        continue
    assert len(dependencies) == 1 and family_for[entry['id']] == entry['family_id']
    resolved = {ident: latest_approved(ident) for ident in dependencies}
    render_id = entry['id'] + '-r1'
    invocation_path = ROOT / 'invocations' / (render_id + '.json')
    if invocation_path.exists():
        existing = a.read(invocation_path)
        already.append(render_id)
        for ident, source in resolved.items():
            if source and source['local_path'] not in existing['arguments'].get('referenced_image_paths', []):
                newer_source_available.append({'prepared_id': render_id, 'latest_passed_source': source,
                                               'action': 'Existing invocation retained unchanged. Root must decide any new revision and reopen affected visual review.'})
        continue
    if not all(resolved.values()):
        waiting.append({'id': render_id, 'dependencies_without_current_exact_pass': [ident for ident, row in resolved.items() if row is None]})
        continue
    arguments = copy.deepcopy(entry['arguments'])
    old_references = list(arguments['referenced_image_paths'])
    actual_references = []
    placeholders_seen = []
    for value in old_references:
        if value.startswith('APPROVED_RENDER:'):
            ident = value.split(':', 1)[1]
            assert ident in resolved
            placeholders_seen.append(ident)
            actual_references.append(resolved[ident]['local_path'])
        else:
            actual_references.append(value)
    assert set(placeholders_seen) == set(dependencies)
    assert len(actual_references) == len(old_references) <= 5
    assert all(Path(path).is_file() for path in actual_references)
    arguments['referenced_image_paths'] = actual_references
    assert arguments['prompt'] == entry['arguments']['prompt']
    assert all(arguments[key] == entry['arguments'][key] for key in arguments if key != 'referenced_image_paths')
    prompt_path = ROOT / 'prompts' / (render_id + '.txt')
    actual_prompt = arguments['prompt'].encode('utf-8')
    document = actual_prompt + b'\n'
    if prompt_path.exists() and prompt_path.read_bytes() not in {actual_prompt, document}:
        conflicts.append({'id': render_id, 'reason': 'Existing prompt differs; no overwrite performed.'})
        continue
    if not prompt_path.exists():
        with prompt_path.open('xb') as output:
            output.write(document)
    invocation = {'id': render_id, 'deliverable_id': entry['id'], 'family_id': entry['family_id'],
                  'tool': 'image_gen__imagegen', 'arguments': arguments, 'status': 'PREPARED',
                  'reason': 'Root-authorized dependent hand/gear preparation using the latest independently passed exact pose PNG; no generation invoked by this helper.',
                  'prepared_from_catalog': {'path': catalog_path.name, 'sha256': catalog_metrics['sha256'], 'entry_id': entry['id']},
                  'dependency_reference_template': old_references,
                  'resolved_approved_dependencies': list(resolved.values())}
    raw = (json.dumps(invocation, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    try:
        with invocation_path.open('xb') as output:
            output.write(raw)
    except FileExistsError:
        conflicts.append({'id': render_id, 'reason': 'Concurrent writer created invocation; no overwrite performed.'})
        continue
    preparation_snapshot = ROOT / 'archive-prepared-invocation-snapshots' / (render_id + '--' + a.metrics(raw)['sha256'] + '.json')
    preparation_snapshot.parent.mkdir(exist_ok=True)
    assert not preparation_snapshot.exists() or preparation_snapshot.read_bytes() == raw
    if not preparation_snapshot.exists():
        preparation_snapshot.write_bytes(raw)
    prepared.append({'id': render_id, 'deliverable_id': entry['id'], 'family_id': entry['family_id'],
                     'source_render_ids': [row['render_id'] for row in resolved.values()],
                     'source_png_sha256': [row['sha256'] for row in resolved.values()],
                     'review_sha256': [row['review_sha256'] for row in resolved.values()],
                     'invocation_sha256': a.metrics(raw)['sha256'],
                     'actual_ordered_reference_inputs': actual_references,
                     'prompt_argument_unchanged': True})

report = {'schema_version': 1, 'status': 'DEPENDENCIES_CHECKED_NO_GENERATION',
          'prepared': prepared, 'already_prepared_preserved': already,
          'waiting': waiting, 'file_conflicts_preserved': conflicts,
          'newer_approved_source_requires_root_decision': newer_source_available,
          'generation_invoked': False, 'requirements_modified': False}
a.write(ROOT / 'archive-dependent-preparation-status.json', report)
print(json.dumps({'newly_prepared_ids': [row['id'] for row in prepared],
                  'already_prepared_count': len(already), 'waiting_count': len(waiting),
                  'file_conflicts': conflicts, 'newer_sources': newer_source_available,
                  'generation_invoked': False}, indent=2))
