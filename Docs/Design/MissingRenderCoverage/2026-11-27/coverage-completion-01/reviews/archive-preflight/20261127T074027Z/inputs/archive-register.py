"""Stage exact generated missing-render attempts and invocation provenance only.

No remote mutations. Research media is never copied through this importer.
"""
from pathlib import Path
import importlib.util
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def resolve(value):
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()


def capture_allowlist(source, relative):
    """Keep exact earlier task-local allowlists when explicit inputs are added."""
    source = Path(source)
    dest = a.OUT / relative
    if dest.exists() and dest.read_bytes() != source.read_bytes():
        old = dest.read_bytes()
        sha = a.metrics(old)['sha256']
        history = dest.parent / 'history' / (dest.stem + '--' + sha + dest.suffix)
        history.parent.mkdir(parents=True, exist_ok=True)
        assert not history.exists() or history.read_bytes() == old
        history.write_bytes(old)
        dest.unlink()
    return a.exact_copy(source, relative)


def register():
    assert not (ROOT / 'archive-content-publication.json').exists(), 'Published content is immutable; do not recapture or overwrite its frozen manifest'
    a.baseline_check()
    # Keep local exact versions of per-render critic records as they arrive.
    # Publication still requires the root's final explicit file allowlist.
    review_index_path = ROOT / 'archive-review-snapshot-index.json'
    review_history = a.read(review_index_path) if review_index_path.exists() else {
        'scope': 'Exact local snapshots of observed per-render critic records; no publication decision yet.',
        'snapshots': []}
    review_seen = {(row['source_path'], row['sha256']) for row in review_history['snapshots']}
    for review_path in sorted((ROOT / 'reviews').glob('critic-*.json')):
        raw = review_path.read_bytes()
        json.loads(raw)
        rm = a.metrics(raw)
        snapshot = ROOT / 'archive-review-snapshots' / (review_path.stem + '--' + rm['sha256'] + '.json')
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        assert not snapshot.exists() or snapshot.read_bytes() == raw
        if not snapshot.exists():
            snapshot.write_bytes(raw)
        key = (str(review_path.resolve()), rm['sha256'])
        if key not in review_seen:
            review_history['snapshots'].append({'source_path': key[0], 'snapshot_path': str(snapshot.resolve()), **rm})
            review_seen.add(key)
    a.write(review_index_path, review_history)
    snapshot_path = ROOT / 'archive-input-snapshot-index.json'
    snapshots = a.read(snapshot_path) if snapshot_path.exists() else {'schema_version': 1, 'snapshots': []}
    config = a.read(ROOT / 'archive-package-config.json')
    names = ['requirements.json'] + [n for n in ['DESIGN_CHECKPOINT.md', 'CHECKPOINT.md'] if (ROOT / n).exists()]
    for name in names:
        source = ROOT / name
        data = source.read_bytes()
        m = a.metrics(data)
        if not any(row['sha256'] == m['sha256'] for row in snapshots['snapshots']):
            target = ROOT / 'archive-input-snapshots' / (source.stem + '--' + m['sha256'] + source.suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            snapshots['snapshots'].append({'original_path': name, 'snapshot_path': str(target.relative_to(ROOT)), **m})
    # Registration captures requirements immediately; discover every exact retained version.
    for target in sorted((ROOT / 'archive-input-snapshots').glob('*--*.*')):
        if not target.is_file():
            continue
        m = a.metrics(target.read_bytes())
        assert m['sha256'] in target.name
        if not any(row['sha256'] == m['sha256'] for row in snapshots['snapshots']):
            original = target.stem.split('--')[0] + target.suffix
            snapshots['snapshots'].append({'original_path': original, 'snapshot_path': str(target.relative_to(ROOT)), **m})
    a.write(snapshot_path, snapshots)
    # Keep byte-exact original preparation records independently of the later
    # output registration, which appends native-image and input hash bindings.
    # A preparation record is history only, never proof that a tool ran.
    prepared_history = []
    for prepared_path in sorted((ROOT / 'archive-prepared-invocation-snapshots').glob('*.json')):
        prepared_raw = prepared_path.read_bytes()
        prepared_record = json.loads(prepared_raw)
        prepared_metrics = a.metrics(prepared_raw)
        assert prepared_metrics['sha256'] in prepared_path.name
        assert prepared_record['status'] == 'PREPARED'
        assert prepared_record['tool'] == 'image_gen__imagegen'
        assert not prepared_record.get('output')
        saved_preparation = a.exact_copy(prepared_path, 'provenance/invocations/prepared/' + prepared_path.name)
        prepared_history.append({'id': prepared_record['id'], 'exact_prepared_record': saved_preparation,
                                 'execution_boundary': 'Exact preparation history; not proof of invocation or generated output.'})
    inputs_by_hash = {}
    for row in snapshots['snapshots']:
        source = ROOT / row['snapshot_path']
        m = a.metrics(source.read_bytes())
        assert m['sha256'] == row['sha256'] and m['bytes'] == row['bytes']
        saved = a.exact_copy(source, 'provenance/input-history/' + source.name)
        inputs_by_hash[row['sha256']] = saved
    baseline = {}
    for row in a.read(ROOT / 'archive-baseline-tree.json')['tree']:
        if row['type'] == 'blob':
            baseline.setdefault(row['sha'], []).append(row['path'])
    generation_input_allowlist = a.read(ROOT / 'archive-generation-input-allowlist.json') if (ROOT / 'archive-generation-input-allowlist.json').exists() else {'allowed_inputs': []}
    allowed_generation_inputs = {str(resolve(row['local_path'])): row for row in generation_input_allowlist['allowed_inputs']}
    derived_input_allowlist = a.read(ROOT / 'archive-derived-input-allowlist.json') if (ROOT / 'archive-derived-input-allowlist.json').exists() else {'allowed_inputs': []}
    allowed_derived_inputs = {str(resolve(row['local_path'])): row for row in derived_input_allowlist['allowed_inputs']}
    design_snapshot_path = ROOT / 'archive-design-snapshot.json'
    design_sources = {row['source_path']: row for row in a.read(design_snapshot_path)['files']} if design_snapshot_path.exists() else {}

    originals = {}
    pending = []
    failed_sources = []
    invocation_sources = []
    for path in sorted((ROOT / 'invocations').glob('*.json')):
        inv = a.read(path)
        if not inv.get('output'):
            if inv.get('status') == 'TOOL_FAILED_NO_IMAGE':
                failed_sources.append((path, inv))
            else:
                pending.append({'id': inv.get('id', path.stem), 'status': inv.get('status'), 'record': str(path)})
            continue
        ident = inv['id']
        assert ident not in originals
        output = inv['output']
        source = resolve(output['local_path'])
        saved = a.exact_copy(source, 'attempts/' + ident + '.png')
        with Image.open(source) as image:
            saved.update(dimensions=list(image.size), actual_format=image.format)
            image.verify()
        assert saved['actual_format'] == 'PNG'
        for key in ['sha256', 'git_blob_sha', 'bytes', 'dimensions']:
            assert saved[key] == output[key], (ident, key)
        assert Path(output['native_returned_locator']).read_bytes() == source.read_bytes()
        saved.update(id=ident, native_returned_locator=output['native_returned_locator'])
        originals[ident] = saved
        invocation_sources.append((path, inv))
    generated_by_hash = {row['sha256']: row for row in originals.values()}

    calls = []
    existing_inputs = {}
    unresolved_inputs = []
    for path, inv in invocation_sources:
        ident = inv['id']
        prompt = resolve(inv['prompt_file']['local_path'])
        prompt_data = prompt.read_bytes()
        source_prompt = a.exact_copy(prompt, 'prompts/' + ident + '.txt')
        for key in ['sha256', 'git_blob_sha', 'bytes']:
            assert source_prompt[key] == inv['prompt_file'][key], (ident, key)
        actual_prompt_data = inv['arguments']['prompt'].encode('utf-8')
        actual_prompt_path = ROOT / 'archive-exact-invoked-prompts' / (ident + '.txt')
        actual_prompt_path.parent.mkdir(parents=True, exist_ok=True)
        assert not actual_prompt_path.exists() or actual_prompt_path.read_bytes() == actual_prompt_data
        actual_prompt_path.write_bytes(actual_prompt_data)
        exact_prompt = a.exact_copy(actual_prompt_path, 'prompts/actual-arguments/' + ident + '.txt')
        prompt_difference = None if prompt_data == actual_prompt_data else {
            'description': 'The preserved source prompt document includes one final newline absent from the recorded invocation argument.',
            'only_single_final_newline': prompt_data == actual_prompt_data + b'\n'}
        assert not prompt_difference or prompt_difference['only_single_final_newline'], 'Unexplained prompt difference: ' + ident
        ordered = inv['ordered_reference_inputs']
        assert len(ordered) <= 5
        assert len(ordered) == len(inv['arguments'].get('referenced_image_paths', []))
        public_inputs = []
        for order, (row, locator) in enumerate(zip(ordered, inv['arguments'].get('referenced_image_paths', [])), 1):
            source = resolve(locator)
            assert source == resolve(row['local_path']) and row['order'] == order
            m = a.metrics(source.read_bytes())
            assert all(m[k] == row[k] for k in ['sha256', 'git_blob_sha', 'bytes']), (ident, order, 'Reference bytes changed')
            binding = {'order': order, 'original_locator': str(source), **m}
            if m['sha256'] in generated_by_hash:
                binding.update(archive_path=generated_by_hash[m['sha256']]['path'], disposition='THIS_TASK_GENERATED_ORIGINAL')
            elif m['git_blob_sha'] in baseline:
                paths = sorted(baseline[m['git_blob_sha']], key=lambda p: ('/selected/' not in p, len(p), p))
                binding.update(disposition='IMMUTABLE_BASELINE_IMAGE', source_commit=a.BASE, repository_path=paths[0],
                    immutable_url='https://github.com/ksolo21-web/HAVENLINE/blob/' + a.BASE + '/' + paths[0])
                existing_inputs[m['sha256']] = binding
            elif str(source) in allowed_generation_inputs:
                allow = allowed_generation_inputs[str(source)]
                assert all(m[k] == allow[k] for k in ['sha256', 'git_blob_sha', 'bytes'])
                saved_input = a.exact_copy(source, allow['archive_relative_path'])
                input_disposition = 'EXPLICIT_AUTHOR_CREATED_GEOMETRY_GUIDE' if allow.get('source_kind') == 'AUTHOR_CREATED_MATHEMATICAL_GUIDE' else 'EXPLICIT_LIMITED_GENERATION_INPUT'
                binding.update(disposition=input_disposition, archive_path=saved_input['path'],
                    source_id=allow['source_id'], role=allow['role'], provenance=allow['provenance'])
            elif str(source) in allowed_derived_inputs:
                allow = allowed_derived_inputs[str(source)]
                assert all(m[k] == allow[k] for k in ['sha256', 'git_blob_sha', 'bytes'])
                saved_input = a.exact_copy(source, allow['archive_relative_path'])
                binding.update(disposition='EXPLICIT_INTERNAL_DERIVED_INPUT', archive_path=saved_input['path'],
                    kind=allow['kind'], derivation=allow['derivation'], role=allow['role'])
            elif str(source) in design_sources:
                recorded = design_sources[str(source)]
                assert all(m[k] == recorded[k] for k in ['sha256', 'git_blob_sha', 'bytes'])
                assert (a.REPO / recorded['path']).read_bytes() == source.read_bytes()
                binding.update(disposition='FROZEN_AUTHORED_DESIGN_INPUT', archive_path=recorded['path'],
                    design_manifest_sha256=a.read(ROOT / 'archive-package-config.json')['frozen_design_manifest_sha256'])
            elif source.is_relative_to(ROOT / 'references'):
                binding.update(disposition='RESEARCH_INPUT_NOT_COPIED_BY_GENERATION_IMPORTER',
                    publication_boundary='Research publication requires an exact individually allowed file binding.')
            else:
                binding.update(disposition='PENDING_EXPLICIT_INPUT_SCOPE')
                unresolved_inputs.append({'invocation_id': ident, **binding})
            public_inputs.append(binding)
        req = inv['requirements_at_generation']
        assert req['sha256'] in inputs_by_hash, 'Missing exact requirements version: ' + req['sha256']
        invocation_sha = a.metrics(path.read_bytes())['sha256']
        exact_invocation = a.exact_copy(path, 'provenance/invocations/' + ident + '--' + invocation_sha + '.json')
        calls.append({'id': ident, 'recorded_status': inv['status'], 'exact_invocation': exact_invocation,
            'exact_invoked_prompt': exact_prompt, 'source_prompt_document': source_prompt,
            'prompt_document_difference': prompt_difference, 'ordered_reference_inputs': public_inputs,
            'requirements': inputs_by_hash[req['sha256']], 'output': originals[ident]})
    failed_calls = []
    for path, inv in failed_sources:
        ident = inv['id']
        assert ident not in originals and inv['output'] is None
        requested = inv['arguments']['prompt'].encode('utf-8')
        prompt_path = ROOT / 'archive-exact-invoked-prompts' / (ident + '.txt')
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        assert not prompt_path.exists() or prompt_path.read_bytes() == requested
        prompt_path.write_bytes(requested)
        exact_prompt = a.exact_copy(prompt_path, 'prompts/actual-arguments/' + ident + '.txt')
        source_prompt = ROOT / 'prompts' / (ident + '.txt')
        saved_prompt = None
        if source_prompt.exists():
            assert source_prompt.read_bytes() in {requested, requested + b'\n'}
            saved_prompt = a.exact_copy(source_prompt, 'prompts/' + ident + '.txt')
        requested_inputs = []
        for order, locator in enumerate(inv['arguments'].get('referenced_image_paths', []), 1):
            source = resolve(locator)
            m = a.metrics(source.read_bytes())
            binding = {'order': order, 'original_locator': str(source), **m,
                'hash_binding_basis': 'Exact retained immutable requested input bytes; this failed tool request produced no image.'}
            if m['sha256'] in generated_by_hash:
                binding.update(archive_path=generated_by_hash[m['sha256']]['path'], disposition='THIS_TASK_GENERATED_ORIGINAL')
            elif m['git_blob_sha'] in baseline:
                paths = sorted(baseline[m['git_blob_sha']], key=lambda p: ('/selected/' not in p, len(p), p))
                binding.update(disposition='IMMUTABLE_BASELINE_IMAGE', source_commit=a.BASE, repository_path=paths[0],
                    immutable_url='https://github.com/ksolo21-web/HAVENLINE/blob/' + a.BASE + '/' + paths[0])
            elif str(source) in allowed_generation_inputs:
                allowed = allowed_generation_inputs[str(source)]
                assert all(m[k] == allowed[k] for k in ['sha256', 'git_blob_sha', 'bytes'])
                saved = a.exact_copy(source, allowed['archive_relative_path'])
                input_disposition = 'EXPLICIT_AUTHOR_CREATED_GEOMETRY_GUIDE' if allowed.get('source_kind') == 'AUTHOR_CREATED_MATHEMATICAL_GUIDE' else 'EXPLICIT_LIMITED_GENERATION_INPUT'
                binding.update(disposition=input_disposition, archive_path=saved['path'],
                    source_id=allowed['source_id'], role=allowed['role'], provenance=allowed['provenance'])
            elif str(source) in allowed_derived_inputs:
                allowed = allowed_derived_inputs[str(source)]
                assert all(m[k] == allowed[k] for k in ['sha256', 'git_blob_sha', 'bytes'])
                saved = a.exact_copy(source, allowed['archive_relative_path'])
                binding.update(disposition='EXPLICIT_INTERNAL_DERIVED_INPUT', archive_path=saved['path'],
                    kind=allowed['kind'], derivation=allowed['derivation'])
            elif str(source) in design_sources:
                recorded = design_sources[str(source)]
                assert all(m[k] == recorded[k] for k in ['sha256', 'git_blob_sha', 'bytes'])
                binding.update(disposition='FROZEN_AUTHORED_DESIGN_INPUT', archive_path=recorded['path'])
            else:
                raise AssertionError('Unresolved requested input for failed invocation: ' + str(source))
            requested_inputs.append(binding)
        inv_sha = a.metrics(path.read_bytes())['sha256']
        exact_invocation = a.exact_copy(path, 'provenance/invocations/' + ident + '--' + inv_sha + '.json')
        req = inv['requirements_at_generation']
        assert req['sha256'] in inputs_by_hash, 'Missing failed-call requirements snapshot'
        error_record = inv.get('tool_error_record')
        if error_record:
            assert error_record['sha256'] in inputs_by_hash, 'Missing exact original tool-error record'
        failed_calls.append({'id': ident, 'recorded_status': 'TOOL_FAILED_NO_IMAGE', 'tool_error': inv.get('tool_error'),
            'exact_invocation': exact_invocation, 'exact_attempted_prompt': exact_prompt, 'source_prompt_document': saved_prompt,
            'requirements': inputs_by_hash[req['sha256']],
            'exact_original_error_record': inputs_by_hash[error_record['sha256']] if error_record else None,
            'attempted_ordered_reference_inputs': requested_inputs, 'output': None, 'generated_image_count': 0,
            'execution_boundary': 'Preserved failed tool attempt. No image, visual approval or completed model generation is claimed.'})
    manifest = {'schema_version': 1, 'generation_frozen': False, 'selected': [],
        'scope': config.get('scope', 'Static Havenline missing-render coverage; no native mesh, rig, animation, or runtime approval.'),
        'generated_original_count': len(originals), 'actual_invocations': calls,
        'failed_no_image_invocations': failed_calls,
        'prepared_invocation_history': prepared_history,
        'pending_invocations': pending, 'existing_baseline_inputs': list(existing_inputs.values()),
        'unresolved_new_input_scope': unresolved_inputs, 'source_input_snapshots': snapshots['snapshots']}
    a.write(ROOT / 'archive-generation-snapshot.json', manifest)
    a.write(a.OUT / 'generation-manifest.json', manifest)
    a.write(a.OUT / 'provenance/input-history/index.json', snapshots)
    if generation_input_allowlist['allowed_inputs']:
        capture_allowlist(ROOT / 'archive-generation-input-allowlist.json', 'generation-inputs/PUBLIC-INPUT-ALLOWLIST.json')
    if derived_input_allowlist['allowed_inputs']:
        capture_allowlist(ROOT / 'archive-derived-input-allowlist.json', 'generation-inputs/INTERNAL-DERIVED-INPUTS.json')
    actual = {str(path.resolve()) for path in (ROOT / 'renders').glob('*.png')}
    registered = {row['source_path'] for row in originals.values()}
    receipt_path = ROOT / 'archive-blob-receipts.json'
    receipts = a.read(receipt_path)['receipts'] if receipt_path.exists() else []
    original_blobs = {row['git_blob_sha'] for row in originals.values()}
    uploaded_original_blobs = original_blobs & {row['git_blob_sha'] for row in receipts}
    a.write(ROOT / 'archive-checkpoint.json', {'stage': 'PREPARING_APPEND_ONLY_ARCHIVE_AWAITING_FINAL_SELECTION',
        'base_commit': a.BASE, 'base_tree': a.BASE_TREE, 'branch': a.BRANCH, 'prefix': a.PREFIX,
        'generated_originals_registered': len(originals), 'required_selected_studies': config.get('required_selected_studies'),
        'uploaded_distinct_original_blobs': len(uploaded_original_blobs),
        'blob_receipt_meaning': 'Unattached objects only until final tree/commit/ref publication and verified readback.',
        'pending_invocations': len(pending), 'unregistered_png_paths': sorted(actual - registered),
        'tool_failed_no_image_invocations': len(failed_calls),
        'research_policy': 'Explicit individual source-input allowlists only; never recursively publish research folders.',
        'final_freeze_received': False, 'remote_branch_created': False, 'remote_content_published': False,
        'next_action': 'Continue capturing immutable generations and source versions; wait for root selection/final documents and independent package approval.'})
    return {'generated_originals': len(originals), 'pending_invocations': len(pending),
        'tool_failed_no_image_invocations': len(failed_calls),
        'source_input_versions': len(snapshots['snapshots']), 'baseline_reference_images': len(existing_inputs),
        'unregistered_png_paths': sorted(actual - registered), 'unresolved_new_input_scope': len(unresolved_inputs)}


if __name__ == '__main__':
    print(json.dumps(register(), indent=2))
