"""Exact art and held pose intake, read only."""
import os, sys, contextlib, io, hashlib
from pathlib import Path
target=Path.cwd(); dep=Path('../level1-c1-collar-assembly-read-v1').resolve()
h=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert h(dep/'ASSEMBLY-READ-SHA256SUMS')=='d6a13f5c2891a905a22917e12789d2740d4124d317fafb7b700b91e9299ab966'
for line in (dep/'ASSEMBLY-READ-SHA256SUMS').read_text().splitlines():
 digest,name=line.split();assert h(dep/name)==digest
sys.path.insert(0,str(dep));os.chdir(dep)
with contextlib.redirect_stdout(io.StringIO()):
 from analyze import f,F,V,R,P,meta,D,edge_face,Qf,M,T
os.chdir(target)
