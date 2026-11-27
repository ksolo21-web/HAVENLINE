"""Build reviewable category galleries and complete native/invocation indexes.

Draft pages use only current hash-verified independent PASS selections. --final
requires all 81 planned sheet identities and no unfinished invocation records.
Neither mode freezes the package or writes a GitHub branch.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import posixpath
import re

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
parser = argparse.ArgumentParser()
parser.add_argument('--final', action='store_true')
args = parser.parse_args()
assert not (ROOT / 'archive-content-publication.json').exists()
requirements_path = ROOT / 'requirements.json'
selection_path = ROOT / 'selection-working.json'
generation_path = ROOT / 'archive-generation-snapshot.json'
requirements = a.read(requirements_path)
working = a.read(selection_path)
generation = a.read(generation_path)
assert not generation['unresolved_new_input_scope'], 'Resolve actual input custody before writing coherent gallery pages'
authored_guide_path = ROOT / 'author-guides/index.json'
authored_guides = a.read(authored_guide_path)['guides'] if authored_guide_path.exists() else []
calls = {row['id']: row for row in generation['actual_invocations']}
selected = {}
family_for = {sheet: family for family in requirements['families'] for sheet in family['required_sheets']}
assert len(family_for) == requirements['planned_selected_sheet_count'] == 81

def category(family):
    if family.get('category') == 'atlas_raider':
        return 'raiders'
    if family.get('category') == 'atlas_animal':
        return 'animals'
    if family.get('category') == 'world':
        return 'world'
    if family['id'].startswith(('customer_', 'survivor_')):
        return 'npcs'
    return 'world'

required_by_category = {key: [sheet for sheet, family in family_for.items() if category(family) == key]
                        for key in ['world', 'npcs', 'animals', 'raiders']}
assert {key: len(value) for key, value in required_by_category.items()} == {
    'world': 35, 'npcs': 12, 'animals': 14, 'raiders': 20}
for row in working['selected']:
    sheet = row['deliverable_id']
    assert sheet in family_for and sheet not in selected
    call = calls[row['render_id']]
    output = call['output']
    assert output['sha256'] == row['sha256'] and output['bytes'] == row['bytes']
    report_path = Path(row['review_path'])
    raw = report_path.read_bytes()
    assert a.metrics(raw)['sha256'] == row['review_sha256'], 'Working selection review changed; refresh status first'
    report = json.loads(raw)
    assert report.get('independent') is True and report.get('reviewer') not in {None, '/root', '/root/missing_archive'}
    assert str(report.get('status', '')).startswith('PASS') and report.get('score') == row['score'] > 9.0
    assert report.get('all_mandatory_visual_checks_passed') is True and not report.get('mandatory_defects_remaining')
    assert not report.get('approval_reopened') and not report.get('approval_invalidated')
    assert report.get('actual_full_native_png_inspected') is True or report.get('actual_full_png_inspected') is True
    reviewed = report['reviewed_image']
    assert reviewed.get('sha256', reviewed.get('source_sha256')) == row['sha256']
    assert reviewed.get('bytes', reviewed.get('source_bytes')) == row['bytes']
    selected[sheet] = {**row, 'selected_path': 'selected/' + sheet + '.png',
                       'original_path': 'attempts/' + row['render_id'] + '.png',
                       'public_review_path': 'reviews/' + report_path.name,
                       'git_blob_sha': output['git_blob_sha'], 'dimensions': output['dimensions']}
if args.final:
    assert set(selected) == set(family_for), 'Final galleries require every planned sheet identity'
    assert not generation['pending_invocations'] and not generation['unresolved_new_input_scope']
    assert working['pending_count'] == 0
counts = {key: sum(sheet in selected for sheet in sheets) for key, sheets in required_by_category.items()}
pending_by_id = {row['deliverable_id']: row for row in working.get('pending', [])}
world_catalog = {row['id']: row for row in a.read(ROOT / 'world-render-catalog.json')['sheets']}
out = ROOT / 'gallery-drafts'
written = []

def destination_link(page, target):
    if target.startswith(('http://', 'https://')):
        return target
    if target.startswith(a.PREFIX + '/'):
        target = target[len(a.PREFIX) + 1:]
    return posixpath.relpath(target, posixpath.dirname(page) or '.')

def link(page, label, target):
    return '[' + label + '](' + destination_link(page, target) + ')'

def clean(value):
    return str(value).replace('|', '/').replace('\n', ' ')

def title(sheet):
    name = sheet.removeprefix('world-').removeprefix('atlas-')
    suffixes = [('-hands-gear', ' · Hands and gear'), ('-hands', ' · Hand details'),
                ('-pose', ' · Body views'), ('-turnaround', ' · Turnaround')]
    suffix = ''
    for ending, label in suffixes:
        if name.endswith(ending):
            name = name[:-len(ending)]
            suffix = label
            break
    return name.replace('-', ' ').title() + suffix

def write_page(relative, text):
    data = (text.rstrip() + '\n').encode('utf-8')
    path = out / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        old = path.read_bytes()
        snapshot = out / 'history' / (relative.replace('/', '__') + '--' + a.metrics(old)['sha256'] + '.txt')
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        assert not snapshot.exists() or snapshot.read_bytes() == old
        if not snapshot.exists():
            snapshot.write_bytes(old)
    path.write_bytes(data)
    written.append({'source_path': str(path.resolve()), 'archive_path': relative, **a.metrics(data)})

stage_label = ('Final static selection' if args.final else 'Working gallery draft')
main = 'README.md'
intro = [
    '# Havenline · Missing render coverage', '',
    f'**{stage_label}: {len(selected)}/81 required sheets have an exact independent static-reference PASS.**', '',
    ('This draft is not a publication freeze. Pending sheets remain visible below; rejected iterations remain preserved.' if not args.final
     else 'All 81 planned sheet identities are present. Every selected PNG is a byte-identical alias of its retained native original.'), '',
    '## Browse the selected sheets', '',
    '| Gallery | Bounded source coverage | Approved / required sheets |',
    '| --- | --- | ---: |',
    f'| {link(main, "World and camp", "galleries/world.md")} | 30 world families, 65 depicted source forms | {counts["world"]}/35 |',
    f'| {link(main, "Survivors and NPCs", "galleries/npcs.md")} | 6 existing identities; body and spread-hand supplements | {counts["npcs"]}/12 |',
    f'| {link(main, "Atlas animals", "galleries/animals.md")} | 14 additional source-specific appearances | {counts["animals"]}/14 |',
    f'| {link(main, "Atlas raiders", "galleries/raiders.md")} | 10 additional appearances; body and hands/gear sheets | {counts["raiders"]}/20 |', '',
    '## Why these assets were added', '',
    'The audit compared the recovered original boards, the Frostbound World Atlas, the earlier selected archive, and the locked machinery/reference evidence. It identified a missing defense platform, additional world forms, hand-reference gaps for six existing human identities, and 24 Atlas appearances requiring their own references. This collection covers the gaps found in those specific sources.', '',
    f'The exact findings remain in the {link(main, "world gap matrix", "audit/world/world-gap-matrix.json")}, '
    f'{link(main, "cast coverage matrix", "audit/cast/cast-coverage-matrix.json")}, '
    f'{link(main, "Atlas census", "audit/cast/atlas-cast-census-v2.json")}, and '
    f'{link(main, "requirements", "requirements.json")}. Previously accepted resource, character, enemy, companion, structure, storage, and conveyor references stay preserved in the '
    f'[immutable starting archive](https://github.com/ksolo21-web/HAVENLINE/tree/{a.BASE}).', '',
    '## Source detail and authored interpretation', '',
    'Source-visible silhouettes, clothing, materials, accessories, and distinct variants guide the new images. Rear faces, opened interiors, individual glove construction, hidden prop surfaces, and coherent open states are authored interpretations where the source does not show them. Atlas examples retain their source-row A/B/C identities and future-concept status; they do not establish new numerical tiers, recipes, capacities, rates, unlocks, or balance values.', '',
    '**These are static concept and reference PNGs.** They are not native meshes, textures/UV packages, rigs, animation cycles, implemented machines, or runtime/device signoffs. Visible spread fingers support modeling reference; they do not demonstrate deformation, rigging, motion, or production readiness.', '',
    '## Every original and its record', '',
    f'- {link(main, "Native originals and rejected revisions", "indexes/originals.md")}: {generation["generated_original_count"]} completed native PNGs captured at this build.',
    f'- {link(main, "Actual invocations, exact prompts, and no-image failures", "indexes/invocations.md")}: {len(generation["actual_invocations"])} image-producing calls and {len(generation["failed_no_image_invocations"])} failed request{("s" if len(generation["failed_no_image_invocations"]) != 1 else "")} with no image.',
    f'- {link(main, "Source and input access", "indexes/sources.md")}: original boards, limited source crops, native detail references, {len(authored_guides)} author-created geometry guide revisions, and immutable prior-art bindings.',
    f'- {link(main, "Generation/selection manifest", "generation-manifest.json")} and {link(main, "exact hash resolver", "provenance/hash-resolver.json")}: complete machine-readable custody.', '',
    'Original PNG bytes, actual prompt strings, ordered image inputs, requirements snapshots, rejected attempts, and independent reviews are retained. Saved prompt documents may include one terminal newline; the exact invoked prompt is preserved separately. The delivery receipt is added only after complete remote tree and file-body checks.', '',
    'The undefined handheld-upgrade roster and the unresolved tiny YT13 crowd identity remain explicitly unresolved. No claim of whole-game completion is made.'
]
write_page(main, '\n'.join(intro))

descriptions = {
    'world': ('World and camp', 'World buildings, machines, infrastructure, defenses, and biome studies. Each source variant has opposing views; relevant open/use states and connection details are included where required. The defense platform has separate turnaround and service/detail sheets. The rope-fence corner is a supplement to its existing identity.'),
    'npcs': ('Survivors and NPCs', 'Six established identities receive four cardinal neutral body views and large palm/dorsal hand details. Their earlier relaxed rotations remain preserved as complementary coverage. Five separated digits, anatomical thumb placement, cuffs, and glove construction are checked as visible static details.'),
    'animals': ('Atlas animals', 'Fourteen source-specific animal appearances receive their own static turnarounds. Source-visible species traits, horns/antlers, coats, armor, tail forms, paws/hooves, and distinct silhouettes guide the references. Hidden surfaces remain authored interpretations.'),
    'raiders': ('Atlas raiders', 'Ten Atlas appearances each require a four-view neutral body sheet and a matching hands/gear sheet. The detailed gloves must agree with the accepted body. Detached gear is opaque fictional visual reference; the images establish no technical internals or functioning weapon mechanisms.')}
for key, sheets in required_by_category.items():
    heading, description = descriptions[key]
    page = 'galleries/' + key + '.md'
    lines = ['# Havenline · ' + heading, '', link(page, 'All categories', 'README.md') + ' · ' + link(page, 'Every native original', 'indexes/originals.md'), '',
             f'**{stage_label}: {counts[key]}/{len(sheets)} sheets approved.**', '', description, '',
             '| Required sheet | Current selected native revision | Score | Access |', '| --- | --- | ---: | --- |']
    for sheet in sheets:
        row = selected.get(sheet)
        if row:
            access = link(page, 'PNG', row['selected_path']) + ' · ' + link(page, 'review', row['public_review_path'])
            lines.append(f'| {title(sheet)} | `{row["render_id"]}` | {row["score"]:.1f} | {access} |')
        else:
            pending = pending_by_id.get(sheet, {})
            state = clean(pending.get('status', 'PENDING_INDEPENDENT_APPROVAL')).replace('_', ' ').lower()
            lines.append(f'| {title(sheet)} | {state} | — | {link(page, "Attempts index", "indexes/originals.md")} |')
    for sheet in sheets:
        if sheet not in selected:
            continue
        row = selected[sheet]
        lines += ['', '## ' + title(sheet), '',
                  f'`{row["render_id"]}` · independent static score **{row["score"]:.1f}/10** · '
                  + link(page, 'Exact review', row['public_review_path']) + ' · '
                  + link(page, 'Retained original', row['original_path']), '']
        if sheet in world_catalog:
            entry = world_catalog[sheet]
            lines += ['Source forms: ' + '; '.join(entry['source_variants']) + '.', '']
            if entry.get('future_visual_concept'):
                lines += ['**Atlas future concept.** A/B/C labels identify source examples; no numerical progression is invented.', '']
        lines += ['![' + title(sheet) + '](' + destination_link(page, row['selected_path']) + ')', '']
    lines += ['', '## Acceptance boundary', '',
              'Every displayed selection has an independent score strictly above 9.0, all mandatory visual checks passed, and an exact PNG hash binding. Approval covers the shown static image only. Source-hidden geometry and surfaces are interpretations; native model, rig, animation, gameplay, and device testing are outside this archive’s approval.']
    write_page(page, '\n'.join(lines))

page = 'indexes/originals.md'
lines = ['# Havenline · Every native original', '', link(page, 'Selected galleries', 'README.md') + ' · ' + link(page, 'Actual calls and failed requests', 'indexes/invocations.md'), '',
         f'**{generation["generated_original_count"]} complete native PNGs captured.** Each original is retained without resizing, recompression, or painted edits. A selected alias has the same exact bytes. Rejected versions remain accessible.', '',
         '| Native original | Required sheet | Review / selection state | Review |', '| --- | --- | --- | --- |']
selected_ids = {row['render_id'] for row in selected.values()}
for ident, call in sorted(calls.items()):
    inv = a.read(Path(call['exact_invocation']['source_path']))
    review_path = ROOT / 'reviews' / ('critic-' + ident + '.json')
    report = a.read(review_path) if review_path.exists() else None
    if ident in selected_ids:
        state = 'Current selected static PASS'
    elif report:
        state = clean(report['status']) + (f' ({report["score"]:.1f}/10)' if isinstance(report.get('score'), (int, float)) else '')
    else:
        state = 'Awaiting independent review'
    review_link = link(page, 'Exact report', 'reviews/' + review_path.name) if report else 'Pending'
    sheet = inv.get('deliverable_id', re.sub(r'-r\d+$', '', ident))
    assert sheet in family_for, 'Original requires an explicit known deliverable binding: ' + ident
    lines.append('| ' + link(page, ident, call['output']['path']) + ' | ' + title(sheet) + ' | ' + state + ' | ' + review_link + ' |')
lines += ['', 'A failed tool request with no image is listed in the invocation index and is never counted as a native original. A prior PASS record does not make an older revision the current selection; the category galleries and frozen generation manifest identify the chosen revision.']
if authored_guides:
    lines += ['', '## Author-created guide images', '',
              'These new mathematical diagrams were rendered from their saved authoring code. They are separate from the image service’s native output count and from the final selected game-art sheets. Each authored revision remains accessible.', '',
              '| Guide revision | Image | Code | Exact parameters | Disposition |', '| --- | --- | --- | --- | --- |']
    for guide in authored_guides:
        lines.append('| `' + guide['id'] + '` | ' + link(page, 'PNG', guide['png_path']) + ' | '
                     + link(page, 'Python', guide['code_path']) + ' | ' + link(page, 'JSON', guide['parameters_path'])
                     + ' | ' + clean(guide['disposition']).replace('_',' ').lower() + ' |')
write_page(page, '\n'.join(lines))

page = 'indexes/invocations.md'
lines = ['# Havenline · Actual calls, prompts, and failures', '', link(page, 'Selected galleries', 'README.md') + ' · ' + link(page, 'Native originals', 'indexes/originals.md'), '',
         'The exact invoked UTF-8 prompt is separate from its saved prompt document, which may add one final newline. Each invocation record retains the ordered input paths and hashes, exact requirements version, and observed result. Original PREPARED records and root refinements remain history; preparation alone is not proof of a tool call.', '',
         '## Failed requests without an image', '']
if generation['failed_no_image_invocations']:
    lines += ['| Attempt | Exact invocation | Exact prompt | Observed error | Requirements |', '| --- | --- | --- | --- | --- |']
    for row in generation['failed_no_image_invocations']:
        error = row.get('exact_original_error_record')
        lines.append('| `' + row['id'] + '` | ' + link(page, 'JSON', row['exact_invocation']['path']) + ' | '
                     + link(page, 'Prompt', row['exact_attempted_prompt']['path']) + ' | '
                     + (link(page, 'Exact service record', error['path']) if error else 'Recorded in invocation JSON') + ' | '
                     + link(page, 'Snapshot', row['requirements']['path']) + ' |')
    lines += ['', 'These attempts produced **zero images**. Their records are retained without a fabricated render, visual review, or successful-generation claim.', '']
else:
    lines += ['No failed no-image calls are present in this capture.', '']
lines += ['## Image-producing invocations', '', '| Native output | Actual invocation | Exact prompt | Saved prompt document | Ordered inputs | Requirements |', '| --- | --- | --- | --- | ---: | --- |']
for ident, row in sorted(calls.items()):
    lines.append('| ' + link(page, ident, row['output']['path']) + ' | '
                 + link(page, 'JSON', row['exact_invocation']['path']) + ' | '
                 + link(page, 'Exact argument', row['exact_invoked_prompt']['path']) + ' | '
                 + link(page, 'Document', row['source_prompt_document']['path']) + ' | '
                 + str(len(row['ordered_reference_inputs'])) + ' | '
                 + link(page, 'Snapshot', row['requirements']['path']) + ' |')
lines += ['', '## Preparation and refinements', '',
          link(page, 'Exact preparation history', 'provenance/invocations/prepared') + ' · '
          + link(page, 'Source and artifact hash mapping', 'provenance/source-and-artifact-bindings.json'), '',
          'A root refinement may change an uninvoked prepared prompt before the real call. Both the original preparation and the later actual invoked record are retained; the actual invocation is the authority for what the image service received.']
write_page(page, '\n'.join(lines))

page = 'indexes/sources.md'
lines = ['# Havenline · Source and input access', '', link(page, 'Selected galleries', 'README.md') + ' · ' + link(page, 'Actual invocations', 'indexes/invocations.md'), '',
         'Original user boards, individually scoped reference crops, and exact prior-art bindings support this package. Full third-party videos, web pages, audio, and broad downloaded frame collections are not republished.', '',
         '## Recovered original boards', '', '| Original source name | Exact archived bytes | Format note |', '| --- | --- | --- |']
source_allow = a.read(ROOT / 'archive-generation-input-allowlist.json')
for row in source_allow['allowed_inputs']:
    if '/original-boards/' not in row['archive_relative_path']:
        continue
    source_name = Path(row['local_path']).name
    format_note = 'Original PNG bytes' if source_name.startswith('Havenline:') else 'Historical .png name contains original JPEG bytes; archived .jpg alias preserves the exact bytes'
    lines.append('| ' + clean(source_name) + ' | ' + link(page, 'Open original', row['archive_relative_path']) + ' | ' + format_note + ' |')
if authored_guides:
    lines += ['', '## Author-created geometry guides', '',
              'These are explicit authored aids, not recovered reference evidence. The double-gate guide uses exact half-arch equations and rigid 90° rotations toward y<0. Its colors, bar counts, and frame details are diagram conventions. Root and independent inspection are recorded separately from the code’s mathematical checks.', '',
              '| Authored revision | Diagram | Authoring provenance | Geometry checks |', '| --- | --- | --- | --- |']
    for guide in authored_guides:
        lines.append('| `' + guide['id'] + '` | ' + link(page, 'PNG', guide['png_path']) + ' | '
                     + link(page, 'Exact code/parameter bindings', guide['provenance_path']) + ' | '
                     + link(page, 'Builder checks', guide['geometry_check_path']) + ' |')
lines += ['', '## Exact inputs actually supplied', '',
          'Repeated uses are grouped by SHA256. The per-call manifest preserves the original order and the source’s role. Source-hidden faces and details remain authored interpretations.', '',
          '| Reference | Binding | SHA256 prefix |', '| --- | --- | --- |']
references = {}
for call in generation['actual_invocations']:
    for row in call['ordered_reference_inputs']:
        references.setdefault(row['sha256'], row)
for call in generation['failed_no_image_invocations']:
    for row in call['attempted_ordered_reference_inputs']:
        references.setdefault(row['sha256'], row)
for row in sorted(references.values(), key=lambda item: item['original_locator']):
    target = row.get('archive_path', row.get('immutable_url'))
    assert target, 'An actual source is still unresolved'
    label = Path(row['original_locator']).name
    kind = row['disposition'].replace('_', ' ').lower()
    lines.append('| ' + link(page, clean(label), target) + ' | ' + kind + ' | `' + row['sha256'][:16] + '` |')
lines += ['', '## Full provenance', '',
          '- ' + link(page, 'Original-source allowlist', 'generation-inputs/PUBLIC-INPUT-ALLOWLIST.json'),
          '- ' + link(page, 'Exact derived-source and native-detail provenance', 'generation-inputs/INTERNAL-DERIVED-INPUTS.json'),
          '- ' + link(page, 'Full source/artifact mapping', 'provenance/source-and-artifact-bindings.json'),
          '- ' + link(page, 'Complete generation manifest', 'generation-manifest.json'),
          '- ' + link(page, 'Exact hash resolver', 'provenance/hash-resolver.json'), '',
          'Prior artwork is linked to immutable baseline commit/blob identities when the exact bytes already exist. New images and source crops retain their original encoding. Enlarged inspection views, if present in review evidence, are separately documented and do not replace native source pixels.']
write_page(page, '\n'.join(lines))

record = {'schema_version': 1, 'status': 'FINAL_STATIC_GALLERIES_AWAITING_ROOT_FREEZE' if args.final else 'DRAFT_GALLERIES_NOT_FROZEN_NOT_PUBLISHED',
          'built_at_utc': datetime.now(timezone.utc).isoformat(),
          'requirements_sha256': a.metrics(requirements_path.read_bytes())['sha256'],
          'working_selection_sha256': a.metrics(selection_path.read_bytes())['sha256'],
          'generation_capture_sha256': a.metrics(generation_path.read_bytes())['sha256'],
          'required_sheets': 81, 'selected_sheets': len(selected), 'selected_by_category': counts,
          'generated_originals': generation['generated_original_count'],
          'failed_no_image_calls': len(generation['failed_no_image_invocations']),
          'authored_guide_revisions': len(authored_guides),
          'proposed_selected_aliases': [{'id': row['render_id'], 'deliverable_id': sheet,
              'source_path': row['local_path'], 'selected_path': row['selected_path'],
              'sha256': row['sha256'], 'bytes': row['bytes'], 'git_blob_sha': row['git_blob_sha'],
              'review_path': row['review_path'], 'review_sha256': row['review_sha256'], 'score': row['score']}
              for sheet, row in selected.items()],
          'public_files': written, 'generation_frozen': False, 'branch_written': False,
          'scope_boundary': 'Static PNG reference only; final exact root freeze and separate archive criticism remain required.'}
a.write(out / 'gallery-manifest.json', record)
print(json.dumps({'status': record['status'], 'selected_sheets': len(selected), 'required_sheets': 81,
                  'selected_by_category': counts, 'native_originals_indexed': generation['generated_original_count'],
                  'failed_calls_indexed': len(generation['failed_no_image_invocations']),
                  'pages': [row['archive_path'] for row in written], 'branch_written': False}, indent=2))
