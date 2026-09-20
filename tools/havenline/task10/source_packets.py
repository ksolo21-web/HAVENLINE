#!/usr/bin/env python3
"""Lossless, whole-function T10 source packets; independent non-voting review only."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

SOURCE_PATH = 'HavenlineGodot/scripts/world_transform_view.gd'
EXPECTED_SOURCE_SHA256 = 'bd91be572015673201982ad4c923960b8ace31c844916c7ca98db24efe005780'
CONTEXT_TOKENS = 12288
INPUT_TOKEN_BUDGET = 4096
OUTPUT_TOKENS = 1000
TOKEN_RESERVE = 128
REQUEST_SECONDS = 1200
DIMENSIONS = ['causal_correctness', 'scope_preservation', 'failure_handling', 'cross_function_consistency', 'evidence_sufficiency']
GROUPS = {
    'lifecycle': ['contract', '_ready', 'configure', 'configure_readability', 'set_locked', 'set_ready', 'show_preview', 'show_blocked', 'show_commit', 'mark_complete', '_clear_blocked'],
    'visuals': ['_material', '_ensure_visuals', '_visual_signature', '_set_lifecycle', '_apply_visuals', '_process', '_target_form_scale'],
    'lighting': ['_enter_tree', '_exit_tree', '_on_shadow_scene_node_changed', '_active_directional_shadow_lights', '_ground_shadow_point', '_projected_response_rect'],
    'placement': ['_label_size_for_wrap', '_minimum_word_wrap_width', '_rect_clearance', 'screen_delta_to_label_offset', '_label_candidate'],
    'projection': ['_label_projection', '_update_camera_lane', 'projected_readability'],
    'feedback': ['_quantities', '_resource_cues', '_readable_reasons', 'feedback_text', 'descriptor'],
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def exact_json(raw: str | bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON ' + value)))
    if not isinstance(result, dict):
        raise ValueError('JSON object required')
    return result


def split_functions(source: str) -> tuple[str, dict]:
    matches = list(re.finditer(r'(?m)^(?:static\s+)?func\s+([A-Za-z_][A-Za-z0-9_]*)\(', source))
    if not matches:
        raise ValueError('source has no top-level functions')
    units = {}
    header = source[:matches[0].start()]
    for index, match in enumerate(matches):
        name = match.group(1)
        if name in units:
            raise ValueError('ambiguous duplicate function ' + name)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        text = source[match.start():end]
        units[name] = {'name': name, 'start_line': source.count('\n', 0, match.start()) + 1,
                       'end_line': source.count('\n', 0, end), 'text': text,
                       'sha256': digest(text.encode())}
    if header + ''.join(unit['text'] for unit in units.values()) != source:
        raise ValueError('lossless reconstruction failed')
    return header, units


def packets(source: str, commit: str, tree: str) -> dict:
    if not re.fullmatch('[0-9a-f]{40}', commit) or not re.fullmatch('[0-9a-f]{40}', tree):
        raise ValueError('exact commit and tree required')
    header, units = split_functions(source)
    assigned = [name for names in GROUPS.values() for name in names]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(units):
        raise ValueError('complete source coverage differs from named packet plan')
    identity = {'path': SOURCE_PATH, 'commit': commit, 'tree': tree, 'sha256': digest(source.encode())}
    unit_index = [{k: unit[k] for k in ('name', 'start_line', 'end_line', 'sha256')} for unit in units.values()]
    result = {'schema_version': 1, 'kind': 'SOURCE_REVIEW_PACKET_MANIFEST', 'source': identity,
              'source_function_count': len(units), 'header_sha256': digest(header.encode()),
              'units': unit_index, 'groups': {}, 'task_approved': False}
    ownership = '; '.join(group + ': ' + ','.join(names) for group, names in GROUPS.items())
    for group, names in GROUPS.items():
        # Raw code is written once, not embedded as JSON-escaped code plus a duplicate diff.
        prompt = '\n'.join([
            'Independent Havenline T10 SOURCE review. This is NOT a C1/C2/C3/C4/C6/C7 final vote or task approval.',
            'Inspect every supplied primary function and the shared declarations. Preserve gameplay, visual, progression, UX, performance, references, G1-G14 and all >9.0 unrounded final gates.',
            'Classify findings as PRODUCT, EVIDENCE, or TOOL. A real source-bound product defect blocks; missing proof must remain EVIDENCE, never an invented gameplay failure or a pass.',
            'This packet contains whole functions. Other function implementations are assigned to named sibling packets, not missing from the source. If a dependency is needed to decide correctness, record that precise evidence gap.',
            'Score all five requested dimensions 0-10 from evidence, without averaging. Any dimension <=9 requires an actionable finding. Do not raise a score just to avoid a finding.',
            'Return exactly the schema fields; coverage_complete means every primary function in THIS packet was inspected. The separate aggregator requires every packet.',
            'Source identity: ' + json.dumps(identity, separators=(',', ':')),
            'Packet: ' + group + '. Primary functions: ' + ', '.join(names),
            'Whole-file assignment: ' + ownership,
            'SHARED DECLARATIONS (exact bytes):\n' + header,
            ('CONTRACT CONTEXT (already primary in lifecycle packet):\n' + units['contract']['text']) if group != 'lifecycle' else '',
            '\n'.join('PRIMARY FUNCTION %s [%s:%d-%d]\n%s' % (name, SOURCE_PATH, units[name]['start_line'], units[name]['end_line'], units[name]['text']) for name in names),
        ])
        result['groups'][group] = {'functions': names, 'prompt': prompt, 'prompt_sha256': digest(prompt.encode()), 'dimensions': DIMENSIONS}
    return result


def schema() -> dict:
    return {'type': 'object', 'properties': {
        'observations': {'type': 'array', 'minItems': 2, 'maxItems': 4, 'items': {'type': 'string', 'maxLength': 180}},
        'defects': {'type': 'array', 'maxItems': 5, 'items': {'type': 'object', 'properties': {
            'layer': {'type': 'string', 'enum': ['PRODUCT', 'EVIDENCE', 'TOOL']},
            'finding': {'type': 'string', 'maxLength': 240}}, 'required': ['layer', 'finding'], 'additionalProperties': False}},
        'coverage_complete': {'type': 'boolean'}, 'confidence': {'type': 'string', 'enum': ['low', 'medium', 'high']},
        'scores': {'type': 'object', 'properties': {d: {'type': 'number', 'minimum': 0, 'maximum': 10} for d in DIMENSIONS}, 'required': DIMENSIONS, 'additionalProperties': False}},
        'required': ['observations', 'defects', 'coverage_complete', 'confidence', 'scores'], 'additionalProperties': False}


def result_errors(row: dict) -> list[str]:
    errors = []
    if set(row) != {'observations', 'defects', 'coverage_complete', 'confidence', 'scores'}:
        errors.append('response field set mismatch')
    observations = row.get('observations')
    if not isinstance(observations, list) or not 2 <= len(observations) <= 4 or any(not isinstance(v, str) or not v.strip() or len(v) > 180 for v in observations):
        errors.append('invalid observations')
    defects = row.get('defects')
    if not isinstance(defects, list) or len(defects) > 5:
        errors.append('invalid defect list')
    elif any(not isinstance(v, dict) or set(v) != {'layer', 'finding'} or v['layer'] not in ['PRODUCT', 'EVIDENCE', 'TOOL'] or not isinstance(v['finding'], str) or not v['finding'].strip() or len(v['finding']) > 240 for v in defects):
        errors.append('invalid classified defect')
    elif defects:
        errors.append('unresolved findings')
    if row.get('coverage_complete') is not True:
        errors.append('coverage incomplete')
    if row.get('confidence') not in ['medium', 'high']:
        errors.append('insufficient confidence')
    scores = row.get('scores')
    if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
        errors.append('mandatory dimension set mismatch')
    else:
        for key, value in scores.items():
            if type(value) not in (int, float) or not math.isfinite(value) or not 9.0 < value <= 10.0:
                errors.append('nonpassing score: ' + key)
        if any('nonpassing score' in e for e in errors) and not defects:
            errors.append('low score lacks actionable finding')
    return errors


def post(endpoint: str, payload: dict, output: Path, timeout: int = 30) -> dict:
    request = json.dumps(payload, ensure_ascii=False).encode()
    output.with_suffix('.request.json').write_bytes(request)
    req = urllib.request.Request('http://127.0.0.1:8080' + endpoint, data=request, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        output.with_suffix('.error-body.txt').write_bytes(error.read())
        raise
    output.with_suffix('.response.json').write_bytes(raw)
    return exact_json(raw)


def check_admission(tokens: list) -> int:
    if not isinstance(tokens, list) or not tokens or any(type(token) is not int for token in tokens):
        raise ValueError('invalid tokenization result')
    count = len(tokens)
    if count > INPUT_TOKEN_BUDGET or count + OUTPUT_TOKENS + TOKEN_RESERVE > CONTEXT_TOKENS:
        raise ValueError('packet exceeds measured input/context budget; inference forbidden')
    return count


def run_group(source: str, tree: str, group: str, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    record = {'source': source, 'tree': tree, 'group': group, 'passed': False, 'task_approved': False, 'non_voting': True, 'final_critic_vote': False}
    proc = None
    log = None
    try:
        if os.environ.get('HAVENLINE_INDEPENDENT_REVIEW_JOB') != '1':
            raise ValueError('separate independent review job required')
        actual_tree = subprocess.check_output(['git', 'rev-parse', source + '^{tree}'], text=True).strip()
        if actual_tree != tree:
            raise ValueError('source tree mismatch')
        raw = subprocess.check_output(['git', 'show', source + ':' + SOURCE_PATH])
        if digest(raw) != EXPECTED_SOURCE_SHA256:
            raise ValueError('source checksum mismatch')
        plan = packets(raw.decode(), source, tree)
        (out / 'packet-manifest.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
        packet = plan['groups'][group]
        record.update(source_sha256=digest(raw), prompt_sha256=packet['prompt_sha256'], functions=packet['functions'], input_manifest_sha256=digest((out / 'packet-manifest.json').read_bytes()))
        production = Path('tools/havenline/production').resolve()
        sys.path.insert(0, str(production))
        from prepare_specialist_runtime import validate_cached_runtime, load_lock
        lock = load_lock()
        cfg = json.loads(Path('Docs/Production/CRITIC_EXECUTION.json').read_text())['local_independent_runtime']
        if (cfg['provider'], cfg['base_model'], cfg['model_revision']) != (lock['publisher'], lock['base_model'], lock['revision']):
            raise ValueError('runtime authority identity mismatch')
        cache = Path(os.path.expanduser(cfg['cache_path']))
        checked = validate_cached_runtime(cache, lock)
        (out / 'runtime-validation.json').write_text(json.dumps(checked, indent=2))
        if not checked['passed'] or lock['runtime_release'] != 'b10809':
            raise ValueError('runtime hash/release mismatch')
        server = Path(checked['server'])
        env = dict(os.environ); env['LD_LIBRARY_PATH'] = str(server.parent) + ':' + env.get('LD_LIBRARY_PATH', '')
        command = [str(server), '-m', str(cache / lock['model_file']), '--mmproj', str(cache / lock['projector_file']), '--host', '127.0.0.1', '--port', '8080', '-c', str(CONTEXT_TOKENS), '-t', '4', '-tb', '4', '-ngl', '0', '--no-mmproj-offload', '--parallel', '1', '--jinja', '--image-min-tokens', '768', '--image-max-tokens', '2048']
        record.update(provider=lock['publisher'], model=lock['base_model'], revision=lock['revision'], runtime_release=lock['runtime_release'], command=command, review_run_id=os.environ.get('GITHUB_RUN_ID'), review_job=os.environ.get('GITHUB_JOB'))
        log = (out / 'runtime.log').open('w')
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        for _ in range(180):
            if proc.poll() is not None:
                raise RuntimeError('reviewer process exited')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3) as response:
                    if json.load(response).get('status') == 'ok': break
            except (OSError, ValueError): pass
            time.sleep(2)
        else:
            raise RuntimeError('reviewer runtime did not become ready')
        body = {'model': 'havenline-specialist-local', 'messages': [{'role': 'user', 'content': packet['prompt']}], 'max_tokens': OUTPUT_TOKENS, 'temperature': 0.2, 'top_p': 0.9, 'seed': 20260920, 'chat_template_kwargs': {'enable_thinking': False}, 'response_format': {'type': 'json_object', 'schema': schema()}, 'cache_prompt': False}
        template = post('/apply-template', {'messages': body['messages'], 'chat_template_kwargs': body['chat_template_kwargs']}, out / 'template')
        if not isinstance(template.get('prompt'), str) or not template['prompt']:
            raise ValueError('chat-template prompt missing')
        tokens = post('/tokenize', {'content': template['prompt'], 'add_special': True, 'parse_special': True}, out / 'tokens')['tokens']
        record['input_tokens'] = check_admission(tokens)
        record['token_admission_passed'] = True
        (out / 'admission.json').write_text(json.dumps(record, indent=2))
        result = post('/v1/chat/completions', body, out / 'review', REQUEST_SECONDS)
        choices = result.get('choices')
        if not isinstance(choices, list) or len(choices) != 1 or choices[0].get('finish_reason') != 'stop':
            raise ValueError('reviewer response incomplete')
        parsed = exact_json(choices[0]['message']['content'])
        errors = result_errors(parsed)
        record.update(review=parsed, errors=errors, passed=not errors, raw_response_sha256=digest((out / 'review.response.json').read_bytes()))
    except Exception as error:
        record.update(passed=False, tool_error=type(error).__name__ + ': ' + str(error))
    finally:
        if proc is not None:
            proc.terminate()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        if log is not None: log.close()
        (out / 'group-result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True); p.add_argument('--tree', required=True)
    p.add_argument('--group', required=True, choices=sorted(GROUPS)); p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = run_group(args.source, args.tree, args.group, args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
