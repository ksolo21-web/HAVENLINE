import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from asset_gate import run, get_file, parse_glb

POLICY=pathlib.Path(__file__).resolve().parents[4]/"Docs/Production/GLOBAL_ASSET_AUTHORING_POLICY.json"
TEMPLATE=ROOT/"examples/T05-cooker-asset.json"

class AssetGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads(POLICY.read_text())
        cls.manifest=json.loads(TEMPLATE.read_text())
    def test_global_policy_scope(self):
        self.assertEqual(self.policy["scope"],"ALL_GAME_ART_ACROSS_ALL_TASKS_AND_FUTURE_BIOMES")
        self.assertEqual(self.policy["exact_style_scores"]["reference_fidelity"],10)
    def test_source_lint_is_not_approval(self):
        with tempfile.TemporaryDirectory() as workspace:
            result=run(self.manifest,self.policy,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"SOURCE_LINT_PASS_NOT_ASSET_APPROVAL")
        self.assertFalse(result["asset_released"])
    def test_incomplete_candidate_fails_closed(self):
        with tempfile.TemporaryDirectory() as workspace:
            result=run(self.manifest,self.policy,pathlib.Path(workspace),"candidate")
        self.assertEqual(result["result"],"FAIL")
        self.assertFalse(result["asset_released"])
        self.assertIn("owner_reference_pixels_sha256",[x["check"] for x in result["checks"] if not x["pass"]])
    def test_reference_style_cannot_be_lowered(self):
        p=copy.deepcopy(self.policy)
        p["exact_style_scores"]["reference_fidelity"]=9.5
        with tempfile.TemporaryDirectory() as workspace:
            result=run(self.manifest,p,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"FAIL")
    def test_exact_reference_mandatory(self):
        m=copy.deepcopy(self.manifest)
        m["owner_reference"]["binding"]="family_board"
        with tempfile.TemporaryDirectory() as workspace:
            result=run(m,self.policy,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"FAIL")
    def test_missing_limits_fails_closed(self):
        m=copy.deepcopy(self.manifest)
        del m["limits"]["texture_mib_max"]
        with tempfile.TemporaryDirectory() as workspace:
            result=run(m,self.policy,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"FAIL")
    def test_no_path_traversal(self):
        with tempfile.TemporaryDirectory() as workspace:
            with self.assertRaises(ValueError):get_file(pathlib.Path(workspace),"../other.png")
            with self.assertRaises(ValueError):get_file(pathlib.Path(workspace),"/tmp/secret")
    def test_invalid_glb_refused(self):
        with tempfile.TemporaryDirectory() as workspace:
            path=pathlib.Path(workspace)/"broken.glb"
            path.write_bytes(b"no glb")
            with self.assertRaises(ValueError):parse_glb(path)
    def test_release_never_inferred_from_technical_lint(self):
        with tempfile.TemporaryDirectory() as workspace:
            result=run(self.manifest,self.policy,pathlib.Path(workspace),"release")
        self.assertEqual(result["result"],"FAIL")
        self.assertFalse(result["asset_released"])
    def test_lint_game_wide_future_biome(self):
        m=copy.deepcopy(self.manifest)
        m["asset_id"]="volcanic_region_shelter"
        m["task_id"]="T84"
        with tempfile.TemporaryDirectory() as workspace:
            result=run(m,self.policy,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"SOURCE_LINT_PASS_NOT_ASSET_APPROVAL")

if __name__=="__main__":unittest.main()
