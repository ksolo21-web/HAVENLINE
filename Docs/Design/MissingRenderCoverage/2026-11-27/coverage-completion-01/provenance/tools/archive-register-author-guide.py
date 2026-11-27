"""Register a fresh authored geometry guide without calling it recovered source art.

Only a separately passed, exactly PNG-bound guide with explicit root input
authorization is added to the image-generation input allowlist. The author's
original files and any historical pending statements remain unchanged.
"""
from pathlib import Path
import argparse
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('archive_tools', ROOT / 'archive-tools.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)

parser = argparse.ArgumentParser()
parser.add_argument('guide_id')
parser.add_argument('--author', required=True)
parser.add_argument('--review')
parser.add_argument('--input-authorization')
parser.add_argument('--root-viewed', action='store_true')
args = parser.parse_args()
assert not (ROOT / 'archive-content-publication.json').exists()
folder = ROOT / 'author-guides' / args.guide_id
assert folder.resolve().parent == (ROOT / 'author-guides').resolve()
names = ['guide.py', 'parameters.json', 'geometry-checks.json', 'provenance.json',
         args.guide_id + '.png', args.guide_id + '.svg']
files = []
for name in names:
    path = folder / name
    files.append({'source_path': str(path.resolve()), 'archive_path': str(path.relative_to(ROOT)),
                  **t.metrics(path.read_bytes())})
parameters = t.read(folder / 'parameters.json')
assert parameters['origin'] == 'AUTHOR_CREATED_MATHEMATICAL_GUIDE'
assert parameters['source_evidence'] is False
assert parameters['existing_bitmaps_read_or_modified'] == []
png = files[-2]
entry = {'id': args.guide_id, 'origin': 'AUTHOR_CREATED_MATHEMATICAL_GUIDE',
         'author': args.author, 'source_evidence': False, 'final_game_art': False,
         'disposition': 'AUTHOR_CREATED_GUIDE_PENDING_INDEPENDENT_INPUT_APPROVAL',
         'files': files, 'png_path': png['archive_path'],
         'code_path': files[0]['archive_path'], 'parameters_path': files[1]['archive_path'],
         'geometry_check_path': files[2]['archive_path'], 'provenance_path': files[3]['archive_path']}
if args.review:
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(ROOT)
    review = t.read(review_path)
    assert review['independent'] is True
    assert review['reviewer'] not in {args.author, '/root/missing_archive', '/root'}
    assert review['status'].startswith('PASS') and review['score'] > 9
    assert review['all_mandatory_checks_passed'] is True
    assert review['actual_full_png_inspected'] is True
    assert review['reviewed_png']['sha256'] == png['sha256']
    assert review['reviewed_png']['bytes'] == png['bytes']
    assert not review.get('mandatory_defects_remaining', [])
    entry['independent_guide_review'] = {
        'path': str(review_path), **t.metrics(review_path.read_bytes()),
        'score': review['score'], 'status': review['status'],
        'approved_use': review.get('approved_use', 'Authored geometry guidance only')}
    entry['disposition'] = 'GUIDE_ONLY_PASS_AWAITING_EXPLICIT_ROOT_INPUT_AUTHORIZATION'
if args.input_authorization:
    assert args.review, 'Input authorization does not replace separate exact guide review'
    entry['root_use_authorization'] = args.input_authorization
    entry['root_direct_png_inspection_confirmed'] = args.root_viewed
    entry['disposition'] = 'GUIDE_ONLY_PASS_ROOT_AUTHORIZED_AS_GEOMETRY_INPUT'
index_path = ROOT / 'author-guides/index.json'
index = t.read(index_path)
old = next((e for e in index['guides'] if e['id'] == args.guide_id), None)
if old:
    assert old['files'] == files, 'Preserve exact authored revisions; create a new folder for changes'
    index['guides'] = [entry if e['id'] == args.guide_id else e for e in index['guides']]
else:
    index['guides'].append(entry)
t.write(index_path, index)
if args.input_authorization:
    source = {'local_path': png['source_path'], **{k: png[k] for k in ['bytes', 'sha256', 'git_blob_sha']},
              'archive_relative_path': png['archive_path'],
              'source_id': 'author-created-' + args.guide_id,
              'source_kind': 'AUTHOR_CREATED_MATHEMATICAL_GUIDE',
              'role': entry['independent_guide_review']['approved_use'] +
                      ' This is author-created geometry guidance, not recovered source evidence or selected final game art.',
              'provenance': {'origin': 'AUTHOR_CREATED_MATHEMATICAL_GUIDE', 'author_agent': args.author,
                             'source_evidence': False, 'final_game_art': False,
                             'root_explicitly_authorized_as_input': True,
                             'root_direct_png_inspection_confirmed': args.root_viewed,
                             'root_use_authorization': args.input_authorization,
                             'authoring_files': files,
                             'independent_guide_review': entry['independent_guide_review'],
                             'author_index_path': str(index_path)}}
    allow_path = ROOT / 'archive-generation-input-allowlist.json'
    allow = t.read(allow_path)
    key = next(k for k,v in allow.items() if isinstance(v,list))
    previous = next((e for e in allow[key] if e['source_id'] == source['source_id']), None)
    if previous:
        assert previous['sha256'] == source['sha256']
        allow[key] = [source if e['source_id'] == source['source_id'] else e for e in allow[key]]
    else:
        allow[key].append(source)
    t.exact_copy(Path(source['local_path']), source['archive_relative_path'])
    t.write(allow_path, allow)
print(json.dumps({'id': entry['id'], 'disposition': entry['disposition'],
                  'png_sha256': png['sha256'], 'root_direct_png_inspection_confirmed': args.root_viewed,
                  'authored_guide_revisions': len(index['guides']), 'branch_written': False}, indent=2))
