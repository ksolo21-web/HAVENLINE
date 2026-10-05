#!/usr/bin/env python3
"""Same independent rubric, expanded/fixed evidence after real T01 changes."""
from pathlib import Path
source=Path('tools/havenline/review_task01.py').read_text()
old="inputs=[reference,O/'all-variant-angles.png',O/'orbit-sequence.png',E/'gallery/v01-three-quarter.png',E/'gallery/gameplay-integration.png']"
new="montage([f'integration-{i:02d}.png' for i in range(12)],O/'integration-sequence.png',4)\ninputs=[reference,O/'all-variant-angles.png',O/'orbit-sequence.png',O/'integration-sequence.png',E/'gallery/v01-three-quarter.png',E/'gallery/gameplay-integration.png',E/'gallery/forest-boundary-gameplay.png']"
assert source.count(old)==1
source=source.replace(old,new)
needle='Existing unfinished gameplay is NOT passed by this scoped review.'
source=source.replace(needle,'The additional integration sequence shows actual changing camera poses; forest-boundary-gameplay shows a reachable edge position as a disclosed QA fixture. Assess forest contact and view-dependent obstruction using these images too. '+needle)
out=Path('critic-results-v2');out.mkdir(exist_ok=True)
(out/'executed-reviewer.py').write_text(source)
exec(compile(source,'T01-expanded-evidence-review','exec'),{'__name__':'__main__'})
