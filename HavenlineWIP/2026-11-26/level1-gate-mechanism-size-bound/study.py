from pathlib import Path
from hashlib import sha256
import json,math
P=Path(__file__).resolve().parent
H=P.parent
def sha(p):return sha256(p.read_bytes()).hexdigest()
sheet=H/'hvn-owner-fence-33036-33035/33040.png'
assert sha(sheet)=='7e86d259cf4cf67d3a795ab0bb150d8ce67af7a03a23c240a8dd0e0cec137bdd'
v=H/'hvn-l1-owner-gate-33035-v4-native-preflight-v1'
o=v/'staged/HavenlineLevel1/previews/clearance_gate/owner_assets'
M=json.loads((H/'hvn-l1-owner-gate-33035-charcoal-latch-paid-v1/graphics-evidence.SC6mjnAN/paid-only-falsifier.json').read_text())['same_roi_evidence']
assert M['v4_paid_frame_hash']==sha(v/'graphics-evidence.cklm7tMU/paid-first-frame.png')
names=['front_handle_rosette','front_handle_owned_bar','front_receiver_keeper']
def parts(folder):
 groups={}
 for s,fn in [(1,'GateLeaf.obj'),(-1,'GateLeaf_Right.obj')]:
  group=None
  for ln in (folder/fn).read_text().splitlines():
   if ln.startswith('g '): group=ln[2:]
   elif ln.startswith('v ') and group in names:
    x,y,z=map(float,ln.split()[1:])
    groups.setdefault(group,[]).append(((x if s>0 else 2.4+x),y,z))
 return groups
earlier=parts(H/'hvn-l1-gate-owner-separated-master-v2/candidate')
v3=parts(H/'hvn-l1-owner-gate-33035-snow-hardware-v3/candidate')
v4=parts(o)
assert v3==v4
def extent(a,i):return max(p[i] for p in a)-min(p[i] for p in a)
bounds={}
for label,g in [('v2',earlier),('v3_and_v4',v4)]:
 all_pts=[p for r in g.values() for p in r]
 bounds[label]={'assembly_m':extent(all_pts,0),'bar_height_m':extent(g[names[1]],1),'bar_width_m':extent(g[names[1]],0),
  'keeper_center_size_y_m':extent(g[names[2]],1),'rosette_size_y_m':extent(g[names[0]],1)}
dims=bounds['v3_and_v4']; f=720/13; a=dims['assembly_m']
# Manually marked owner full front bounds; use +/- 2 pixel uncertain edges rather than exact ratios.
# Both moving leaves span x116..532; plate to plate x307..348. Closeup marked x1034..1172;
# connector bright silhouette top/bottom y882..901.  Bounds span computed with doubled tolerance.
d={'sheet_full_hardware_to_leaf_span_ratio_range':[(41-4)/(416+4),(41+4)/(416-4)],
 'sheet_closeup_bar_height_to_mechanism_span_ratio_range':[(19-4)/(138+4),(19+4)/(138-4)],
 'v4_assembly_to_leaf_span_ratio':a/2.4,'v4_bar_height_over_assembly_span':dims['bar_height_m']/a}
assert d['v4_assembly_to_leaf_span_ratio']>d['sheet_full_hardware_to_leaf_span_ratio_range'][1]
lo,hi=d['sheet_closeup_bar_height_to_mechanism_span_ratio_range']
assert lo<d['v4_bar_height_over_assembly_span']<hi
perp_y=f*math.sqrt(1-(11*11)/291)
p={}
for gate,pct in [('gate-south',11/math.sqrt(170)),('gate-east',7/math.sqrt(170))]:
 lateral=f*pct
 roi=M['groups_at_each_gate'][gate]
 p[gate]={'assembly_screen_perp_to_vertical_width_px':a*lateral,'additional_2px_width_needs_m':2/lateral,
  'new_assembly_fraction_if_plus_2px':(a+2/lateral)/2.4,
  'additional_2px_vertical_lever_bulk_needs_m_min':2/perp_y,
  'lever_max_ratio_if_plus_2px_y':(dims['bar_height_m']+2/perp_y)/a,
  'actual_paid_projected_v4_groups_px':{k:{'count':w['pixels'],'box':w['pixel_bounds_xyxy']} for k,w in roi.items()}}
print(json.dumps({'decision':'HOLD / do not author another mechanism','reference_hash':sha(sheet),'exact_v4_frame_sha256':M['v4_paid_frame_hash'],
 'reference_dimensions':d,'geometry_m':bounds,'projected':p,'pixels_are_projected_roi_not_segmentation':True},indent=2))
