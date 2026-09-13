#!/usr/bin/env python3
"""Run only the missing Task 3 cross-shelter-lanes reference group locally.

The hosted reference role already returned ten scored 10/10 judgments. This
wrapper reuses the checksum-pinned local public reviewer for the single group
that repeatedly received no hosted verdict. No completed score is rerun.
"""
from pathlib import Path
import hashlib,os
base=Path('tools/havenline/review_task03_local_reference.py')
source=base.read_text();base_sha=hashlib.sha256(base.read_bytes()).hexdigest()
assert "EXPECTED=set(sum(GROUPS.values(),[]));assert EXPECTED==set(FILES) and len(EXPECTED)==11" in source
source=source.replace("EXPECTED=set(sum(GROUPS.values(),[]));assert EXPECTED==set(FILES) and len(EXPECTED)==11","EXPECTED=set(sum(GROUPS.values(),[]));assert EXPECTED==set(FILES) and len(EXPECTED)==11\nGROUPS={2:['cross-shelter-lanes']}\n",1)
source=source.replace("OUT=Path('task03-local-reference')","OUT=Path('task03-local-one')",1)
os.environ['REVIEW_SHARD']='2'
out=Path('task03-local-one');out.mkdir(exist_ok=True)
(out/'wrapper-provenance.txt').write_text('base_sha256='+base_sha+'\nmissing_group=cross-shelter-lanes\nhosted_completed_reference_scores_retried=false\n')
exec(compile(source,str(Path(__file__).resolve()),'exec'),{'__name__':'__main__','__file__':str(Path(__file__).resolve())})
