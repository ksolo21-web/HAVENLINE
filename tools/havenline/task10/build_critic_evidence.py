#!/usr/bin/env python3
"""Package measured T10 evidence for existing independent specialist gates."""
import argparse
import hashlib
import json
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

    for cid in ('C3', 'C4', 'C7'):
        groups = []
        if cid == 'C7':
            rows = [item('critic-input/progression.json', 'progression_simulation'), item('HavenlineGodot/data/world_transform_recipes.json', 'transaction_state_graph', 'json', 'Exact configured recipe graph. Executable graph guards, hostile recovery, ordering and bounds are independently exercised in the source-bound progression proof.'), item('critic-input/review-summary.json', 'recovery_evidence'), item('critic-input/save-matrix/save-matrix.json', 'recovery_evidence')]
            groups.append(dict(id='transaction-integrity', items=rows))
        else:
            rows = [item('critic-input/review-summary.json', 'control_state' if cid == 'C3' else 'feedback_state'), item('critic-input/motion-timeline.json', 'loop_evidence' if cid == 'C3' else 'feedback_state')]
            for state in capture['states']:
                rows.append(item('critic-input/native4k/' + state + '-front.png', 'gameplay_state', 'image', state + ': real-authority neutral framework'))
            groups.append(dict(id='full-lifecycle', items=rows))
            frames = sorted((out / 'capture').glob('motion-*.png'))
            assert len(frames) >= 12, 'continuous lifecycle motion frames missing'
            for start in range(0, len(frames), 12):
                groups.append(dict(id='motion-' + str(start), items=[item(str(p.relative_to(ROOT)), 'loop_evidence' if cid == 'C3' else 'feedback_state', 'motion_frame', 'continuous 2fps sample from preserved 30fps lifecycle video') for p in frames[start:start+12]]))
            rows = []
            for folder in sorted((out / 'device-layout').iterdir()):
                if not folder.is_dir(): continue
                for state in ('blocked', 'complete'):
                    rows.append(item(str((folder / (state + '-front.png')).relative_to(ROOT)), 'control_state' if cid == 'C3' else 'feedback_state', 'image', folder.name + ': use actual pixel dimensions; canonical labels may not equal aspect ratio'))
            groups.append(dict(id='device-readability', items=rows))
        for group in groups:
            group['items'].append(item('Docs/Production/T10/FROZEN_SCOPE.md', 'task_scope', 'text', 'Authoritative bounded T10 scope; no exclusion of mandatory dimensions'))
            if not any(x['path']=='critic-input/review-summary.json' for x in group['items']):
                group['items'].append(item('critic-input/review-summary.json', 'control_state' if cid=='C3' else 'feedback_state', 'json', 'Complete executed functional context for this visual group'))
        manifest = dict(schema_version=1, task_id='T10', critic_id=cid, candidate_commit=a.candidate, groups=groups)
        errors = validate(manifest)
        if errors: raise SystemExit('\n'.join(errors))
        (out / (cid + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    references=sorted((ROOT/'Docs/Production/T05/ReferenceFrames').glob('*.png'))
    assert references,'locked reference pixels required'
    for cid in ('C1','C2'):
        manifest={'schema_version':1,'task_id':'T10','critic_id':cid,'candidate_commit':a.candidate,'scope':'T10 neutral transaction framework; T11 final authored camp art and main-loop binding excluded; all critic dimensions and thresholds unchanged','groups':[{'id':'references','items':[item(str(p.relative_to(ROOT)),'reference_lock','image') for p in references]},{'id':'lifecycle','items':[item('critic-input/native4k/'+row['file'],'world_response','image') for row in capture['records']]},{'id':'motion','items':[item('critic-input/motion-timeline.json','motion_timeline')]}],'video':{'path':'critic-input/capture/lifecycle.mp4','sha256':digest(out/'capture/lifecycle.mp4')},'device_manifest_sha256':digest(out/'device-layout-evidence.json')}
        (out/(cid+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    index = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out / 'evidence-index.json').write_text(json.dumps({'candidate': a.candidate, 'files': index}, indent=2) + '\n')


if __name__ == '__main__':
    main()
