from pathlib import Path
import subprocess,hashlib,json,sys
p=Path(__file__).resolve().parent
root=p.parent
stage,out=Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve()
assert not out.is_relative_to(stage)
pins={'hvn-l1-actual-near-flight-candidate-v1':'bfcfadd07231f2ba40c2f206a30347c41b613e23b845fec807a161305bce6f6c',
'hvn-l1-actual-near-flight-first-result-v1':'100ff1cb0f912f7a15e36c63084c38c85ab757aca486593d1bfa07eab17e2369',
'hvn-l1-near-flight-live-body-observer-v1':'7688c8843dc45af01e8212304615e6652841dbbdd49c8b77cc32aba064334f08'}
# Independent seal is mandatory; until supplied this script is not runnable.
ins=(p/'independent.txt').read_text().split()
assert len(ins)==2
pins[ins[0]]=ins[1]
for n,h in pins.items():
 q=root/n
 assert hashlib.sha256((q/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=q,check=True)
subprocess.run([sys.executable,str(root/'hvn-l1-actual-near-flight-candidate-v1/prepare.py'),str(stage),str(out)],check=True)
old=out.read_text()
assert hashlib.sha256(old.encode()).hexdigest()=='951ae96023d7ebf7fc83716a2ceeb9b7287c35bf088601c9eed6c49199113043'
r=(root/'hvn-l1-near-flight-live-body-observer-v1/native.txt').read_text().splitlines()
rows=[l.split(' ',1)[1] for l in r if l.startswith('EXAM_SUPPORT_INPUT ')]
assert len(rows)==1 and json.loads(rows[0])['tick']==1333
raw_sha=hashlib.sha256(rows[0].encode()).hexdigest()
s=old
edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a
 edits.append((a,b));s=s.replace(a,b,1)
edit('func finite_plan(plans:Array, ids:Array[int], mount:Node3D) -> Dictionary:', (p/'support.gdfrag').read_text().replace('@INPUT_SHA@',raw_sha)+'\nfunc finite_plan(plans:Array, ids:Array[int], mount:Node3D) -> Dictionary:')
a='\t\t\tvar actor_gap:=gap_box(fitted[k],expected_body)'
edit(a,a+'''
			if i==0 and k==1:
				actor_gap=prove_first_only(plans,mount,mesh,local,actor_gap)
				if not is_finite(actor_gap):
					print("EXAM_NAMED_FIRST_MID_LIVE_WITNESS_HOLD")
					return {}''')
out.write_text(s)
for a,b in reversed(edits):
 assert s.count(b)==1;s=s.replace(b,a,1)
assert s==old
