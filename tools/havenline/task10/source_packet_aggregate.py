#!/usr/bin/env python3
"""Aggregate all independent non-voting packets without partial-coverage passes."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import source_packets as m


def aggregate(root: Path, source: str, tree: str, source_text: str) -> dict:
    expected = m.packets(source_text, source, tree)
    errors = []
    rows = []
    seen = set()
    results = sorted(root.rglob('group-result.json'))
    for path in results:
        try:
            row = m.exact_json(path.read_text())
            group = row.get('group')
            if group not in expected['groups'] or group in seen:
                raise ValueError('unknown or duplicate group')
            seen.add(group)
            packet = expected['groups'][group]
            required = {'source': source, 'tree': tree, 'source_sha256': expected['source']['sha256'],
                        'functions': packet['functions'], 'prompt_sha256': packet['prompt_sha256'],
                        'passed': True, 'task_approved': False, 'non_voting': True, 'final_critic_vote': False,
                        'token_admission_passed': True, 'provider': 'unsloth/Qwen3.5-9B-GGUF',
                        'model': 'Qwen/Qwen3.5-9B', 'revision': '3885219b6810b007914f3a7950a8d1b469d598a5',
                        'runtime_release': 'b10809'}
            if any(row.get(k) != value or type(row.get(k)) is not type(value) for k, value in required.items()):
                raise ValueError('source/runtime/completion identity mismatch')
            if type(row.get('input_tokens')) is not int or not 0 < row['input_tokens'] <= m.INPUT_TOKEN_BUDGET:
                raise ValueError('missing measured input admission')
            manifest_path = path.parent / 'packet-manifest.json'
            manifest_raw = manifest_path.read_bytes()
            if m.digest(manifest_raw) != row.get('input_manifest_sha256') or m.exact_json(manifest_raw) != expected:
                raise ValueError('packet-manifest content/hash mismatch')
            raw_path = path.parent / 'review.response.json'
            raw_bytes = raw_path.read_bytes()
            if m.digest(raw_bytes) != row.get('raw_response_sha256'):
                raise ValueError('raw review hash mismatch')
            raw = m.exact_json(raw_bytes)
            choices = raw.get('choices')
            if not isinstance(choices, list) or len(choices) != 1 or choices[0].get('finish_reason') != 'stop':
                raise ValueError('raw review incomplete')
            review = m.exact_json(choices[0]['message']['content'])
            if review != row.get('review') or m.result_errors(review) or row.get('errors') != [] or row.get('tool_error'):
                raise ValueError('nonpassing or unbound review')
            rows.append({'group': group, 'functions': packet['functions'], 'scores': review['scores'],
                         'defects': review['defects'], 'result_sha256': m.digest(path.read_bytes()),
                         'raw_response_sha256': row['raw_response_sha256'], 'input_tokens': row['input_tokens'],
                         'review_run_id': row.get('review_run_id'), 'review_job': row.get('review_job')})
        except (ValueError, OSError, KeyError, TypeError) as error:
            errors.append(str(path.relative_to(root)) + ': ' + str(error))
    if len(results) != len(expected['groups']) or seen != set(expected['groups']):
        errors.append('complete independent packet set missing or duplicated')
    return {'kind': 'INDEPENDENT_PRODUCT_SOURCE_PACKET_REVIEW', 'source': source, 'tree': tree,
            'source_sha256': expected['source']['sha256'], 'required_groups': sorted(expected['groups']),
            'validated_groups': len(rows), 'covered_primary_functions': sum(len(row['functions']) for row in rows),
            'required_primary_functions': expected['source_function_count'], 'groups': rows,
            'lowest_score': min((v for row in rows for v in row['scores'].values()), default=0),
            'passed': not errors, 'errors': errors, 'non_voting': True, 'task_approved': False,
            'final_critic_vote': False, 'T11_unlocked': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True); parser.add_argument('--tree', required=True)
    parser.add_argument('--input', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    text = subprocess.check_output(['git', 'show', args.source + ':' + m.SOURCE_PATH]).decode()
    report = aggregate(args.input, args.source, args.tree, text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['passed'] else 1)
