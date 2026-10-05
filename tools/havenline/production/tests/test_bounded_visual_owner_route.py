import json
import subprocess
import tempfile
import shutil
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import workstream


class BoundedOwnerRouteTests(unittest.TestCase):
    foreign = "HavenlineGodot/scripts/camp_boundary_view.gd"
    request = {"requesting_task": "T05", "status": "AUTHORIZED",
               "integration_owner_disposition": "APPROVED_BOUNDED_REFERENCE_BOUNDARY",
               "target_path": [foreign]}

    def errors(self, paths, authorized=None, integration="trusted", ancestor=True):
        with patch.object(workstream.subprocess, "run", return_value=SimpleNamespace(returncode=0 if ancestor else 1)), patch.object(workstream, "approved_change_requests", return_value=set(authorized or [])) as read:
            errors = workstream.visual_repair_path_errors("T05", paths, ["Docs/Production/T05/**"], integration)
            if integration and ancestor:
                read.assert_called_once_with("T05", integration)
            else:
                read.assert_not_called()
            return errors

    def test_owned_and_exact_owner_target_pass(self):
        self.assertEqual(self.errors([self.foreign, "Docs/Production/T05/proof.json"], [self.foreign]), [])

    def test_arbitrary_foreign_path_is_rejected(self):
        self.assertTrue(self.errors(["HavenlineGodot/scripts/main.gd"], [self.foreign]))

    def test_no_trusted_head_is_rejected(self):
        self.assertTrue(self.errors([self.foreign], [self.foreign], integration=None))

    def test_nonancestor_is_rejected(self):
        self.assertTrue(self.errors([self.foreign], [self.foreign], ancestor=False))

    def test_forbidden_control_plane_even_if_listed(self):
        for path in workstream.VISUAL_REPAIR_FORBIDDEN | {"Docs/Production/ChangeRequests/self-approval.json"}:
            with self.subTest(path=path):
                self.assertTrue(self.errors([path], [path]))

    def test_traversal_and_noncanonical_changed_paths_rejected(self):
        for path in ["../main.gd", "/main.gd", "a//b", "a/./b", "a\\b", "a/*"]:
            with self.subTest(path=path):
                self.assertTrue(self.errors([path], [path]))

    def test_request_schema_is_exact_and_fail_closed(self):
        self.assertEqual(workstream.authorized_change_request_targets(self.request, "T05"), {self.foreign})
        variants = [{"requesting_task":"T03"}, {"status":"REQUESTED"}, {"integration_owner_disposition":"AUTHORIZED"},
                    {"target_path":[self.foreign,self.foreign]}, {"target_path":["HavenlineGodot/**"]},
                    {"target_path":["../main.gd"]}, {"target_path":["/main.gd"]}, {"target_path":[]}]
        for change in variants:
            with self.subTest(change=change):
                self.assertEqual(workstream.authorized_change_request_targets(dict(self.request, **change), "T05"), set())

    def test_candidate_local_request_does_not_grant_authority(self):
        with patch.object(workstream.subprocess, "check_output", return_value="" ) as read:
            self.assertEqual(workstream.approved_change_requests("T05", "trusted"), set())
            self.assertEqual(read.call_args.args[0][4], "trusted")

    def test_request_reads_are_bound_to_trusted_git_ref(self):
        path="Docs/Production/ChangeRequests/owner.json"
        def read(args, **kwargs):
            if args[1] == "ls-tree":
                self.assertIn("trusted", args)
                return path+"\n"
            self.assertEqual(args, ["git","show","trusted:"+path])
            return json.dumps(self.request)
        with patch.object(workstream.subprocess, "check_output", side_effect=read):
            self.assertEqual(workstream.approved_change_requests("T05", "trusted"), {self.foreign})

    def test_tampered_candidate_helper_cannot_approve_its_own_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)/'candidate';repo.mkdir()
            production=repo/'tools/havenline/production'
            shutil.copytree(Path(workstream.__file__).parent,production,ignore=shutil.ignore_patterns('__pycache__'))
            def git(*args):
                return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL,text=True).strip()
            git('init');git('config','user.name','Route test');git('config','user.email','test@example.invalid')
            git('add','tools');git('commit','-m','Trusted validator');trusted=git('rev-parse','HEAD')
            (production/'workstream.py').write_text('def visual_repair_path_errors(*args):return []\n')
            git('add','tools');git('commit','-m','Malicious candidate helper')
            workflow=(Path(__file__).resolve().parents[4]/'.github/workflows/havenline-candidate-guard.yml').read_text()
            start=workflow.index('          import io,tarfile,tempfile')
            end=workflow.index('          errors=visual_repair_path_errors',start)
            loader='\n'.join(line[10:]for line in workflow[start:end].splitlines())
            script='import os,subprocess,sys\nintegration='+repr(trusted)+'\n'+loader+'\nerrors=visual_repair_path_errors("T05",["tools/havenline/production/workstream.py"],[],integration)\nassert errors, "Candidate helper self-approved"\nprint("TRUSTED_REJECTION")\n'
            result=subprocess.check_output([sys.executable,'-c',script],cwd=repo,text=True)
            self.assertIn('TRUSTED_REJECTION',result)


if __name__ == "__main__":
    unittest.main()
