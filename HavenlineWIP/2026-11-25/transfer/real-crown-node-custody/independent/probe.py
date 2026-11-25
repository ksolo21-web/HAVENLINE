"""Run deliberately out-of-contract mutations in disposable copies."""
import pathlib, tempfile, shutil, subprocess, sys, json
packet, source, lock = (pathlib.Path(i).resolve() for i in sys.argv[1:])
def probe(base, patch, label):
    needle, change = patch
    assert base.count(needle) == 1
    with tempfile.TemporaryDirectory(prefix='hvn-custody-critic-') as tmp:
        tmp = pathlib.Path(tmp)
        for name in ('planner_upstream.gd', 'project.godot', 'run.sh'):
            shutil.copyfile(packet/name, tmp/name)
        (tmp/'test.gd').write_text(base.replace(needle, change))
        cmd = ['bash', str(tmp/'run.sh'), str(source), str(lock)]
        out = subprocess.check_output(cmd, text=True, timeout=35)
        result = json.loads(next(l for l in out.splitlines() if l.startswith('{')))
        assert result['checks']==1116 and result['failures']==[]
        return {'probe':label, 'checks':result['checks'], 'failures':result['failures']}

base = (packet/'test.gd').read_text()
t = '\tvalidate([actor,actor,actor,actor],"initial")'
a = probe(base,(t,'\tvar wrapper := make_mount(flight, "HiddenFromDirectScan")\n\tvar nested := make_visual(wrapper,mesh,"ExtraVisibleCrown",Vector3.ZERO)\n\tnested.set_meta("slot",0)\n'+t),'nested_visible_duplicate_not_scanned')
t = 'node.position = Vector3(lerpf(-2,2,u),lerpf(1,.5,u)+.65*4*u*(1-u),(i-1.5)*SPACING)'
b = probe(base,(t,'node.position = Vector3(9999.0*u,-9999.0*u,(i-1.5)*SPACING)'),'off_course_xy_path_not_checked')
print(json.dumps([a,b],indent=2))
