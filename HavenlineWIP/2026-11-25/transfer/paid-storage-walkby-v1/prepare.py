from pathlib import Path
import sys,hashlib,json,subprocess
import numpy as np
root=Path(__file__).resolve().parent.parent
stage=Path(sys.argv[1]); dest=Path(sys.argv[2])
n=root/'hvn-l1-wood-paid-two-piece-candidate-v1'
r=root/'hvn-l1-wood-storage-near-row-v1'
for p,h in [(n,'2dbde03441fe996bab357c37291ee9cbe229bf7a4fbdaf0885313f90cac2c8f5'),(r,'b8f6061ab8f7b685beda4629ade265407b7bd5e5dfc649b2197a9b902b8767d6')]:
 assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
assert (stage/'tests/paid_two_visual_probe.gd').read_bytes()==(n/'probe.gd').read_bytes()
for f,h in [('previews/integrated_opening.gd','b0b09db8b3634b4308d327cefce463f86d2a71db'),('wood_stock_view.gd','f1a892ccb8b346580537107e1a4fff7dcdf156be')]:
 assert subprocess.check_output(['git','hash-object',stage/f]).decode().strip()==h
ends=json.loads((r/'result.json').read_text())['detached_log_transforms']
def v(x): return 'Vector3('+','.join(map(str,x))+')'
def tr(row):
 b=np.array(row['R_source_to_source_world']).T.tolist()
 return 'Transform3D(Basis('+','.join(map(v,b))+'),'+v(row['t_source_to_source_world'])+')'
old=(n/'probe.gd').read_text()
prefix=old[old.index('func run() -> void:'):old.index('\tcheck(quick_clearance("paid_south_inner_still")')]
new='extends "res://tests/paid_two_visual_probe.gd"\nconst REST := ['+','.join(map(tr,ends))+']\n'+(root/'hvn-l1-paid-storage-walkby-v1/witness.gdfrag').read_text().replace('@OPENING_PREFIX@',prefix)
dest.write_text(new)
