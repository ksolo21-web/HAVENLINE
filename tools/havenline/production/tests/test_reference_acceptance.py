from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

PRODUCTION = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRODUCTION))
import reference_acceptance as acceptance
from closure_validator import validate_raw_critic_record
from lib import DOCS, load_json


class ReferenceAcceptanceTests(unittest.TestCase):
    def record(self, score=10, phase="final"):
        return {"scores": {"one": score, "two": score}, "defects": [],
                "coverage_complete": True, "passed": True, "status": "PASS",
                "reference_acceptance": acceptance.acceptance_binding(phase)}

    def test_current_policy_is_valid_and_preserves_stronger_visual_rules(self):
        cfg = load_json(acceptance.POLICY_PATH)
        self.assertEqual([], acceptance.policy_errors(cfg))
        for critic in acceptance.VISUAL_CRITICS:
            with self.subTest(critic=critic):
                self.assertEqual([], acceptance.score_errors({"one": 10}, ["one"], critic))
                self.assertTrue(acceptance.score_errors({"one": 9.99}, ["one"], critic))

    def test_non_reference_floor_is_9_5(self):
        for critic in ("C6", "C7", "C8", "C9", "C10"):
            with self.subTest(critic=critic):
                self.assertEqual([], acceptance.score_errors({"ordinary": 9.5}, ["ordinary"], critic))
                self.assertTrue(acceptance.score_errors({"ordinary": 9.49999}, ["ordinary"], critic))

    def test_reference_floor_is_9_9_and_cannot_round_up(self):
        self.assertEqual([], acceptance.score_errors({"reference_match": 9.9}, ["reference_match"], "C7"))
        for score in (9.5, 9.8, 9.899999999):
            with self.subTest(score=score):
                self.assertTrue(acceptance.score_errors({"reference_match": score}, ["reference_match"], "C7"))

    def test_additional_reference_declaration_can_only_tighten(self):
        args = ({"scenario_match": 9.5}, ["scenario_match"], "C7")
        self.assertEqual([], acceptance.score_errors(*args))
        self.assertTrue(acceptance.score_errors(*args, reference_dimensions=["scenario_match"]))
        self.assertTrue(acceptance.score_errors({"reference_match": 9.5}, ["reference_match"], "C7", reference_dimensions=[]))
        self.assertTrue(acceptance.score_errors(*args, reference_dimensions=["unscored"]))

    def test_one_weak_dimension_cannot_be_hidden_by_an_average(self):
        self.assertTrue(acceptance.score_errors({"one": 10, "two": 9.89}, ["one", "two"], "C3"))
        record = self.record()
        record["reference_acceptance"]["score_averaging_used"] = True
        self.assertTrue(acceptance.record_errors(record, ["one", "two"], "C3"))

    def test_missing_extra_or_duplicate_dimensions_fail(self):
        for scores, dims in (({}, ["one"]), ({"one": 10}, ["one", "two"]),
                             ({"one": 10, "extra": 10}, ["one"]),
                             ({"one": 10}, ["one", "one"]), ({"one": 10}, [])):
            with self.subTest(scores=scores, dims=dims):
                self.assertTrue(acceptance.score_errors(scores, dims, "C3"))

    def test_invalid_numeric_scores_fail_without_exceptions(self):
        for value in (True, False, None, "10", float("nan"), float("inf"), float("-inf"),
                      -1, 10.00001, 10**400, [], {}):
            with self.subTest(type=type(value).__name__):
                self.assertTrue(acceptance.score_errors({"one": value}, ["one"], "C3"))

    def test_high_scores_do_not_hide_missing_evidence_or_defects(self):
        self.assertEqual([], acceptance.record_errors(self.record(), ["one", "two"], "C3"))
        for field, value in (("coverage_complete", None), ("coverage_complete", False),
                             ("defects", None), ("defects", ["visible contact gap"]),
                             ("passed", False), ("status", "BLOCKED")):
            broken = self.record()
            broken[field] = value
            with self.subTest(field=field, value=value):
                self.assertTrue(acceptance.record_errors(broken, ["one", "two"], "C3"))

    def test_current_policy_binding_is_mandatory(self):
        for field, value in (("policy_id", "old"), ("policy_sha256", "0" * 64),
                             ("phase", "interim"), ("scores_unrounded", False),
                             ("scores_unrounded", 1), ("score_averaging_used", 0)):
            record = self.record()
            record["reference_acceptance"][field] = value
            with self.subTest(field=field, value=value):
                self.assertTrue(acceptance.record_errors(record, ["one", "two"], "C3"))
        record = self.record()
        record.pop("reference_acceptance")
        self.assertTrue(acceptance.record_errors(record, ["one", "two"], "C3"))

    def test_interim_9_5_remains_non_approving(self):
        record = self.record(9.5, "interim")
        record["approval_allowed"] = False
        record["status"] = "INTERIM_CHECKPOINT_ONLY"
        self.assertEqual([], acceptance.record_errors(record, ["one", "two"], "C3", phase="interim"))
        self.assertTrue(acceptance.record_errors(record, ["one", "two"], "C3"))
        record["scores"] = {"one": 10, "two": 10}
        self.assertTrue(acceptance.record_errors(record, ["one", "two"], "C3"))

    def test_weaker_or_unavailable_policy_fails_closed(self):
        cfg = load_json(acceptance.POLICY_PATH)
        for field, value in (("minimum_dimension_score", 9), ("reference_minimum_dimension_score", 9.5),
                             ("exact_score", 9.9), ("exact_score_critic_ids", ["C1"]),
                             ("forbid_averaging", False)):
            broken = copy.deepcopy(cfg)
            broken["final_acceptance"][field] = value
            self.assertTrue(acceptance.score_errors({"one": 10}, ["one"], "C3", policy=broken))
        with patch.object(acceptance, "POLICY_PATH", pathlib.Path("/missing/reference-policy.json")):
            self.assertTrue(acceptance.score_errors({"one": 10}, ["one"], "C3"))

    def test_required_critics_add_motion_and_style_without_mutating_history(self):
        original = ["C2", "C6"]
        for task in ("T09", "T16", "T19", "T21", "T23"):
            required = acceptance.required_final_critics(task, original, style_required=True)
            self.assertEqual(["C2", "C6", "C5", "C1"], required)
        self.assertEqual(["C2", "C6"], original)
        self.assertEqual(original, acceptance.required_final_critics("T07", original))
        self.assertEqual(["C1", "C5"], acceptance.required_final_critics("T09", ["C1", "C5"], style_required=True))
        for task in ("T00", "T71", "T80", "T99", None):
            with self.assertRaises(ValueError):
                acceptance.required_final_critics(task, original)

    def test_historical_receipt_requires_exact_bytes_and_never_approves(self):
        cfg = load_json(acceptance.POLICY_PATH)
        candidate = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / "receipt.json"
            original = b'{"historical":true}\n'
            path.write_bytes(original)
            cfg["historical_preservation"] = {"receipts": [{"task_id": "T01", "candidate_sha": candidate,
                "path": "receipt.json", "sha256": hashlib.sha256(original).hexdigest()}]}
            with patch.object(acceptance, "ROOT", root):
                result = acceptance.validate_historical_receipt("T01", candidate, "receipt.json", cfg)
                self.assertTrue(result["passed"])
                self.assertFalse(result["approval_allowed"])
                self.assertEqual("HISTORICAL_RECEIPT_ONLY", result["validation_kind"])
                path.write_bytes(original + b" ")
                self.assertFalse(acceptance.validate_historical_receipt("T01", candidate, "receipt.json", cfg)["passed"])
                path.write_bytes(original)
                self.assertFalse(acceptance.validate_historical_receipt("T01", "b" * 40, "receipt.json", cfg)["passed"])
                self.assertFalse(acceptance.validate_historical_receipt("T01", candidate, "other.json", cfg)["passed"])

    def test_new_review_of_old_candidate_still_requires_current_policy(self):
        raw = load_json(DOCS / "T09/CriticRaw/C2.json")
        args = ("C2", "T09", raw["candidate_commit"], raw["workflow_run_id"], raw["artifact_id"],
                raw["artifact_sha256"], raw["complete_evidence_index_sha256"], raw["scores"], raw["review_export_commit"])
        # Integrity-only historical helper remains available to pinned receipt validation.
        self.assertEqual([], validate_raw_critic_record(raw, *args))
        # The terminal closure always requests this forward path, even for an old SHA.
        self.assertTrue(validate_raw_critic_record(raw, *args, forward=True, expected_dimensions=list(raw["scores"])))
        self.assertNotIn("reference_acceptance", raw)

    def test_forward_raw_receipt_validates_current_threshold_and_binding(self):
        dims=load_json(DOCS/'CRITIC_EXECUTION.json')['critics']['C2']['dimensions']
        raw={'task_id':'T09','critic_id':'C2','candidate_commit':'a'*40,'workflow_run_id':123,'artifact_id':456,
             'artifact_sha256':'f'*64,'complete_evidence_index_sha256':'e'*64,'input_manifest_sha256':'e'*64,
             'scores':{key:10 for key in dims},'minimum_dimension_score':10,'reference_acceptance':acceptance.acceptance_binding(),
             'acceptance_rule':acceptance.final_rule(),'reference_sensitive_dimensions':[],'status':'PASS','passed':True,
             'coverage_complete':True,'defects':[],'confidence':'high','score_reuse':False,'review_export_commit':'b'*40,
             'provider':'unit-test','model':'unit-test','request_or_run_id':'unit-test/not-a-real-review'}
        def check(value):
            args = ("C2", "T09", value["candidate_commit"], value["workflow_run_id"], value["artifact_id"],
                    value["artifact_sha256"], value["complete_evidence_index_sha256"], value["scores"], value["review_export_commit"])
            return validate_raw_critic_record(value, *args, forward=True, expected_dimensions=list(raw["scores"]))
        with tempfile.TemporaryDirectory(dir=acceptance.ROOT) as directory:
            root=pathlib.Path(directory);request=root/'request.json';response=root/'response.json'
            request.write_text(json.dumps({'candidate_commit':raw['candidate_commit'],'input_manifest_sha256':raw['input_manifest_sha256']}))
            response.write_text(json.dumps({key:raw[key] for key in ('scores','coverage_complete','defects','confidence')}))
            raw['review_transport']={'kind':'automated_request_response_v1','request_path':str(request.relative_to(acceptance.ROOT)),
                'request_sha256':hashlib.sha256(request.read_bytes()).hexdigest(),'response_path':str(response.relative_to(acceptance.ROOT)),
                'response_sha256':hashlib.sha256(response.read_bytes()).hexdigest()}
            self.assertEqual([], check(raw))
            broken = copy.deepcopy(raw)
            broken['scores'][next(iter(broken['scores']))] = 9.99
            broken['minimum_dimension_score'] = 9.99
            self.assertTrue(check(broken))

    def test_historical_scope_cannot_be_relabelled_with_current_policy(self):
        for extra in ({'review_scope':'historical'},{'validation_kind':'HISTORICAL_RECEIPT_ONLY'},
                      {'historical_only':True},{'approval_allowed':False}):
            record={**self.record(),**extra}
            self.assertTrue(acceptance.binding_errors(record))

    def test_final_dispositions_require_explicit_pass_and_strict_booleans(self):
        for field,value in [('status','PENDING'),('status','fail'),('status','UNKNOWN'),('status',None),
                            ('passed',0),('passed',None),('passed','false'),('approval_allowed',0),
                            ('approval_allowed',None),('approval_allowed','true')]:
            record={**self.record(),field:value}
            with self.subTest(field=field,value=value):
                self.assertTrue(acceptance.record_errors(record,['one','two'],'C2'))
        for field in ('status','passed'):
            record=self.record();record.pop(field)
            self.assertTrue(acceptance.record_errors(record,['one','two'],'C2'))
        bare={'scores':{'one':10},'defects':[],'coverage_complete':True}
        self.assertEqual([],acceptance.record_errors(bare,['one'],'C2',require_binding=False))

    def test_strict_forward_json_rejects_duplicate_keys_and_constants(self):
        for body in ('{"score":7,"score":10}','{"scores":{"one":7,"one":10}}',
                     '{"score":NaN}','{"score":Infinity}','{"score":-Infinity}'):
            with self.subTest(body=body),self.assertRaises(ValueError):acceptance.strict_json_loads(body)
        self.assertEqual({'one':9.9},acceptance.strict_json_loads('{"one":9.9}'))


if __name__ == "__main__":
    unittest.main()
