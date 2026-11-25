#!/usr/bin/env python3
import difflib, hashlib, json, subprocess, sys
from pathlib import Path
p='HavenlineLevel1/pad_v5_view.gd'
expected='43f88e9deebb74d5eaf69290ced38681f59a8b36'
base='11c14a1c41971067c7dc97db69375f720a408f68'
def git(*a):
 return subprocess.check_output(['git','-C',sys.argv[1],*a])
a=git('show',base+':'+p)
assert git('rev-parse',base+':'+p).decode().strip()==expected
r=json.loads(Path('result.json').read_text())
new=r['search']['unchanged']
assert r['search']['price_trial_scale_with_3mm_clearance']['witness'] is None and r['search']['price_trial_scale_with_3mm_clearance']['unresolved_tiny_cells']==0
x,z=new['rounded_source_offsets']
assert [x,z]==[.682963,-.362559]
q=b'\t_cost = _new_label("Cost", 0.18, 0.0032)\n'
assert a.count(q)==1
v=(f'\t_cost = _new_label("Cost", {z:.6f}, 0.0032)\n\t_cost.position.x = {x:.6f}\n').encode()
b=a.replace(q,v)
patch=''.join(difflib.unified_diff(a.decode().splitlines(keepends=True), b.decode().splitlines(keepends=True),fromfile='a/'+p,tofile='b/'+p))
print(patch,end='')
