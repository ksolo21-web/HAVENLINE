#!/usr/bin/env python3
"""Existing independent rubric plus two supplementary actual profile views.
New geometry/material source requires fresh review. No unchanged-score fishing.
Normal gameplay frames remain required; isolated diagnostics are labelled and
must not be interpreted as shipping visibility or proof of full-game completion.
"""
from pathlib import Path
import hashlib,json
p=Path('tools/havenline/review_task02_fullsize.py');base=p.read_text()
old="'native4k/native-overview.png'],"
assert base.count(old)==1
s=base.replace(old,"'native4k/native-overview.png','native4k/terrain-only-floor-profile.png'],")
old="'gallery/lakeshore-rear.png','native4k/lakeshore-gameplay.png'],"
assert s.count(old)==1
s=s.replace(old,"'gallery/lakeshore-rear.png','native4k/lakeshore-gameplay.png','native4k/terrain-only-bank-profile.png'],")
needle="out=Path('task02-review');out.mkdir(exist_ok=True)"
assert s.count(needle)==1
addition='''extra="\\nSupplementary terrain-only-floor-profile and terrain-only-bank-profile images are actual native-resolution diagnostic renders of the same surface. Unrelated models were hidden only for those labelled diagnostic captures, so inspect the snow/earth shape and bank profile without overhanging roofs. All normal gameplay images remain present and must also be inspected. Intentional isolation does not prove missing shipping objects or override a defect visible in normal gameplay. The terrain-only profiles are not concept art or evidence of hardware frame rate. Evaluate the demonstrated surfaces independently using the unchanged dimensions and standard."
marker="(OUT/'instructions.txt').write_text(PROMPT);"
assert s.count(marker)==1
s=s.replace(marker,'PROMPT+='+repr(extra)+'\\n'+marker)
'''
s=s.replace(needle,addition+'\n'+needle)
out=Path('task02-review');out.mkdir(exist_ok=True)
(out/'executed-profile-wrapper.py').write_text(s)
(out/'profile-review-provenance.json').write_text(json.dumps({'original_wrapper_sha256':hashlib.sha256(base.encode()).hexdigest(),'executed_wrapper_sha256':hashlib.sha256(s.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'change':'Two additional source-bound profile captures; every original required candidate view retained','rubric_dimensions_and_threshold_unchanged':True,'previous_failed_reviews_preserved':True,'game_or_score_modified_by_reviewer':False},indent=2)+'\n')
exec(compile(s,'T02-additional-ground-profiles','exec'),{'__name__':'__main__','__file__':__file__})
