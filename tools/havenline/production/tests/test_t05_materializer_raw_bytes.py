"""Raw-byte regression for the observed T05 materializer LFS false-dirty failure."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / '.github/workflows/havenline-visual-repair-asset-materializer.yml'


class T05MaterializerRawBytesTests(unittest.TestCase):
    def test_actual_workflow_preserves_authority_and_whole_repository_checks(self):
        text = WORKFLOW.read_text()
        workflow = yaml.safe_load(text)
        job = workflow['jobs']['materialize-t05']
        expected = [('filter.lfs.process', ''), ('filter.lfs.clean', 'cat'),
                    ('filter.lfs.smudge', 'cat'), ('filter.lfs.required', 'false')]
        self.assertEqual(job['env']['GIT_CONFIG_COUNT'], '4')
        for index, (key, value) in enumerate(expected):
            self.assertEqual(job['env'][f'GIT_CONFIG_KEY_{index}'], key)
            self.assertEqual(job['env'][f'GIT_CONFIG_VALUE_{index}'], value)
        self.assertIn('git diff --exit-code', text)
        self.assertIn('git diff --cached --exit-code', text)
        self.assertIn('git ls-files --others --exclude-standard', text)
        self.assertIn('Materializer generated unauthorized path', text)
        self.assertIn('Unauthorized staged path', text)
        self.assertIn('git merge-base --is-ancestor', text)
        self.assertIn('test "$remote_head" = "$GITHUB_SHA"', text)
        self.assertIn("f'{integration}:Docs/Production/APPROVAL_INVALIDATIONS.json'", text)
        self.assertNotIn('git add .', text)
        self.assertNotIn('git push --force', text)

    def test_raw_detection_reproduces_old_failure_and_still_detects_real_changes(self):
        job = yaml.safe_load(WORKFLOW.read_text())['jobs']['materialize-t05']
        raw = {k: v for k, v in os.environ.items() if not k.startswith('GIT_CONFIG_')}
        raw.update({k: str(v) for k, v in job['env'].items()})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def git(*args, env=raw, check=True):
                return subprocess.run(['git', *args], cwd=root, env=env,
                                      capture_output=True, check=check)

            git('init', '-q')
            git('config', 'user.name', 'test')
            git('config', 'user.email', 'test@example.invalid')
            (root / '.gitattributes').write_text('*.png filter=lfs\n*.obj filter=lfs\n*.zip filter=lfs\n')
            files = {
                'Assets/TutorialInfo/Icons/URP.png': b'original-icon\x00',
                'HavenlineGodot/assets/t03_boundary_v2/fence_panel.obj': b'original-fence\n',
                'bundle.zip': b'version https://git-lfs.github.com/spec/v1\noid sha256:' + b'0' * 64 + b'\nsize 10\n',
                'HavenlineGodot/assets/stations_v2/hearth_vessel.glb': b'glTF-original',
                'HavenlineGodot/assets/stations_v2/catalog.json': b'{}\n',
            }
            for path, value in files.items():
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(value)
            git('add', '.')
            git('commit', '-qm', 'baseline')
            converter = root / '.git/fake_clean.py'
            converter.write_text('import sys,hashlib\nb=sys.stdin.buffer.read()\nif b.startswith(b"version https://git-lfs.github.com/spec/v1"):\n sys.stdout.buffer.write(b)\nelse:\n print("version https://git-lfs.github.com/spec/v1\\noid sha256:"+hashlib.sha256(b).hexdigest()+"\\nsize "+str(len(b)))\n')
            git('config', 'filter.lfs.process', '')
            git('config', 'filter.lfs.clean', f'python3 {converter}')
            git('config', 'filter.lfs.smudge', 'cat')
            git('config', 'filter.lfs.required', 'true')
            old_env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_CONFIG_')}
            (root / 'Assets/TutorialInfo/Icons/URP.png').touch()
            self.assertIn('URP.png', git('diff', '--name-only', env=old_env).stdout.decode())
            self.assertEqual(git('diff', '--exit-code', check=False).returncode, 0)
            self.assertEqual((root / 'bundle.zip').read_bytes(), files['bundle.zip'])
            for path in ['Assets/TutorialInfo/Icons/URP.png', 'HavenlineGodot/assets/t03_boundary_v2/fence_panel.obj']:
                (root / path).write_bytes(files[path] + b'actual-mutation')
                self.assertIn(path, git('diff', '--name-only').stdout.decode())
                (root / path).write_bytes(files[path])
            target = 'HavenlineGodot/assets/stations_v2/hearth_vessel.glb'
            (root / target).write_bytes(b'glTF-repaired')
            self.assertEqual(git('diff', '--name-only').stdout.decode().splitlines(), [target])
            git('add', 'HavenlineGodot/assets/stations_v2')
            self.assertEqual(git('diff', '--cached', '--name-only').stdout.decode().splitlines(), [target])
            self.assertEqual(git('show', ':' + target).stdout, b'glTF-repaired')
            git('commit', '-qm', 'materialized')
            self.assertEqual(git('diff', '--exit-code', check=False).returncode, 0)
            self.assertEqual(git('show', 'HEAD:Assets/TutorialInfo/Icons/URP.png').stdout, files['Assets/TutorialInfo/Icons/URP.png'])
            self.assertEqual(git('diff', 'HEAD^', 'HEAD', '--', '.gitattributes').stdout, b'')


if __name__ == '__main__':
    unittest.main()
