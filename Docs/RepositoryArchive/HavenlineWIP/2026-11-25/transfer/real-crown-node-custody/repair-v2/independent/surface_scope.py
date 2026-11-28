"""Document a cosmetic coverage limit on a disposable exact repair copy."""
import json, pathlib, shutil, subprocess, sys, tempfile
packet, source, lock = (pathlib.Path(arg).resolve() for arg in sys.argv[1:])
test = (packet/'test.gd').read_text()
needle = '\tvalidate([actor,actor,actor,actor],"initial")'
assert test.count(needle) == 1
with tempfile.TemporaryDirectory(prefix='hvn-material-scope-') as tmp:
    tmp = pathlib.Path(tmp)
    for name in ('planner_upstream.gd','project.godot','run.sh'):
        shutil.copyfile(packet/name, tmp/name)
    change = '\tvar injected := StandardMaterial3D.new()\n\tinjected.albedo_color = Color.MAGENTA\n\tlogs[0].set_surface_override_material(0, injected)\n'
    (tmp/'test.gd').write_text(test.replace(needle, change + needle))
    result = subprocess.run(['bash', str(tmp/'run.sh'), str(source), str(lock)], capture_output=True, text=True, timeout=35)
    report = json.loads(next(line for line in result.stdout.splitlines() if line.startswith('{')))
    assert result.returncode == 0 and report['checks'] == 1831 and not report['failures'] and not result.stderr.strip()
    print(json.dumps({'probe':'single_log_per_surface_override_not_observed', 'exit':result.returncode,
                      'checks':report['checks'],'failures':report['failures']}, indent=2))
