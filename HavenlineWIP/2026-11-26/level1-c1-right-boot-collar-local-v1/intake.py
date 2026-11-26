from pathlib import Path
import os,inspect,runpy
import numpy as np
D=Path.cwd(); legacy=Path('../level1-c1-opposed-contact-key-v1/correction').resolve()
s=legacy/'once.py'
from hashlib import file_digest
def sha(p):
 with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
assert sha(legacy/'CENTER-KEY-SHA256SUMS')=='fb21d6e21cf6bae4d0e8482d41e09e37387e12de86ec283ec0df6686bf23f1aa'
for z in (legacy/'CENTER-KEY-SHA256SUMS').read_text().splitlines():
 h,p=z.split();assert sha(legacy/p)==h
os.chdir(legacy)
ctx={}
exec(s.read_text().split("foot={}")[0],ctx)
os.chdir(D)
f,P,T=ctx['f'],ctx['P'],ctx['T']
F,V=f.F,f.V
M=np.stack([T[k] for k in f.slots])@f.inv
