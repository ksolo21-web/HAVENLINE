"""Inspect real GLB payloads and record reproducible import/release evidence."""
import argparse, hashlib, json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'HavenlineGodot'

def inspect(path):
    blob=path.read_bytes()
    assert struct.unpack_from('<III',blob)==(0x46546C67,2,len(blob)),path
    length,kind=struct.unpack_from('<II',blob,12)
    assert kind==0x4E4F534A
    data=json.loads(blob[20:20+length])
    assert not any('uri' in b for b in data.get('buffers',[])), 'External GLB buffer'
    return {'file':str(path.relative_to(PROJECT)), 'sha256':hashlib.sha256(blob).hexdigest(),
        'bytes':len(blob),'vertices':sum(data['accessors'][p['attributes']['POSITION']]['count'] for m in data['meshes'] for p in m['primitives']),
        'mesh_count':len(data['meshes']),'material_count':len(data.get('materials',[])),
        'joint_count':sum(len(s['joints']) for s in data.get('skins',[])),
        'clips':[{'name':a.get('name',''),'duration':max(max(data['accessors'][s['input']].get('max',[0])) for s in a['samplers'])} for a in data.get('animations',[])],
        'visual_approval':'UNTESTED','whole_rig_approval':'UNTESTED'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--release',action='store_true');args=parser.parse_args()
    manifest=json.loads((PROJECT/'data/asset-manifest.json').read_text())
    assets=[inspect(p) for p in sorted((PROJECT/'assets').rglob('*.glb'))]
    by_path={a['file']:a for a in assets}
    failures=[]
    for item in manifest['characters']:
        asset=by_path.get(item['file'])
        if not asset or asset['sha256']!=item['sha256']:failures.append('Character changed: '+item['file'])
    required=json.loads((PROJECT/'data/release-status.json').read_text())['required']
    blocked={k:v for k,v in required.items() if v!='PASS'}
    report={'schema':1,'asset_integrity_passed':not failures,'assets':assets,'failures':failures,'production_release_passed':not failures and not blocked,'release_blockers':blocked}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'asset_integrity_passed':not failures,'asset_count':len(assets),'production_release_passed':report['production_release_passed'],'release_blockers':blocked}))
    return 1 if failures or (args.release and blocked) else 0

if __name__=='__main__':raise SystemExit(main())
