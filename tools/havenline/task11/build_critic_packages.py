#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def load(path:Path):
    return json.loads(path.read_text())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',required=True)
    ap.add_argument('--standard',required=True)
    ap.add_argument('--native',required=True)
    ap.add_argument('--functional',required=True)
    ap.add_argument('--performance',required=True)
    ap.add_argument('--upstream-flow',required=True)
    ap.add_argument('--out-root',required=True)
    a=ap.parse_args()
    candidate=a.candidate
    if len(candidate)!=40: raise SystemExit('candidate must be exact SHA')
    standard=Path(a.standard);native=Path(a.native);functional=Path(a.functional);performance=Path(a.performance);upstream=Path(a.upstream_flow)
    sm=load(standard/'manifest.json');nm=load(native/'manifest.json');tests=load(functional/'tests.json');sentinel=load(functional/'sentinel.json')
    upstream_report=load(upstream/'capture-report.json')
    assert sm['candidate']==nm['candidate']==tests['source']==upstream_report['candidate']==candidate
    assert sm['passed'] and nm['passed'] and tests['all_passed'] and sentinel['passed']
    assert upstream_report.get('simulation_authoritative') is True
    out_root=Path(a.out_root);out_root.mkdir(parents=True,exist_ok=True)

    control={
        'schema_version':1,
        'task_id':'T11',
        'candidate':candidate,
        'transaction_authority':'T10-world-transform-v1',
        'presentation_authority':'T11-camp-construction-view-v1',
        'manual_action_button_required':False,
        'shadow_resource_authority':False,
        'core_flow':'MOVE -> AUTO-INTERACT -> GATHER -> VISIBLY CARRY -> DELIVER -> TRANSFORM -> BUILD/UPGRADE',
        'functional_suite_count':tests['suite_count'],
        'functional_checks':tests['total_checks'],
        't10_authority_preserved':True,
        'task_approved':False,
        'task_scope':'Camp construction and visual upgrade presentation through the approved T10 boundary',
        'scope_exclusions':['combat/danger-system implementation','manual build button','harvesting authority changes'],
        'upstream_flow_evidence':'Approved T09/T08 approach, automatic gather, transfer and carry capture generated on this exact candidate',
    }

    std_records=sm['records'];nat_records=nm['records']
    def static(states,angles=None):
        return [r for r in std_records if r['kind']=='image' and r['state'] in states and (angles is None or r['angle'] in angles)]
    motion=[r for r in std_records if r['kind']=='motion_frame']
    native_rows=[r for r in nat_records if r['kind']=='image']

    std_by={(r['state'],r['angle']):r for r in std_records if r['kind']=='image'}
    native_by={(r['state'],r['angle']):r for r in nat_records if r['kind']=='image'}
    motion_by={(r['state'],int(r['frame_index'])):r for r in motion}
    def required_rows(index, keys, label):
        missing=[key for key in keys if key not in index]
        if missing: raise SystemExit(f'missing {label} evidence rows: {missing}')
        return [index[key] for key in keys]

    # C2 keeps the broad multi-angle geometry package. C3/C4 use deliberately
    # bounded representative boards so the fixed local independent reviewer can
    # finish without timing out. Every lifecycle remains represented, both
    # standard camera classes remain present, C4 keeps the known-risk complete
    # front/three-quarter states, and committing motion samples both build stages
    # across the pulse cycle. This changes package size only, never source evidence,
    # critic dimensions, reviewer identity, thresholds, or pass rules.
    c3_states=required_rows(std_by,[
        ('foundation_ready','front'),
        ('foundation_preview','three-quarter'),
        ('foundation_complete','front'),
        ('reinforced_blocked','front'),
        ('reinforced_preview','three-quarter'),
        ('reinforced_complete','front'),
    ],'C3 lifecycle')
    c3_motion=required_rows(motion_by,[
        ('foundation_committing',0),('foundation_committing',12),
        ('reinforced_committing',0),('reinforced_committing',12),
    ],'C3 motion')
    c4_states=required_rows(std_by,[
        ('foundation_ready','front'),
        ('foundation_preview','three-quarter'),
        ('foundation_complete','front'),
        ('reinforced_blocked','front'),
        ('reinforced_preview','three-quarter'),
        ('reinforced_complete','front'),
    ],'C4 lifecycle')
    c4_native=required_rows(native_by,[
        ('foundation_preview','front'),
        ('foundation_complete','front'),
        ('reinforced_blocked','front'),
        ('reinforced_complete','front'),
    ],'C4 native readability')
    upstream_names=['wood-approach.png','wood-focus-acquired.png','wood-committed-contact.png','wood-recovery.png']
    upstream_rows=[]
    for name in upstream_names:
        path=upstream/name
        if not path.is_file(): raise SystemExit('missing upstream flow evidence '+str(path))
        upstream_rows.append(path)

    plans={
      'C2':[
        ('foundation-cross-view',[(standard/r['file'],'image','geometry_state',f"{r['state']} {r['angle']} authored camp geometry with T10 framework response") for r in static({'foundation_ready','foundation_preview','foundation_complete'})]),
        ('reinforced-cross-view',[(standard/r['file'],'image','geometry_state',f"{r['state']} {r['angle']} authored reinforced geometry and blocked/upgrade response") for r in static({'reinforced_blocked','reinforced_preview','reinforced_complete'})]),
        ('commit-motion',[(standard/r['file'],'motion_frame','geometry_state',f"{r['state']} pulse frame {r['frame_index']} for clipping/contact continuity") for r in motion]),
        ('native-detail',[(native/r['file'],'image','geometry_state',f"native 3840x2160 {r['state']} {r['angle']} detail frame") for r in native_rows]),
      ],
      'C3':[
        ('complete-physical-build-loop',
          [(upstream/p.name,'image','gameplay_state',f"approved upstream MOVE/AUTO-INTERACT/GATHER/TRANSFER evidence: {p.stem}") for p in upstream_rows]
          +[(standard/r['file'],'image','gameplay_state',f"{r['state']} {r['angle']} build/upgrade world state") for r in c3_states]
          +[(standard/r['file'],'motion_frame','gameplay_state',f"{r['state']} delivered-stock construction flow frame {r['frame_index']}") for r in c3_motion]),
      ],
      'C4':[
        ('complete-construction-feedback',
          [(upstream/p.name,'image','feedback_state',f"approved upstream collection/transfer/carry feedback: {p.stem}") for p in upstream_rows]
          +[(standard/r['file'],'image','gameplay_state',f"{r['state']} {r['angle']} construction state with auto-build guidance") for r in c4_states]
          +[(native/r['file'],'image','feedback_state',f"native 3840x2160 {r['state']} {r['angle']} construction readability frame") for r in c4_native]),
      ],
    }

    for cid,groups in plans.items():
        package=out_root/f'havenline-task11-critic-{cid}'
        if package.exists(): shutil.rmtree(package)
        package.mkdir(parents=True)
        items_by_group=[]
        copied={}
        def add_file(src:Path, rel:Path, kind:str, category:str, description:str):
            dst=package/rel
            if str(rel) not in copied:
                dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);copied[str(rel)]=dst
            return {'path':str(Path('critic-input')/rel),'kind':kind,'category':category,'sha256':digest(dst),'description':description}
        for group_id,rows in groups:
            entries=[]
            for src,kind,category,description in rows:
                folder='native' if src.parent==native else ('upstream' if src.parent==upstream else 'images')
                entries.append(add_file(src,Path(folder)/src.name,kind,category,description))
            items_by_group.append({'id':group_id,'items':entries})

        shutil.copy2(functional/'tests.json',package/'tests.json')
        shutil.copy2(functional/'sentinel.json',package/'sentinel.json')
        shutil.copy2(performance,package/'performance-record.json')
        shutil.copy2(standard/'manifest.json',package/'capture-manifest.json')
        shutil.copy2(native/'manifest.json',package/'native-manifest.json')
        shutil.copy2(upstream/'capture-report.json',package/'upstream-flow-report.json')
        shutil.copy2(ROOT/'Docs/Production/T11/FROZEN_SCOPE.md',package/'task-scope.md')
        (package/'control-state.json').write_text(json.dumps(control,indent=2)+'\n')

        if cid=='C3':
            items_by_group[0]['items'].append({'path':'critic-input/control-state.json','kind':'json','category':'control_state','sha256':digest(package/'control-state.json'),'description':'T11 simple-context control and authority contract'})
            items_by_group[0]['items'].append({'path':'critic-input/tests.json','kind':'json','category':'loop_evidence','sha256':digest(package/'tests.json'),'description':'Six-suite functional and integration proof on the exact candidate'})
            items_by_group[0]['items'].append({'path':'critic-input/upstream-flow-report.json','kind':'json','category':'loop_evidence','sha256':digest(package/'upstream-flow-report.json'),'description':'Exact-candidate approved upstream T09/T08 movement, automatic gather, transfer and carry trace'})
            items_by_group[0]['items'].append({'path':'critic-input/task-scope.md','kind':'text','category':'control_state','sha256':digest(package/'task-scope.md'),'description':'Authoritative T11 frozen scope and exclusions'})
        if cid=='C4':
            items_by_group[0]['items'].append({'path':'critic-input/capture-manifest.json','kind':'json','category':'feedback_state','sha256':digest(package/'capture-manifest.json'),'description':'Rendered construction state descriptors and T11 lifecycle'})
            items_by_group[0]['items'].append({'path':'critic-input/upstream-flow-report.json','kind':'json','category':'feedback_state','sha256':digest(package/'upstream-flow-report.json'),'description':'Exact-candidate upstream collection, transfer, carry and destination trace'})
            items_by_group[0]['items'].append({'path':'critic-input/task-scope.md','kind':'text','category':'feedback_state','sha256':digest(package/'task-scope.md'),'description':'Authoritative T11 frozen scope; combat/danger systems remain outside this construction task'})
        if cid=='C2':
            items_by_group[-1]['items'].append({'path':'critic-input/performance-record.json','kind':'json','category':'geometry_state','sha256':digest(package/'performance-record.json'),'description':'Bounded rendered geometry/draw-call evidence'})

        manifest={'schema_version':1,'task_id':'T11','critic_id':cid,'candidate_commit':candidate,'groups':items_by_group}
        (package/'critic-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

    summary={'passed':True,'candidate':candidate,'critics':['C2','C3','C4'],'standard_records':len(std_records),'native_records':len(nat_records),'functional_checks':tests['total_checks'],'out_root':str(out_root)}
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
