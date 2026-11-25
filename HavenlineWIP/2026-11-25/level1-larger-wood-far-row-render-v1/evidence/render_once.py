"""One bounded correction; inherit exact canonical intake renderer read-only."""
import hashlib,json,sys
from pathlib import Path
root=Path.cwd()
old=root/'hvn-l1-wood-receiver-render-intake-v1'/'render_granted.py'
gate=root/'hvn-l1-wood-receiver-silhouette-gate-v1'/'result.json'
H=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
assert H(old)=='3c2b4501221954c85efc3de23419bb1baea1d64881446726c06069ec806abedb'
assert H(gate)=='6911158faee993d0c242bbfd51311d5eaffd52cc2b88e845b1203234ac7128cd'
s=old.read_text()
edits={
"for i,t in enumerate(spec['one_near_row_two_anchor_offsets_local']):":"for i,t in enumerate(far_seats):",
"for name,hide in [('empty',True),('two-settled',False)]:":"for name,hide in [('two-settled-far',False)]:",
"['empty.png','two-settled.png']":"['two-settled-far.png']",
}
for reference,new in edits.items():
 assert s.count(reference)==1
 s=s.replace(reference,new)
far_seats=json.loads(gate.read_bytes())['candidate_anchor_offsets_normalized']
assert len(far_seats)==2 and all(t[2]<0 for t in far_seats)
exec(compile(s,str(old),'exec'),{'__file__':str(old),'__name__':'__main__','far_seats':far_seats})
