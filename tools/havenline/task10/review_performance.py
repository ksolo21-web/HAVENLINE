#!/usr/bin/env python3
"""Ingest an original independent C6 judgment plus its measured supplement."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/havenline/production'))
from critic_harness import validate_raw, c6
from aggregate_critics import verify_original, verify_performance_binding


def validate(record_path, manifest_path, performance_path, candidate):
    record_path, manifest_path, performance_path = [Path(p).resolve() for p in (record_path, manifest_path, performance_path)]
    record = json.loads(record_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    assert record['input_manifest_hash'] == hashlib.sha256(manifest_path.read_bytes()).hexdigest(), 'manifest digest mismatch'
    original_raw_path = Path(record['raw_output_path'])
    raw_path = (record_path.parent / original_raw_path).resolve()
    if not raw_path.is_relative_to(record_path.parent) or not raw_path.is_file():
        raw_path = record_path.parent / original_raw_path.name
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == record['raw_output_hash'], 'raw digest mismatch'
    assert record.get('request_or_run_id') and record.get('provider') and record.get('model'), 'actual reviewer provenance required'
    payload = json.loads(raw_path.read_text())
    assert payload.get('candidate_hash') == candidate and payload.get('critic_id') == 'C6', 'raw C6 identity mismatch'
    verify_original(record, payload, manifest, 'C6', candidate)
    normalized=dict(record,raw_output_path=str(raw_path),transport_original_record_sha256=hashlib.sha256(record_path.read_bytes()).hexdigest(),transport_original_raw_path=record['raw_output_path'])
    with tempfile.TemporaryDirectory(prefix='t10-c6-ingest-') as temporary:
        normalized_path=Path(temporary)/'transport-record.json'
        normalized_path.write_text(json.dumps(normalized))
        result = validate_raw(normalized_path, 'C6', candidate)
    verify_performance_binding(performance_path, manifest, candidate)
    supplement = c6(performance_path, candidate)
    return dict(critic_id='C6', candidate=candidate, scored_review=result, quantitative_c6=supplement,
                passed=result['passed'] and supplement['passed'])


def main():
    ap = argparse.ArgumentParser()
    for key in ('candidate', 'manifest', 'record', 'performance', 'output'):
        ap.add_argument('--'+key, required=True)
    a = ap.parse_args()
    result = validate(a.record, a.manifest, a.performance, a.candidate)
    Path(a.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['passed'] else 1)

if __name__ == '__main__':
    main()
