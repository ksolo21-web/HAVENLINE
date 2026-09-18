#!/usr/bin/env python3
"""Package measured T10 evidence for existing independent specialist gates."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/havenline/production'))
from specialist_evidence_manifest import validate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--evidence-root', required=True)
    a = ap.parse_args()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == a.candidate
    src = ROOT / a.evidence_root
    out = ROOT / 'critic-input'
    if out.exists():
        raise SystemExit('critic-input exists; use a fresh evidence workspace')
    shutil.copytree(src, out)
    reports = {}
    for name in ('domain-tests.json', 'integration-tests.json', 'progression.json'):
        report = json.loads((out / name).read_text())
        assert report.get('candidate', report.get('candidate_commit')) == a.candidate, name
        assert report.get('passed') is True, name
        reports[name] = report
    capture = json.loads((out / 'native4k/manifest.json').read_text())
    assert capture['candidate'] == a.candidate and capture['exact_replay_verified']
    perf = capture['performance_peaks']
    assert perf['visible_triangles'] > 0 and perf['draw_calls'] > 0 and perf['process_memory_mb'] > 0
    files = subprocess.check_output(['git', 'ls-files', 'HavenlineGodot'], cwd=ROOT, text=True).splitlines()
    perf['storage_download_mb'] = sum((ROOT / p).stat().st_size for p in files) / 1048576
    perf.update(candidate_commit=a.candidate, scope=capture['performance_scope'], source_manifest_sha256=digest(out / 'native4k/manifest.json'), physical_certification=False)
    (out / 'performance.json').write_text(json.dumps(perf, indent=2) + '\n')
    # These are summaries of preserved raw reports, never substituted scores.
    summary = {'task_id': 'T10', 'candidate': a.candidate, 'scope': 'Neutral transform framework. T11 owns authored camp content and main-loop binding.', 'controls': 'No added action controls. Preview is pure; delivered stored resources alone pay; simulation owns debit; T10 accepts receipt once.', 'reports': {}}
    for name, report in reports.items():
        summary['reports'][name] = {k: v for k, v in report.items() if k not in ('checks', 'source_hashes', 'source_sha256')}
        summary['reports'][name]['raw_sha256'] = digest(out / name)
    (out / 'review-summary.json').write_text(json.dumps(summary, indent=2) + '\n')

    def item(path, category, kind='json', description=''):
        p = ROOT / path
        return dict(path=path, category=category, kind=kind, description=description, sha256=digest(p))

    for cid in ('C3', 'C4', 'C7'):
        groups = []
        if cid == 'C7':
            rows = [item('critic-input/progression.json', 'progression_simulation'), item('HavenlineGodot/scripts/world_transform.gd', 'transaction_state_graph', 'text'), item('critic-input/review-summary.json', 'recovery_evidence')]
            groups.append(dict(id='transaction-integrity', items=rows))
        else:
            rows = [item('critic-input/review-summary.json', 'control_state' if cid == 'C3' else 'feedback_state')]
            for state in capture['states']:
                rows.append(item('critic-input/native4k/' + state + '-front.png', 'gameplay_state', 'image', state + ': real-authority neutral framework'))
            groups.append(dict(id='full-lifecycle', items=rows))
            frames = sorted((out / 'capture').glob('motion-*.png'))
            assert len(frames) >= 12, 'continuous lifecycle motion frames missing'
            for start in range(0, len(frames), 12):
                groups.append(dict(id='motion-' + str(start), items=[item(str(p.relative_to(ROOT)), 'loop_evidence' if cid == 'C3' else 'feedback_state', 'motion_frame', 'continuous 2fps sample from preserved 30fps lifecycle video') for p in frames[start:start+12]]))
            rows = []
            for folder in sorted((out / 'device-layout').iterdir()):
                if not folder.is_dir(): continue
                for state in ('blocked', 'complete'):
                    rows.append(item(str((folder / (state + '-front.png')).relative_to(ROOT)), 'control_state' if cid == 'C3' else 'feedback_state', 'image', folder.name + ': use actual pixel dimensions; canonical labels may not equal aspect ratio'))
            groups.append(dict(id='device-readability', items=rows))
        manifest = dict(schema_version=1, task_id='T10', critic_id=cid, candidate_commit=a.candidate, groups=groups)
        errors = validate(manifest)
        if errors: raise SystemExit('\n'.join(errors))
        (out / (cid + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    index = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out / 'evidence-index.json').write_text(json.dumps({'candidate': a.candidate, 'files': index}, indent=2) + '\n')


if __name__ == '__main__':
    main()
