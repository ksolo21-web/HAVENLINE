#!/usr/bin/env python3
"""Freeze one exact diagnostic patch; no canonical source or approval writes."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import traceback

BRANCH = 'refs/heads/havenline/review-T10-light-context-preflight'
PATCH = 'Docs/Production/T10/DiagnosticInputs/light-context-repair.patch'
PATCH_SHA = 'c9ef630e3931b8a41c13533b7c584b206a8956782c5eb86bb8f2d48da2c33543'
BEFORE = {
    'HavenlineGodot/scripts/world_transform_view.gd': '88bea24eca5b411cdc220d44ba1a544f61e43689',
    'HavenlineGodot/tests/test_task10_integration.gd': '111386adb7f35e34b216ae9645a8341430e7e3f3',
}
AFTER = {
    'HavenlineGodot/scripts/world_transform_view.gd': 'bd91be572015673201982ad4c923960b8ace31c844916c7ca98db24efe005780',
    'HavenlineGodot/tests/test_task10_integration.gd': '2e908082d4292e3269b0f7e3a6039b99cda525951f62bd3dfe8f3bc7735b2254',
    'HavenlineGodot/tests/test_task10_world_transform.gd': 'ae337e64a7159901bf8fc6df7d1448af70bbedc34cd8b4b45f339672cb407c6e',
}


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], text=True, timeout=60).strip()


def raw_snapshot(paths: list[str], root: Path = Path('.')) -> dict:
    """Measure actual bytes and modes without Git clean/smudge interpretation."""
    rows = {}
    for name in paths:
        path = root / name
        if path.is_symlink():
            raw = os.readlink(path).encode()
            kind = 'symlink'
        elif path.is_file():
            raw = path.read_bytes()
            kind = 'file'
        else:
            rows[name] = {'kind': 'missing'}
            continue
        rows[name] = {'kind': kind, 'mode': path.lstat().st_mode & 0o777,
                      'sha256': hashlib.sha256(raw).hexdigest()}
    return rows


def changed_raw(before: dict, after: dict) -> set[str]:
    return {name for name in set(before) | set(after) if before.get(name) != after.get(name)}


def main() -> int:
    out = Path('light-context-input'); out.mkdir(exist_ok=True)
    record = {'kind': 'DIAGNOSTIC_SOURCE_FREEZE', 'task_approved': False,
              'canonical_branch_changed': False, 'force_push': False,
              'T11_unlocked': False, 'passed': False}
    try:
        assert os.environ['GITHUB_REF'] == BRANCH
        assert os.environ['GITHUB_RUN_ATTEMPT'] == '1'
        parent = git('rev-parse', 'HEAD')
        assert parent == os.environ['GITHUB_SHA']
        record.update(workflow_source=parent, branch=BRANCH)
        patch = Path(PATCH)
        assert hashlib.sha256(patch.read_bytes()).hexdigest() == PATCH_SHA
        assert not git('diff', '--cached', '--name-only')
        paths = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
        paths = [name for name in paths if name]
        before = raw_snapshot(paths)
        baseline = out / 'checkout-raw-manifest.json'
        baseline.write_text(json.dumps(before, sort_keys=True, indent=2) + '\n')
        record['baseline_sha256'] = hashlib.sha256(baseline.read_bytes()).hexdigest()
        record['checkout_filter_dirty_paths'] = git('diff', '--name-only').splitlines()
        for path, blob in BEFORE.items():
            assert git('rev-parse', 'HEAD:' + path) == blob, path
        subprocess.run(['git', 'apply', '--check', PATCH], check=True)
        subprocess.run(['git', 'apply', PATCH], check=True)
        after = raw_snapshot(paths)
        assert changed_raw(before, after) == set(BEFORE), sorted(changed_raw(before, after))
        for path, digest in AFTER.items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
        subprocess.run(['git', 'diff', '--check', '--', *sorted(BEFORE)], check=True)
        subprocess.run(['git', 'add', '--', *sorted(BEFORE)], check=True)
        assert set(git('diff', '--cached', '--name-only').splitlines()) == set(BEFORE)
        git('config', 'user.name', 'Havenline diagnostic source builder')
        git('config', 'user.email', 'diagnostic@users.noreply.github.com')
        git('commit', '-m', 'T10 diagnostic: tested live lighting-context repair; no approval')
        source = git('rev-parse', 'HEAD')
        assert git('rev-parse', 'HEAD^') == parent
        assert set(git('diff', '--name-only', parent, source).splitlines()) == set(BEFORE)
        assert git('ls-remote', '--exit-code', 'origin', BRANCH).split() == [parent, BRANCH]
        git('push', 'origin', 'HEAD:' + BRANCH)
        assert git('ls-remote', '--exit-code', 'origin', BRANCH).split() == [source, BRANCH]
        record.update(source=source, tree=git('rev-parse', 'HEAD^{tree}'),
                      files_sha256=AFTER, patch_sha256=PATCH_SHA,
                      raw_changed_paths=sorted(BEFORE), passed=True)
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('source=' + source + '\n')
    except Exception as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
        (out / 'failure.txt').write_text(traceback.format_exc())
    finally:
        (out / 'source-binding.json').write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps(record))
    return 0 if record['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
