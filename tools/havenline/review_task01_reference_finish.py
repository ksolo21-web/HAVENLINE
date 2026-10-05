#!/usr/bin/env python3
"""Same reference/integrity rubric; new tree source and resolution-aware crops.
No previous score, desired numeric result or expected defect is sent to inference.
"""
from pathlib import Path
import hashlib,os
p=Path('tools/havenline/review_task01_second_family.py');raw=p.read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='c9216e4fd93caa1b9ef52fbd25af652dee1da033'
s=raw.decode();source=os.environ['TASK_SOURCE']
assert len(source)==40 and all(c in '0123456789abcdef' for c in source)
old="SOURCE='41f5446b2ecc4e29ad63ae814ad8491cc2763674'";assert s.count(old)==1
s=s.replace(old,'SOURCE='+repr(source))
assert s.count("pro['revision']==6")==1;s=s.replace("pro['revision']==6","pro['revision']==7")
old=" if isinstance(n,ast.FunctionDef) and n.name=='board':exec(compile(ast.Module(body=[n],type_ignores=[]),'preserved-board-helper','exec'),globals())"
assert s.count(old)==1
new=""" if isinstance(n,ast.FunctionDef) and n.name=='board':
  helper=ast.get_source_segment(raw.decode(),n)
  needle='if crop:image=image.crop(crop)';assert helper.count(needle)==1
  helper=helper.replace(needle,'if crop:\\n   crop=tuple(round(v*(image.width/1280 if j%2==0 else image.height/720)) for j,v in enumerate(crop))\\n   image=image.crop(crop)')
  exec(compile(helper,'resolution-aware-source-crops','exec'),globals())"""
s=s.replace(old,new)
out=Path('critic-results');out.mkdir(exist_ok=True)
(out/'executed-reviewer.py').write_text(s)
(out/'reviewer-wrapper.txt').write_text('New source and resolution-aware coordinates only; independent rubric, score threshold, model, and raw output preserved. Full original 4K clearance PNGs retained.\n')
exec(compile(s,'T01-new-reference-finish-review','exec'),{'__name__':'__main__','__file__':str(out/'executed-reviewer.py')})
