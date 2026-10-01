"""Execute every workflow's builder-call boundary with isolated external stubs."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[4]
BRANCH = 'codex/havenline-sequential-task-01'
INTEGRATION = 'a' * 40
CANDIDATE = 'b' * 40
CALL = re.compile(r'python3\s+tools/havenline/production/builder_repair_gate\.py\s')


class BuilderWorkflowCallersTests(unittest.TestCase):
    def callers(self):
        found = []
        for path in sorted((ROOT / '.github/workflows').glob('*.yml')):
            workflow = yaml.safe_load(path.read_text())
            for job in workflow.get('jobs', {}).values():
                for index, step in enumerate(job.get('steps', [])):
                    if CALL.search(step.get('run', '')):
                        found.append((path.name, workflow, job, index))
        self.assertGreaterEqual(len(found), 4)
        return found

    def replay(self, caller, repair_base, mutation=None, ancestry=True):
        name, workflow, job, index = caller
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / 'Docs/Production/T10'
            docs.mkdir(parents=True)
            for filename in ('C0_ROOT_CAUSE.json', 'REPAIR_PLAN.json'):
                shutil.copyfile(ROOT / 'Docs/Production/T10' / filename, docs / filename)
            plan = json.loads((docs / 'REPAIR_PLAN.json').read_text())
            plan['repair_base'] = repair_base
            (docs / 'REPAIR_PLAN.json').write_text(json.dumps(plan))
            shutil.copyfile(ROOT / 'Docs/Production/WORKSTREAM_REGISTRY.json', docs.parent / 'WORKSTREAM_REGISTRY.json')
            bin_path = root / 'bin'
            bin_path.mkdir()
            # Inline Python is the actual workflow code. Only heavyweight script
            # commands are replaced; the builder boundary records real argv/env.
            python_stub = '''#!REALPY
import json,os,sys
from pathlib import Path
args=sys.argv[1:]
if args and args[0].endswith('/builder_repair_gate.py'):
    Path('boundary.json').write_text(json.dumps({'argv':args,'env':dict(os.environ)}))
    raise SystemExit(0)
if args and (args[0] in ('-', '-c') or not args[0].startswith(('tools/', '-m'))):
    os.execv('REALPY',['REALPY',*args])
'''.replace('REALPY', sys.executable)
            git_stub = '''#!REALPY
import json,os,sys
from pathlib import Path
a=sys.argv[1:]
with open('git-calls.jsonl','a') as f:f.write(json.dumps(a)+'\\n')
if a[0]=='ls-remote':
    assert a[-1]=='refs/heads/BRANCH'
    print('INTEGRATION refs/heads/BRANCH')
elif a[0]=='fetch':
    assert a[-1]=='BRANCH'
    Path('fetched').write_text('INTEGRATION')
elif a[0]=='rev-parse':
    assert Path('fetched').read_text()=='INTEGRATION'
    assert a[-1] in ('FETCH_HEAD','origin/BRANCH')
    print('INTEGRATION')
elif a[0]=='merge-base':
    raise SystemExit(0 if os.environ['ANCESTRY']=='yes' else 1)
elif a[0]=='diff':raise SystemExit(1)
else:raise SystemExit('unexpected git call '+repr(a))
'''.replace('REALPY', sys.executable).replace('BRANCH', BRANCH).replace('INTEGRATION', INTEGRATION)
            for filename, content in [('python3', python_stub), ('python', python_stub), ('git', git_stub)]:
                path = bin_path / filename
                path.write_text(content)
                path.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if k not in ('INTEGRATION_BRANCH', 'INTEGRATION_HEAD', 'TASK', 'BASE')}
            env.update(PATH=str(bin_path) + os.pathsep + env['PATH'], GITHUB_SHA=CANDIDATE,
                       GITHUB_HEAD_REF='havenline/T10-layout-solver-repair', GITHUB_REF_NAME='havenline/T10-layout-solver-repair',
                       GITHUB_ENV=str(root / 'github-env'), ANCESTRY='yes' if ancestry else 'no')
            env.update(workflow.get('env', {}))
            env.update(job.get('env', {}))
            result = None
            for step in job['steps'][:index + 1]:
                if 'run' not in step:
                    continue
                step_env = dict(env, **step.get('env', {}))
                script = step['run']
                # Stop at the recorded boundary: no nested tests or unrelated
                # steps after the builder invocation are part of this harness.
                if CALL.search(script):
                    lines = script.splitlines()
                    start = next(i for i, line in enumerate(lines) if CALL.search(line))
                    end = start
                    while lines[end].rstrip().endswith('\\'):
                        end += 1
                    script = '\n'.join(lines[:end + 1])
                    if mutation:
                        script, step_env = mutation(script, step_env)
                result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script], cwd=root, env=step_env, text=True, capture_output=True)
                if result.returncode:
                    break
                if (root / 'github-env').exists():
                    for line in (root / 'github-env').read_text().splitlines():
                        key, value = line.split('=', 1)
                        env[key] = value
            boundary = json.loads((root / 'boundary.json').read_text()) if (root / 'boundary.json').exists() else None
            return result, boundary

    def test_every_actual_caller_supplies_source_bound_authority_and_plan_base(self):
        for caller in self.callers():
            for base in ('c' * 40, 'd' * 40):
                with self.subTest(workflow=caller[0], base=base):
                    result, boundary = self.replay(caller, base)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIsNotNone(boundary)
                    self.assertEqual(boundary['env'].get('INTEGRATION_BRANCH'), BRANCH)
                    self.assertEqual(boundary['env'].get('INTEGRATION_HEAD'), INTEGRATION)
                    args = boundary['argv']
                    for flag, expected in [('--base', base), ('--c0', 'Docs/Production/T10/C0_ROOT_CAUSE.json'),
                                           ('--plan', 'Docs/Production/T10/REPAIR_PLAN.json')]:
                        self.assertEqual(args[args.index(flag) + 1], expected)
                    self.assertIn(args[args.index('--head') + 1], ('HEAD', CANDIDATE))

    def test_real_callee_rejects_missing_or_redirected_authority(self):
        sys.path.insert(0, str(ROOT / 'tools/havenline/production'))
        from builder_repair_gate import verify_integration_branch, verify_inherited_noncausal
        plan = json.loads((ROOT / 'Docs/Production/T10/REPAIR_PLAN.json').read_text())
        for branch in (None, '', 'candidate-controlled'):
            self.assertTrue(verify_integration_branch(branch))
        for head in (None, '', 'f' * 40):
            self.assertTrue(verify_inherited_noncausal(plan, 'HEAD', head))

    def test_shared_guard_preserves_malformed_base_and_ancestry_rejection(self):
        caller = next(row for row in self.callers() if row[0] == 'havenline-candidate-guard.yml')
        for base, ancestry in [('short', True), ('c' * 40, False)]:
            result, boundary = self.replay(caller, base, ancestry=ancestry)
            self.assertNotEqual(result.returncode, 0)
            self.assertIsNone(boundary)
