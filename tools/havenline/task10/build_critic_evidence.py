#!/usr/bin/env python3
"""Package measured T10 evidence for existing independent specialist gates."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/havenline/production'))
from specialist_evidence_manifest import validate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def motion_errors(states, segments, video):
    errors=[]
    if video.get('r_frame_rate')!='30/1' or int(video.get('nb_frames',0))<180:
        errors.append('complete 30fps lifecycle recording required')
    if [x.get('state') for x in segments]!=states:
        errors.append('every lifecycle state requires an ordered frame range')
    prior_end=-1
    for row in segments:
        start=row.get('start_frame',-1);end=row.get('end_frame',-1)
        if start<0 or start<prior_end or end-start<30 or end>int(video.get('nb_frames',0)):
            errors.append('invalid or incomplete continuous state frame range')
        prior_end=end
    return errors


SCOPE_SYNOPSIS = '''T10 neutral world-transformation framework; judge all mandatory dimensions in this scope.
R01 stable ordered recipes/costs/prerequisites/presentation keys. R02 pure eligibility with exact blockers. R03 atomic authoritative debit and transition once. R04 stable identity rejects duplicate/stale/out-of-order commits. R05 truthful ready/preview/committing/complete/blocked lifecycle. R06 only physically delivered stored resources pay; carried harvest cannot. R07 monotonic branches, explicit reciprocal inverses only. R08 simulation owns resources, model owns state, view only presents. R09 deterministic component recovery rejects malformed state atomically; global saves belong to T14. R10 neutral branching fixtures; authored camp structures and main-loop binding belong to T11. R11 readable world response at gameplay and six adaptive layouts. R12 bounded previews/events/nodes/history, unchanged state does not rebuild. R13 T05/T08/T09 approved and real authority bound; integration still requires owner acceptance. R14 C1/C2/C3/C4/C6/C7 every mandatory dimension >9.0 unrounded, G1-G14 and impacted regression, zero defects.
No added buttons, menus, grids, capacity walls, combat, danger, economy or population. Existing approach/context controls remain; no harvesting/carry-rule changes. Collection is delivered-stock debit, not new harvesting. No new danger system is in scope; judge truthful blocking/error feedback. Do not penalize absent T11 art or T14 global saves; do not waive any dimension.
'''


def compact_progression(report):
    from validate_progression import REQUIRED
    assert report.get('passed') is True and report.get('executed') is True
    rows = report['suites']
    assert len(rows) == len(REQUIRED) and {r['suite'] for r in rows} == set(REQUIRED)
    for row in rows:
        assert row['passed'] is True and set(row['required_checks']) == set(REQUIRED[row['suite']])
    return '\n'.join(r['suite']+' '+str(r['checks'])+' checks PASS:\n'+'\n'.join(r['required_checks']) for r in rows)


def rendered_group_text(group, root=ROOT):
    chunks=[]
    for item in group['items']:
        if item['kind'] not in ('text','json'): continue
        text=(root/item['path']).read_text()
        if item['kind']=='json': text=json.dumps(json.loads(text),sort_keys=True,indent=2)
        assert len(text)<=14000, 'shared runner would truncate evidence'
        chunks.append('['+item['category']+'] '+item['description']+'\n'+text)
    return '\n\n'.join(chunks)


def prompt_errors(manifest, root=ROOT):
    errors=[]
    cid=manifest['critic_id']
    for group in manifest['groups']:
        try:
            rendered=rendered_group_text(group,root)
            limit=7500 if cid=='C7' else 2800
            image=any(i['kind'] in ('image','motion_frame') for i in group['items'])
            estimate=1000+(2048 if image else 0)+math.ceil(len(rendered)/2.5)
            if len(rendered)>limit or estimate>4200: errors.append('oversized model input: '+group['id'])
        except (OSError,AssertionError,ValueError) as exc: errors.append(str(exc))
    return errors


def benchmark_errors(report, candidate):
    errors=[]
    finite=lambda v:isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
    if report.get('passed') is not True: errors.append('benchmark execution did not pass')
    if any(not finite(report.get(k)) for k in ('render_scale','frame_cap','cycles','active_seconds','idle_seconds','active_duty_fraction')):errors.append('invalid benchmark scalar')
    if report.get('candidate_commit')!=candidate or report.get('task_id')!='T10': errors.append('benchmark source mismatch')
    version=report.get('engine_version',{})
    expected_version=dict(major=4,minor=7,patch=2,status='stable',build='official',hash='ed1daf0bf001b61586d9930840f2f1394092c079')
    if not isinstance(version,dict) or any(type(version.get(k)) is not type(v) or version.get(k)!=v for k,v in expected_version.items()): errors.append('benchmark structured engine identity mismatch')
    if report.get('engine')!='4.7.2-stable (official)' or version.get('string')!=report.get('engine') or not re.fullmatch(r'mobile/llvmpipe(?: \(.+\))?',str(report.get('renderer',''))) or report.get('resolution')!=[3840,2160] or report.get('render_scale')!=1: errors.append('benchmark environment mismatch')
    if report.get('physical_certification') is not False or report.get('measurement_io') is not False or report.get('fixed_fps') is not False or report.get('frame_cap')!=60: errors.append('benchmark method mismatch')
    if report.get('cpu_frame_ms') is not None or report.get('gpu_frame_ms_where_measurable') is not None: errors.append('physical timing claim forbidden')
    phases=report.get('phases',[])
    if report.get('cycles')!=3 or len(phases)!=9 or [(x.get('cycle'),x.get('state')) for x in phases]!=[(c,s) for c in range(3) for s in ('hidden','frozen','pulse')]: errors.append('benchmark repeated phases missing')
    try:
        identity=phases[0]['identity_before']
        assert identity['descriptor']['lifecycle']=='committing'
        assert all(identity.get(k) for k in ('view_id','ring_mesh','ghost_mesh','ring_material','ghost_material','label_text','camera_transform','camera_size'))
        for phase in phases:
            assert phase['identity_before']==phase['identity_after']==identity
            assert phase['view_visible'] is (phase['state']!='hidden') and phase['pulse_enabled'] is (phase['state']=='pulse')
            scalars=('cycle','warmup_frames','samples','elapsed_seconds','node_min','node_max','visual_build_count','visual_node_count','visual_apply_delta')
            assert all(finite(phase.get(k)) for k in scalars)
            assert phase['warmup_frames']>=120 and phase['samples']>=360 and phase['elapsed_seconds']>0
            motion=phase['raw_pulse_samples'];base=phase['base_scale']
            assert len(motion)==phase['samples'] and len(base)==3 and all(finite(v) and v>0 for v in base)
            revision=identity['descriptor']['target_revision']
            assert base==[1.0,min(1.35,1.0+0.25*max(0,revision-1)),1.0]
            for sample in motion:
                t=sample['time'];scale=sample['scale'];y=sample['y']
                assert finite(t) and 0<=t<10 and len(scale)==3 and all(finite(v) for v in scale) and finite(y)
                pulse=1+math.sin(t*math.tau*1.4)*.18
                assert all(math.isclose(v,b*pulse,rel_tol=1e-5,abs_tol=1e-5) for v,b in zip(scale,base))
                assert math.isclose(y,.08+.75*scale[1],rel_tol=1e-5,abs_tol=1e-5)
                if phase['state']!='pulse':assert t==0 and all(math.isclose(v,b,abs_tol=1e-5) for v,b in zip(scale,base))
            if phase['state']=='pulse':
                assert len({s['time'] for s in motion})>100
                assert max(s['scale'][0] for s in motion)-min(s['scale'][0] for s in motion)>.2

            for metric,raw in [('frame_interval_ms','raw_frame_interval_ms'),('process_proxy_ms','raw_process_proxy_ms')]:
                values=phase[raw];stats=phase[metric];count=len(values)
                assert finite(stats['count']) and count==phase['samples']==stats['count']
                assert all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 for v in values) and max(values)>0
                ordered=sorted(values);half=count//2
                expected={'mean':sum(values)/count,'p95':ordered[math.ceil(count*.95)-1],'p99':ordered[math.ceil(count*.99)-1],'max':max(values),'first_half_mean':sum(values[:half])/half,'last_half_mean':sum(values[half:])/half,'half_drift':(sum(values[half:])-sum(values[:half]))/half}
                assert all(finite(stats[k]) and math.isclose(stats[k],v,rel_tol=1e-5,abs_tol=1e-4) for k,v in expected.items())
            assert math.isclose(phase['elapsed_seconds'],sum(phase['raw_frame_interval_ms'])/1000,rel_tol=1e-5,abs_tol=1e-4)
            for k in ('rss_start_mb','rss_end_mb','rss_endpoint_peak_mb','static_start_mb','static_end_mb','static_peak_mb','draw_min','draw_max','primitive_min','primitive_max','texture_min_mb','texture_max_mb'):
                assert finite(phase[k]) and phase[k]>0
            assert phase['node_min']==phase['node_max'] and phase['visual_build_count']==1 and phase['visual_node_count']==4 and phase['visual_apply_delta']==0
            assert phase['draw_min']==phase['draw_max'] and phase['primitive_min']==phase['primitive_max'] and phase['texture_min_mb']==phase['texture_max_mb']
            assert phase['static_peak_mb']>=max(phase['static_start_mb'],phase['static_end_mb'])
            assert math.isclose(phase['rss_endpoint_peak_mb'],max(phase['rss_start_mb'],phase['rss_end_mb']),rel_tol=1e-5,abs_tol=1e-4)
            # Sampling needs bounded allocator overhead; review still judges all drift.
            assert phase['static_peak_mb']-phase['static_start_mb']<16 and phase['rss_end_mb']-phase['rss_start_mb']<32
        assert len(report['active_minus_idle'])==3
        for cycle in range(3):
            hidden,idle,active=phases[cycle*3:cycle*3+3];delta=report['active_minus_idle'][cycle]
            assert finite(delta['cycle']) and delta['cycle']==cycle
            for key,metric in [('frame_mean_ms','frame_interval_ms'),('process_mean_ms','process_proxy_ms')]:
                assert finite(delta[key]) and math.isclose(delta[key],active[metric]['mean']-idle[metric]['mean'],rel_tol=1e-5,abs_tol=1e-4)
            for key,metric in [('presentation_frame_mean_ms','frame_interval_ms'),('presentation_process_mean_ms','process_proxy_ms')]:
                assert finite(delta[key]) and math.isclose(delta[key],idle[metric]['mean']-hidden[metric]['mean'],rel_tol=1e-5,abs_tol=1e-4)
            for key in ('draw_min','primitive_min','texture_min_mb'):
                assert idle[key]==active[key]
        update=report['isolated_update']
        assert type(update['batches']) is int and update['batches']>=20 and type(update['calls_per_batch']) is int and update['calls_per_batch']>=100
        for name in ('gross','empty'):
            values=update['raw_'+name+'_usec_per_call'];stats=update[name+'_usec_per_call'];n=len(values);half=n//2
            assert n==update['batches']==stats['count'] and n%2==0 and all(finite(v) and v>=0 for v in values)
            if name=='gross':assert max(values)>0
            ordered=sorted(values)
            expected={'mean':sum(values)/n,'p95':ordered[math.ceil(n*.95)-1],'p99':ordered[math.ceil(n*.99)-1],'max':max(values),'first_half_mean':sum(values[:half])/half,'last_half_mean':sum(values[half:])/half,'half_drift':(sum(values[half:])-sum(values[:half]))/half}
            assert all(finite(stats[k]) and math.isclose(stats[k],v,rel_tol=1e-5,abs_tol=1e-4) for k,v in expected.items())
        active=sum(p['elapsed_seconds'] for p in phases if p['state']=='pulse');idle=sum(p['elapsed_seconds'] for p in phases if p['state']=='frozen')
        assert math.isclose(report['active_seconds'],active,rel_tol=1e-5) and math.isclose(report['idle_seconds'],idle,rel_tol=1e-5)
        assert math.isclose(report['active_duty_fraction'],active/(active+idle),rel_tol=1e-5)
        assert phases[-1]['rss_end_mb']-phases[0]['rss_start_mb']<32
    except (KeyError,TypeError,AssertionError,ValueError,ZeroDivisionError): errors.append('invalid or unstable benchmark samples/statistics')
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--evidence-root', required=True)
    a = ap.parse_args()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == a.candidate
    src = ROOT / a.evidence_root
    out = ROOT / 'critic-input'
    if out.exists():
        raise SystemExit('critic-input exists; use a fresh evidence workspace')
    shutil.copytree(src, out)
    reports = {}
    for name in ('domain-tests.json', 'integration-tests.json', 'progression.json'):
        report = json.loads((out / name).read_text())
        assert report.get('candidate', report.get('candidate_commit')) == a.candidate, name
        assert report.get('passed') is True, name
        reports[name] = report
    capture = json.loads((out / 'native4k/manifest.json').read_text())
    assert capture['candidate'] == a.candidate and capture['exact_replay_verified']
    perf = capture['performance_peaks']
    assert perf['visible_triangles'] > 0 and perf['draw_calls'] > 0 and perf['process_memory_mb'] > 0
    files = subprocess.check_output(['git', 'ls-files', 'HavenlineGodot'], cwd=ROOT, text=True).splitlines()
    perf['storage_download_mb'] = sum((ROOT / p).stat().st_size for p in files) / 1048576
    perf.update(scene_state='maximum measured across six lifecycle states and six native4K cameras', resolution=capture['capture_resolution'], renderer=capture['renderer'], render_scale=capture['render_scale'], triangles_or_primitives=perf['visible_triangles'], materials={'conservative_upper_bound':perf['materials_visible'],'method':'submitted draw calls bound distinct visible materials, including internal font passes'}, texture_memory_if_measurable=perf['texture_gpu_memory_mb'], cpu_frame_time_if_measurable=None, gpu_frame_time_if_measurable=None, physics_body_count=perf['physics_active_bodies'], animation_count=perf['animated_rigs_active'], population_count=perf['npc_companion_active_population'], process_memory_if_measurable=perf['process_memory_mb'], storage_delta={'tracked_project_mb':perf['storage_download_mb'],'method':'uncompressed tracked project bytes; not a shipping APK estimate'}, measurement_method='Godot rendering/physics monitors at post-draw; ps RSS for exact Godot PID; max across native4K captures; known empty neutral fixture rig/population topology', known_unmeasured_fields={'cpu_frame_time':'capture includes screenshot/file IO; no representative full-game steady-state frame measurement','gpu_frame_time':'software Vulkan capture is not physical GPU timing','physical_certification':'T68/T69 only'})
    perf.update(candidate_commit=a.candidate, scope=capture['performance_scope'], source_manifest_sha256=digest(out / 'native4k/manifest.json'), physical_certification=False)
    (out / 'performance.json').write_text(json.dumps(perf, indent=2) + '\n')
    benchmark=json.loads((out/'benchmark/manifest.json').read_text())
    assert not benchmark_errors(benchmark,a.candidate),benchmark_errors(benchmark,a.candidate)
    perf['steady_state_benchmark']={'path':'critic-input/benchmark/manifest.json','sha256':digest(out/'benchmark/manifest.json'),'physical_certification':False}
    (out/'performance.json').write_text(json.dumps(perf,indent=2)+'\n')
    baseline=json.loads((out/'capture/manifest.json').read_text())
    probe=json.loads((out/'capture/motion-probe.json').read_text())
    video=next(x for x in probe['streams'] if x['codec_type']=='video')
    segments=baseline['motion_segments']
    errors=motion_errors(capture['states'],segments,video)
    assert not errors,errors
    timeline={'candidate_commit':a.candidate,'fps':30,'frame_count':int(video['nb_frames']),'duration_seconds':float(video['duration']),'video_sha256':digest(out/'capture/lifecycle.mp4'),'segments':segments,'sample_stride_frames':15,'sample_origin_frame':0,'sample_mapping':[{'file':p.name,'frame':i*15,'seconds':i/2,'state':next((x['state'] for x in segments if x['start_frame']<=i*15<x['end_frame']),'transition')} for i,p in enumerate(sorted((out/'capture').glob('motion-*.png')))]}
    (out/'motion-timeline.json').write_text(json.dumps(timeline,indent=2)+'\n')
    saves=json.loads((out/'save-matrix/save-matrix.json').read_text())
    assert saves['candidate_commit']==a.candidate and saves['passed'] and len(saves['cases'])==7
    # These are summaries of preserved raw reports, never substituted scores.
    summary = {'task_id': 'T10', 'candidate': a.candidate, 'scope': 'Neutral transform framework. T11 owns authored camp content and main-loop binding.', 'controls': 'No added action controls. Preview is pure; delivered stored resources alone pay; simulation owns debit; T10 accepts receipt once.', 'reports': {}}
    for name, report in reports.items():
        summary['reports'][name] = {k: v for k, v in report.items() if k not in ('checks', 'source_hashes', 'source_sha256')}
        summary['reports'][name]['raw_sha256'] = digest(out / name)
    (out / 'review-summary.json').write_text(json.dumps(summary, indent=2) + '\n')

    def item(path, category, kind='json', description=''):
        p = ROOT / path
        return dict(path=path, category=category, kind=kind, description=description, sha256=digest(p))

    shutil.copyfile(ROOT/'Docs/Production/T10/FROZEN_SCOPE.md',out/'FROZEN_SCOPE.md')
    shutil.copyfile(ROOT/'HavenlineGodot/data/world_transform_recipes.json',out/'recipes.json')
    full_sources=['FROZEN_SCOPE.md','recipes.json','progression.json','domain-tests.json','integration-tests.json','review-summary.json','motion-timeline.json','save-matrix/save-matrix.json','benchmark/manifest.json','performance.json']
    preserved=[item('critic-input/'+p,'preserved_raw','text' if p.endswith('.md') else 'json') for p in full_sources]
    (out/'scope-brief.txt').write_text(SCOPE_SYNOPSIS)
    context=('Exact source '+a.candidate+'. Executed domain '+str(reports['domain-tests.json']['check_count'])+' and integration '+str(reports['integration-tests.json']['check_count'])+' checks PASS; 7 save cases PASS. Real delivered authority/exact debit/replay verified. Four view nodes, one build, zero repeated-state rebuilds. READY states exact cost; BLOCKED states exact shortfall; COMPLETE states paid cost and next prerequisite.\n'
             +'30fps video '+str(timeline['frame_count'])+' frames: '+','.join(x['state']+' '+str(x['start_frame'])+'-'+str(x['end_frame']) for x in segments)+'. Motion images sampled every15 frames; full video preserved.\n'
             +'Full scope/proofs and hashes: preserved_sources in this source-bound manifest. Neutral fixture deliberately omits T11 camp art and main-loop wiring.\n')
    (out/'visual-brief.txt').write_text(context)
    proof=compact_progression(reports['progression.json'])
    proof+='\nRaw critic-input/progression.json SHA256 '+digest(out/'progression.json')+'\n'
    (out/'progression-brief.txt').write_text(proof)
    save_brief='Seven actual save cases: '+json.dumps([{k:r[k] for k in ('case','passed') if k in r} for r in saves['cases']],separators=(',',':'))+'\nRaw critic-input/save-matrix/save-matrix.json SHA256 '+digest(out/'save-matrix/save-matrix.json')
    (out/'save-brief.txt').write_text(save_brief)
    for cid in ('C3','C4','C7'):
        groups=[]
        if cid=='C7':
            groups=[dict(id='transaction-integrity',items=[item('critic-input/progression-brief.txt','progression_simulation','text'),item('critic-input/recipes.json','transaction_state_graph'),item('critic-input/save-brief.txt','recovery_evidence','text')])]
        else:
            rows=[item('critic-input/visual-brief.txt','control_state' if cid=='C3' else 'feedback_state','text')]
            rows += [item('critic-input/native4k/'+state+'-front.png','gameplay_state','image',state+': neutral real-authority fixture') for state in capture['states']]
            groups.append(dict(id='full-lifecycle',items=rows))
            frames=sorted((out/'capture').glob('motion-*.png'))
            assert len(frames)>=12
            for start in range(0,len(frames),12):
                groups.append(dict(id='motion-'+str(start),items=[item(str(p.relative_to(ROOT)),'loop_evidence' if cid=='C3' else 'feedback_state','motion_frame','30fps video sampled every15 frames; '+timeline['sample_mapping'][i]['state']+' frame '+str(i*15)) for i,p in enumerate(frames) if start<=i<start+12]))
            rows=[]
            for folder in sorted((out/'device-layout').iterdir()):
                if folder.is_dir():
                    rows += [item(str((folder/(state+'-front.png')).relative_to(ROOT)),'control_state' if cid=='C3' else 'feedback_state','image',folder.name+' '+state+'; judge actual pixel aspect ratio') for state in ('blocked','complete')]
            groups.append(dict(id='device-readability',items=rows))
        for group in groups:
            group['items'].append(item('critic-input/scope-brief.txt','task_scope','text'))
            if cid!='C7' and not any(i['path']=='critic-input/visual-brief.txt' for i in group['items']):
                group['items'].append(item('critic-input/visual-brief.txt','control_state' if cid=='C3' else 'feedback_state','text'))
        manifest=dict(schema_version=1,task_id='T10',critic_id=cid,candidate_commit=a.candidate,groups=groups,preserved_sources=preserved,prompt_budget_method='conservative estimate, not tokenizer: 1000 + image2048 + ceil(textchars/2.5) <=4200')
        errors=validate(manifest)+prompt_errors(manifest)
        if errors: raise SystemExit('\n'.join(errors))
        (out/(cid+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    c6manifest=dict(schema_version=1,task_id='T10',critic_id='C6',candidate_commit=a.candidate,groups=[dict(id='measured-performance',items=[item('critic-input/performance.json','quantitative_budgets'),item('critic-input/benchmark/manifest.json','steady_state'),item('critic-input/domain-tests.json','bounded_growth'),item('critic-input/integration-tests.json','bounded_growth')])],preserved_sources=preserved,physical_certification=False)
    (out/'C6-manifest.json').write_text(json.dumps(c6manifest,indent=2)+'\n')
    references=sorted((ROOT/'Docs/Production/T05/ReferenceFrames').glob('*.png'))
    assert references,'locked reference pixels required'
    for cid in ('C1','C2'):
        manifest={'schema_version':1,'task_id':'T10','critic_id':cid,'candidate_commit':a.candidate,'scope':'T10 neutral transaction framework; T11 final authored camp art and main-loop binding excluded; all critic dimensions and thresholds unchanged','groups':[{'id':'references','items':[item(str(p.relative_to(ROOT)),'reference_lock','image') for p in references]},{'id':'lifecycle','items':[item('critic-input/native4k/'+row['file'],'world_response','image') for row in capture['records']]},{'id':'motion','items':[item('critic-input/motion-timeline.json','motion_timeline')]}],'video':{'path':'critic-input/capture/lifecycle.mp4','sha256':digest(out/'capture/lifecycle.mp4')},'device_manifest_sha256':digest(out/'device-layout-evidence.json')}
        (out/(cid+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    index = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out / 'evidence-index.json').write_text(json.dumps({'candidate': a.candidate, 'files': index}, indent=2) + '\n')


if __name__ == '__main__':
    main()
