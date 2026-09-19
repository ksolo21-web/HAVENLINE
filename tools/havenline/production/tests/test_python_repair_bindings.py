"""Exercise canonical source admission with real Git objects, never candidate imports."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify_python_repair_bindings as verifier


class CanonicalPythonBindingGitTests(unittest.TestCase):
    causal = "tools/havenline/production/candidate_advisor.py"
    record_path = "Docs/Production/ChangeRequests/T10-repeated-python-source-review.json"
    plan_path = "Docs/Production/T10/REPAIR_PLAN.json"
    c0_path = "Docs/Production/T10/C0_ROOT_CAUSE.json"
    report_path = "Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json"

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Binding Test")
        self.git("config", "user.email", "binding-test@example.invalid")
        self.git("config", "core.filemode", "true")
        self.write(verifier.SELF_PATH, Path(verifier.__file__).read_bytes())
        self.before = "VALUE = 'base'\n"
        self.marker = self.repo / "CANDIDATE_CODE_EXECUTED"
        # Valid reviewed source would leave evidence and raise if imported or run.
        self.after = ("from pathlib import Path\n"
                      f"Path({str(self.marker)!r}).write_text('executed')\n"
                      "raise RuntimeError('candidate source must never execute')\n")
        self.c0 = {"task_id": "T10", "diagnosis_id": "TEST-DIAG"}
        c0_bytes = self.json_bytes(self.c0)
        self.write(self.c0_path, c0_bytes)
        self.write(self.causal, self.before)
        self.base = self.commit("base with canonical verifier and advisor")
        self.git("switch", "-q", "-c", "reviewed")
        self.write(self.causal, self.after)
        self.inherited = [
            "Docs/Production/ChangeRequests/T10-benchmark-liveness-contract.json",
            "Docs/Production/ChangeRequests/T10-c0-decoded-complete-evidence.json",
            "Docs/Production/ChangeRequests/T10-c0r-structured-mechanism-detection.json",
            self.record_path,
        ]
        self.plan = {
            "task_id": "T10", "diagnosis_id": "TEST-DIAG",
            "c0_report_sha256": self.digest(c0_bytes),
            "reconciled_integration_head": self.base,
            "inherited_noncausal_files": [],
            "fixes": [{"files": [self.causal] + self.inherited}],
            "repair_sufficiency": {"repair_groups": [{
                "group_id": "python-family", "same_family_attempt_count": 2,
                "failure_family": {"id": "source-binding"},
                "implementation_diff_contract": {
                    "comparison_base": self.base, "causal_files": [self.causal],
                    "required_operations": ["verify canonical bytes before execution"]
                }
            }]}
        }
        self.write(self.plan_path, self.json_bytes(self.plan))
        self.c0r = {"decision": "REPAIR_PLAN_ACCEPTED", "input_bindings": {
            "plan_sha256": self.digest(self.json_bytes(self.plan)),
            "c0_sha256": self.digest(c0_bytes)}}
        self.write(self.report_path, self.json_bytes(self.c0r))
        self.reviewed = self.commit("independently reviewed source and frozen metadata")
        self.reviewed_tree = self.git("rev-parse", self.reviewed + "^{tree}")
        self.git("switch", "-q", "-c", "canonical", self.base)
        binding = verifier.repeated_python_bindings(self.plan)[0]
        binding.update(before_sha256=self.digest(self.before.encode()),
                       after_sha256=self.digest(self.after.encode()),
                       before_mode="100644", after_mode="100644")
        self.review = {
            "schema_version": 1, "task_id": "T10", "diagnosis_id": "TEST-DIAG",
            "decision": "ACCEPTED_BOUNDED_SOURCE", "non_voting": True,
            "task_approved": False, "thresholds_unchanged": True,
            "runtime_model_contracts_unchanged": True,
            "c0_sha256": self.digest(c0_bytes),
            "canonical_inherited_paths": self.inherited,
            "independent_review": {
                "reviewer": "fixture-independent-reviewer", "review_id": "fixture-review-1",
                "reviewed_commit": self.reviewed, "reviewed_tree": self.reviewed_tree,
                "evidence_sha256": "a" * 64
            },
            "bindings": [binding],
            "causal_source_set_sha256": verifier._stable_digest([binding])
        }
        for path in self.inherited[:-1]:
            self.write(path, self.json_bytes({"owner_authorized": True, "path": path}))
        self.write(self.record_path, self.json_bytes(self.review))
        self.canonical = self.commit("owner publishes bounded source review")
        self.pin()
        self.git("switch", "-q", "-c", "candidate", self.reviewed)
        self.git("merge", "--no-ff", "-m", "candidate reconciles canonical review", self.canonical)
        self.reconcile_metadata()
        self.head = self.commit("candidate metadata after reviewed source and canonical merge")

    def git(self, *args, input=None):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], input=input,
            stderr=subprocess.PIPE, env=dict(os.environ, GIT_CONFIG_NOSYSTEM="1")
        ).decode().strip()

    @staticmethod
    def digest(data):
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def json_bytes(value):
        return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()

    def write(self, relative, data):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode() if isinstance(data, str) else data)

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def pin(self):
        self.git("update-ref", "refs/remotes/origin/" + verifier.PINNED_BRANCH, self.canonical)

    def reconcile_metadata(self):
        self.plan["reconciled_integration_head"] = self.canonical
        self.plan["inherited_noncausal_files"] = self.inherited.copy()
        for fix in self.plan["fixes"]:
            fix["files"] = [path for path in fix["files"] if path not in self.inherited]
        raw = self.json_bytes(self.plan)
        self.write(self.plan_path, raw)
        self.c0r["input_bindings"]["plan_sha256"] = self.digest(raw)
        self.write(self.report_path, self.json_bytes(self.c0r))

    def verify(self):
        return verifier.verify_candidate(self.repo, self.canonical, self.head, "T10")

    def reject(self, fragment):
        report = self.verify()
        self.assertFalse(report["passed"], report)
        self.assertIn(fragment, "\n".join(report["errors"]), report)
        self.assertFalse(self.marker.exists())
        return report

    def test_real_reviewed_merge_and_metadata_head_pass_without_executing_candidate(self):
        report = self.verify()
        self.assertTrue(report["passed"], report)
        self.assertEqual([], report["errors"])
        self.assertEqual(self.head, report["candidate_commit"])
        self.assertEqual(self.reviewed_tree, self.git("rev-parse", self.reviewed + "^{tree}"))
        self.assertEqual(self.digest(self.after.encode()), report["sources"][0]["candidate"]["sha256"])
        self.assertFalse(self.marker.exists())
        self.assertFalse(report["task_approved"])

    def test_candidate_source_mutation_is_rejected(self):
        self.write(self.causal, self.after + "# unreviewed mutation\n")
        self.head = self.commit("change reviewed source bytes")
        self.reject("source mode or reviewed blob mismatch")

    def test_candidate_executable_mode_mutation_is_rejected(self):
        (self.repo / self.causal).chmod(0o755)
        self.head = self.commit("change reviewed source mode")
        self.reject("source mode or reviewed blob mismatch")

    def test_candidate_symlink_is_rejected_without_following_target(self):
        path = self.repo / self.causal
        path.unlink()
        path.symlink_to(self.marker)
        self.head = self.commit("replace source with symlink")
        self.reject("nonregular source blob")

    def test_stale_pinned_branch_is_rejected(self):
        self.git("update-ref", "refs/remotes/origin/" + verifier.PINNED_BRANCH, self.base)
        self.reject("canonical head differs from fetched pinned branch")

    def test_candidate_authorization_record_substitution_is_rejected(self):
        substituted = copy.deepcopy(self.review)
        substituted["independent_review"]["review_id"] = "candidate-self-authorization"
        self.write(self.record_path, self.json_bytes(substituted))
        self.head = self.commit("substitute canonical review")
        self.reject("candidate record differs from canonical authority")

    def test_candidate_verifier_substitution_is_rejected_not_executed(self):
        self.write(verifier.SELF_PATH, self.after)
        self.head = self.commit("replace verifier with candidate code")
        self.reject("candidate verifier differs from canonical bytes")

    def test_group_semantic_mutation_is_rejected(self):
        self.plan["repair_sufficiency"]["repair_groups"][0]["failure_family"]["id"] = "different-family"
        self.write(self.plan_path, self.json_bytes(self.plan))
        self.head = self.commit("mutate group meaning")
        self.reject("Python source review contract mismatch")

    def test_operation_contract_mutation_is_rejected(self):
        self.plan["repair_sufficiency"]["repair_groups"][0]["implementation_diff_contract"]["required_operations"] = ["different operation"]
        self.write(self.plan_path, self.json_bytes(self.plan))
        self.head = self.commit("mutate reviewed operation contract")
        self.reject("operation_contract_sha256")

    def test_dropping_repeated_family_does_not_erase_authoritative_bindings(self):
        self.plan["repair_sufficiency"]["repair_groups"] = []
        self.write(self.plan_path, self.json_bytes(self.plan))
        self.head = self.commit("drop family from plan")
        self.reject("exact causal file set mismatch")

    def test_c0_bytes_remain_authority_bound(self):
        self.c0["candidate_added_claim"] = True
        self.write(self.c0_path, self.json_bytes(self.c0))
        self.head = self.commit("mutate authoritative diagnosis")
        self.reject("authoritative C0 source binding mismatch")

    def test_matching_reviewed_tree_without_reviewed_ancestry_is_rejected(self):
        # A real unrelated commit has identical reviewed tree/blob bytes. It must
        # still fail: matching content is not proof this review is in ancestry.
        unrelated = self.git("commit-tree", self.reviewed_tree, "-m", "unrelated reviewed history")
        self.git("switch", "-q", "canonical")
        self.review["independent_review"]["reviewed_commit"] = unrelated
        self.write(self.record_path, self.json_bytes(self.review))
        self.canonical = self.commit("owner record refers to unrelated reviewed commit")
        self.pin()
        self.git("switch", "-q", "candidate")
        self.git("merge", "--no-ff", "-m", "consume owner record", self.canonical)
        self.reconcile_metadata()
        self.head = self.commit("reconcile metadata to new owner head")
        self.assertNotEqual(0, subprocess.run(
            ["git", "-C", str(self.repo), "merge-base", "--is-ancestor", unrelated, self.head],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode)
        self.reject("canonical source verification failed")

    def test_unreviewed_workflow_change_is_rejected(self):
        self.write(".github/workflows/candidate.yml", "name: unreviewed\n")
        self.head = self.commit("add unreviewed workflow")
        self.reject("unreviewed post-freeze path change")

    def test_unbound_python_change_is_rejected(self):
        self.write("tools/havenline/production/unbound.py", self.after)
        self.head = self.commit("add unbound executable candidate source")
        self.reject("unreviewed post-freeze path change")

    def test_c0r_change_beyond_plan_hash_is_rejected(self):
        self.c0r["decision"] = "candidate-forged-decision"
        self.write(self.report_path, self.json_bytes(self.c0r))
        self.head = self.commit("change C0R beyond allowed hash reconciliation")
        self.reject("post-review C0R report exceeds")

    def test_hostile_git_environment_cannot_redirect_repository(self):
        with patch.dict(os.environ, {"GIT_DIR": str(self.repo / "nonexistent-git-dir"),
                                     "GIT_WORK_TREE": str(self.repo / "nonexistent-worktree"),
                                     "GIT_CONFIG_COUNT": "1",
                                     "GIT_CONFIG_KEY_0": "alias.show",
                                     "GIT_CONFIG_VALUE_0": "!false"}):
            report = self.verify()
        self.assertTrue(report["passed"], report)
        self.assertFalse(self.marker.exists())

    def test_duplicate_causal_path_across_groups_is_rejected(self):
        group = copy.deepcopy(self.plan["repair_sufficiency"]["repair_groups"][0])
        group["group_id"] = "same-path-different-group"
        self.plan["repair_sufficiency"]["repair_groups"].append(group)
        self.write(self.plan_path, self.json_bytes(self.plan))
        self.head = self.commit("duplicate causal path across groups")
        self.reject("exact causal file set mismatch")
        # Even a record with both group/path keys and valid source hashes must
        # reject the same physical source being authorized twice.
        duplicate_review = copy.deepcopy(self.review)
        bindings = verifier.repeated_python_bindings(self.plan)
        for binding in bindings:
            binding.update(before_sha256=self.digest(self.before.encode()),
                           after_sha256=self.digest(self.after.encode()),
                           before_mode="100644", after_mode="100644")
        duplicate_review["bindings"] = bindings
        duplicate_review["causal_source_set_sha256"] = verifier._stable_digest(bindings)
        errors = verifier.python_source_review_errors(
            self.plan, duplicate_review,
            {self.causal: self.git("show", self.base + ":" + self.causal) + "\n"},
            {self.causal: self.git("show", self.reviewed + ":" + self.causal) + "\n"})
        self.assertIn("Python source review exact causal file set mismatch", errors)


if __name__ == "__main__":
    unittest.main()
