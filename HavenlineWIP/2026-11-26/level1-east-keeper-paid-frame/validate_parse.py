from pathlib import Path
from hashlib import sha256
import json,re,sys
P=Path(__file__).resolve().parent
D=Path(sys.argv[1]).resolve()
assert D.parent==P and D.name.startswith('parse-evidence.')
files=('owner_mesh.gd','clearance_gate_view.gd','hvn_l1_combined_route.gd','hvn_l1_combined_draw.gd','hvn_l1_paid_east_keeper.gd')
raw=[s.split('\t') for s in (D/'results.tsv').read_text().splitlines()]
assert [(a,Path(b).name) for a,b,_ in raw]==[(a,b) for a in ('failed','proposed') for b in files]
old={Path(s).name:int(rc) for a,s,rc in raw if a=='failed'}
new={Path(s).name:int(rc) for a,s,rc in raw if a=='proposed'}
problems=r'ERROR:|Parse Error|SCRIPT ERROR|Failed to load|Cannot infer'
for s in files:
 q=(D/f'proposed.{s}.log').read_text()
 assert new[s]==0 and 'Godot Engine v4.7.2.stable.official.' in q and not re.search(problems,q,re.I),s
assert old['owner_mesh.gd']==0, 'Independent imported mesh reader must remain parseable.'
assert old['hvn_l1_paid_east_keeper.gd']!=0, 'Original failure did not reproduce under the no-render gate.'
hits={}
for s,lines in [('clearance_gate_view.gd',(59,60,61)),('hvn_l1_combined_draw.gd',(242,243))]:
 log=(D/f'failed.{s}.log').read_text()
 for line in lines:
  if f'{s}:{line})' in log and re.search(problems,log,re.I):
   hits[s]=line
assert hits, 'Direct original compile did not diagnose the candidate-only inferred selector; inspect logs and do not render.'
print(json.dumps({'old_direct_parser_diag':hits,'new_all_five_parse_status':new,'scope':'Compile only; no scene mount/pose/camera or art pass',
    'diagnostic_sha256':{f.name:sha256(f.read_bytes()).hexdigest() for f in sorted(D.glob('*.log'))}},indent=2))
