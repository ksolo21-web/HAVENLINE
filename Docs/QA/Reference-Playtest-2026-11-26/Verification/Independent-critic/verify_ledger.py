"""Independent implementation of the documented JSON release check, with this project's 9.5 threshold."""
import hashlib,json,sys,struct
from pathlib import Path
p=Path(sys.argv[1]).resolve();j=json.loads(p.read_text());problem=[];c=j['candidate'];model=Path(c['path']);model=model if model.is_absolute() else p.parent/model;b=model.read_bytes();sha=hashlib.sha256(b).hexdigest()
if sha!=c['sha256']:problem.append('Candidate hash differs')
size=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+size]);names={g['nodes'][k]['name'] for skin in g['skins'] for k in skin['joints']};clips={a['name'] for a in g['animations']};parts=j['parts'];covered={i for part in parts for i in part['joints']}
if names!=covered:problem.append(['Skin joint inventory differs',sorted(names^covered)])
if set(j['clips'])!=clips:problem.append('Clip inventory differs')
expected={('*','*',s) for s in ('preservation','skeleton_integrity','animation_integrity','export_integrity')}|{('*',a,k) for a in clips for k in ('loop_continuity','contact','motion_intent')}|{(part['id'],a,k) for part in parts for a in clips for k in ('transforms','deformation','clearance','temporal')};obs=set();statuses={};failed=[]
for r in j['checks']:
 key=tuple(r[x] for x in ('part','clip','check'));cst=r['status'];statuses[cst]=statuses.get(cst,0)+1
 if key in obs:problem.append(['Duplicate',key])
 obs.add(key)
 if cst!='PASS':failed.append(key)
 if not r.get('evidence'):problem.append(['Missing evidence',key]);continue
 for z in r['evidence']:
  if not (p.parent/Path(z)).is_file():problem.append(['Missing evidence file',key,z])
if expected!=obs:problem.append(['Rows incomplete',list(sorted(expected^obs))])
if failed:problem.append(['Nonpassing rows',len(failed)])
if not 9.5<=j['score']<=10 or j['score']!=min(x['score'] for x in j['critics']):problem.append('Independent score below 9.5 or not lowest')
print(json.dumps({'validator':'independent implementation of the documented skill and project requirements','candidate_sha256':sha,'score':j['score'],'minimum':9.5,'clip_count':len(clips),'joint_count':len(names),'required_rows':len(expected),'observed_rows':len(obs),'statuses':statuses,'defects':problem,'passed':not problem},indent=2));sys.exit(int(bool(problem)))
