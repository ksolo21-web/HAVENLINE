"""Exercise four on-foot warehouse scenarios using the signed Android game's own resources."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

CASES = (
    ('full', 'Build8-paid-workshops.json', 23),
    ('money', 'Build9-settled.json', 5),
    ('cold', None, 8),
    ('starter', 'Build10-earned-opening.json', 5),
)


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def archive_hashes(path, prefix):
    result = {}
    with ZipFile(path) as archive:
        for item in archive.infolist():
            if item.is_dir() or not item.filename.startswith(prefix):
                continue
            name = item.filename.removeprefix(prefix)
            if name in result:
                raise ValueError('Repeated game resource ' + name)
            with archive.open(item) as resource:
                result[name] = hashlib.file_digest(resource, 'sha256').hexdigest()
    return result


def replay(pack, source, output, profile, case):
    mode, fixture_name, expected = case
    journal = profile / 'field-inventory-v1.json'
    if fixture_name:
        shutil.copyfile(source / 'Fixtures' / fixture_name, journal)
    before = digest(journal)
    command = ['godot', '--headless', '--audio-driver', 'Dummy', '--fixed-fps', '60',
               '--main-pack', str(pack), '--script', str(source / 'check_signed_shelf_walk.gd'),
               '--', '--l1-disposable-profile=' + str(profile), '--walk-shelf=' + mode]
    env = dict(os.environ, XDG_DATA_HOME=str(profile/'data'), XDG_CONFIG_HOME=str(profile/'config'),
               XDG_CACHE_HOME=str(profile/'cache'), LP_NUM_THREADS='1', WAREHOUSE_WALK_CAPTURE='')
    job = subprocess.run(command, cwd=profile, env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, timeout=240)
    log = output.parent / ('Signed-shelf-walk-' + mode + '.log')
    log.write_text(job.stdout)
    rows = [json.loads(line.removeprefix('SHELF_WALK ')) for line in job.stdout.splitlines()
            if line.startswith('SHELF_WALK ')]
    checks = rows[0]['checks'] if len(rows) == 1 else {}
    if (job.returncode or len(checks) != expected or not all(value is True for value in checks.values())
            or any(error in job.stdout for error in ('ERROR:', 'WARNING:'))):
        raise RuntimeError(f'{mode} failed, see {log}')
    return {'mode': mode, 'source_journal': fixture_name or 'money checkpoint from preceding process',
            'before_sha256': before, 'after_sha256': digest(journal), 'log': log.name,
            'log_sha256': digest(log), 'result': rows[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pack', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--apk', type=Path, help='Android artifact from which the resource pack was extracted')
    args = parser.parse_args()
    pack, output = args.pack.resolve(), args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve().parent
    game = json.loads((source/'Reviewed-files.json').read_text())
    apk = args.apk or output.parent.parent / 'Play' / 'Havenline-Camp-Field-Android-arm64.apk'
    android = json.loads((output.parent / 'Android.json').read_text())
    apk_sha = digest(apk)
    if not android['signed_v2'] or android['sha256'] != apk_sha or android['source'] != game['commit']:
        raise ValueError('APK must match the signed build and its reviewed source')

    resources = archive_hashes(pack, '')
    if not resources.get('project.binary') or resources != archive_hashes(apk, 'assets/'):
        raise ValueError('The desktop-readable game resources differ from the signed APK')
    with tempfile.TemporaryDirectory(prefix='havenline-l1-v3-signed-shelf-', dir='/tmp') as folder:
        profile = Path(folder)
        (profile/'L1-DISPOSABLE').write_text('HAVENLINE-ALFRED-V3-DISPOSABLE\n')
        runs = [replay(pack, source, output, profile, case) for case in CASES]
    if runs[1]['after_sha256'] != runs[2]['before_sha256']:
        raise ValueError('Cold launch did not reopen the preceding warehouse visit')

    proof = {'passed': True, 'source': game['commit'], 'scene': 'res://field_opening.tscn',
             'engine': subprocess.check_output(['godot', '--version'], text=True).strip(),
             'runtime': 'Desktop headless, executing verified resources from the signed Android package',
             'apk_sha256': apk_sha, 'apk_certificate_sha256': android['certificate_sha256'],
             'resource_pack_sha256': digest(pack), 'identical_files_from_apk': len(resources),
             'probe_sha256': digest(source/'check_signed_shelf_walk.gd'),
             'assertions': sum(len(r['result']['checks']) for r in runs), 'runs': runs}
    output.write_text(json.dumps(proof, indent=2) + '\n')
    print(f"Passed {proof['assertions']} shelf assertions in {len(runs)} launches, {len(resources)} signed resources")


if __name__ == '__main__':
    main()
