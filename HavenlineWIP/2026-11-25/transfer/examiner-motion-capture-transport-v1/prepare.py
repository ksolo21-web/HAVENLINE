import hashlib,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
stage,art,out=sys.argv[1:4]
pack=p.parent/'hvn-l1-examiner-motion-capture-observer-v1'
assert hashlib.sha256((pack/'SHA256SUMS').read_bytes()).hexdigest()=='c333e961cab707dcf8f6d1bdb8a06711ad768b481b582c7673b7fb9d21894909'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=pack,check=True)
subprocess.run([sys.executable,str(pack/'prepare.py'),stage,art,out],check=True)
o=Path(out)
old=o.read_text();s=old
assert hashlib.sha256(old.encode()).hexdigest()=='00aacab506975d7f00d59991e355190925ad9f6abc9237370aee0916a4727954'
edits=[]
def apply(a,b):
 global s
 assert s.count(a)==1,a
 edits.append((a,b));s=s.replace(a,b,1)
for name in ('CAP_PRIVATE_START','CAP_PRIVATE_FRAME'):
 a='print("'+name+' ",JSON.stringify('
 b='write_capture("'+name+'",JSON.stringify('
 apply(a,b)
a='func capped_hero_sample() -> Dictionary:'
apply(a,(p/'transport.gdfrag').read_text()+'\n'+a)
o.write_text(s)
for a,b in reversed(edits):
 assert s.count(b)==1;s=s.replace(b,a,1)
assert s==old
