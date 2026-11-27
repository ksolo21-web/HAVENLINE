"""Reconcile native cached PNG bytes with registered outputs or baseline blobs.

Unknown cache files are reported for root to bind to their real tool outcomes.
No image identity, prompt or invocation history is inferred from appearances.
"""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
registered = defaultdict(list)
for path in sorted((ROOT / 'invocations').glob('*.json')):
    invocation = a.read(path)
    if invocation.get('output'):
        output = invocation['output']
        m = a.metrics(Path(output['local_path']).read_bytes())
        assert all(m[key] == output[key] for key in ['sha256', 'bytes', 'git_blob_sha'])
        registered[output['sha256']].append(invocation['id'])
baseline = defaultdict(list)
for row in a.read(ROOT / 'archive-baseline-tree.json')['tree']:
    if row['type'] == 'blob':
        baseline[row['sha']].append(row['path'])
rows = []
for path in sorted((ROOT.parent / 'generated_images').glob('*.png')):
    m = a.metrics(path.read_bytes())
    row = {'path': str(path), **m,
           'mtime_utc': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}
    if m['sha256'] in registered:
        row.update(disposition='REGISTERED_TASK_ORIGINAL', render_ids=registered[m['sha256']])
    elif m['git_blob_sha'] in baseline:
        aliases = sorted(baseline[m['git_blob_sha']], key=lambda value: ('/selected/' not in value, len(value), value))
        row.update(disposition='EXACT_BASELINE_BLOB', source_commit=a.BASE,
                   repository_path=aliases[0], all_exact_baseline_alias_paths=aliases)
    else:
        row.update(disposition='UNBOUND_CACHE_OUTPUT_REQUIRES_ROOT_TOOL_OUTCOME_CUSTODY')
    rows.append(row)
counts = dict(Counter(row['disposition'] for row in rows))
unknown = [row for row in rows if row['disposition'].startswith('UNBOUND')]
report = {'schema_version': 1, 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
          'status': 'PASS_CURRENT_NATIVE_CACHE_BINDINGS' if not unknown else 'WORKING_NATIVE_CACHE_CUSTODY_CHECK',
          'scope': 'Every PNG currently present in this workspace generated_images directory, compared by exact bytes to registered task outputs and immutable baseline Git blob identities. This is a custody check, not a publication freeze or independent visual approval.',
          'active_tool_call_boundary': 'While calls remain active, new native cache files may precede their returned outcomes and registration. Root must settle all actual outcomes before the final freeze.',
          'counts': counts, 'files': rows, 'unbound_file_count': len(unknown),
          'no_invented_identity_or_prompt_bindings': True}
a.write(ROOT / 'archive-native-cache-custody-working.json', report)
print(json.dumps({'status': report['status'], 'counts': counts, 'unbound_files': unknown}, indent=2))
