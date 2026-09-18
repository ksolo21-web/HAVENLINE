import copy
import json
import pathlib
import re
import subprocess
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from validate_architecture_v32_t10 import validate
from lib import ROOT

class GovernanceConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow=(ROOT/'.github/workflows/havenline-production-governance.yml').read_text()
        expressions=re.findall(r"jq -e '(.*?)' /tmp/v32-release-lock.json",workflow)
        assert len(expressions)==1
        cls.expression=expressions[0]
        cls.report=validate()
    def accepts(self,report):
        return subprocess.run(['jq','-e',self.expression],input=json.dumps(report),text=True,capture_output=True).returncode==0
    def test_actual_producer_output_passes_actual_consumer(self):
        self.assertTrue(self.report['passed'],self.report['errors'])
        self.assertTrue(self.accepts(self.report))
    def test_hostile_contract_changes_fail(self):
        changes=self.report['authorized_changes']
        for field,value in [('passed',False),('unchanged_locked_files',47),('unchanged_locked_files',46),('unchanged_locked_files',45),('authorized_changes',changes[:-1]),('authorized_changes',changes+['unapproved']),('authorized_changes',list(reversed(changes))),('predecessor_accepted_source','0'*40),('predecessor_manifest_sha256','0'*64)]:
            with self.subTest(field=field,value=value):
                bad=copy.deepcopy(self.report);bad[field]=value
                self.assertFalse(self.accepts(bad))
