from pathlib import Path
import hashlib,subprocess,sys
p=Path(__file__).resolve().parent
root=p.parent
stage=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
pins={'hvn-l1-paid-turn-fixture-adapter-v1':'a3e65c87e6dfc3f51a8a4c34a9a246e5d583e583c3204c80266f504b4e040099',
'hvn-l1-paid-turn-adapter-independent-v1.EzRwr3':'83bf263d6e6d4c9ae06e5d380354eeadd1168520017f3f70324fa82e6d624966',
'hvn-l1-storage-examiner-two-run-v1':'2d7cf4eea3483ee007e7523751776a3b535516045ee6a1aa13bc0927bc6e672e'}
for n,h in pins.items():
 d=root/n
 assert hashlib.sha256((d/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=d,check=True)
assert not out.is_relative_to(stage)
subprocess.run([sys.executable,str(root/'hvn-l1-paid-turn-fixture-adapter-v1/prepare.py'),str(stage),str(out)],check=True)
original=out.read_text()
s=original
ed=[]
def change(a,b):
 global s
 assert s.count(a)==1,a
 ed.append((a,b));s=s.replace(a,b,1)
# Pre-existing test-only driver functions copied verbatim other than hash observation.
ts=(stage/'tests/test_integrated_opening.gd').read_text()
calls=ts[ts.index('func send_touch'):ts.index('func gate_cross')]
for marker,call in [('game._input(tap)','input_obs("screen_touch",[tap.pressed,tap.index,fixed_obs(tap.position.x),fixed_obs(tap.position.y)])'),
 ('game._input(event)','input_obs("physical_key",[event.physical_keycode,event.pressed])'),
 ('game._input(ev)','input_obs("screen_drag",[ev.index,fixed_obs(ev.position.x),fixed_obs(ev.position.y)])')]:
 assert calls.count(marker)==1
 # Existing tabs before the replacement remain; indent identical to original.
 indent='\t\t' if marker.endswith('(ev)') else '\t'
 calls=calls.replace(marker,call+'\n'+indent+marker)
change('func tick(n:int) -> void:',(p/'observer.gdfrag').read_text()+'\n'+calls+'\nfunc tick(n:int) -> void:')
change('\t\t_turn_observe_owner(carrying)','\t\t_turn_observe_owner(carrying)\n\t\tprefix_observe()')
a='\tcheck(probe_geometry(),"baseline settled paired source/camera")'
change(a,a+'\n\tprefix_observe()')
a='\tcheck(probe_geometry(),"native arrived near edge camera sample")'
change(a,a+'''
	if OS.get_environment(OBS_MODE)=="B":
		var hold:= not prefix_bad and prefix_count==57 and tick_count==1333 and count_mount(2) and failures==0 and _turn_frames.size()==3 and _turn_warnings.size()==1 and not _turn_fault and _turn_author_source()
		for j in range(_turn_frames.size()):
			hold=hold and j<3 and _turn_frames[j]==TURN_EXPECTED.frames[j]
		hold=hold and _turn_warnings.size()==1 and _turn_warnings[0]==TURN_EXPECTED.warnings[0]
		print("PFX_B_STATUS ",JSON.stringify({"admission_prefix":hold,"prefix":prefix_count,"native_tick_end":tick_count,"request_dispatched":false,"reason":"UNPROVEN_EXACT_LIVE_FLIGHT_OR_RECEIVER_VISUAL_DEPTH"}))
		quit(0 if hold else 14)
		return''')
a=next(l for l in s.splitlines() if 'print("TURN_ADMISSION ",' in l)
call=a.split(',_turn_phase_a_context(',1)[1][:-1]
change(a,'\tvar turn_context:Dictionary=_turn_phase_a_context('+call+'\n\tprint("TURN_ADMISSION ",turn_context)'+'''
	var admitted_turns:Array=[]
	for k in [1306,1353]:
		if turn_context.has(k):
			var c:Dictionary=turn_context[k]
			admitted_turns.append({"tick":k,"foot_quantized":vec_obs(c.foot),"original_safe_fraction":c.sphere,"ids":c.observed_obstacle_ids,"oriented_clearance":c.swept_oriented_clearance_m})
	print("PFX_A_STATUS ",JSON.stringify({"end_tick":tick_count,"prefix":prefix_count,"observer_valid":not prefix_bad,"request_dispatched":false,"turn_records":admitted_turns}))''')
# Both A and B must be explicitly opted in by isolated runner. No implicit world mutation.
change('func run() -> void:\n\tgame=GAME.instantiate()','func run() -> void:\n\tif OS.get_environment(OBS_MODE) not in ["A","B"]:\n\t\tquit(13)\n\t\treturn\n\tgame=GAME.instantiate()')
out.write_text(s)
for a,b in reversed(ed):
 assert s.count(b)==1;s=s.replace(b,a,1)
assert s==original
