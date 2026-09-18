#!/usr/bin/env python3
"""Collect completed-job logs while the diagnostic's parent run is still active."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def collect(run, jobs, run_id, repository, output):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('canonical owner/repository required')
    if type(run_id) is not int or run_id <= 0 or run.get('id') != run_id:
        raise ValueError('run identity mismatch')
    if run.get('repository', {}).get('full_name') != repository:
        raise ValueError('repository identity mismatch')
    status, conclusion = run.get('status'), run.get('conclusion')
    cancelled = status == 'completed' and conclusion == 'cancelled'
    if not (status == 'in_progress' and conclusion is None or
            status == 'completed' and conclusion in ('failure', 'timed_out', 'cancelled', 'startup_failure')):
        raise ValueError('inconsistent or unsupported run state')
    rows = jobs.get('jobs')
    if not isinstance(rows, list) or jobs.get('total_count') != len(rows):
        raise ValueError('complete jobs response required')
    seen, selected = set(), []
    for job in rows:
        jid = job.get('id')
        if type(jid) is not int or jid <= 0 or jid in seen or job.get('run_id') != run_id:
            raise ValueError('duplicate, invalid or cross-run job identity')
        seen.add(jid)
        if job.get('status') != 'completed':
            if job.get('conclusion') is not None or status == 'completed':
                raise ValueError('inconsistent job state')
            continue
        if job.get('conclusion') not in ('success', 'failure', 'neutral', 'cancelled', 'skipped', 'timed_out', 'action_required', 'stale', 'startup_failure'):
            raise ValueError('completed job requires a recognized terminal conclusion')
        if job.get('conclusion') in ('failure', 'timed_out') or cancelled and job.get('conclusion') == 'cancelled':
            selected.append(job)
    marker = None
    if not selected:
        if cancelled:
            marker = 'CANCELLED_NO_FAILED_JOB'
        elif status == 'completed' and conclusion == 'startup_failure':
            marker = 'STARTUP_FAILURE_NO_JOB_LOG'
        else:
            raise ValueError('no completed failed job logs available')
    envelope = {'schema_version': 1, 'run_id': run_id, 'repository': repository,
                'run_status': status, 'run_conclusion': conclusion,
                'run_cancelled': cancelled, 'non_product_diagnostic': cancelled or marker is not None,
                'diagnostic_marker': marker, 'jobs': []}
    for job in sorted(selected, key=lambda row: row['id']):
        result = subprocess.run(['gh', 'api', f"repos/{repository}/actions/jobs/{job['id']}/logs"], capture_output=True)
        if result.returncode or not result.stdout.strip():
            raise ValueError(f"job {job['id']} log retrieval failed or empty")
        raw = result.stdout
        envelope['jobs'].append({'job_id': job['id'], 'name': job.get('name'),
            'conclusion': job['conclusion'], 'log_bytes': len(raw),
            'log_sha256': hashlib.sha256(raw).hexdigest(), 'raw_log': raw.decode('utf-8', errors='replace')})
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as stream:
            temporary = stream.name
            json.dump(envelope, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return envelope


def main():
    parser = argparse.ArgumentParser()
    for arg in ('run', 'jobs', 'repository', 'output'):
        parser.add_argument('--' + arg, required=True)
    parser.add_argument('--run-id', required=True, type=int)
    args = parser.parse_args()
    collect(json.loads(Path(args.run).read_text()), json.loads(Path(args.jobs).read_text()),
            args.run_id, args.repository, args.output)


if __name__ == '__main__':
    main()
