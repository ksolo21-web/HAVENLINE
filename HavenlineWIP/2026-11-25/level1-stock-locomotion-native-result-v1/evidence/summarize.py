import json,math,sys
from pathlib import Path
rows=[json.loads(l.split(' ',1)[1]) for l in Path(sys.argv[1]).open() if l.startswith('STOCK_PRIVATE_FRAME ')]
data={}
for phase,clip in [('idle','idle'),('walk','walk'),('run','run'),('turn','run'),('stop','idle')]:
 f=[x for x in rows if x['phase']==phase and x['clip'].endswith('/'+clip) and x['clip_t']>.02]
 v=[x['speed'] for x in f]
 data[phase]={'true_sample_count':len(f),'speeds_m_s':[min(v),max(v)],
    'first_last_observed_tick':[f[0]['tick'],f[-1]['tick']]}
print(json.dumps(data,indent=2))
