from pathlib import Path
s=Path('build.py').read_text()
ns={'__file__':str(Path('build.py').resolve())}
exec(s[:s.index('exam=')],ns)
exec(s[s.index('def inside('):s.index("old=parts['timber_terminal_9']")],ns)
from itertools import product
np=ns['np'];base=ns['parts']['timber_terminal_9']; inside=ns['inside']
raw=s[s.index('def rope('):s.index('for high in')]
rank=[]
for x,z,ax,az in product([-8.270,-8.274,-8.277],[4.339,4.350,4.361],[.100,.105,.110],[.089,.093,.097]):
 exec(raw.replace('X,Z=-8.25975,4.345',f'X,Z={x},{z}').replace('a,b=.114,.100',f'a,b={ax},{az}'),ns)
 scores=[];ok=True
 for d in (False,True):
  for i in (0,1):
   p=ns['rope'](d,i)
   if p[:,:,0].min() < -8.39742 or p[:,:,2].max()>4.4668424 or p[:,:,2].min()<4.2174:ok=False;break
   c=p.mean(axis=1)
   b=np.array(inside(c,base))
   scores.append((np.count_nonzero(b),np.count_nonzero((c[:,0]<-8.35)&~b)))
  if not ok:break
 if ok:rank.append((min(v for t,v in scores),(x,z,ax,az),scores))
print(sorted(rank,reverse=True)[:10])
