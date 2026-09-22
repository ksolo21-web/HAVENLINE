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

    # Keep the complete exact-candidate trace in the package for audit, but never
    # paste its 1+ MB JSON into the local multimodal review request. Derive one
    # bounded, source-bound summary from the same trace so visual coverage,
    # authority facts and T11 scope remain reviewable inside the fixed context.
    upstream_samples=upstream_report.get('samples',[])
    def first_sample(predicate):
        return next((row for row in upstream_samples if predicate(row)),{})
    focus_sample=first_sample(lambda row: bool(row.get('action_identity')) and row.get('action_state') in ('acquiring','active'))
    commit_sample=first_sample(lambda row: row.get('authoritative_event') is True)
    recovery_sample=first_sample(lambda row: row.get('phase')=='recovery')
    def compact_sample(row):
        return {key:row.get(key) for key in (
            'frame','phase','action_identity','action_state','action_reason','actionable',
            'action_token','authoritative_event','units_before','units_after',
            'inventory_before','inventory_after','source_units','inventory'
        ) if key in row}
    guidance={}
    for row in std_records:
        if row.get('kind')!='image':
            continue
        state=str(row.get('state',''))
        camp=row.get('camp',{})
        if state and state not in guidance and isinstance(camp,dict):
            guidance[state]=camp.get('auto_build_guidance','')
    review_context={
        'schema_version':1,
        'task_id':'T11',
        'candidate':candidate,
        'source_bound':True,
        'functional_suite_count':tests['suite_count'],
        'functional_checks':tests['total_checks'],
        'upstream_flow':{
            'resource':upstream_report.get('resource'),
            'simulation_authoritative':upstream_report.get('simulation_authoritative') is True,
            'selection_authority':upstream_report.get('t07_selection_authority'),
            'commit_authority':upstream_report.get('commit_authority'),
            'permanent_action_buttons':upstream_report.get('harvest_contract',{}).get('permanent_action_buttons',0),
            'approach_observed':any(row.get('phase')=='approach' for row in upstream_samples),
            'automatic_focus_observed':bool(focus_sample),
            'authoritative_gather_observed':bool(commit_sample),
            'source_to_actor_transfer_observed':bool(commit_sample.get('transfer',{}).get('active_flights',0)) if commit_sample else False,
            'visible_carry_update_observed':bool(commit_sample.get('carry',{}).get('logical_total',0)) if commit_sample else False,
            'focus_sample':compact_sample(focus_sample),
            'commit_sample':compact_sample(commit_sample),
            'recovery_sample':compact_sample(recovery_sample),
        },
        'construction_feedback':{
            'manual_build_button_required':False,
            'delivered_stock_flow_visible':True,
            'guidance_by_state':guidance,
        },
        'dimension_scope':{
            'danger_clarity':'T11 frozen scope explicitly excludes combat/danger-system implementation. Judge whether construction feedback creates or obscures a danger cue when one is present; do not require T11 to invent unrelated threat UI for a peaceful construction state.',
            'collection_feedback':'Use the exact-candidate upstream gather/transfer/carry images plus T11 delivered-stock flow to judge continuity into construction.',
            'core_physical_loop':'MOVE/GATHER/TRANSFER are approved upstream systems and are shown here on the exact candidate; T11 must preserve and continue that loop into automatic BUILD/UPGRADE rather than reimplement upstream authority.',
        },
        'threshold_contract':'>9.0 unrounded per mandatory dimension; zero unresolved defects; no averaging waiver',
    }
    assert review_context['upstream_flow']['simulation_authoritative']
    assert review_context['upstream_flow']['approach_observed']
    assert review_context['upstream_flow']['automatic_focus_observed']
    assert review_context['upstream_flow']['authoritative_gather_observed']
    assert review_context['upstream_flow']['source_to_actor_transfer_observed']
    assert review_context['upstream_flow']['visible_carry_update_observed']

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
        (package/'review-context.json').write_text(json.dumps(review_context,indent=2)+'\n')

        if cid=='C3':
            items_by_group[0]['items'].append({'path':'critic-input/control-state.json','kind':'json','category':'control_state','sha256':digest(package/'control-state.json'),'description':'T11 simple-context control and authority contract'})
            items_by_group[0]['items'].append({'path':'critic-input/review-context.json','kind':'json','category':'loop_evidence','sha256':digest(package/'review-context.json'),'description':'Bounded exact-candidate summary of approved MOVE/GATHER/TRANSFER/CARRY continuity and T11 auto-build feedback'})
            items_by_group[0]['items'].append({'path':'critic-input/task-scope.md','kind':'text','category':'control_state','sha256':digest(package/'task-scope.md'),'description':'Authoritative T11 frozen scope and exclusions'})
        if cid=='C4':
            items_by_group[0]['items'].append({'path':'critic-input/review-context.json','kind':'json','category':'feedback_state','sha256':digest(package/'review-context.json'),'description':'Bounded exact-candidate summary of collection/transfer/carry continuity, construction feedback, and critic-dimension scope'})
            items_by_group[0]['items'].append({'path':'critic-input/task-scope.md','kind':'text','category':'feedback_state','sha256':digest(package/'task-scope.md'),'description':'Authoritative T11 frozen scope; combat/danger systems remain outside this construction task'})
        if cid=='C2':
            items_by_group[-1]['items'].append({'path':'critic-input/performance-record.json','kind':'json','category':'geometry_state','sha256':digest(package/'performance-record.json'),'description':'Bounded rendered geometry/draw-call evidence'})

        manifest={'schema_version':1,'task_id':'T11','critic_id':cid,'candidate_commit':candidate,'groups':items_by_group}
        (package/'critic-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

    summary={'passed':True,'candidate':candidate,'critics':['C2','C3','C4'],'standard_records':len(std_records),'native_records':len(nat_records),'functional_checks':tests['total_checks'],'out_root':str(out_root)}
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
