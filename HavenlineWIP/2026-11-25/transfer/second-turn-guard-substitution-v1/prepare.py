from pathlib import Path
import json,hashlib,subprocess,sys
d=Path(__file__).resolve().parent
base=d.parent
stage,out=Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve()
assert not out.is_relative_to(stage)
pins={'hvn-l1-first-turn-guard-substitution-v1':'214caa0b3bdec527ed3e468d9bef071703c2c5c83b49e317e25776c6d3841fe0',
'hvn-l1-first-turn-guard-native-result-v1':'246c2f698724b32c40949ded91eafd43af493ccdecafbfc2b1c8896cc7392308',
'hvn-l1-near-flight-live-body-observer-v1':'7688c8843dc45af01e8212304615e6652841dbbdd49c8b77cc32aba064334f08'}
# Both second-specific seals are intentionally mandatory.
for line in (d/'second_authority.txt').read_text().splitlines():
 k,h=line.split();assert k not in pins
 pins[k]=h
assert len(pins)==5
for k,h in pins.items():
 q=base/k
 assert hashlib.sha256((q/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=q,check=True)
subprocess.run([sys.executable,str(base/'hvn-l1-first-turn-guard-substitution-v1/prepare.py'),str(stage),str(out)],check=True)
first=out.read_text()
assert hashlib.sha256(first.encode()).hexdigest()=='ba89d88074f274182191f14bcace4e18b7f831cd64ba39d996377897af389c72'
obs=(base/'hvn-l1-near-flight-live-body-observer-v1/native.txt').read_text().splitlines()
raw,=[s.split(' ',1)[1] for s in obs if s.startswith('EXAM_SUPPORT_INPUT ')]
start=raw.index('"plan":[')+len('"plan":[')
dec=json.JSONDecoder()
one,n=dec.raw_decode(raw,start)
assert raw[n]==','
two,end=dec.raw_decode(raw,n+1)
assert raw[end]==']' and one!=two
second_raw=raw[n+1:end]
assert json.loads(second_raw)==json.loads(raw)['plan'][1]
sha=hashlib.sha256(second_raw.encode()).hexdigest()
# Copy only the first distinct certificate's proven support method. Original
# function, invocation, geometry and first certificate remain byte identical.
template=(base/'hvn-l1-first-turn-guard-substitution-v1/support.gdfrag').read_text()
calc=template[template.index('func prove_first_only'):]
assert first.count(calc)==1
sub={
'prove_first_only':'prove_second_only',
'mount.paid_crowns[0]':'mount.paid_crowns[1]',
'or first_mid_certificate_m!=0.':'or second_mid_certificate_m!=0. or first_mid_certificate_m<NEEDLE',
'var p:Dictionary=plans[0]':'var p:Dictionary=plans[1]',
'first_mid_certificate_m=least':'second_mid_certificate_m=least',
'EXAM_FIRST_MID_SUPPORT':'EXAM_SECOND_MID_SUPPORT',
'"unchanged_input_sha256":NATIVE_INPUT_SHA':'"unchanged_input_sha256":NATIVE_INPUT_SHA,"distinct_second_plan_sha256":SECOND_PLAN_SHA'}
for old,new in sub.items():
 assert calc.count(old)==1
 calc=calc.replace(old,new)
needle='\tif mesh.mesh==null or mesh.mesh.get_surface_count()!=2:\n'
assert calc.count(needle)==1
calc=calc.replace(needle,'''	var second:Dictionary=plans[1]
	var keys:Array=[]
	for k in second.key:
		keys.append(pt(k))
	if JSON.stringify({"source":tf(second.source),"rest":tf(second.rest),
		"key":keys,"age_ticks":second.ages},"",true,true).sha256_text()!=SECOND_PLAN_SHA:
		return -INF
'''+needle)
c='const SECOND_PLAN_SHA := "'+sha+'"\nvar second_mid_certificate_m := 0.\n\n'+calc
new=first
ed=[]
def apply(a,b):
 global new
 assert new.count(a)==1
 ed.append((a,b));new=new.replace(a,b,1)
a='func finite_plan(plans:Array, ids:Array[int], mount:Node3D) -> Dictionary:'
apply(a,c+'\n'+a)
a='\t\t\tvar pair_gap:=maxf(gap_box(fitted[k],other_local),gap_box(world[k],other_box))'
apply(a,'''			if i==1 and k==1:
				actor_gap=prove_second_only(plans,mount,mesh,local,actor_gap)
				if not is_finite(actor_gap):
					print("EXAM_NAMED_SECOND_MID_LIVE_WITNESS_HOLD")
					return {}
'''+a)
out.write_text(new)
for a,b in reversed(ed):
 assert new.count(b)==1;new=new.replace(b,a,1)
assert new==first
print("bound distinct second plan sha256",sha)
