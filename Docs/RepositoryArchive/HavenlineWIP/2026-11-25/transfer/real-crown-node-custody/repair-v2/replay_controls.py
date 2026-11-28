"""Replay the first critic's exact source mutations on disposable repair copies."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

packet = Path(__file__).resolve().parent
source, lock = (Path(arg).resolve() for arg in sys.argv[1:])
base = (packet / 'test.gd').read_text()
controls = [
    ('nested-participating', '\tvalidate([actor,actor,actor,actor],"initial")',
     '\tvar wrapper := make_mount(flight, "HiddenFromDirectScan")\n'
     '\tvar nested := make_visual(wrapper,mesh,"ExtraVisibleCrown",Vector3.ZERO)\n'
     '\tnested.set_meta("slot",0)\n', ': recursive all-mesh census', True),
    ('off-course-full-path',
     'node.position = Vector3(lerpf(-2,2,u),lerpf(1,.5,u)+.65*4*u*(1-u),(i-1.5)*SPACING)',
     'node.position = Vector3(9999.0*u,-9999.0*u,(i-1.5)*SPACING)', ': XY arc oracle', False),
]
results = []
for label, needle, change, expected_failure, prefix in controls:
    assert base.count(needle) == 1, label
    with tempfile.TemporaryDirectory(prefix='hvn-custody-replay-') as tmp:
        tmp = Path(tmp)
        for name in ('planner_upstream.gd', 'project.godot', 'run.sh'):
            shutil.copyfile(packet / name, tmp / name)
        (tmp / 'test.gd').write_text(base.replace(needle, change + needle if prefix else change))
        run = subprocess.run(['bash', str(tmp / 'run.sh'), str(source), str(lock)], capture_output=True, text=True, timeout=35)
        report = json.loads(next(line for line in run.stdout.splitlines() if line.startswith('{')))
        assert run.returncode == 1 and any(f.endswith(expected_failure) for f in report['failures']), (run.stdout, run.stderr)
        assert not run.stderr.strip(), run.stderr
        results.append(dict(label=label, code=run.returncode, checks=report['checks'],
                            failures=len(report['failures']), first_failure=report['failures'][0]))
print(json.dumps(results, indent=2))
