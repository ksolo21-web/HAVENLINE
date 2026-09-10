#!/usr/bin/env python3
"""Fresh source-bound full lake review after the material repair.
No reuse of old grades or retries of returned low scores. Only transport/malformed
response failures receive a bounded retry, with the failure and raw files kept.
The context panel prevents a cropped contact view being read as the whole map.
"""
from pathlib import Path
import hashlib,json
base=Path('tools/havenline/review_lake_east_west.py')
source=base.read_text()
assert hashlib.sha256(base.read_bytes()).hexdigest()=='183cd79808cb4cf4eb68801b62b3f06f3b846806efaa820a13b9f153c4659b1e'
needle='def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()'
assert source.count(needle)==1
source=source.replace(needle,"GROUPS['snow-contact'].append('lake4k/lake-entire-east-west.png')\n"+needle)
needle="(OUT/'rubric.txt').write_text(PROMPT)"
assert source.count(needle)==1
source=source.replace(needle,"PROMPT+='\\nEach evidence group is a scoped inspection, not a complete map. Snow/forest contact closeups need to show the material contacts, not the whole lake; the same unmodified full-lake overview is also included as context. Full east-west extent is independently judged in its dedicated group. A lake outside a closeup camera is not proof it is absent from the world. Do not waive any visible seam, clipping, obstruction or water defect.'\n"+needle)
assert source.count('def request(image,prompt,label):')==1
source=source.replace('def request(image,prompt,label):','def request_once(image,prompt,label):')
needle='rows=[];error=None'
assert source.count(needle)==1
replacement='''def request(image,prompt,label):
 for attempt in range(3):
  try:
   return request_once(image,prompt,label)
  except Exception as exc:
   # This is not a retry of a scored verdict: no complete parsed review returned.
   failed=OUT/'transport-failures'/f'{label}-{attempt+1}'
   failed.mkdir(parents=True,exist_ok=True)
   (failed/'error.txt').write_text(type(exc).__name__+': '+str(exc))
   for suffix in ('-raw.json','-raw.txt','-request.json'):
    path=OUT/(label+suffix)
    if path.exists(): path.replace(failed/path.name)
   if attempt==2: raise
   time.sleep(5*(attempt+1))
rows=[];error=None'''
source=source.replace(needle,replacement)
out=Path('lake-review');out.mkdir(exist_ok=True)
executed=out/'executed-reviewer.py';executed.write_text(source)
(out/'reviewer-provenance.json').write_text(json.dumps({'base_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'executed_sha256':hashlib.sha256(source.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'all59_original_frames_required':True,'additional_existing_context_image_for_contact':True,'scored_verdicts_are_never_retried':True,'threshold_and_dimensions_unchanged':True},indent=2))
exec(compile(source,str(executed),'exec'),{'__name__':'__main__','__file__':str(executed.resolve())})
