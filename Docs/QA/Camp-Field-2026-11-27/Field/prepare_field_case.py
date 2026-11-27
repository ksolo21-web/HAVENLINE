from pathlib import Path
import json,math,hashlib,sys
src=Path(sys.argv[4]) if len(sys.argv)>4 else Path(__file__).resolve().parents[1]/'Source/Fixtures/HUD-paid-profile.json'
envelope=json.loads(src.read_text());save=json.loads(envelope['payload'])
mode=sys.argv[2]; target=Path(sys.argv[1]);w=save['world']
sett=save['settlement']
# Complete the earlier opening receipts on top of the historical all-purchases journal.
sett.update(survivor_wood=8,survivor_paid=True,rescued=True,owl_hits=1,worker_deliveries=1,worker_receipts=['wood-74000'],processed_wood=1,processed_stone=1)
for i in range(8):
 save['collected']['earned-rescue-'+str(i)]='wood'
save['collected']['wood-74000']='wood'
save['collected']['earned-quarry']='stone'
if mode in ('pile','overflow'):
 x,z=24.,11.
 w['player'].update(x=x,z=z,hp=18)
 w['serial']=76000
 w['drops']=[]
 for n in range(72 if mode=='pile' else 128):
  kind='meat' if n%3 else 'stone'
  angle=math.tau*n/40;radius=(.25 if n<20 else (1.24 if n<40 else 2.0))
  w['drops'].append([kind+'-'+str(75500+n),kind,x+radius*math.cos(angle),z+radius*math.sin(angle),91.])
 w['pack']['remaining']=.2
 if len(sys.argv)>3 and sys.argv[3]=='camera': w['player'].update(x=x+4.,z=z+.5)
elif mode=='repeat':
 w['player'].update(x=-.4,z=11.25,hp=24)
 w['serial']=76000;w['drops']=[];w['pack']['remaining']=.1
else:
 w['player'].update(x=-3.,z=0.,hp=30)
 if len(sys.argv)>3 and sys.argv[3]=='camera': w['player'].update(x=-1.1,z=1.45)
for n in range(5200):
 kind=('wood','stone','meat')[n%3] if mode=='store' else 'slate'
 save['collected']['stress-'+str(n)]=kind
 save['carried' if mode=='store' else 'stored'][kind]+=1
outer=json.dumps(save,sort_keys=True,separators=(',',':'))
envelope.update(payload=outer,sha256=hashlib.sha256(outer.encode()).hexdigest())
(target/'field-inventory-v1.json').write_text(json.dumps(envelope,sort_keys=True,separators=(',',':')))
