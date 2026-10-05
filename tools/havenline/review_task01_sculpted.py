#!/usr/bin/env python3
"""New R8 geometry, same independent review criteria and full evidence coverage."""
from pathlib import Path
p=Path('tools/havenline/review_task01_reference_finish.py')
s=p.read_text()
old='"pro[\'revision\']==7"';assert s.count(old)==1
s=s.replace(old,'"pro[\'revision\']==8"')
out=Path('critic-results');out.mkdir(exist_ok=True)
(out/'revision-wrapper.py').write_text(s)
exec(compile(s,'T01-sculpted-source-review','exec'),{'__name__':'__main__','__file__':str(out/'revision-wrapper.py')})
