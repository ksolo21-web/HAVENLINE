#!/usr/bin/env python3
"""Build a deterministic PROPOSED T10 closeout overlay; never approve or publish.

Input JSON contains candidate, base, integration_head (source or later governance ancestor of export),
export_commit, approved_at, export_arguments (the existing exporter's original
API/archive/reviewer inputs), and hash references {path, sha256} for gates,
path_validation, tests, progression, factory_observation and defect_dispositions.
Gate input is {candidate_commit, gates: {G1: {status, proofs: [reference]}, ...}}.
Every proof is a successful exact-source JSON result, not a caller boolean.
Defect dispositions contain candidate_commit and nonempty individual defects
with id, classification, affected_object, causal_files, command_or_gate,
reviewer_or_owner, proof_candidate, unresolved=false, status=VERIFIED_CLOSED,
and verification_proofs. Each proof must repeat its blocker_id, affected_object,
causal_files, command_or_gate and reviewer_or_owner exactly. Causal files equal
the canonical authorized files actually changed from C0's failed candidate,
excluding canonical C0/repair-plan bookkeeping. Their IDs must equal the canonical C0 report blocker
set; c0_report is itself a hash reference to the canonical C0_ROOT_CAUSE.json.

All assembly and actual consumer execution happens in a disposable local clone
with its remote removed. Only a complete passing PROPOSED overlay is emitted.
An integration owner must separately review and atomically publish that overlay.
There is intentionally no diagnostic bypass in this command-line entry point.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
TASK = 'Docs/Production/T10'
EVIDENCE = 'Docs/Production/Evidence/T10'
PRODUCTION = 'tools/havenline/production'
CRITICS = ('C1', 'C2', 'C3', 'C4', 'C6', 'C7')
AUTHORITIES = ('DEPENDENCY_GRAPH.json', 'WORKSTREAM_REGISTRY.json',
               'PATH_OWNERSHIP.json', 'task-gates.json', 'GATE_RESULT_INDEX.json')


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def load(path):
    return json.loads(Path(path).read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reject_diagnostic(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require(not (key.lower() in {'diagnostic_only', 'synthetic', 'test_fixture', 'fixture_only'} and item),
                    'diagnostic inputs cannot become production closeout')
            reject_diagnostic(item)
    elif isinstance(value, list):
        for item in value:
            reject_diagnostic(item)
    elif isinstance(value, str):
        require(not any(token in value.lower() for token in
                        ('synthetic-test', 'diagnostic-only', 'fixture-provider', 'test-only-fixture')),
                'diagnostic provenance cannot become production closeout')


def read_reference(ref):
    require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}, 'hash-bound file reference required')
    path = Path(ref['path'])
    require(path.is_file() and not path.is_symlink(), 'proof must be a regular non-symlink file')
    data = path.read_bytes()
    require(digest(data) == ref['sha256'], 'proof hash mismatch: ' + str(path))
    value = json.loads(data)
    reject_diagnostic(value)
    return value, data


def source_pass(value, candidate, label):
    sources = [value[k] for k in ('candidate_commit', 'candidate', 'source_sha', 'candidate_hash') if k in value]
    require(sources and all(v == candidate for v in sources), label + ': exact source required')
    require((value.get('passed') is True or value.get('status') == 'PASS') and value.get('passed') is not False and value.get('status', 'PASS') == 'PASS', label + ': successful result required')
    require(not value.get('errors') and not value.get('defects'), label + ': unresolved errors/defects')


def run_cli(repo, relative, *args):
    command = [sys.executable, str(repo / relative), *map(str, args)]
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
    return {'command': [relative, *map(str, args)], 'exit_code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def successful(report):
    require(report['exit_code'] == 0, 'consumer failed: ' + report['command'][0] + '\n' + report['stdout'] + report['stderr'])
    return report


def write(repo, rel, value):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else encoded(value))


def stage_authorities(repo, candidate, base, approved_at, minimum, artifact, index_hash, environment):
    """Pure staged transition, preserving other tasks and original owner identity."""
    docs = repo / 'Docs/Production'
    data = {name: load(docs / name) for name in AUTHORITIES}
    graph, registry, ownership, gates, index = (data[n] for n in AUTHORITIES)
    require(all(graph['tasks'][f'T{i:02d}']['status'] == 'APPROVED' for i in range(1, 10)), 'approved dependency prefix required')
    require(all(graph['tasks'][f'T{i:02d}']['status'] == 'LOCKED' for i in range(11, 71)), 'future tasks must remain locked')
    rows = [r for r in registry['workstreams'] if r.get('task_id') == 'T10']
    owners = [r for r in ownership['active_owners'] if r.get('task_id') == 'T10']
    require(len(rows) == len(owners) == 1, 'unique active T10 owner/workstream required')
    require(not any(str(r.get('task_id', '')) >= 'T11' for r in ownership['active_owners']), 'future active owner')
    require(not any(r.get('task_id') == 'T10' for r in ownership['completed_production_owners']), 'T10 already closed')
    ws, owner = rows[0], owners[0]
    require(ws['status'] in {'UNDER_REVIEW', 'INTEGRATION_READY', 'INTEGRATING'}, 'T10 must be integration-ready or under review')
    require(ws['base_commit'] == owner['base_commit'] and re.fullmatch('[0-9a-f]{40}', ws['base_commit']), 'assignment owner/base identity mismatch')
    require(all(owner[a] == ws[b] for a, b in [('workstream', 'workstream_id'), ('owner', 'owner'), ('branch', 'branch')]), 'owner identity mismatch')
    graph['tasks']['T10']['status'] = 'APPROVED'
    ws.update(status='APPROVED', candidate_commit=candidate, known_blockers=[],
              integration_status='APPROVED; exact source ' + candidate,
              next_action='Preserve T10 closure; T11 remains locked pending separate activation.', status_updated_at=approved_at)
    completed = dict(owner, status='APPROVED', accepted_source=candidate, integrated_source=candidate)
    ownership['active_owners'].remove(owner)
    ownership['completed_production_owners'].append(completed)
    for key in gates:
        if key.startswith('active_'):
            gates[key] = None
    require(gates['approved_tasks'] == [f'T{i:02d}' for i in range(1, 10)], 'unexpected approved task prefix')
    gates['approved_tasks'].append('T10')
    gates['approved_task_count'] = 10
    gates['completed_task_records']['T10'] = dict(status='APPROVED', accepted_source=candidate,
        integrated_source=candidate, minimum_mandatory_dimension_score=minimum, gate_operator='> 9.0',
        integrated_evidence_run=artifact['run_id'], artifact_id=artifact['artifact_id'],
        record=TASK + '/verified-completion.json', later_regression_reopens_task=True)
    wave = [r for r in gates['next_post_t03_wave'] if r.get('task') == 'T10']
    require(len(wave) == 1, 'unique T10 wave required')
    wave[0].update(state='APPROVED', owner=ws['owner'], branch=ws['branch'], base_commit=ws['base_commit'],
                   reason='Exact-source strict closeout; see verified-completion.json.')
    require(not any(r.get('task_id') == 'T10' and r.get('candidate') == candidate for r in index['records']), 'duplicate source provenance')
    index['records'].append(dict(record_type='exact_source_provenance', task_id='T10',
        gate_family='integrated_candidate_g1_g14', candidate=candidate, result='PASS', reuse_eligible=False,
        recorded_at=approved_at, workflow_run_id=artifact['run_id'], runner_provenance=environment, evidence=dict(
            original_artifact_id=artifact['artifact_id'], original_artifact_sha256=artifact['digest'].removeprefix('sha256:'),
            complete_evidence_index_sha256=index_hash,
            retained_artifact_id=artifact['artifact_id'], retained_artifact_sha256=artifact['digest'].removeprefix('sha256:'),
            retained_until=artifact['expires_at'])))
    for name, value in data.items():
        write(repo, 'Docs/Production/' + name, value)


def assemble_records(repo, spec, inputs):
    """Serialization only. Production caller verifies originals before entering."""
    candidate = spec['candidate']
    index_path = EVIDENCE + '/complete-evidence-index.json'
    index = load(repo / index_path)
    index_hash = digest((repo / index_path).read_bytes())
    require(index['candidate_commit'] == candidate and index['task_id'] == 'T10', 'canonical index source mismatch')
    review_manifest = load(repo / EVIDENCE / 'REVIEW_EVIDENCE_MANIFEST.json')
    require(len(review_manifest['records']) == 1, 'single review artifact required')
    retained_row = review_manifest['records'][0]
    identity = retained_row['content_identity']
    retained = dict(run_id=identity['original_run_id'], artifact_id=identity['original_artifact_id'],
                    digest='sha256:' + identity['original_artifact_sha256'], expires_at=retained_row['expires_at'])
    common = dict(candidate_commit=candidate, workflow_run_id=retained['run_id'], artifact_id=retained['artifact_id'],
                  artifact_sha256=identity['original_artifact_sha256'], complete_evidence_index_sha256=index_hash)
    critics = {}
    for cid in CRITICS:
        rel = TASK + '/CriticRaw/' + cid + '.json'
        raw = load(repo / rel)
        original = load(repo / TASK / 'ReviewExports' / (cid + '-original-record.json'))
        require(original['independent_runtime'] is True and original['scores'] == raw['scores'], 'independent original mismatch')
        require(all(raw.get(k) == v for k, v in common.items()), 'canonical critic identity mismatch')
        critics[cid] = {k: copy.deepcopy(raw[k]) for k in ('status', 'candidate_commit', 'scores', 'coverage_complete', 'defects', 'minimum_dimension_score')}
        critics[cid].update(independent_runtime=original['independent_runtime'], raw_record_path=rel,
                            raw_record_sha256=digest((repo / rel).read_bytes()))
    critics['C7'].update(task_id='T10', deterministic_supplement=inputs['progression'])
    minimum = min(min(row['scores'].values()) for row in critics.values())
    aggregate = dict(common, task_id='T10', status='PASS', disposition='APPROVED', approved_at=spec['approved_at'],
        coverage_complete=True, unresolved_mandatory_defects=[], minimum_mandatory_dimension_score=minimum, critics=critics,
        retained_review_evidence=dict(workflow_run_id=retained['run_id'], artifact_id=retained['artifact_id'],
                                      artifact_sha256=identity['original_artifact_sha256'], expires_at=retained['expires_at']))
    dispositions = inputs['defect_dispositions']
    ledger = dict(dispositions, candidate_commit=candidate, integrated_commit=candidate, unresolved_mandatory_count=0,
                  unresolved_tooling_count=0, critic_approval_pending=False,
                  critic_scores={cid: min(row['scores'].values()) for cid, row in critics.items()})
    completion = dict(common, task_id='T10', base_commit=spec['base'], critics=critics,
        critic_review_export_commit=spec['export_commit'], retained_review_evidence=retained,
        path_validation=inputs['path_validation'], tests=inputs['tests'], gates=inputs['gates']['gates'],
        evidence=dict(candidate_commit=candidate, provenance_hash=index_hash, root='.', files={index_path: index_hash}),
        unresolved_mandatory_defects=[], integration=dict(candidate_commit=candidate, regression_passed=True),
        resource_actor_contract=dict(applicable=False), game_master_contract=dict(applicable=False))
    for name, value in [('independent-critic-review.json', aggregate), ('defect-ledger.json', ledger), ('verified-completion.json', completion)]:
        write(repo, TASK + '/' + name, value)
    stage_authorities(repo, candidate, spec['base'], spec['approved_at'], minimum, retained, index_hash, inputs['factory_observation']['environment_provenance'])
    return completion


def write_approval_retention(repo, spec, completion):
    paths = [TASK + '/' + n for n in ('verified-completion.json', 'independent-critic-review.json', 'defect-ledger.json', 'task-state.json')]
    paths += [EVIDENCE + '/REVIEW_EVIDENCE_MANIFEST.json'] + [TASK + '/CriticRaw/' + cid + '.json' for cid in CRITICS]
    manifest = dict(schema_version=1, task_id='T10', accepted_source=spec['candidate'], retention_class='approval_provenance',
        records=[dict(kind='approval_provenance', sha256=digest((repo / rel).read_bytes()),
            locator='repo://ksolo21-web/HAVENLINE/' + rel, reproducible=True, retention_days=3650) for rel in sorted(paths)],
        regeneration_contract=dict(workflow='.github/workflows/havenline-task10-isolated.yml', exact_source=spec['candidate'],
            source_run_id=completion['workflow_run_id'], source_artifact_id=completion['artifact_id'],
            complete_evidence_index_sha256=completion['evidence']['provenance_hash'], review_export_commit=spec['export_commit']))
    write(repo, EVIDENCE + '/APPROVAL_EVIDENCE_MANIFEST.json', manifest)


def validate_consumers(repo, spec):
    reports = []
    commands = [
        (PRODUCTION + '/task_state_snapshot.py', 'T10', '--candidate', spec['candidate'], '--last-gate', 'G1-G14', '--output', TASK + '/task-state.json'),
    ]
    for command in commands:
        reports.append(successful(run_cli(repo, *command)))
    state = load(repo / TASK / 'task-state.json')
    require(state['lifecycle_status'] == 'APPROVED' and not state['blockers'], 'derived final state blocked')
    write_approval_retention(repo, spec, load(repo / TASK / 'verified-completion.json'))
    commands = [
        (PRODUCTION + '/evidence_retention.py', 'validate-manifest', EVIDENCE + '/APPROVAL_EVIDENCE_MANIFEST.json'),
        (PRODUCTION + '/evidence_retention.py', 'validate-manifest', EVIDENCE + '/REVIEW_EVIDENCE_MANIFEST.json'),
        (PRODUCTION + '/closure_validator.py', TASK + '/verified-completion.json'),
        (PRODUCTION + '/validate_migration.py',),
        (PRODUCTION + '/architecture_v3.py', 'validate'),
        (PRODUCTION + '/architecture_v31.py', 'validate'),
        (PRODUCTION + '/validate_architecture_v32_t10.py',),
        (PRODUCTION + '/validate_integration_scope.py', '--base', spec['base'], '--head', spec['candidate']),
        (PRODUCTION + '/factory_closeout_gate.py', '--task', 'T10', '--candidate', spec['candidate'], '--observation', EVIDENCE + '/CloseoutInputs/factory_observation.json'),
    ]
    for command in commands:
        reports.append(successful(run_cli(repo, *command)))
    return reports


def verify_inputs(spec):
    reject_diagnostic(spec)
    for name in ('candidate', 'base', 'integration_head', 'export_commit'):
        require(re.fullmatch('[0-9a-f]{40}', str(spec.get(name, ''))), 'exact ' + name + ' required')
    instant = datetime.fromisoformat(spec['approved_at'].replace('Z', '+00:00'))
    require(instant.tzinfo is not None and instant <= datetime.now(timezone.utc), 'valid nonfuture timestamp required')
    c0, c0_bytes = read_reference(spec['c0_report'])
    require(c0.get('task_id') == 'T10' and c0.get('complete_known_blocker_set') is True and c0.get('validated') is True, 'canonical complete C0 report required')
    canonical = (ROOT / TASK / 'C0_ROOT_CAUSE.json').read_bytes()
    require(canonical == c0_bytes, 'C0 input differs from canonical authority')
    inputs, proof_bytes = {}, {'C0_ROOT_CAUSE.json': c0_bytes}
    for label in ('gates', 'path_validation', 'tests', 'progression', 'factory_observation', 'defect_dispositions'):
        value, data = read_reference(spec[label])
        inputs[label] = value
        proof_bytes[label + '.json'] = data
        if label not in ('gates', 'defect_dispositions'):
            source_pass(value, spec['candidate'], label)
        else:
            require(value.get('candidate_commit') == spec['candidate'], label + ': exact source required')
    require(inputs['path_validation'].get('candidate') == spec['candidate'] and inputs['path_validation'].get('base') == spec['base'], 'exact path validation required')
    require(inputs['tests'].get('records'), 'test records required')
    require(inputs['progression'].get('candidate_commit') == spec['candidate'], 'canonical progression source required')
    gates = inputs['gates'].get('gates', {})
    require(set(gates) == {f'G{i}' for i in range(1, 15)}, 'all fourteen gates required')
    def proofs(refs, label, disposition=None):
        require(isinstance(refs, list) and refs, label + ': actual proof references required')
        for ref in refs:
            value, data = read_reference(ref)
            source_pass(value, spec['candidate'], label)
            if disposition is not None:
                for field in ('blocker_id', 'affected_object', 'causal_files', 'command_or_gate', 'reviewer_or_owner'):
                    expected_value = disposition['id'] if field == 'blocker_id' else disposition[field]
                    require(value.get(field) == expected_value, label + ': verification proof ' + field + ' mismatch')
            if re.fullmatch(r'G(?:[1-9]|1[0-4])', label):
                require(value.get('gate_id') == label or value.get('gate') == label or value.get('gates', {}).get(label, {}).get('status') == 'PASS', label + ': proof does not identify this gate')
            proof_bytes[digest(data) + '.json'] = data
    for gate, row in gates.items():
        require(row.get('status') == 'PASS', gate + ': all mandatory gates must pass')
        proofs(row.get('proofs'), gate)
    defects = inputs['defect_dispositions'].get('defects', [])
    ids = [r.get('id') for r in defects]
    expected = [row['id'] for row in c0['blockers']]
    require(expected and len(expected) == len(set(expected)), 'canonical C0 blocker inventory must be unique and nonempty')
    require(re.fullmatch('[0-9a-f]{40}', str(c0.get('failed_candidate', ''))), 'canonical C0 repair source required')
    subprocess.run(['git', 'merge-base', '--is-ancestor', c0['failed_candidate'], spec['candidate']], cwd=ROOT, check=True)
    changed = set(subprocess.check_output(['git', 'diff', '--name-only', c0['failed_candidate'], spec['candidate']], cwd=ROOT).decode().splitlines())
    bookkeeping = {TASK + '/C0_ROOT_CAUSE.json', TASK + '/REPAIR_PLAN.json'}
    require(ids and len(ids) == len(set(ids)) and set(ids) == set(expected), 'complete unique C0 defect disposition inventory required')
    for row in defects:
        require(row.get('status') == 'VERIFIED_CLOSED', 'unresolved defect ' + str(row.get('id')))
        require(all(row.get(k) for k in ('classification', 'affected_object', 'causal_files', 'command_or_gate', 'reviewer_or_owner')), 'individual causal disposition required')
        require(row.get('proof_candidate') == spec['candidate'] and row.get('unresolved') is False, 'individual exact-source closure required')
        require(all(isinstance(row[key], str) and row[key].strip() for key in ('command_or_gate', 'reviewer_or_owner')), 'command/gate and reviewer identity must be nonempty strings')
        blocker = next(item for item in c0['blockers'] if item['id'] == row['id'])
        require(row['classification'] == blocker['classification'], 'defect classification changed')
        require(row['affected_object'] == blocker['affected_object'], 'defect affected_object differs from canonical C0')
        causal = row['causal_files']
        require(isinstance(causal, list) and all(isinstance(path, str) for path in causal) and len(causal) == len(set(causal)), 'causal files must be a unique path list')
        authorized_actual = (set(blocker['files_to_change']) & changed) - bookkeeping
        require(authorized_actual and set(causal) == authorized_actual, 'causal files must equal actual authorized changes excluding canonical bookkeeping')
        proofs(row.get('verification_proofs'), 'defect ' + str(row['id']), row)
    # Preserve actual documents and replace transient input locators with durable copies.
    for value in inputs.values():
        def rewrite(node):
            if isinstance(node, dict):
                if set(node) == {'path', 'sha256'}:
                    node['path'] = EVIDENCE + '/CloseoutInputs/' + node['sha256'] + '.json'
                else:
                    for child in node.values(): rewrite(child)
            elif isinstance(node, list):
                for child in node: rewrite(child)
        rewrite(value)
    return inputs, proof_bytes


def verify_export_storage(repo):
    directory = repo / TASK / 'ReviewExports'
    require((directory / '.gitattributes').read_bytes() == b'*.zip -filter -diff -merge\n', 'exact task-owned ZIP attribute override required')
    paths = sorted(directory.glob('*.zip'))
    require(paths, 'immutable exported ZIPs required')
    outside = subprocess.check_output(['git', 'check-attr', 'filter', '--', TASK + '/outside-review-export.zip'], cwd=repo).decode().strip()
    require(outside.endswith(': lfs'), 'ZIP override must not affect files outside ReviewExports')
    for path in paths:
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 24 * 1024 * 1024, 'export ZIP must be a regular file no larger than 24 MiB')
        rel = path.relative_to(repo).as_posix()
        blob = subprocess.check_output(['git', 'show', 'HEAD:' + rel], cwd=repo)
        require(not blob.startswith(b'version https://git-lfs.github.com/spec/'), 'export ZIP is an LFS pointer')
        require(blob == path.read_bytes(), 'immutable export ZIP differs from committed bytes')
        attrs = subprocess.check_output(['git', 'check-attr', 'filter', 'diff', 'merge', '--', rel], cwd=repo).decode().splitlines()
        require(len(attrs) == 3 and all(row.endswith(': unset') for row in attrs), 'ZIP export attributes not bounded to normal Git blobs')


def assemble(spec, out):
    inputs, proof_bytes = verify_inputs(spec)
    out = Path(out).resolve()
    require(not out.exists(), 'output must be a new directory')
    require(not out.is_relative_to(ROOT.resolve()), 'proposal must be outside the production checkout')
    export_args = dict(spec['export_arguments'])
    require(not {'candidate', 'integration_head', 'export_commit', 'out'} & set(export_args), 'identity/output cannot be overridden')
    for key in ('run', 'artifact', 'regression_run', 'regression_artifact', 'hosted_artifacts'):
        reject_diagnostic(load(export_args[key]))
    for path in Path(export_args['records_root']).rglob('*.json'):
        reject_diagnostic(load(path))
    with tempfile.TemporaryDirectory(prefix='t10-proposed-') as temporary:
        repo = Path(temporary) / 'repo'
        subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(ROOT), str(repo)], check=True)
        subprocess.run(['git', 'remote', 'remove', 'origin'], cwd=repo, check=True)
        subprocess.run(['git', 'checkout', '--quiet', spec['export_commit']], cwd=repo, check=True)
        require(not subprocess.check_output(['git', 'remote'], cwd=repo).strip(), 'staging repository must have no remotes')
        verify_export_storage(repo)
        require((repo / TASK / 'C0_ROOT_CAUSE.json').read_bytes() == proof_bytes['C0_ROOT_CAUSE.json'], 'C0 authority differs from the immutable export checkout')
        changed = subprocess.check_output(['git', 'diff', '--name-only', spec['candidate'], spec['integration_head'], '--', 'HavenlineGodot', 'tools'], cwd=repo).decode().strip()
        require(not changed, 'integration governance head changed reviewed runtime or tools; freeze and review that source')
        args = dict(export_args, candidate=spec['candidate'], integration_head=spec['integration_head'], export_commit=spec['export_commit'], out=str(repo))
        command = []
        for key, value in args.items(): command.extend(['--' + key.replace('_', '-'), str(value)])
        reports = [successful(run_cli(repo, 'tools/havenline/task10/export_closure_records.py', *command))]
        with zipfile.ZipFile(export_args['archive']) as archive:
            indexed = json.loads(archive.read('evidence-index.json'))['files']
            input_directory = Path(temporary) / 'critic-input'
            # Exporter has already rejected traversal/duplicates and verified all hashes.
            for name in indexed:
                write(input_directory, name, archive.read(name))
            require(spec['progression']['sha256'] in indexed.values(), 'progression must be the exact indexed hosted proof')
            runtime = [json.loads(archive.read(name)) for name in indexed if name.endswith('runtime-provenance.json')]
            require(len(runtime) == 1 and inputs['factory_observation']['environment_provenance'] == runtime[0], 'factory environment differs from indexed runtime provenance')
        run = load(export_args['run'])
        integration_branch = load(repo / 'Docs/Production/WORKSTREAM_REGISTRY.json')['integration_branch']
        require(run.get('head_branch') == integration_branch and load(export_args['regression_run']).get('head_branch') == integration_branch, 'fresh post-integration runs on the integration branch required')
        require(inputs['factory_observation']['workflow_run_id'] == run['id'], 'factory observation belongs to another run')
        artifact = load(export_args['artifact'])
        require(datetime.fromisoformat(artifact['expires_at'].replace('Z', '+00:00')) > datetime.now(timezone.utc), 'retained evidence already expired')
        transport_directory = Path(temporary) / 'transport-review'
        reports.append(successful(run_cli(repo, 'tools/havenline/task10/aggregate_critics.py', '--candidate', spec['candidate'], '--records-root', export_args['records_root'], '--inputs-root', input_directory, '--out', transport_directory)))
        write(repo, EVIDENCE + '/CloseoutInputs/critic-transport-aggregate.json', (transport_directory / 'critic-aggregate.json').read_bytes())
        for name, data in proof_bytes.items(): write(repo, EVIDENCE + '/CloseoutInputs/' + name, data)
        assemble_records(repo, spec, inputs)
        reports += validate_consumers(repo, spec)
        reports = json.loads(json.dumps(reports).replace(str(repo), '<STAGING>'))
        # Preserve all staged changes; originals in E remain byte-identical and are
        # also included so the proposal can be reviewed as a complete closure set.
        names = [f'Docs/Production/{n}' for n in AUTHORITIES]
        for directory in (TASK + '/ReviewExports', TASK + '/CriticRaw', EVIDENCE):
            names += [p.relative_to(repo).as_posix() for p in (repo / directory).rglob('*') if p.is_file()]
        names += [TASK + '/' + n for n in ('verified-completion.json', 'independent-critic-review.json', 'defect-ledger.json', 'task-state.json')]
        files = {name: (repo / name).read_bytes() for name in sorted(set(names))}
        report = dict(status='PROPOSED', task_approved=False, approval_authority_granted=False,
                      candidate_commit=spec['candidate'], export_commit=spec['export_commit'],
                      files={name: digest(data) for name, data in files.items()}, consumers=reports)
        staging = Path(temporary) / 'proposal'
        for name, data in files.items(): write(staging / 'overlay', name, data)
        write(staging, 'proposal.json', report)
        shutil.copytree(staging, out)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        report = assemble(load(args.spec), args.out)
        print(json.dumps(dict(status=report['status'], task_approved=False, files=len(report['files']))))
        return 0
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status='BLOCKED', task_approved=False, error=str(exc))))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
