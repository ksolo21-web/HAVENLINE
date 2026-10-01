"""Capture the current R01 through unchanged shipping main.gd and its QA modes.
This is isolated-branch evidence; it does not mean the candidate was integrated.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from PIL import Image
from verify_r01_v4_scope import verify

ROOT=Path(__file__).resolve().parents[3]
PROFILES=[
 ('phone-opening',2400,1080,'opening','front'),
 ('tablet-opening',2560,1600,'opening','front'),
 ('firebox-front',1920,1080,'furnace-detail','rear'),
 ('furnace-rear',1920,1080,'furnace-detail','front'),
 ('night',1920,1080,'night','front'),
 ('blizzard',1920,1080,'blizzard','front'),
 ('warmth4',1920,1080,'warmth4','front'),
]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run(engine,source,out):
    proof=verify(source);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    main_hash=digest(ROOT/'HavenlineGodot/scripts/main.gd')
    for name,width,height,scenario,view in PROFILES:
        dest=out/name;dest.mkdir(exist_ok=True)
        command=['xvfb-run','-a','-s',f'-screen 0 {width}x{height}x24',engine,
                 '--path',str(ROOT/'HavenlineGodot'),'--rendering-method','mobile',
                 '--rendering-driver','vulkan','--audio-driver','Dummy','--resolution',f'{width}x{height}',
                 '--','--capture='+str(dest),'--scenario='+scenario,'--view='+view]
        print('Capturing shipping call site:',name,flush=True)
        with (dest/'capture.log').open('w') as log:
            subprocess.run(command,cwd=ROOT,check=True,timeout=240,stdout=log,stderr=subprocess.STDOUT)
        log=(dest/'capture.log').read_text()
        assert not any(marker in log for marker in ('SCRIPT ERROR','Parse Error','ERROR:')),name
        report=json.loads((dest/'render-evidence.json').read_text())
        assert report['renderer']=='mobile' and report['render_scale']==1.0,name
        assert report['capture_scenario']==scenario and report['capture_view']==view,name
        assert report['scene_script_sha256']==main_hash,name
        assert report['render_review'] is False,name
        assert report['task05_station_kit']['authority_id']=='T05-station-kit-v1',name
        assert report['task05_station_kit']['camp']['total_catalog_triangles']==49160,name
        images={}
        for filename in ('native-scene.png','gameplay.png'):
            path=dest/filename
            with Image.open(path) as image:size=list(image.size)
            if filename=='native-scene.png':
                assert size==report['internal_render'] and size[0]>=3840 and size[1]>=2160,(name,size)
            else:assert size==[width,height],(name,size)
            images[filename]={'sha256':digest(path),'size':size}
        rows.append({'name':name,'scenario':scenario,'qa_view':view,'shipping_main_call_site_exercised':True,
                     'qa_camera_override':scenario=='furnace-detail' or view!='front',
                     'report_sha256':digest(dest/'render-evidence.json'),'images':images})
    assert len(rows)==7
    result={'schema_version':1,'task':'T05','subtask':'R01-V4','source':source,'model_sha256':proof['model_sha256'],
            'shipping_main_sha256':main_hash,'profiles':rows,'passed':True,'source_bound':True,
            'shipping_main_call_site_exercised':True,'integrated_into_canonical_branch':False,
            'stage_kind':'actual-main-scene-with-disclosed-QA-fixtures',
            'critics_executed':False,'task_approved':False,'physical_4k60_verified':False}
    (out/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='profiles'},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();run(a.engine,a.source,Path(a.out).resolve())
