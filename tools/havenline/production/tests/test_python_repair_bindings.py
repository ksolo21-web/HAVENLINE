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
        self.origin_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.origin_directory.cleanup)
        self.origin = Path(self.origin_directory.name)
        subprocess.check_output(["git", "init", "--bare", "-q", str(self.origin)],
                                stderr=subprocess.PIPE)
        self.git("remote", "add", "origin", str(self.origin))
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
        self.git("push", "--force", "origin",
                 self.canonical + ":refs/heads/" + verifier.PINNED_BRANCH)
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

    def promote_candidate(self):
        """Advance the real canonical ref; retain the frozen plan's authority H."""
        authority = self.plan["reconciled_integration_head"]
        self.canonical = self.head
        self.pin()
        self.assertEqual(authority, json.loads(self.git("show", self.head + ":" + self.plan_path))[
            "reconciled_integration_head"])
        return authority

    def assert_rejected(self):
        report = self.verify()
        self.assertFalse(report["passed"], report)
        self.assertTrue(report["errors"], report)
        self.assertFalse(self.marker.exists())
        return report

    def test_isolated_authority_equals_active_head_before_candidate(self):
        report = self.verify()
        self.assertTrue(report["passed"], report)
        self.assertEqual(self.canonical, report["authority_head"])
        self.assertEqual("ISOLATED_REPAIR", report["execution_mode"])
        self.assertNotEqual(self.head, self.canonical)

    def test_integrated_exact_tip_retains_historical_authority_without_plan_rewrite(self):
        frozen_plan = self.git("show", self.head + ":" + self.plan_path)
        authority = self.promote_candidate()
        report = self.verify()
        self.assertTrue(report["passed"], report)
        self.assertEqual(authority, report["authority_head"])
        self.assertEqual(self.head, report["canonical_head"])
        self.assertEqual("INTEGRATED_REPAIR", report["execution_mode"])
        self.assertEqual(frozen_plan, self.git("show", self.head + ":" + self.plan_path))
        self.assertFalse(self.marker.exists())

    def test_stale_isolated_snapshot_rejected_even_when_active_is_candidate_ancestor(self):
        # H < A < C is stale, although the old ancestry-only check succeeds.
        self.git("switch", "-q", "canonical")
        self.git("commit", "--allow-empty", "-q", "-m", "owner advances canonical")
        self.canonical = self.git("rev-parse", "HEAD")
        self.pin()
        self.git("switch", "-q", "candidate")
        self.git("merge", "--no-ff", "-m", "candidate consumes advance but keeps old plan", self.canonical)
        self.head = self.git("rev-parse", "HEAD")
        self.git("merge-base", "--is-ancestor", self.canonical, self.head)
        self.assert_rejected()

    def test_integrated_candidate_ancestor_of_active_is_not_exact_active_tip(self):
        self.promote_candidate()
        self.git("commit", "--allow-empty", "-q", "-m", "owner advances beyond reviewed candidate")
        self.canonical = self.git("rev-parse", "HEAD")
        self.pin()
        self.git("merge-base", "--is-ancestor", self.head, self.canonical)
        self.assert_rejected()

    def test_missing_or_nonancestor_historical_authority_is_rejected(self):
        original_head = self.head
        original_authority = self.canonical
        unrelated = self.git("commit-tree", self.git("rev-parse", self.canonical + "^{tree}"),
                             "-m", "same authority bytes without ancestry")
        for snapshot in ("f" * 40, unrelated, "HEAD"):
            with self.subTest(snapshot=snapshot):
                self.git("reset", "--hard", original_head)
                self.canonical = original_authority
                self.plan["reconciled_integration_head"] = snapshot
                self.write(self.plan_path, self.json_bytes(self.plan))
                self.c0r["input_bindings"]["plan_sha256"] = self.digest(self.json_bytes(self.plan))
                self.write(self.report_path, self.json_bytes(self.c0r))
                self.head = self.commit("candidate substitutes authority snapshot")
                self.promote_candidate()
                self.assert_rejected()

    def test_authority_snapshot_itself_cannot_self_authorize_as_candidate(self):
        # A full SHA cannot be embedded in its own commit. Exercise the real
        # equal-tip snapshot object instead: it contains authorization, not the
        # later reviewed candidate and its reconciled plan.
        self.head = self.canonical
        self.assert_rejected()

    def test_equal_self_snapshot_context_is_rejected_before_ancestry(self):
        # Exercise the equality contract directly: constructing a commit that
        # embeds its own full SHA is not a realizable Git fixture.
        mode, errors = verifier.authority_context(
            {"reconciled_integration_head": self.head}, self.head, self.head,
            lambda *_: self.fail("self-authorization must fail before ancestry"))
        self.assertIsNone(mode)
        self.assertIn("authority snapshot cannot authorize itself as repair candidate", errors)

    def test_record_verifier_and_inherited_metadata_drift_in_both_contexts(self):
        original_head = self.head
        authority = self.canonical
        paths = (self.record_path, verifier.SELF_PATH, self.inherited[0])
        for integrated in (False, True):
            for path in paths:
                for mutation in ("bytes", "mode"):
                    with self.subTest(integrated=integrated, path=path, mutation=mutation):
                        self.git("reset", "--hard", original_head)
                        self.canonical = authority
                        self.pin()
                        target = self.repo / path
                        if mutation == "mode":
                            target.chmod(0o755)
                        elif path.endswith(".json"):
                            value = json.loads(target.read_text())
                            value["unreviewed_candidate_change"] = True
                            self.write(path, self.json_bytes(value))
                        else:
                            self.write(path, self.after)
                        self.head = self.commit("mutate authority-bound file " + mutation)
                        if integrated:
                            self.promote_candidate()
                        self.assert_rejected()

    def test_integrated_unreviewed_source_and_workflow_deltas_are_rejected(self):
        original_head = self.head
        authority = self.canonical
        for path, content in ((self.causal, self.after + "# mutation\n"),
                              ("tools/havenline/production/unbound.py", self.after),
                              (".github/workflows/candidate.yml", "name: unreviewed\n")):
            with self.subTest(path=path):
                self.git("reset", "--hard", original_head)
                self.canonical = authority
                self.write(path, content)
                self.head = self.commit("integrated unreviewed delta")
                self.promote_candidate()
                self.assert_rejected()

    def test_remote_ref_advance_during_verification_rejects_both_contexts(self):
        isolated_active = self.canonical
        for integrated in (False, True):
            with self.subTest(integrated=integrated):
                self.canonical = isolated_active
                self.pin()
                if integrated:
                    self.promote_candidate()
                advanced = self.git("commit-tree", self.git("rev-parse", self.canonical + "^{tree}"),
                                    "-p", self.canonical, "-m", "concurrent canonical advance")
                real_check_output = subprocess.check_output
                changed = []
                ref = "refs/remotes/origin/" + verifier.PINNED_BRANCH

                def advance_after_first_read(command, *args, **kwargs):
                    result = real_check_output(command, *args, **kwargs)
                    if command[-2:] == ["rev-parse", ref] and not changed:
                        real_check_output(["git", "-C", str(self.repo), "update-ref", ref, advanced])
                        changed.append(True)
                    return result

                with patch.object(verifier.subprocess, "check_output", side_effect=advance_after_first_read):
                    self.assert_rejected()
                self.assertEqual([True], changed)

    def test_bare_origin_advance_rejects_with_unchanged_local_tracking_in_both_contexts(self):
        isolated_active = self.canonical
        for integrated in (False, True):
            with self.subTest(integrated=integrated):
                self.canonical = isolated_active
                self.pin()
                if integrated:
                    self.promote_candidate()
                advanced = self.git("commit-tree", self.git("rev-parse", self.canonical + "^{tree}"),
                                    "-p", self.canonical, "-m", "real origin advances")
                # Transfer the new object without updating the pinned branch or
                # its local tracking ref. The later concurrent update is remote-only.
                self.git("push", "--force", "origin", advanced + ":refs/heads/race-staging")
                real_check_output = subprocess.check_output
                changed = []
                tracking = "refs/remotes/origin/" + verifier.PINNED_BRANCH
                remote_ref = "refs/heads/" + verifier.PINNED_BRANCH

                def advance_origin_after_first_tracking_read(command, *args, **kwargs):
                    result = real_check_output(command, *args, **kwargs)
                    if command[-2:] == ["rev-parse", tracking] and not changed:
                        real_check_output(["git", "--git-dir", str(self.origin),
                                           "update-ref", remote_ref, advanced])
                        changed.append(True)
                    return result

                with patch.object(verifier.subprocess, "check_output",
                                  side_effect=advance_origin_after_first_tracking_read):
                    self.assert_rejected()
                self.assertEqual([True], changed)
                self.assertEqual(self.canonical, self.git("rev-parse", tracking))
                self.assertEqual(advanced + "\t" + remote_ref,
                                 self.git("ls-remote", "--exit-code", "origin", remote_ref))

    def test_remote_tip_parser_requires_one_exact_pinned_full_sha_ref(self):
        ref = "refs/heads/" + verifier.PINNED_BRANCH
        valid = (self.canonical + "\t" + ref + "\n").encode()
        self.assertEqual(self.canonical, verifier._remote_tip(valid))
        malformed = (
            b"", valid + valid, valid + b"unexpected output\n",
            (self.canonical + "\trefs/heads/redirected\n").encode(),
            (self.canonical[:12] + "\t" + ref + "\n").encode(),
            ("g" * 40 + "\t" + ref + "\n").encode(),
            (self.canonical + " " + ref + "\n").encode(),
            b"\xff\t" + ref.encode() + b"\n",
        )
        for raw in malformed:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    verifier._remote_tip(raw)

    def promotion_commit(self, parents):
        args = ["commit-tree", self.git("rev-parse", self.head + "^{tree}")]
        for parent in parents:
            args.extend(["-p", parent])
        return self.git(*args, "-m", "owner constructs bounded promotion")

    def test_exact_promotion_dag_passes_and_nonforce_push_is_idempotent(self):
        authority = self.canonical
        promotion = self.promotion_commit([self.reviewed, authority])
        report = verifier.verify_candidate(self.repo, authority, promotion, "T10",
                                           require_promotion_dag=True)
        self.assertTrue(report["passed"], report)
        self.assertEqual([self.reviewed, authority], report["promotion_dag"]["parents"])
        self.assertTrue(report["promotion_dag"]["required"])
        ref = "refs/heads/" + verifier.PINNED_BRANCH
        # Actual ordinary pushes, with no force option, succeed both initially
        # and idempotently. The same object then validates in integrated mode.
        self.git("push", "origin", promotion + ":" + ref)
        self.git("push", "origin", promotion + ":" + ref)
        integrated = verifier.verify_candidate(self.repo, promotion, promotion, "T10",
                                               require_promotion_dag=True)
        self.assertTrue(integrated["passed"], integrated)
        self.assertEqual("INTEGRATED_REPAIR", integrated["execution_mode"])
        self.assertEqual(authority, integrated["authority_head"])
        self.assertFalse(self.marker.exists())

    def test_promotion_rejects_swapped_extra_and_wrong_parent_identities(self):
        wrong_reviewed = self.git("commit-tree", self.reviewed_tree, "-p", self.reviewed,
                                  "-m", "unreviewed child of reviewed source")
        wrong_authority = self.git("commit-tree", self.git("rev-parse", self.canonical + "^{tree}"),
                                   "-p", self.canonical, "-m", "different authority child")
        cases = {
            "swapped": [self.canonical, self.reviewed],
            "extra": [self.reviewed, self.canonical, self.base],
            "wrong reviewed": [wrong_reviewed, self.canonical],
            "wrong authority": [self.reviewed, wrong_authority],
        }
        for label, parents in cases.items():
            with self.subTest(case=label):
                promotion = self.promotion_commit(parents)
                report = verifier.verify_candidate(self.repo, self.canonical, promotion, "T10",
                                                   require_promotion_dag=True)
                self.assertFalse(report["passed"], report)
                self.assertIn("promotion requires exact ordered reviewed-source and authority parents",
                              report["promotion_dag"]["errors"])
                self.assertFalse(self.marker.exists())

    def test_promotion_rejects_authority_already_in_reviewed_source_ancestry(self):
        # Real Git history with H < R, unlike the required sibling authority
        # snapshot. Evaluate the DAG invariant independently of record contents.
        reviewed_after_authority = self.git("commit-tree", self.reviewed_tree,
                                            "-p", self.canonical, "-m", "review after authority")
        promotion = self.promotion_commit([reviewed_after_authority, self.canonical])

        def ancestor(base, tip):
            return subprocess.run(["git", "-C", str(self.repo), "merge-base", "--is-ancestor", base, tip],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

        errors = verifier.promotion_dag_errors(
            promotion, [reviewed_after_authority, self.canonical],
            reviewed_after_authority, self.canonical, ancestor)
        self.assertIn("promotion authority must be outside reviewed-source ancestry", errors)

    def test_remote_advance_after_final_read_blocks_ordinary_promotion_push(self):
        promotion = self.promotion_commit([self.reviewed, self.canonical])
        report = verifier.verify_candidate(self.repo, self.canonical, promotion, "T10",
                                           require_promotion_dag=True)
        self.assertTrue(report["passed"], report)
        competing = self.git("commit-tree", self.git("rev-parse", self.canonical + "^{tree}"),
                             "-p", self.canonical, "-m", "owner concurrent forward advance")
        self.git("push", "origin", competing + ":refs/heads/competing-owner")
        ref = "refs/heads/" + verifier.PINNED_BRANCH
        # This update occurs after verification's final live read. It is a
        # forward child of H, but is not contained in P's exact [R,H] ancestry.
        subprocess.check_output(["git", "--git-dir", str(self.origin), "update-ref", ref, competing],
                                stderr=subprocess.PIPE)
        with self.assertRaises(subprocess.CalledProcessError):
            self.git("push", "origin", promotion + ":" + ref)
        self.assertEqual(competing + "\t" + ref,
                         self.git("ls-remote", "--exit-code", "origin", ref))
        self.assertFalse(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
