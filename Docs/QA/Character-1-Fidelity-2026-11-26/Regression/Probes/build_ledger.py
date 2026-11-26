"""Material and cargo re-audit of the exact-skin practical rig ledger."""
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
import argparse, hashlib, json, re, struct, subprocess

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text())

def save(p, obj):
    p.write_text(json.dumps(obj,indent=2)+'\n')

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('project',type=Path);cli.add_argument('source')
    cli.add_argument('prior_review',type=Path);cli.add_argument('output',type=Path)
    cli.add_argument('--git-dir',required=True,type=Path)
    args=cli.parse_args();o=args.output.resolve();p=args.project.resolve();prior=args.prior_review.resolve()
    assert re.fullmatch('[0-9a-f]{40}',args.source)
    prev=read(prior/'Rig/Final/Ledger.json')
    old_locations=read(prior/'Rig/Final/Ledger-evidence-locations.json')['evidence']
    prev_archive='5c8bb92fdfb9561aea14b19b1ea484c4b06ae55a'
    archive_url='https://github.com/ksolo21-web/HAVENLINE/blob/'+prev_archive+'/Docs/QA/World-One-Critic-2026-11-26/'
    asset=p/'assets/characters/Character1Fresh.glb';bits=asset.read_bytes()
    g=json.loads(bits[20:20+struct.unpack_from('<I',bits,12)[0]])
    names={g['nodes'][i]['name'] for s in g['skins'] for i in s['joints']}
    expected_clips=[x['name'] for x in g['animations']]
    checked_names=[joint for group in prev['parts'] for joint in group['joints']]
    assert sorted(checked_names)==sorted(names) and sorted(expected_clips)==sorted(prev['clips'])
    shape=read(o/'Skin-equivalence.json');assert shape['passed'] and shape['candidate_sha256']==sha(asset)
    assert all(row['max_skinned_vertex_component_difference_m']==0. for row in shape['clips'].values())
    src=read(o/'Source.json');assert src['source']==args.source
    suite=read(o/'Native/Native-results.json');assert suite['source']==args.source and suite['passed']
    assert suite['suites']==22 and suite['native_runs']==23
    gait=(o/'Gait-turn-stability.log').read_text()
    assert not re.search(r'(?:WARNING|ERROR):',gait)
    stability=next(json.loads(line) for line in gait.splitlines() if line.startswith('{'))
    assert stability['passed'] and stability['physics_ticks']==5600 and stability['first_bad_tick']==-1
    assert stability['min_scale']>=.999 and stability['max_scale']<=1.001
    for log in (o/'Geometry').glob('*.log'):
        assert not re.search(r'(?:WARNING|ERROR):',log.read_text()),log
    contact=read(o/'Geometry/Gear-contact-120Hz.json')
    for r in contact['tests'].values():
        assert r['phase_samples']==108 and r['headings']==12 and r['collision_sample_pairs']==0
    assert not contact['different_material_triangle_intersections']
    assert contact['loads']['full-72']==72 and contact['loads']['30-mixed']==30
    support=read(o/'Geometry/Rack-support.json')
    assert all(sample['rays_over_rack'] and sample['min_vertical_surface_distance_m'] < .005
               for arrangement in ('mixed','single_family') for sample in support[arrangement].values())
    body=read(o/'Geometry/Body-and-pack.json')
    coverage={}
    for key,row in body['stages'].items():
        actual=[k for k in row['overlapping_props'] if 'rack.' not in k]
        assert not actual,actual
        coverage[key]=row['frames']
    assert sum(coverage.values())>=416
    radial=read(o/'Geometry/Continuous-clearance.json')
    assert radial['results']['axe']['guarantees_separation']
    assert all(result['settled_separation_proven'] for result in radial['results'].values())
    prior_proofs={}
    for name,x in old_locations.items():
        # Prior evidence is checked and linked by Git location and hash. It is used only
        # where the same physical skeleton/surface and motion were verified above.
        if 'review_file' in x:
            url=archive_url+quote(x['review_file'])
            assert sha(prior/x['review_file'])==x['sha256'],name
        else:
            url=x['archived_blob']
        commit,blob=unquote(urlsplit(url).path.split('/blob/')[1]).split('/',1)
        data=subprocess.check_output(['git','-C',str(args.git_dir),'cat-file','blob',commit+':'+blob])
        assert hashlib.sha256(data).hexdigest()==x['sha256'],name
        prior_proofs[name]={'url':url,'sha256':x['sha256']}
    snap=read(prior/'Rig/Final/Source-receipt.json')
    assert snap['sha256']['gait_motor.gd']==sha(p/'gait_motor.gd')
    assert snap['sha256']['orbit_locomotion.gd']==sha(p/'orbit_locomotion.gd')
    checks=[]
    body_parts={x['id'] for x in prev['parts']}
    seen=set()
    for old in prev['checks']:
        part=old['part'];clip=old['clip'];check=old['check']
        key=(part,clip,check)
        assert key not in seen and old['status']=='PASS'
        seen.add(key)
        related=['Source.json','Skin-equivalence.json']
        if check=='cargo mesh clearance':
            related.extend(['Geometry/Gear-contact-120Hz.json','Geometry/Continuous-clearance.json','Geometry/Body-and-pack.json'])
        elif check=='rack support reach':
            related.extend(['Geometry/Rack-support.json','Geometry/Body-and-pack.json'])
        elif check in ('export_integrity','contact','support continuity at 9.5 polish'):
            related.extend(['Native/Native-results.json','Geometry/Body-and-pack.json','Gait-turn-stability.log'])
        elif check=='clearance' or check=='deformation':
            related.extend(['Geometry/Body-and-pack.json'])
        related=[{'file':file,'sha256':sha(o/file)} for file in related]
        checks.append(dict(part=part,clip=clip,check=check,status='PASS',evidence=related,
                           archived_physical_comparisons=old['evidence']))
    for part in body_parts:
        for clip in expected_clips:
            for check in ['transforms','deformation','temporal','clearance']:
                assert (part,clip,check) in seen
    assert len(checks)==403
    signed=o.parent/'Critic/Scores.json'
    grades=read(signed)
    assert grades['source']==args.source
    for item in grades['dimensions'].values():
        for receipt in item['evidence']:
            assert sha(o.parent/receipt['file'])==receipt['sha256'],receipt
    result=dict(source=args.source,scene='res://field_opening.tscn',
        scope='Technical preservation, anatomical and equipment regression. Independent appearance judgment, reference fidelity and its scores are documented by the visual critic.',
        original_ledger=archive_url+'Rig/Final/Ledger.json',original_ledger_sha256=sha(prior/'Rig/Final/Ledger.json'),
        candidate_sha256=sha(asset),parts=prev['parts'],clips=expected_clips,actual_joints=len(names),
        rows=len(checks),status='PASS',gait_and_body_tests=coverage,
        verified_archival_evidence=len(prior_proofs),gait_stability=stability,
        independent_visual_review={'file':'../Critic/Scores.json','sha256':sha(signed),
            'scores':{name:grade['score'] for name,grade in grades['dimensions'].items()}},
        archive_evidence_catalog=prior_proofs,checks=checks)
    save(o/'Practical-rig-ledger.json',result)
    print('Checked all',len(checks),'unique rows,',len(names),'joints and',len(expected_clips),'clips on',args.source)

if __name__=='__main__':main()
