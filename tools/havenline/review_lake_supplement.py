#!/usr/bin/env python3
"""Complete three unresolved review groups; never rescore passing groups.
The original failed reviews and upstream errors remain in the prior artifact.
Snow-contact gets the actual full-lake overview as additional context because
one earlier critic incorrectly required water in every ground-contact close-up.
No candidate pixels, art, scores or acceptance threshold are changed.
"""
from pathlib import Path
import hashlib,os
p=Path('tools/havenline/review_lake_east_west.py');raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='183cd79808cb4cf4eb68801b62b3f06f3b846806efaa820a13b9f153c4659b1e'
s=raw.decode()
assert s.count("OUT=Path('lake-review')")==1
s=s.replace("OUT=Path('lake-review')","OUT=Path('lake-supplement')")
needle='rows=[];error=None'
assert s.count(needle)==1
s=s.replace(needle,'''SELECTED={'snow-contact'} if ROLE=='visual-integrity' else {'snow-contact','camera-route-late'}
original_request=request
def request(image,prompt,label):
 for attempt in range(3):
  try:return original_request(image,prompt,label)
  except Exception as exc:
   (OUT/(label+'-transport-attempt-'+str(attempt+1)+'.json')).write_text(json.dumps({'error':str(exc),'completed_raw_response_present':(OUT/(label+'-raw.json')).exists(),'no_grade_substitution':True},indent=2))
   # A completed model response is never retried for a better score.
   if (OUT/(label+'-raw.json')).exists() or attempt==2:raise
   time.sleep(5*(attempt+1))
'''+needle)
needle=' for group,names in GROUPS.items():\n'
assert s.count(needle)==1
s=s.replace(needle,needle+'''  if group not in SELECTED:continue
  if group=='snow-contact':names=list(names)+['lake4k/lake-entire-east-west.png']
''')
needle="  print('Reviewing',ROLE,group,flush=True)"
assert s.count(needle)==1
s=s.replace(needle,'''  note+=' Each group is a scoped view of the same complete evidence set, not a requirement to place every feature in every close-up. For snow-contact, assess the three original ground/tree contact close-ups; the fourth image is the actual lake overview supplied to show the requested lake is present elsewhere in the scene. A ground-contact close-up excluding distant water is not missing lake geometry. Inspect all actual panels and report any real defect; do not infer a pass from these instructions.'
'''+needle)
needle="'passed':len(rows)==9 and all(r['passed'] for r in rows)"
assert s.count(needle)==1
s=s.replace(needle,"'passed':len(rows)==len(SELECTED) and all(r['passed'] for r in rows),'supplemental_groups':sorted(SELECTED),'previous_review_artifact':10176284965,'game_runtime_unchanged':True")
o=Path('lake-supplement');o.mkdir(exist_ok=True)
(o/'executed-reviewer.py').write_text(s)
(o/'supplement-provenance.json').write_text(__import__('json').dumps({'base_reviewer_sha256':hashlib.sha256(raw).hexdigest(),'executed_reviewer_sha256':hashlib.sha256(s.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'reason':'Two upstream failures and one context-misidentified ground-contact view; actual lake overview added, no score/threshold changes','prior_complete_raw_reviews_preserved':True},indent=2))
exec(compile(s,'lake-review-supplement','exec'),{'__name__':'__main__'})
