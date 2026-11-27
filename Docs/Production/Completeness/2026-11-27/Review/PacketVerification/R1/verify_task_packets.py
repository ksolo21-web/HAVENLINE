#!/usr/bin/env python3
"""Capture actual task_packet.main output without writing into its repository.

This is source/packet-contract verification only. It never runs the game or
approves task activation, visuals, animation, gameplay, or release quality.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
from unittest import mock

sys.dont_write_bytecode = True
TASKS = ['T01', 'T23', 'T26', 'T27', 'T33', 'T43', 'T44', 'T58', 'T70']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(path, root=None):
    if not path.is_file():
        return {'path': str(path.relative_to(root) if root else path), 'exists': False}
    data = path.read_bytes()
    return {'path': str(path.relative_to(root) if root else path), 'exists': True,
            'bytes': len(data), 'sha256': digest(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, type=pathlib.Path)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    output = args.output.resolve()
    if output.is_relative_to(candidate):
        raise SystemExit('Verification output must be outside the candidate.')
    output.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    docs = candidate / 'Docs/Production'
    production = candidate / 'tools/havenline/production'
    canonical_paths = set(docs.rglob('TASK_PACKET.md'))
    canonical_paths.update(docs / 'Evidence' / task / 'TASK_PACKET.md' for task in TASKS)
    canonical_before = [identity(p, candidate) for p in sorted(canonical_paths)]
    guard_paths = set(production.rglob('*.py'))
    guard_paths.update(docs / name for name in [
        'WHOLE_GAME_COMPLETENESS.json', 'GAMEPLAY_DEPTH_CONTRACT.json',
        'CURRENT_GAMEPLAY_SOURCE.json', 'REFERENCE_ACCEPTANCE_POLICY.json',
        'RESOURCE_ACTION_REGISTRY.json', 'ACTOR_CAPABILITY_MATRIX.json',
        'ANIMATION_ACTION_MATRIX.json', 'DEPENDENCY_GRAPH.json',
        'WORKSTREAM_REGISTRY.json', 'PATH_OWNERSHIP.json', 'CRITIC_MATRIX.json',
        'CRITIC_EXECUTION.json', 'task-gates.json',
        'Completeness/2026-11-27/ACTORS_COMBAT_GAPS.json',
        'Completeness/2026-11-27/PROGRESSION_ECONOMY_GAPS.json',
        'Completeness/2026-11-27/TRANSACTIONS_AND_RECOVERY.json',
    ])
    guarded_before = [identity(p, candidate) for p in sorted(guard_paths)]
    read_paths = set()
    blocked_direct_mutations = []

    def under_candidate(value):
        if not isinstance(value, (str, bytes, os.PathLike)):
            return False
        try:
            return pathlib.Path(os.fsdecode(value)).absolute().is_relative_to(candidate)
        except (TypeError, ValueError):
            return False

    def audit(event, values):
        # Extra guard beyond the requested Path.mkdir/write_text interception.
        if event == 'open' and under_candidate(values[0]):
            path, mode, flags = values
            writing = (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
            if writing:
                blocked_direct_mutations.append({'event': event, 'path': str(path)})
                raise RuntimeError('Read-only candidate guard rejected direct write: ' + str(path))
            read_paths.add(str(pathlib.Path(os.fsdecode(path)).absolute().relative_to(candidate)))
        elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.symlink'}:
            if any(under_candidate(v) for v in values[:2]):
                blocked_direct_mutations.append({'event': event, 'arguments': repr(values)})
                raise RuntimeError('Read-only candidate guard rejected mutation: ' + event)

    sys.addaudithook(audit)
    sys.path.insert(0, str(production))
    import task_packet as packet
    import completeness

    contract = json.loads((docs / 'WHOLE_GAME_COMPLETENESS.json').read_text())
    gd_contract = json.loads((docs / 'GAMEPLAY_DEPTH_CONTRACT.json').read_text())
    selector = json.loads((docs / 'CURRENT_GAMEPLAY_SOURCE.json').read_text())
    policy = json.loads((docs / 'REFERENCE_ACCEPTANCE_POLICY.json').read_text())
    original_schema = packet.validate_resource_actor_schema
    original_completeness_section = packet.completeness_section
    original_load_json = packet.load_json
    checks = []

    def check(name, passed, details=None):
        checks.append({'check': name, 'passed': bool(passed), 'details': details})

    def capture(task, *, malformed_attack=False, malformed_outcome=False):
        writes, events, mkdirs = {}, [], []
        stdout = io.StringIO()
        expected_target = docs / 'Evidence' / task / 'TASK_PACKET.md'

        def intercept_mkdir(path, *a, **kw):
            mkdirs.append(str(path))
            events.append({'stage': 'intercepted_mkdir', 'path': str(path)})

        def intercept_write_text(path, data, encoding=None, errors=None, newline=None):
            events.append({'stage': 'intercepted_write_text', 'path': str(path)})
            if path != expected_target or str(path) in writes:
                raise RuntimeError('Unexpected/duplicate attempted packet output: ' + str(path))
            writes[str(path)] = data
            return len(data)

        def schema(*a, **kw):
            events.append({'stage': 'resource_schema_start'})
            result = original_schema(*a, **kw)
            events.append({'stage': 'resource_schema_result', 'errors': result})
            return result

        def completeness_section(*a, **kw):
            events.append({'stage': 'completeness_start'})
            result = original_completeness_section(*a, **kw)
            events.append({'stage': 'completeness_return'})
            return result

        def load_json(path):
            result = original_load_json(path)
            if malformed_attack and path == packet.ANIMATION_MATRIX:
                result = copy.deepcopy(result)
                del result['profiles']['fox_attack']
            return result

        mutated_data = None
        if malformed_outcome:
            mutated_data = copy.deepcopy(completeness.load())
            del mutated_data[2]['progression_goals'][98]['outcome']
        failure = None
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(pathlib.Path, 'mkdir', intercept_mkdir))
            stack.enter_context(mock.patch.object(pathlib.Path, 'write_text', intercept_write_text))
            stack.enter_context(mock.patch.object(packet, 'validate_resource_actor_schema', schema))
            stack.enter_context(mock.patch.object(packet, 'completeness_section', completeness_section))
            stack.enter_context(mock.patch.object(packet, 'load_json', load_json))
            stack.enter_context(mock.patch.object(sys, 'argv', ['task_packet.py', task]))
            stack.enter_context(contextlib.redirect_stdout(stdout))
            if mutated_data is not None:
                stack.enter_context(mock.patch.object(completeness, 'load', return_value=mutated_data))
            try:
                packet.main()
            except (Exception, SystemExit) as exc:
                failure = {'type': type(exc).__name__, 'message': str(exc)}
        return {'task_id': task, 'failure': failure, 'stdout': stdout.getvalue(),
                'events': events, 'intercepted_mkdir_calls': mkdirs,
                'intercepted_write_count': len(writes), 'writes': writes}

    packets = []
    for task in TASKS:
        result = capture(task)
        check(task + ': main returned successfully', result['failure'] is None, result['failure'])
        check(task + ': exactly one packet write captured', result['intercepted_write_count'] == 1)
        text = next(iter(result['writes'].values()), '')
        expected_cg = [r['id'] for r in contract['requirements'] if task in r['owner_tasks'] + r['consumer_tasks']]
        actual_cg = re.findall(r'^- \*\*(CG\d{2}) —', text, flags=re.M)
        expected_gd = [r['id'] for r in gd_contract['requirements'] if task in r['owner_tasks'] + r['consumer_tasks']]
        actual_gd = re.findall(r'^- \*\*(GD\d{2}) —', text, flags=re.M)
        expected_cd = sorted({decision for r in contract['requirements'] if r['id'] in expected_cg for decision in r['decision_ids']} |
                             {r['id'] for r in contract['decisions'] if task in r['owner_tasks']})
        cd_line = re.search(r'^Applicable selected decisions: ([^\n]*)\.$', text, flags=re.M)
        actual_cd = cd_line.group(1).split(', ') if cd_line and cd_line.group(1) else []
        check(task + ': exact applicable CG IDs', actual_cg == expected_cg, {'expected': expected_cg, 'actual': actual_cg})
        check(task + ': exact applicable GD IDs retained', actual_gd == expected_gd, {'expected': expected_gd, 'actual': actual_gd})
        check(task + ': exact applicable selected CD IDs', actual_cd == expected_cd, {'expected': expected_cd, 'actual': actual_cd})
        check(task + ': CD behavior supersession with unproved evidence',
              'The CD choices supersede the earlier D01–D05 open behavior wording; numeric tuning and actual game evidence remain open.' in text)
        check(task + ': current source selector is required reading', '`CURRENT_GAMEPLAY_SOURCE.json`' in text,
              'Packet references the current selector; branch/head/project/scene are dereferenced and verified separately below, not falsely claimed embedded in packet text.')
        check(task + ': unrounded reference minimum and exact-10 gates retained',
              'Final reference-sensitive dimensions >=9.9 unrounded; preserve all stronger exact-10 visual gates.' in text and
              'A reference-sensitive 9.5 is interim only.' in text and 'No averaging, rounding, missing evidence or unresolved mandatory defects.' in text)
        check(task + ': no new activation or runtime approval',
              'These responsibilities are not new dependency edges or task activation' in text and
              'All gameplay scenarios remain unrun by this audit.' in text)
        if task == 'T44':
            check('T44: stronger regional C5 applies to approved-clip reuse without new-clip requirement',
                  'regional_resource_contact' in text and
                  '`animation_delta=false` cannot waive actual regional contact proof' in text and
                  'including approved-clip reuse' in text and 'reuse does not require a new clip' in text)
        captured_path = output / (task + '.TASK_PACKET.md')
        captured_path.write_text(text, encoding='utf-8')
        stdout_path = output / (task + '.stdout.txt')
        stdout_path.write_text(result['stdout'], encoding='utf-8')
        result.pop('writes')
        result.update({'output': identity(captured_path), 'expected_cg_ids': expected_cg,
                       'actual_cg_ids': actual_cg, 'expected_gd_ids': expected_gd,
                       'actual_gd_ids': actual_gd, 'expected_cd_ids': expected_cd,
                       'actual_cd_ids': actual_cd})
        packets.append(result)
        print('Captured ' + task, flush=True)

    negatives = []
    for name, task, flags, expected_type, expected_message, completeness_calls in [
        ('removed_fox_attack', 'T26', {'malformed_attack': True}, 'SystemExit',
         'Invalid resource/actor declarations:', 0),
        ('missing_level_099_outcome', 'T70', {'malformed_outcome': True}, 'ValueError',
         'Invalid completeness contract: 100 distinct authored outcomes required', 1),
    ]:
        result = capture(task, **flags)
        failure = result['failure'] or {}
        check(name + ': rejected by expected gate', failure.get('type') == expected_type and expected_message in failure.get('message', ''), failure)
        check(name + ': no packet write attempted', result['intercepted_write_count'] == 0)
        check(name + ': no packet directory creation attempted', not result['intercepted_mkdir_calls'])
        check(name + ': expected gate order',
              sum(e['stage'] == 'completeness_start' for e in result['events']) == completeness_calls and
              result['events'][0]['stage'] == 'resource_schema_start', result['events'])
        result.pop('writes')
        result['probe'] = name
        result['mutation_scope'] = 'Deep copy of loaded data only; no file or registry changed.'
        negatives.append(result)

    check('Current selector uses requested newer Codex source',
          selector['selected_branch'] == 'trial/world-one-expansion-2026-11-26' and
          selector['observed_head'] == '3fad812b384335bd8ca9b5e47dc9d9557110eb4a' and
          selector['project'] == 'HavenlineLevel1/project.godot' and selector['main_scene'] == 'res://field_opening.tscn', selector)
    check('Source selector does not authorize runtime, reassignment, merge or workflow activation',
          all(selector[k] is False for k in ['runtime_approval_allowed', 'ownership_reassignment_allowed', 'gameplay_merge_performed', 'workflow_activation_allowed']))
    check('Policy keeps >=9.9 unrounded and stronger exact10 with mandatory independent evidence',
          policy['final_acceptance']['reference_minimum_dimension_score'] == 9.9 and
          policy['final_acceptance']['exact_score'] == 10 and
          all(policy['final_acceptance'][k] is True for k in ['forbid_averaging', 'require_unrounded', 'all_mandatory_checks_pass', 'complete_evidence_required', 'independent_review_required']))
    canonical_after = [identity(p, candidate) for p in sorted(canonical_paths)]
    actual_canonical_paths = set(docs.rglob('TASK_PACKET.md'))
    check('All existing canonical packet bytes and requested output absences unchanged', canonical_before == canonical_after)
    check('No unexpected canonical packet created', actual_canonical_paths == {p for p in canonical_paths if p.is_file()})
    guarded_after = [identity(p, candidate) for p in sorted(guard_paths)]
    check('All guarded generator/helper sources and contract inputs unchanged', guarded_before == guarded_after)
    check('No direct candidate filesystem mutation attempted', not blocked_direct_mutations, blocked_direct_mutations)
    code_names = ['task_packet.py', 'completeness.py', 'resource_actor_contract.py']
    report = {
        'schema_version': 1,
        'scope': 'Actual task_packet.main execution and bounded packet-contract verification; no runtime game, motion, visual, device, activation or release approval.',
        'candidate_path': str(candidate), 'candidate_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=candidate).decode().strip(),
        'started_at_utc': started, 'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'runtime_tested': False, 'runtime_approval_allowed': False, 'canonical_packets_modified': False,
        'requested_tasks': TASKS, 'positive_main_calls': len(packets),
        'positive_calls_succeeded': sum(r['failure'] is None for r in packets),
        'captured_packet_write_calls': sum(r['intercepted_write_count'] for r in packets),
        'negative_main_calls': len(negatives),
        'negative_calls_rejected': sum(r['failure'] is not None for r in negatives),
        'negative_packet_write_calls': sum(r['intercepted_write_count'] for r in negatives),
        'check_count': len(checks), 'passed_count': sum(c['passed'] for c in checks),
        'failed_count': sum(not c['passed'] for c in checks),
        'all_checks_passed': all(c['passed'] for c in checks),
        'generator_and_validator_bindings': [identity(production / n, candidate) for n in code_names],
        'verification_script': identity(pathlib.Path(__file__).resolve()),
        'canonical_packets_before': canonical_before, 'canonical_packets_after': canonical_after,
        'guarded_sources_before': guarded_before, 'guarded_sources_after': guarded_after,
        'python_read_paths': sorted(read_paths), 'packets': packets, 'negative_probes': negatives,
        'checks': checks,
        'limitations': [
            'Captured packets are prospective output; historical canonical packets remain unchanged.',
            'Current source selection is dereferenced from the required selector file; no live branch fetch or gameplay source editing performed.',
            'Dates in captured packet bodies are the real generator timestamps and are included in raw output hashes.',
            'Path.mkdir and Path.write_text were intercepted for every main call; a separate audit hook blocked direct candidate mutations.',
            'The older GD decision wording remains historical; the following CD section explicitly supersedes those open behavior choices.',
            'Static declaration and fail-fast checks do not prove pet attacks, 100 levels, animation, economy balance, runtime safety or reference-match scores.',
        ],
    }
    (output / 'PACKET_VERIFICATION_REPORT.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    lines = ['# Actual task-packet verification', '',
             f"**{report['passed_count']}/{report['check_count']} checks passed; {report['failed_count']} failed.**",
             f"Actual generator calls: {report['positive_calls_succeeded']}/{report['positive_main_calls']} succeeded; both deliberate invalid-data calls were rejected, with zero packet writes.", '',
             'This report verifies prospective packet content and rejection behavior. It grants no game, motion, visual, device or activation approval.', '',
             '## Actual packet captures', '', '| Task | CG IDs | Selected CD IDs | Output SHA-256 |', '|---|---|---|---|']
    for r in packets:
        lines.append('| ' + ' | '.join([r['task_id'], ', '.join(r['actual_cg_ids']) or 'none', ', '.join(r['actual_cd_ids']) or 'none', r['output']['sha256']]) + ' |')
    lines += ['', '## Rejection probes', '']
    for r in negatives:
        lines.append('- **' + r['probe'] + ':** ' + str(r['failure']) + '; packet writes: ' + str(r['intercepted_write_count']) + '.')
    lines += ['', '## Preservation and source binding', '',
              f"{sum(r['exists'] for r in canonical_before)} existing canonical packets remained byte-identical. All nine requested Evidence output paths retained their prior existence/absence. {len(guarded_before)} guarded source/input files remained unchanged.",
              'Generator, completeness validator, resource validator, verification script, every captured output and all canonical before/after hashes are bound in the JSON report.', '',
              'T44 retains regional contact/use-state C5 evidence even for approved-clip reuse; animation_delta=false does not waive contact proof and reuse does not require a new clip.', '',
              'Every packet retains applicable GD obligations, the current CG/CD decisions, explicit supersession of D01–D05 behavior choices, required reading of the current Codex source selector, >=9.9 unrounded reference checks and stronger exact-10 visual gates.', '',
              '## Limits', '']
    lines += ['- ' + x for x in report['limitations']]
    if not report['all_checks_passed']:
        lines += ['', '## Failures', ''] + ['- ' + c['check'] + ': ' + repr(c['details']) for c in checks if not c['passed']]
    (output / 'PACKET_VERIFICATION_REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['positive_main_calls', 'positive_calls_succeeded', 'negative_main_calls', 'negative_calls_rejected', 'negative_packet_write_calls', 'check_count', 'passed_count', 'failed_count', 'all_checks_passed']}, indent=2), flush=True)
    raise SystemExit(0 if report['all_checks_passed'] else 1)


if __name__ == '__main__':
    main()
