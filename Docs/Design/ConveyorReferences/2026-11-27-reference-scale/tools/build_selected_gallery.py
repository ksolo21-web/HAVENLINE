"""Build a selected-only Markdown gallery and exact asset/file manifests.

This never generates, edits, resizes or selects an image. Unselected attempts are
excluded. A final 36-row critic snapshot is required to claim static closure.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import re
from PIL import Image

PKG=Path(__file__).resolve().parents[1]
DEFAULT_CRITIC=Path('/workspace/scratch/59f000bd1476/conveyor-reference-revision/critic')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def gitblob(path):
    data=path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def write_json(path,data): path.write_text(json.dumps(data,indent=2)+'\n')
def exact_copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if source.resolve()!=target.resolve():
        if not target.exists() or sha(source)!=sha(target): shutil.copyfile(source,target)
    assert sha(source)==sha(target)
def pass_review(review):
    status=str(review.get('status',review.get('verdict','')))
    return status.startswith('PASS') and review.get('score')==10
def candidate_records(review):
    values=[]
    for key in ['candidate','candidates','reviewed_candidates','candidate_files']:
        value=review.get(key)
        if isinstance(value,dict): values.append(value)
        elif isinstance(value,list): values.extend(x for x in value if isinstance(x,dict))
    return [x for x in values if x.get('sha256') and x.get('path')]

DESCRIPTIONS={
 '01':('Approved conveyor baseline','The owner-selected low orange/yellow line, dense black rollers, gray transfer plate and blue machinery, with its accepted larger fish context.'),
 '02':('Approved ordinary resource size','Cash, raw meat, wood and the ordinary small fish beside the unchanged Character1 anchor.'),
 '03':('Raw resources','Eight selected raw-resource identities at the revised ordinary presentation size.'),
 '04':('Processed resources','Nine selected processed food, building and industrial material identities.'),
 '05':('Assemblies, containers and valuables','Six selected assembly/container/valuable identities. Cargo is a container presentation; the relay component remains a finite project object.'),
 '06':('Four views of the shore conveyor','A document layout preserves the reviewed front, rear and right panels and pairs them with the corrected left panel. The PDF and source map retain every source identity; superseded full sheets remain archived.'),
 '07':('Animal meat studies — six','Stag-family and hostile-wolf meat references plus four additional animal-cut art studies. Shared meat inventory remains unchanged.'),
 '08':('Animal meat studies — four reserves','Four more historical animal-cut identities, kept as art reserves with no new spawn or drop claims.'),
 '09':('Fish types and sizes','Common and Perch are small studies, Trout medium and Salmon large. These are presentation variants within fish, not new resource wallets or a claimed live species catalogue.'),
 '10':('Transport modules','Straight, corner and height-adapter forms in the approved conveyor family. Joined use and directional states are covered by the separately reviewed connection studies.'),
 '11':('Routing and finite buffers','Typed routing, diverters, merges, finite buffers and visible hold states; the linked review controls the precise displayed scope.'),
 '12':('Storage connections','Four distinct utility/food ports, supported approaches, local transfers and preserved house access. Use together with the utility wall closeup below.'),
 '12b':('Utility wall transfer closeup','Separate through-wall IN/OUT channels reach their own receiving/dispatch positions, a local shuttle/lift and a supported shelf interface. This closes the storage overview’s hidden handoff.'),
 '13':('Food-processing connections','Selected food-machine identities and typed input/output connections. Authored later food branches do not automatically become current market products.'),
 '14':('Timber and mineral connections','Typed utility handling with selected saw/quarry identities and distinct raw/processed material forms.'),
 '15a':('Metallurgy connections','Smelter, metal bench and forge interfaces follow their current authored inputs and outputs; the central warmth heater remains separate.'),
 '15b':('Assembly and fuel interfaces','Separate assembly ingredient bays, finished modules, sealed oil handling and refinery interfaces. Manual collection remains explicit.'),
 '16':('Reserved food-assembly interfaces','A separate two-input food-assembly topology study. Its recipe/menu remains reserved; it introduces no new canonical food or wallet.'),
 '17':('Self-service food counter','Register-free meal restock, visiting-player bulk delivery, autonomous customer access, separate cash and coherent ready/full gates.'),
 '17b':('Self-service material counter','Current eligible planks and blocks use nonfood lanes; wrong raw wood and full-output blocks remain visibly held upstream.'),
 '18':('Connected camp','A proposed meat→meal→storage→self-service study, with two clear gates, central warmth heater and opposing access views.'),
 '19':('Conveyor crossing','Separate supported routes and item-clearance views; the independent review determines the displayed crossing scope.'),
 '20':('Joined modules and routing use states','Additional joined, directional and held/selected-path evidence that standalone module images cannot provide.'),
 '21':('Loaded transport and reverse views','Straight-item fit, rise/fall profiles and the merge reverse view supplement the selected conveyor family; these views do not by themselves close expanded-network coverage.'),
 '22':('Processor connection details','Focused smelter full-hold, forge coal-route, parked-cassette outlet and reverse-cooker details. The linked exact review controls the completed interface scope.'),
 '23':('Expanded compatible networks','Traceable timber, mineral and industrial connection studies. Storage modes stay typed, current planks/blocks remain the material sales examples, and industrial outputs use manual collection.'),
}
GROUPS=[
 ('Owner-selected baselines',{'01','02'}),
 ('Resources and visual variants',{'03','04','05','07','08','09'}),
 ('Conveyor modules and routing',{'06','10','11','19','20','21'}),
 ('Storage and machine connections',{'12','12b','13','14','15a','15b','16','22'}),
 ('Counters and connected camp',{'17','17b','18','23'}),
]

def row_snapshot(path, required_ids):
    """Bind the critic's explicit rows to exact images/reports; never infer closure."""
    if not path:
        return {'source':None,'status':'PENDING_FINAL_INDEPENDENT_ROW_SNAPSHOT','required_count':len(required_ids),'approved_count':None,'all_required_static_cells_approved':False,'rows':[]}
    source=Path(path);d=json.loads(source.read_text())
    assert d.get('required_rows')==len(required_ids), 'Critic required-row count differs'
    assert d.get('source_matrix',{}).get('sha256')==sha(PKG/'plan/REQUIRED_CONVEYOR_RENDER_MATRIX.json'), 'Critic matrix binding differs'
    rows=d.get('rows',[])
    assert isinstance(rows,list), 'Unsupported critic row schema'
    assert {r.get('id') for r in rows}==required_ids and len(rows)==len(required_ids), 'Missing, duplicate or unexpected critic row'
    normalized=[]
    for x in rows:
        key=x['id'];status=str(x.get('status',''));score=x.get('score')
        images=[];reports=[]
        for item in x.get('evidence_images',[]):
            original=Path(item['path'])
            candidate=original if original.is_absolute() else PKG/original
            # Reviews keep their immutable original capture paths. Resolve the
            # exact same bytes in this relocated package for portable delivery.
            try:
                candidate.resolve().relative_to(PKG.resolve())
                in_package=True
            except ValueError:
                in_package=False
            if not in_package or not candidate.is_file():
                matches=[p for p in PKG.rglob(original.name) if p.is_file() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256']]
                assert matches, f'Bound image not preserved in package for {key}: {original}'
                candidate=sorted(matches,key=lambda p:('attempts' not in p.parts,str(p)))[0]
            assert candidate.is_file() and candidate.stat().st_size==item['bytes'] and sha(candidate)==item['sha256'], f'Changed image evidence for {key}: {candidate}'
            with Image.open(candidate) as im: assert list(im.size)==item['dimensions']
            relative=candidate.resolve().relative_to(PKG.resolve())
            images.append(dict(item,path=str(relative),original_source_path=item['path']))
        for item in x.get('review_reports',[]):
            original=Path(item['path'])
            candidate=original if original.is_absolute() else source.parent/original
            assert candidate.is_file() and candidate.stat().st_size==item['bytes'] and sha(candidate)==item['sha256'], f'Changed review evidence for {key}: {candidate}'
            try: relative=candidate.relative_to(source.parent)
            except ValueError: relative=Path(candidate.name)
            target=PKG/'reviews/coverage'/relative;exact_copy(candidate,target)
            if candidate.with_suffix('.md').exists():exact_copy(candidate.with_suffix('.md'),target.with_suffix('.md'))
            reports.append(dict(item,path=str(target.relative_to(PKG)),original_source_path=item['path']))
        mandatory=x.get('mandatory_static_evidence_complete') is True
        approved=status=='PASS' and score==10 and mandatory and bool(images) and bool(reports) and bool(x.get('reviewer')) and not x.get('remaining_requirement')
        normalized.append({'id':key,'status':status,'score':score,'mandatory_static_evidence_complete':mandatory,'reviewer':x.get('reviewer'),'evidence_images':images,'review_reports':reports,'remaining_kind':x.get('remaining_kind'),'remaining_requirement':x.get('remaining_requirement'),'source_sheet_has_other_unresolved_panels':x.get('source_sheet_has_other_unresolved_panels',False),'approved':approved,'source_row':x})
    ids=[x['id'] for x in normalized]
    all_pass=d.get('all_static_rows_pass') is True and len(ids)==len(required_ids) and len(set(ids))==len(required_ids) and all(x['approved'] for x in normalized)
    target=PKG/'reviews/coverage-snapshots'/f'CONVEYOR_COVERAGE_{sha(source)[:12]}.json';exact_copy(source,target)
    if source.with_suffix('.md').exists():exact_copy(source.with_suffix('.md'),target.with_suffix('.md'))
    return {'source':str(target.relative_to(PKG)),'source_sha256':sha(target),'source_status':d.get('status'),'source_counts':d.get('counts'),'source_provenance_note':d.get('provenance_note'),'status':'PASS_ALL_REQUIRED_STATIC_CELLS' if all_pass else 'PENDING_OR_HELD_STATIC_CELLS','required_count':len(required_ids),'approved_count':sum(x['approved'] for x in normalized),'all_required_static_cells_approved':all_pass,'rows':normalized,'source_layout_note':'Only explicit independent PASS + exact score10 + mandatory evidence complete + unchanged bound images/reports closes a row. A row may pass while another panel on its source sheet remains held; retain that source warning.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--critic-root',default=str(DEFAULT_CRITIC));ap.add_argument('--coverage-review');args=ap.parse_args()
    now=datetime.now(timezone.utc).isoformat();critic=Path(args.critic_root)
    if not critic.exists():critic=PKG/'reviews/independent'
    owner=json.loads((PKG/'OWNER_APPROVAL.json').read_text());owned={x['sha256']:x for x in owner['files'] if x['path'].startswith('selected/')}
    reviews=[]
    for file in critic.rglob('*.json'):
        try:d=json.loads(file.read_text())
        except (ValueError,UnicodeError):continue
        if not isinstance(d,dict) or not pass_review(d):continue
        for candidate in candidate_records(d):reviews.append((candidate['sha256'],file,d,candidate))
    selected=[];missing=[]
    for file in sorted((PKG/'selected').glob('*.png')):
        digest=sha(file);prefix=file.stem.split('-')[0];title,caption=DESCRIPTIONS.get(prefix,(file.stem.replace('-',' ').title(),'Selected static concept sheet; see the exact independent review for its scope.'))
        matches=[x for x in reviews if x[0]==digest]
        bindings=[]
        for _,rf,review,candidate in matches:
            target=PKG/'reviews/independent'/rf.relative_to(critic);exact_copy(rf,target)
            if rf.with_suffix('.md').exists():exact_copy(rf.with_suffix('.md'),target.with_suffix('.md'))
            bindings.append({'path':str(target.relative_to(PKG)),'sha256':sha(target),'reviewer':review.get('reviewer'),'status':review.get('status',review.get('verdict')),'score':review.get('score'),'scope':review.get('scope'),'candidate_source_path':candidate['path']})
        if digest not in owned and not bindings:missing.append(str(file.relative_to(PKG)))
        with Image.open(file) as im:dimensions=list(im.size)
        selected.append({'path':str(file.relative_to(PKG)),'prefix':prefix,'title':title,'caption':caption,'bytes':file.stat().st_size,'sha256':digest,'git_blob_sha1':gitblob(file),'dimensions':dimensions,'artifact_kind':'PDF page render of source panels' if prefix=='06' else 'imagegen original','owner_selected_baseline':digest in owned,'owner_record':'OWNER_APPROVAL.json' if digest in owned else None,'independent_reviews':bindings,'runtime_approval':False})
    if missing:raise SystemExit('Selected files lack exact PASS10 candidate binding: '+', '.join(missing))
    matrix=json.loads((PKG/'plan/REQUIRED_CONVEYOR_RENDER_MATRIX.json').read_text());required={r['id'] for r in matrix['required']}
    coverage=row_snapshot(args.coverage_review,required)
    write_json(PKG/'STATIC_COVERAGE_CHECKPOINT.json',{'schema_version':1,'recorded_utc':now,'coverage':coverage,'runtime_approved':False,'whole_task_approved':False})
    manifest={'schema_version':1,'built_utc':now,'scope':'Only selected PNGs with exact owner baseline or independent PASS10 candidate bindings. Static image approval does not approve motion/native implementation.','selected_count':len(selected),'selected':selected,'canonical_resource_count':27,'variants_are_metadata_not_new_wallets':True,'static_coverage':coverage,'runtime_approved':False,'original_images_modified':False}
    write_json(PKG/'SELECTED_ASSET_MANIFEST.json',manifest)
    status=(f"All {len(required)} required static conveyor cells have explicit independent passing evidence." if coverage['all_required_static_cells_approved'] else 'The selected sheets below are approved within their stated static scopes. Whole-catalogue closure is pending the final independent row review; unfinished or untested cells remain open.')
    lines=['# Havenline — selected resources and conveyors','',f'**{len(selected)} selected full-size sheets.** {status}','',
      'The approved conveyor proportions and ordinary small resource size remain the baseline. Character1 is unchanged. Fish types/sizes and animal-specific meat are visual variants within the existing resource families. Bigger stockpiles use more units.', '',
      'These are static concept renders. Native asset integration, continuous motion, collisions and inventory behavior require their own gameplay evidence.', '',
      '[Exact selected-file manifest](SELECTED_ASSET_MANIFEST.json) · [36-cell coverage](STATIC_COVERAGE_CHECKPOINT.json) · [Variant contract](integration/RESOURCE_VARIANT_CONTRACT.json) · [Function handoff](integration/CONVEYOR_FUNCTION_CONTRACT.md)', '',
      'Click any sheet to open its original PNG. All images below are the unchanged selected files; rejected and intermediate attempts remain archived separately.','']
    displayed=set()
    for group,prefixes in GROUPS+[('Additional selected studies',set(x['prefix'] for x in selected)-set().union(*(g[1] for g in GROUPS)))]:
        members=[x for x in selected if x['prefix'] in prefixes]
        if not members:continue
        lines += [f'## {group}','']
        for x in members:
            displayed.add(x['path']);lines += [f"### {x['title']}",'',x['caption'],'',f"[![{x['title']}]({x['path']})]({x['path']})",'']
            if x['owner_selected_baseline']:lines += ['[Owner selection](OWNER_APPROVAL.json).','']
            elif x['independent_reviews']:lines += [f"[Independent static review]({x['independent_reviews'][0]['path']}).",'']
            if x['prefix']=='06':lines += ['[Download the four-view PDF](presentation/06-conveyor-four-view-reference.pdf) · [Source map](presentation/06-conveyor-four-view-pdf-source-map.json)','']
    assert len(displayed)==len(selected)
    lines += ['## Scope retained','',
      'All 27 canonical resource IDs are preserved. Current active market examples use meal, planks and blocks; additional food/machine studies do not add sales eligibility or recipes. The ten animal meat references retain shared meat accounting, and reserve animals are not newly enabled spawns. The historical two-input food assembler remains reserved.', '',
      'Storage is reviewed as the overview **plus** the utility-wall closeup. Its four ports, local transfer mechanism and protected entrances must remain together in implementation. Self-service counters have no register or permanent clerk, and cash stays separate from stock.', '',
      'Source-video playback notes record only the actual sampled native playback reviewed. They do not claim full continuous reference coverage or a functioning Havenline candidate. See [the source playback ledger](integration/SOURCE_PLAYBACK_LEDGER.md).','']
    (PKG/'GALLERY.md').write_text('\n'.join(lines))
    # Recheck frozen selection after reading/report copies; reject a concurrent image mutation.
    assert all(sha(PKG/x['path'])==x['sha256'] for x in selected)
    files=[]
    for path in sorted(PKG.rglob('*')):
        if not path.is_file() or path==PKG/'PACKAGE_FILE_HASHES.json':continue
        files.append({'path':str(path.relative_to(PKG)),'bytes':path.stat().st_size,'sha256':sha(path),'git_blob_sha1':gitblob(path)})
    write_json(PKG/'PACKAGE_FILE_HASHES.json',{'schema_version':1,'built_utc':now,'status':'SNAPSHOT_REBUILD_AFTER_ANY_PACKAGE_MUTATION','excludes':['PACKAGE_FILE_HASHES.json (self-reference)'],'file_count':len(files),'files':files})
    print(json.dumps({'selected_sheets':len(selected),'all_selected_have_exact_approval_binding':True,'gallery':str(PKG/'GALLERY.md'),'required_static_cells':len(required),'final_static_coverage_approved':coverage['all_required_static_cells_approved'],'package_files_hashed':len(files)},indent=2))

if __name__=='__main__':main()
