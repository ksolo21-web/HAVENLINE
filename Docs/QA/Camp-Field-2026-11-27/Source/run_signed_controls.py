"""Replay a touchscreen warehouse visit and select the four real characters from the Android pack."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('pack', type=Path)
    cli.add_argument('report', type=Path)
    args = cli.parse_args()
    source = Path(__file__).resolve().parent
    fixture = source / 'Fixtures' / 'Build11-snow.json'
    probe = source / 'check_signed_controls.gd'
    with tempfile.TemporaryDirectory(prefix='havenline-l1-v3-signed-control-') as folder:
        profile = Path(folder)
        env = dict(os.environ, LP_NUM_THREADS='1', XDG_DATA_HOME=str(profile/'data'),
                   XDG_CACHE_HOME=str(profile/'cache'), XDG_CONFIG_HOME=str(profile/'config'))
        (profile/'L1-DISPOSABLE').write_text('HAVENLINE-ALFRED-V3-DISPOSABLE\n')
        shutil.copyfile(fixture, profile/'field-inventory-v1.json')
        command = ['godot', '--headless', '--audio-driver', 'Dummy', '--fixed-fps', '60',
                   '--main-pack', str(args.pack.resolve()), '--script', str(probe), '--',
                   '--l1-disposable-profile='+folder, '--warehouse-ui']
        result = subprocess.run(command, env=env, cwd=folder, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=140)
    log = args.report.with_suffix('.log')
    log.write_text(result.stdout)
    if result.returncode or any(x in result.stdout for x in ('ERROR:', 'WARNING:')):
        raise RuntimeError(str(log)+' '+result.stdout[-1500:])
    checks = json.loads(next(line.removeprefix('CAMP_WAREHOUSE_CONTROLS ') for line in result.stdout.splitlines()
                             if line.startswith('CAMP_WAREHOUSE_CONTROLS ')))
    assert all(checks.values()) and len(checks)>=15
    args.report.write_text(json.dumps(dict(checks=checks, resource_pack_sha256=digest(args.pack), fixture_sha256=digest(fixture),
                          probe_sha256=digest(probe), source=json.loads((source/'Reviewed-files.json').read_text())['commit']),indent=2)+'\n')
    print('Passed',len(checks),'controls on the signed Android resources')

if __name__=='__main__':
    main()
