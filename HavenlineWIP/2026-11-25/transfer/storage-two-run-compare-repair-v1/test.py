from pathlib import Path
import hashlib,json,runpy,subprocess,sys
here=Path(__file__).resolve().parent
root=here.parent
pins={
'hvn-l1-storage-two-run-admission-native-v1':'96239426d0de1d747f531b43e11eeb1568801127ab3ff03ac167fd1229e24689',
'hvn-l1-storage-two-run-admission-result-v1':'a2a143c6c1884cd4e948518668ae9080c1bc26a9672f90dda1b7616ba4ed8d4f',
'hvn-l1-storage-two-run-admission-independent-v1.9ICoRc':'71ce6f15d1ee4f18f1372e4ef5fdf3fabc24d462fe7d6586c8e74c54485d7730'}
for name,digest in pins.items():
 d=root/name
 assert hashlib.sha256((d/'SHA256SUMS').read_bytes()).hexdigest()==digest
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=d,check=True)
original=root/'hvn-l1-storage-two-run-admission-native-v1/compare.py'
old=runpy.run_path(str(original))
new=runpy.run_path(str(here/'compare.py'))
d=root/'hvn-l1-storage-two-run-admission-result-v1'
a,b=[(d/n).read_text() for n in ['A.log','B.log']]
w1,w2=old['rows'](a,'WALK_OBSTRUCTION')
swap=lambda s,u,v:s.replace('WALK_OBSTRUCTION '+u,'WALK_OBSTRUCTION '+v,1)
assert new['phases'](a,b)==old['phases'](a,b)==json.loads((d/'result.json').read_text())
attack=swap(b,w1,w2)
assert old['phases'](a,attack)==old['phases'](a,b)
assert old['rows'](b,'PFX_OBS')==old['rows'](attack,'PFX_OBS')
cases={
 'independent_genuine_A_later_warning_in_B':(a,attack),
 'B_right_tick_wrong_motion_phase':(a,swap(b,w1,w1.replace('near_edge_approach','return_south'))),
 'B_right_tick_wrong_safe_fraction':(a,swap(b,w1,w1.replace('0.755859375','0.755859374'))),
 'B_right_tick_wrong_exact_origin':(a,swap(b,w1,w1.replace('-4.90033340454102','-4.90033340454103'))),
 'B_reformatted_lookalike':(a,swap(b,w1,json.dumps(json.loads(w1),sort_keys=True))),
 'A_warning_order_swapped':(swap(swap(swap(a,w1,'temporary'),w2,w1),'temporary',w2),b),
 'A_and_B_colluding_first_warning_changes':(swap(a,w1,w1.replace('true','false')),swap(b,w1,w1.replace('true','false'))),
 'A_first_shape_claim_swapped':(a.replace(new['EXPECTED_SHAPES'][0],new['EXPECTED_SHAPES'][1],1),b),
 'A_shape_index_wrong':(a.replace(new['EXPECTED_SHAPES'][0],new['EXPECTED_SHAPES'][0][:-1]+'1',1),b),
}
results={'exact_existing_pair_output_unchanged':True,'independent_attack_reproduced_against_original':True}
for name,(al,bl) in cases.items():
 try:new['phases'](al,bl)
 except ValueError as e: results[name]='HOLD: '+str(e)
 else: raise AssertionError(name)
print(json.dumps(results,sort_keys=True,indent=2))
