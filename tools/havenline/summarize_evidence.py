"""Summarize real Godot test output; no marker-only or visual auto-approval."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args()
suites = []
for name in ('test_simulation', 'test_crew_and_persistence', 'test_motion_and_performance', 'test_population'):
    path = args.artifacts / f'{name}.log'
    reports = [json.loads(line) for line in path.read_text().splitlines() if line.startswith('{')]
    if not reports:
        raise SystemExit(f'Missing test result: {path}')
    report = reports[-1]
    if not report.get('passed') or not all(check['passed'] for check in report['checks']):
        raise SystemExit(f'Godot suite failed: {name}')
    suites.append({'suite': name, 'checks': len(report['checks']), 'passed': True})
result = {'engine': 'Godot 4.7.2', 'suites': suites,
          'total_checks': sum(s['checks'] for s in suites),
          'all_checks_passed': True, 'whole_rig_approved': False,
          'art_approved': False, 'physical_4k60_certified': False,
          'game_complete': False}
(args.artifacts / 'test-summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
