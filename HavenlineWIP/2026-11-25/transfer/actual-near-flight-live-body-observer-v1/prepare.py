from pathlib import Path
import subprocess,sys,hashlib
p=Path(__file__).resolve().parent
root=p.parent
pins={
'hvn-l1-actual-near-flight-candidate-v1':'bfcfadd07231f2ba40c2f206a30347c41b613e23b845fec807a161305bce6f6c',
'hvn-l1-actual-near-flight-first-result-v1':'100ff1cb0f912f7a15e36c63084c38c85ab757aca486593d1bfa07eab17e2369',
'hvn-l1-near-flight-independent-v1.Rve76I':'34c24d19dfc7c46de78cd6ad9d2faf9a532c20b1273a4357f0b5e1fa8dbb8a63'}
for d,sha in pins.items():
 q=root/d
 assert hashlib.sha256((q/'SHA256SUMS').read_bytes()).hexdigest()==sha
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=q,check=True)
stage,out=map(Path,sys.argv[1:3])
subprocess.run([sys.executable,str(root/'hvn-l1-actual-near-flight-candidate-v1/prepare.py'),str(stage),str(out)],check=True)
old=out.read_text(); s=old; edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a
 edits.append((a,b));s=s.replace(a,b,1)
key='func finite_plan(plans:Array, ids:Array[int], mount:Node3D) -> Dictionary:'
edit(key,(p/'observer.gdfrag').read_text()+'\n'+key)
edit('\texpected_body=grown_box(live_box[0],BODY_PAD)','\texpected_body=grown_box(live_box[0],BODY_PAD)\n\twitness_input(plans,mount)')
edit('\t\tvar fitted: Array[AABB]=[local1,local2,local3]','\t\tvar fitted: Array[AABB]=[local1,local2,local3]\n\t\twitness_gaps(i,fitted)')
# Diagnostic run must not reach any state changes if the exact old denial drifts.
key='\t\treturn {}\n\tfor i in range(2):\n\t\tvar shape:AABB=own_view.paid_crowns[i].get_aabb()'
edit(key,'\t\treturn {}\n\tif not certified.is_empty():\n\t\tprint("EXAM_SUPPORT_UNEXPECTED_PASS no dispatch")\n\t\treturn {}\n\tfor i in range(2):\n\t\tvar shape:AABB=own_view.paid_crowns[i].get_aabb()')
out.write_text(s)
for a,b in reversed(edits):
 assert s.count(b)==1
 s=s.replace(b,a,1)
assert s==old
