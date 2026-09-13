#!/usr/bin/env python3
"""Faster checksum-pinned local fallback for only cross-shelter-lanes.
Uses exactly 1024 visual tokens: not below the grounding threshold that failed
prior reviewers. Same evidence, prompt, schema, model bytes and >=9 gate.
"""
from pathlib import Path
import hashlib,os
base=Path('tools/havenline/review_task03_local_reference.py');source=base.read_text();base_sha=hashlib.sha256(base.read_bytes()).hexdigest()
marker="EXPECTED=set(sum(GROUPS.values(),[]));assert EXPECTED==set(FILES) and len(EXPECTED)==11"
assert source.count(marker)==1;source=source.replace(marker,marker+"\nGROUPS={2:['cross-shelter-lanes']}\n",1)
assert source.count("OUT=Path('task03-local-reference')")==1;source=source.replace("OUT=Path('task03-local-reference')","OUT=Path('task03-local-fast')",1)
assert source.count("'--image-max-tokens','2048'")==1;source=source.replace("'--image-max-tokens','2048'","'--image-max-tokens','1024'",1)
os.environ['REVIEW_SHARD']='2';out=Path('task03-local-fast');out.mkdir(exist_ok=True)
(out/'wrapper-provenance.txt').write_text('base_sha256='+base_sha+'\nmissing_group=cross-shelter-lanes\nimage_min_tokens=1024\nimage_max_tokens=1024\nhosted_completed_reference_scores_retried=false\n')
exec(compile(source,str(Path(__file__).resolve()),'exec'),{'__name__':'__main__','__file__':str(Path(__file__).resolve())})
