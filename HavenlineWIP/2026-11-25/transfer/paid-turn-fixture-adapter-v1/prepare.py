from pathlib import Path
import hashlib,json,subprocess,sys
here=Path(__file__).resolve().parent
root=here.parent
stage=Path(sys.argv[1]); out=Path(sys.argv[2])
pins={
'hvn-l1-storage-optin-e2e-scaffold-v1':'a40f0f20e4a2112a59970f9dcd111a07a6c28efc34c6638a0435ec1c630d71ee',
'hvn-l1-paid-turn-precision-independent-v1.iFZGWA':'44f8fe399b442b3500ce63ade63cd84863d85931d26f74a774387b461079d4ae',
'hvn-l1-paid-walkby-turn-precision-v1':'d8c52a7404a4690d0cd35e5f4cb1b01c37ff28fb8b30ee68c70190518047e594'}
for name,digest in pins.items():
 d=root/name
 assert hashlib.sha256((d/'SHA256SUMS').read_bytes()).hexdigest()==digest
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=d,check=True)
capture=root/'hvn-l1-paid-walkby-turn-precision-v1'
files={
'resource_tree.gd':'07ba9aad4902e815cdb801cbd79ed7f76eec70ac60eac2318c14646cfb1ffc0f',
'terrain_source.gd':'4c1580f7f6ad946f7fcd23c0d2a74d0e2ccd8644ecff72697bfd80ad7d762394',
'previews/terrain_water_preview.tscn':'cc556af2a5fcb5b47da2f4fb12036fb6fec0d1a80418c3a186cc176f2151ac7a',
'opening.gd':'d1a8d6901a8d52a5c5084f19fe429c376800189c46dbeaea9a4012c7a72c59c1',
'previews/hero_locomotion.gd':'0a3bd14ab66d5384ab0a7915b4cbebfcaa99d582fb41cfc8ed23a8088714d0a4',
'tests/test_integrated_opening.gd':'b5e01fe68711c73e8067332a454050e1ff97877c4f5bf88bbb4846acd6a8477d',
'previews/integrated_opening.tscn':'3c524b99c9142e27196c6846efb9beec3f87a66c67d612eb1689f498ee5004ba',
'project.godot':'6707e0aa5f940a257c1212ed2d3fb678df62c0076448992d954ea26a398f85d5',
'previews/integrated_opening.gd':'910e64ec73038d5c42f3453d1b0787c0b27c4d47a170914431796349fcaec9ec',
'wood_stock_view.gd':'250bfc0449da9b24784d7b00301ab9b107dfccca8cb1dcacdf33868ccbef2643',
'tests/paid_two_visual_probe.gd':'f8f18713dfa62b83ea168b1f7f0f932803a2c08920ef59eba30bafedf4774496',
'assets/studio/starter_ground_wood_lod.glb':'31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554',
'technical_gate.gd':'e3483ca3ff564693280783bdea689a1ebcb2231abd1d2b645180dba7ba3d1ad4',
'layout.json':'e3fc7eb561ae7288d4dc77ffc47b05cac924e8bb2dc2b99ec789a33d430f4458'}
for path,digest in files.items(): assert hashlib.sha256((stage/path).read_bytes()).hexdigest()==digest
subprocess.run([sys.executable,str(capture/'prepare.py'),str(stage),str(out)],check=True)
old=out.read_text()
expected={'frames':[],'warnings':[],'summary':None}
for line in (capture/'native.txt').read_text().splitlines():
 tag,payload=line.split(' ',1)
 if tag=='TURN_DETAIL': expected['frames'].append(payload)
 elif tag=='WALK_OBSTRUCTION': expected['warnings'].append(payload)
 elif tag=='WALK_SUM': expected['summary']=payload
 else: raise ValueError(tag)
assert [json.loads(s)['tick'] for s in expected['frames']]==[1305,1306,1307,1352,1353,1354]
assert [json.loads(s)['tick'] for s in expected['warnings']]==[1306,1353]
assert json.loads(expected['summary'])['failures']==1 and json.loads(expected['summary'])['ticks']==146
s=old
edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a
 edits.append((a,b)); s=s.replace(a,b,1)
edit('func tick(n:int) -> void:',(here/'adapter.gdfrag').read_text().replace('@EXPECTED@',json.dumps(expected)).replace('@FILES@',json.dumps({'res://'+k:v for k,v in files.items()}))+'\nfunc tick(n:int) -> void:')
edit('\tprint("TURN_DETAIL ",JSON.stringify(', '\t_turn_record(_turn_frames,')
edit('"crowns":probes}))','"crowns":probes})')
edit('\t\tvar curr:Array[Transform3D]=[]','\t\t_turn_observe_owner(carrying)\n\t\tvar curr:Array[Transform3D]=[]')
line=next(l for l in s.splitlines() if 'print("WALK_OBSTRUCTION "' in l)
edit(line,line+'\n'+line.replace('print("WALK_OBSTRUCTION ",JSON.stringify(', '_turn_record(_turn_warnings,')[:-1])
line=next(l for l in s.splitlines() if 'print("WALK_SUM "' in l)
payload=line.split('JSON.stringify(',1)[1][:-2]
edit(line,line+'\n\tprint("TURN_ADMISSION ",_turn_phase_a_context('+payload+'))')
out.write_text(s)
for a,b in reversed(edits):
 assert s.count(b)==1,b
 s=s.replace(b,a,1)
assert s==old
(here/'expected.json').write_text(json.dumps(expected,indent=2)+'\n') if '--emit-fixture' in sys.argv[3:] else None
