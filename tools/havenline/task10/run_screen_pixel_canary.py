#!/usr/bin/env python3
"""Bounded local raster canary; never product approval or physical certification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
import verify_screen_pixel_clearance as verifier

PROFILES=('phone_16_9__0.85','phone_16_9__1.0','phone_16_9__1.35','native4k_full','foldable_inner__1.35')
FULL_PROFILES=tuple(f'{device}__{scale}' for device in verifier.DEVICES for scale in (1.0,0.85,1.35))+('native4k_full',)
ENGINE_ARCHIVE_SHA512='9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65'
FILES=('HavenlineGodot/scripts/world_transform_view.gd','HavenlineGodot/tests/capture_task10_world_transform.gd','tools/havenline/task10/verify_screen_pixel_clearance.py','tools/havenline/task10/run_screen_pixel_canary.py','HavenlineGodot/assets/world_transform_v1/resource_symbols.tres')

def bound_files(repo,source):
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()!=source:
        raise ValueError('canary source is not checked-out HEAD')
    hashes={}
    for name in FILES:
        original=subprocess.check_output(['git','show',f'{source}:{name}'],cwd=repo)
        actual=(repo/name).read_bytes()
        if actual!=original:raise ValueError('unfrozen canary input '+name)
        hashes[name]=hashlib.sha256(actual).hexdigest()
    return hashes

def run(args):
    repo=args.repo.resolve();output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    hashes=bound_files(repo,args.source)
    profiles=FULL_PROFILES if args.domain=='full684' else PROFILES
    expected_cases=684 if args.domain=='full684' else 180
    if hashlib.sha512(args.engine_archive.read_bytes()).hexdigest()!=ENGINE_ARCHIVE_SHA512:
        raise ValueError('wrong pinned engine archive')
    with zipfile.ZipFile(args.engine_archive) as archive:
        engine_bytes=archive.read('Godot_v4.7.2-stable_linux.x86_64')
    if args.engine.read_bytes()!=engine_bytes:raise ValueError('engine differs from pinned archive')
    env=dict(os.environ)
    env['LD_LIBRARY_PATH']=str(args.library_path)+':'+env.get('LD_LIBRARY_PATH','')
    env['VK_ICD_FILENAMES']=str(args.vulkan_icd.resolve())
    env['PATH']=str(args.xvfb.parent)+':'+env['PATH']
    display=next(i for i in range(191,221) if not Path(f'/tmp/.X{i}-lock').exists())
    env['DISPLAY']=f':{display}'
    xvfb_cmd=[str(args.xvfb),env['DISPLAY'],'-screen','0','3840x2160x24','-nolisten','tcp']
    metadata={'source':args.source,'input_hashes':hashes,'profiles':list(profiles),'expected_cases':expected_cases,'domain':args.domain,'engine_sha256':hashlib.sha256(engine_bytes).hexdigest(),'engine_archive_sha512':ENGINE_ARCHIVE_SHA512,'xvfb_sha256':verifier.sha256(args.xvfb),'vulkan_icd':json.loads(args.vulkan_icd.read_text()),'xvfb_command':xvfb_cmd,'execution_kind':args.execution_kind,'physical_certification':False,'task_approved':False}
    (output/'execution.json').write_text(json.dumps(metadata,indent=2))
    summaries=[]
    with (output/'xvfb.log').open('w') as log:
        server=subprocess.Popen(xvfb_cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
        try:
            for _ in range(200):
                if server.poll() is not None:raise RuntimeError('Xvfb exited; see retained log')
                if Path(f'/tmp/.X11-unix/X{display}').exists():break
                time.sleep(.1)
            else:raise RuntimeError('Xvfb did not create display')
            for profile in profiles:
                if bound_files(repo,args.source)!=hashes:raise ValueError('canary changed during execution')
                logical,physical,scale=verifier.PROFILES[profile]
                folder=output/profile;folder.mkdir()
                command=[str(args.engine),'--path',str(repo/'HavenlineGodot'),'--rendering-method','mobile','--rendering-driver','vulkan','--audio-driver','Dummy','--resolution',f'{physical[0]}x{physical[1]}','--script','res://tests/capture_task10_world_transform.gd','--',f'--candidate={args.source}',f'--domain-profile={profile}',f'--device-id={profile}',f'--width={physical[0]}',f'--height={physical[1]}',f'--logical-width={logical[0]}',f'--logical-height={logical[1]}',f'--readability-scale={scale}',f'--out={folder}',f'--product-view-sha256={hashes[FILES[0]]}',f'--probe-source={args.source}',f'--probe-capture-sha256={hashes[FILES[1]]}',f'--probe-verifier-sha256={hashes[FILES[2]]}',f'--probe-workflow-sha256={hashes[FILES[3]]}']
                (folder/'command.json').write_text(json.dumps(command,indent=2))
                try:
                    with (folder/'capture.log').open('w') as capture_log:
                        result=subprocess.run(command,stdout=capture_log,stderr=subprocess.STDOUT,env=env,timeout=480)
                    status=result.returncode
                except subprocess.TimeoutExpired:status=124
                (folder/'capture-exit.txt').write_text(str(status)+'\n')
                row={'profile':profile,'capture_exit':status,'passed':False}
                try:
                    report=verifier.verify(folder,folder/'manifest.json',folder/'masks',args.source,hashes[FILES[0]],'candidate',args.source,hashes[FILES[1]],hashes[FILES[2]],hashes[FILES[3]],hashes[FILES[4]],profile)
                    (folder/'report.json').write_text(json.dumps(report,indent=2))
                    row.update(case_count=len(report['rows']),failure_count=report['failure_count'],passed=status==0 and report['passed'],report_sha256=verifier.sha256(folder/'report.json'))
                    capture_text=(folder/'capture.log').read_text(errors='replace')
                    if any(x in capture_text for x in ('SCRIPT ERROR','Parse Error','ObjectDB instances were leaked')):row.update(passed=False,error='engine_error_in_log')
                except Exception as exc:row['error']=f'{type(exc).__name__}: {exc}'
                summaries.append(row)
                (output/'progress.json').write_text(json.dumps(summaries,indent=2))
                print(json.dumps(row),flush=True)
        finally:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()
    if bound_files(repo,args.source)!=hashes:raise ValueError('canary changed during execution')
    result={'source':args.source,'domain':args.domain,'expected_cases':expected_cases,'domain_complete':args.domain=='full684' and sum(x.get('case_count',0) for x in summaries)==684,'profiles':summaries,'case_count':sum(x.get('case_count',0) for x in summaries),'passed':len(summaries)==len(profiles) and all(x['passed'] for x in summaries) and sum(x.get('case_count',0) for x in summaries)==expected_cases,'task_approved':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--output',type=Path,required=True)
    p.add_argument('--domain',choices=['canary180','full684'],default='canary180')
    p.add_argument('--execution-kind',choices=['LOCAL_BOUNDED_RASTER_CANARY','HOSTED_BOUNDED_RASTER_CANARY','HOSTED_FULL_RASTER_PROOF'],default='LOCAL_BOUNDED_RASTER_CANARY')
    p.add_argument('--source',required=True);p.add_argument('--engine',type=Path,required=True)
    p.add_argument('--engine-archive',type=Path,required=True);p.add_argument('--xvfb',type=Path,required=True)
    p.add_argument('--library-path',type=Path,required=True);p.add_argument('--vulkan-icd',type=Path,required=True)
    result=run(p.parse_args());print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
