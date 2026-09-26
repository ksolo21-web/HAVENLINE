#!/usr/bin/env python3
"""Cheap hosted pipeline proof. Diagnostic only; never critic or approval evidence."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/havenline/production'))
from collect_failure_job_logs import collect

MARKER = 'T10_B052_EXPECTED_DIAGNOSTIC_FAILURE'
PRODUCER = 'expected-diagnostic-failure'


def verify_probe(run, jobs, envelope, repository, run_id, candidate):
    if run.get('head_sha') != candidate or run.get('head_branch') != 'havenline/T10-pipeline-preflight':
        raise ValueError('probe source or branch mismatch')
    if run.get('id') != run_id or run.get('repository', {}).get('full_name') != repository:
        raise ValueError('probe run/repository mismatch')
    producer = [j for j in jobs['jobs'] if j.get('name') == PRODUCER]
    setup = [j for j in jobs['jobs'] if j.get('name') == 'cheap-boundary-checks']
    if len(setup) != 1 or setup[0].get('conclusion') != 'success':
        raise ValueError('cheap boundary checks did not pass')
    if len(producer) != 1 or producer[0].get('status') != 'completed' or producer[0].get('conclusion') != 'failure':
        raise ValueError('expected producer must actually fail')
    rows = envelope.get('jobs', [])
    if len(rows) != 1 or rows[0]['job_id'] != producer[0]['id'] or rows[0]['conclusion'] != 'failure':
        raise ValueError('unexpected failed job inventory')
    # Require the emitted line, not just the echoed script containing the marker.
    if f'\x1b[31m{MARKER}:{candidate}:{run_id}\x1b[0m' not in rows[0]['raw_log']:
        raise ValueError('actual ANSI sentinel bytes missing from downloaded log')
    return dict(schema_version=1, candidate=candidate, repository=repository, run_id=run_id,
                diagnostic_only=True, non_voting=True, reusable_for_approval=False,
                task_approved=False, integration_allowed=False, passed=True,
                expected_workflow_conclusion='failure', expected_failed_job_id=producer[0]['id'],
                explanation='The deliberate producer failure is required; only transport and setup are verified.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    repository, run_id, candidate = os.environ['GITHUB_REPOSITORY'], int(os.environ['GITHUB_RUN_ID']), os.environ['GITHUB_SHA']
    def api(endpoint, name):
        raw = subprocess.check_output(['gh', 'api', endpoint])
        (out/name).write_bytes(raw)
        return json.loads(raw)
    run = api(f'repos/{repository}/actions/runs/{run_id}', 'run.json')
    jobs = api(f'repos/{repository}/actions/runs/{run_id}/jobs?per_page=100', 'jobs.json')
    envelope = collect(run, jobs, run_id, repository, out/'job-logs.json')
    report = verify_probe(run, jobs, envelope, repository, run_id, candidate)
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
