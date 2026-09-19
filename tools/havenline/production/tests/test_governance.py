import json, pathlib, sys, tempfile, unittest
from types import SimpleNamespace
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve()
PROD=HERE.parents[1]
sys.path.insert(0,str(PROD))
from lib import DOCS, load_json, ensure_score_strictly_above_nine, any_match
from validate_migration import ALLOWED_MIGRATION_PATTERNS
from workstream import approved_change_requests, authorized_change_request_targets, registry_errors, governance_only_drift, candidate_scope_assessment
from change_impact import calculate

class GovernanceTests(unittest.TestCase):
    def test_scalar_detector_distinguishes_ratio_from_integration(self):
        from repair_sufficiency_critic import SCALAR_PATCH
        self.assertIsNone(SCALAR_PATCH.search("CONTRACT_REDIRECT[INTEGRATION_BRANCH]"))
        self.assertIsNotNone(SCALAR_PATCH.search("adjust the ratio to 0.95"))
        self.assertIsNotNone(SCALAR_PATCH.search("reduce pixel_size to 0.0057"))

    def test_shared_candidate_guard_supplies_pinned_builder_authority(self):
        import yaml
        from builder_repair_gate import PINNED_INTEGRATION_BRANCH, verify_integration_branch
        workflow=yaml.safe_load((HERE.parents[4]/".github/workflows/havenline-candidate-guard.yml").read_text())
        steps=workflow["jobs"]["validate-candidate"]["steps"]
        callers=[step for step in steps if "--c0" in step.get("run","") and "builder_repair_gate.py" in step.get("run","")]
        self.assertEqual(len(callers),1)
        self.assertEqual(callers[0]["env"]["INTEGRATION_BRANCH"],PINNED_INTEGRATION_BRANCH)
        self.assertTrue(verify_integration_branch(None))
        self.assertTrue(verify_integration_branch("candidate-controlled-branch"))

    def test_candidate_validation_requires_integration_authority(self):
        from workstream import validate_candidate
        with patch("workstream.approved_change_requests") as requests:
            with self.assertRaises(SystemExit):
                validate_candidate("T10","base","HEAD",None)
            requests.assert_not_called()

    def test_change_request_consumer_supports_exact_legacy_and_bounded_schemas(self):
        legacy={"requesting_task":"T10","status":"APPROVED","integration_owner_disposition":"AUTHORIZED","target_path":"one.py"}
        bounded={"requesting_task":"T10","status":"AUTHORIZED","integration_owner_disposition":"APPROVED_BOUNDED_QA_GOV_CANARY","target_path":["two.py","three.py"]}
        self.assertEqual({"one.py"},authorized_change_request_targets(legacy,"T10"))
        self.assertEqual({"two.py","three.py"},authorized_change_request_targets(bounded,"T10"))
        for hostile in (
            [],
            dict(bounded,target_path=["dir/line\nfile.py"]),
            dict(bounded,target_path=["C:/escape"]),
            dict(legacy,target_path=["one.py","two.py"]),
            dict(bounded,target_path="two.py"),
            dict(bounded,status="REQUESTED"),
            dict(bounded,integration_owner_disposition="AUTHORIZED"),
            dict(bounded,integration_owner_disposition="APPROVED_BOUNDED_"),
            dict(bounded,requesting_task="T11"),
            dict(bounded,target_path=["../escape"]),
            dict(bounded,target_path=["..\\escape"]),
            dict(bounded,target_path=["dir//file.py"]),
            dict(bounded,target_path=["dir/./file.py"]),
            dict(bounded,target_path=["dir/*.py"]),
            dict(bounded,target_path=["same.py","same.py"]),
            dict(bounded,target_path=["ok.py",7]),
        ):
            self.assertEqual(set(),authorized_change_request_targets(hostile,"T10"),hostile)

    def test_t10_integrated_bounded_authorizations_are_consumed(self):
        authorized=approved_change_requests("T10","29be5ddae67cf47fd6674de8dfb3beb673116776")
        self.assertTrue({
            "Docs/Production/C0R_REPAIR_SUFFICIENCY_STANDARD.md",
            "Docs/Production/C0R_REPORT_SCHEMA.json",
            "tools/havenline/production/builder_repair_gate.py",
            "tools/havenline/production/c0_root_cause_advisor.py",
            "tools/havenline/production/repair_sufficiency_critic.py",
            "tools/havenline/production/tests/test_c0_builder.py",
            "tools/havenline/production/tests/test_repair_sufficiency_critic.py",
            "tools/havenline/production/validate_architecture_v32_t10.py",
        } <= authorized)

    def test_candidate_added_authorization_is_not_read_from_integration_ref(self):
        candidate_record={
            "requesting_task":"T10",
            "status":"AUTHORIZED",
            "integration_owner_disposition":"APPROVED_BOUNDED_TEST_ONLY",
            "target_path":["candidate-only.py"],
        }
        with tempfile.TemporaryDirectory() as td:
            docs=pathlib.Path(td)
            requests=docs/"ChangeRequests"
            requests.mkdir()
            (requests/"candidate-added.json").write_text(json.dumps(candidate_record))
            with patch("workstream.DOCS",docs):
                local=approved_change_requests("T10")
                integrated=approved_change_requests("T10","29be5ddae67cf47fd6674de8dfb3beb673116776")
        self.assertIn("candidate-only.py",local)
        self.assertNotIn("candidate-only.py",integrated)

    def test_t09_closeout_workflow_is_exactly_allowlisted(self):
        self.assertTrue(any_match(".github/workflows/havenline-task09-harvesting.yml",ALLOWED_MIGRATION_PATTERNS))
        self.assertFalse(any_match(".github/workflows/havenline-task10-world-transformation.yml",ALLOWED_MIGRATION_PATTERNS))
        self.assertFalse(any_match("HavenlineGodot/scripts/world_transformation.gd",ALLOWED_MIGRATION_PATTERNS))

    def test_strict_score_rule(self):
        self.assertTrue(ensure_score_strictly_above_nine({"x":9.0}))
        self.assertEqual(ensure_score_strictly_above_nine({"x":9.000001}),[])

    def test_exact_70_task_graph_and_lifecycle_consistency(self):
        graph=load_json(DOCS/"DEPENDENCY_GRAPH.json")
        tasks=graph["tasks"]
        self.assertEqual(list(tasks),[f"T{i:02d}" for i in range(1,71)])
        for task_id in ["T01","T02","T03"]:
            self.assertEqual(tasks[task_id]["status"],"APPROVED")

        registry=load_json(DOCS/"WORKSTREAM_REGISTRY.json")
        allowed=set(registry["allowed_states"])
        registry_tasks={w["task_id"]:w for w in registry["workstreams"] if w["task_id"] in tasks}

        # Lifecycle tests must validate invariants, not freeze the current active
        # task. Legitimate PREPARED/ASSIGNED/BUILDING transitions must not turn
        # the next governance run red merely because a checkpoint advanced.
        for task_id,node in tasks.items():
            self.assertIn(node["status"],allowed,task_id)
            if task_id in registry_tasks:
                self.assertEqual(node["status"],registry_tasks[task_id]["status"],task_id)
            if node["status"]!="LOCKED":
                for dependency in node["dependencies"]:
                    self.assertEqual(tasks[dependency]["status"],"APPROVED",f"{task_id} unlocked before {dependency} approval")

    def test_graph_is_acyclic(self):
        g=load_json(DOCS/"DEPENDENCY_GRAPH.json")["tasks"];seen=set();stack=set()
        def visit(t):
            if t in seen:return
            self.assertNotIn(t,stack)
            stack.add(t)
            for d in g[t]["dependencies"]:
                self.assertIn(d,g);visit(d)
            stack.remove(t);seen.add(t)
        for t in g:visit(t)
        self.assertEqual(len(seen),70)

    def test_registry_has_no_active_ownership_collision(self):
        self.assertEqual(registry_errors(),[])

    def test_governance_only_candidate_drift_does_not_force_rebase(self):
        self.assertTrue(governance_only_drift(["Docs/Production/WORKSTREAM_REGISTRY.json"]))
        self.assertTrue(governance_only_drift(["tools/havenline/production/test_placeholder.py"]))
        self.assertFalse(governance_only_drift(["HavenlineGodot/scripts/camera_composition.gd"]))
        self.assertFalse(governance_only_drift(["HavenlineGodot/scripts/unregistered_future_runtime.gd"]))

    def test_candidate_scope_excludes_shared_assignment_checkpoint(self):
        completed=lambda stdout="": SimpleNamespace(returncode=0,stdout=stdout,stderr="")
        with patch("workstream.subprocess.run",side_effect=[completed("claim-commit\n"),completed()]), \
             patch("workstream.changed_files",return_value=["HavenlineGodot/scripts/camera_composition.gd"]) as changed:
            scope=candidate_scope_assessment("pre-claim","candidate","integration")
        self.assertEqual(scope["branch_point"],"claim-commit")
        self.assertEqual(scope["changed_files"],["HavenlineGodot/scripts/camera_composition.gd"])
        changed.assert_called_once_with("claim-commit","candidate")

    def test_candidate_scope_falls_back_when_branch_point_predates_registry_base(self):
        completed=lambda code=0,stdout="": SimpleNamespace(returncode=code,stdout=stdout,stderr="")
        with patch("workstream.subprocess.run",side_effect=[completed(stdout="older\n"),completed(code=1)]), \
             patch("workstream.changed_files",return_value=["foreign.txt"]) as changed:
            scope=candidate_scope_assessment("pre-claim","candidate","integration")
        self.assertEqual(scope["branch_point"],"pre-claim")
        changed.assert_called_once_with("pre-claim","candidate")

    def test_critic_matrix(self):
        c=load_json(DOCS/"CRITIC_MATRIX.json")
        self.assertEqual(set(c["critics"]),{f"C{i}" for i in range(1,12)})
        self.assertEqual(set(c["task_applicability"]),{f"T{i:02d}" for i in range(1,71)})
        self.assertEqual(c["task_applicability"]["T03"],["C1","C2","C6"])

    def test_change_impact_river_and_t03(self):
        r=calculate(["HavenlineGodot/scripts/river_geometry.gd"])
        self.assertIn("T02",r["impacted_approved_tasks"])
        self.assertIn("T03",r["impacted_approved_tasks"])
        self.assertIn("test_task02_river",r["required_suites"])

    def test_t09_change_impact_is_fail_closed(self):
        expected_tasks={"T06","T07","T08","T09"}
        expected_suites={
            "test_motion_and_performance","test_task06_character1",
            "test_task07_context_director","test_task07_integration",
            "test_task08_inventory","test_task08_integration",
            "test_task09_harvesting","test_task09_integration",
        }
        for path in [
            "HavenlineGodot/assets/harvesting_v1/axe.glb",
            "HavenlineGodot/scripts/harvest_presentation.gd",
            "HavenlineGodot/tests/test_task09_harvesting.gd",
            "HavenlineGodot/tests/test_task09_integration.gd",
            "HavenlineGodot/tests/capture_task09_harvesting.gd",
        ]:
            result=calculate([path])
            self.assertTrue(expected_tasks.issubset(result["impacted_approved_tasks"]),path)
            self.assertTrue(expected_suites.issubset(result["required_suites"]),path)
            self.assertFalse(result["governance_only"],path)
            self.assertFalse(result["unknown_production_fallback"],path)

    def test_governance_only_change(self):
        r=calculate(["Docs/Production/WORKSTREAM_REGISTRY.json"])
        self.assertTrue(r["governance_only"])
        self.assertFalse(r["unknown_production_fallback"])

    def test_qa_capture_harness_is_governance_only(self):
        r=calculate(["HavenlineGodot/tests/production_capture_harness.gd"])
        self.assertTrue(r["governance_only"])
        self.assertFalse(r["unknown_production_fallback"])

    def test_unknown_runtime_is_never_hidden_by_docs_match(self):
        r=calculate(["Docs/Production/WORKSTREAM_REGISTRY.json","HavenlineGodot/scripts/unregistered_future_runtime.gd"])
        self.assertFalse(r["governance_only"])
        self.assertTrue(r["unknown_production_fallback"])
        self.assertIn("HavenlineGodot/scripts/unregistered_future_runtime.gd",r["unknown_production_files"])
        self.assertIn("T01",r["impacted_approved_tasks"])
        self.assertIn("T02",r["impacted_approved_tasks"])
        self.assertIn("T03",r["impacted_approved_tasks"])

    def test_performance_budget_fields(self):
        b=load_json(DOCS/"PERFORMANCE_BUDGETS.json")["global_soft_budgets"]
        for key in ["visible_triangles","draw_calls","materials_visible","texture_gpu_memory_mb","cpu_frame_ms","gpu_frame_ms_where_measurable","physics_active_bodies","animated_rigs_active","npc_companion_active_population","process_memory_mb","storage_download_mb"]:
            self.assertIn(key,b)

    def test_completed_t03_registry_checkpoint(self):
        r=load_json(DOCS/"WORKSTREAM_REGISTRY.json")
        t3=next(w for w in r["workstreams"] if w["task_id"]=="T03")
        self.assertEqual(t3["status"],"APPROVED")
        self.assertEqual(t3["candidate_commit"],"5df9726e0b1c33f0f8865385b1c49aca229fd461")
        self.assertEqual(t3["tests"]["checks"],807)
        self.assertEqual(t3["tests"]["result"],"PASS")
        self.assertEqual(t3["known_blockers"],[])
        self.assertIn("PASS_BY_QUORUM",t3["critic_status"]["C1+C2"])
        self.assertIn("PASS",t3["critic_status"]["C6"])

    def test_t06_closeout_and_t07_lifecycle_checkpoint(self):
        graph=load_json(DOCS/"DEPENDENCY_GRAPH.json")["tasks"]
        registry=load_json(DOCS/"WORKSTREAM_REGISTRY.json")
        gates=load_json(DOCS/"task-gates.json")
        t6=next(w for w in registry["workstreams"] if w["task_id"]=="T06")
        t7=next(w for w in registry["workstreams"] if w["task_id"]=="T07")
        completion=load_json(DOCS/"T06/verified-completion.json")
        ledger=load_json(DOCS/"T06/DEFECT_LEDGER.json")
        self.assertEqual(graph["T06"]["status"],"APPROVED")
        self.assertEqual(t6["candidate_commit"],"47f86fae25b099abb5c7096c37ca7495453b2b8f")
        self.assertEqual(t6["tests"]["checks"],1345)
        self.assertEqual(completion["integrated_source"],"91f35f331aaabe2b1785b10c0d911f20da6f12d9")
        self.assertTrue(completion["source_identity"]["reviewed_runtime_and_gate_files_byte_identical"])
        self.assertEqual({row["status"] for row in ledger["defects"]},{"VERIFIED_CLOSED"})
        self.assertEqual(graph["T07"]["status"],t7["status"])
        self.assertIn(t7["status"],{"ASSIGNED","BUILDING_ISOLATED","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED"})
        if t7["status"]=="APPROVED":
            self.assertIn("T07",gates["approved_tasks"])
            self.assertIn(graph["T08"]["status"],{"LOCKED","PREPARED","ASSIGNED","BUILDING_ISOLATED","INTEGRATION_READY","INTEGRATING","UNDER_REVIEW","FIX_REQUIRED","APPROVED","BLOCKED"})
            if graph["T08"]["status"] == "LOCKED":
                self.assertIsNone(gates["active_task"])
            elif graph["T08"]["status"] != "APPROVED":
                self.assertEqual(gates["active_task"],"T08")
                self.assertEqual(gates["active_status"],graph["T08"]["status"])
                self.assertTrue((DOCS/"T08/FROZEN_SCOPE.md").exists())
                self.assertTrue((DOCS/"T08/TASK_PACKET.md").exists())
            completion7=load_json(DOCS/"T07/verified-completion.json")
            ledger7=load_json(DOCS/"T07/defect-ledger.json")
            review7=load_json(DOCS/"T07/independent-critic-review.json")
            self.assertEqual(completion7["integrated_source"],"94b3f6c5097356a3857ebd13a77fb1e316eb06ae")
            self.assertEqual(completion7["mechanical_evidence"]["total_assertions_checks"],1441)
            self.assertTrue(all(score>9.0 for score in review7["scores"].values()))
            self.assertEqual(review7["unresolved_mandatory_defects"],[])
            self.assertEqual({row["status"] for row in ledger7["defects"]},{"VERIFIED_CLOSED"})
            if graph["T08"]["status"]=="APPROVED":
                completion8=load_json(DOCS/"T08/verified-completion.json")
                ledger8=load_json(DOCS/"T08/defect-ledger.json")
                review8=load_json(DOCS/"T08/independent-critic-review.json")
                self.assertEqual(completion8["integrated_source"],"9d56ea8ae972d0a0705ff8b985e13fab31dde493")
                self.assertEqual(completion8["mechanical_evidence"]["total_assertions_checks"],1535)
                self.assertEqual(completion8["source_identity"]["locked_reference_frames_verified"],44)
                self.assertEqual(completion8["source_identity"]["locked_source_recordings_verified"],2)
                self.assertTrue(all(score>9.0 for score in review8["scores"].values()))
                self.assertEqual(review8["unresolved_mandatory_defects"],[])
                self.assertEqual({row["status"] for row in ledger8["defects"]},{"VERIFIED_CLOSED"})
                if graph["T09"]["status"]=="APPROVED":
                    completion9=load_json(DOCS/"T09/verified-completion.json")
                    ledger9=load_json(DOCS/"T09/defect-ledger.json")
                    review9=load_json(DOCS/"T09/independent-critic-review.json")
                    self.assertEqual(completion9["candidate_commit"],"5415d85838ecf4bea8b3c71662072670e61797a0")
                    self.assertTrue(all(score>9.0 for row in review9["critics"].values() for score in row["scores"].values()))
                    self.assertEqual(review9["unresolved_mandatory_defects"],[])
                    self.assertEqual({row["status"] for row in ledger9["defects"]},{"VERIFIED_CLOSED"})
                    owner9=next(w for w in load_json(DOCS/"PATH_OWNERSHIP.json")["completed_production_owners"] if w["task_id"]=="T09")
                    self.assertEqual(owner9["accepted_source"],completion9["candidate_commit"])
                    if graph["T10"]["status"]=="LOCKED":
                        self.assertIsNone(gates["active_task"])
                        self.assertIsNone(gates["active_status"])
                    elif graph["T10"]["status"]!="APPROVED":
                        self.assertEqual(gates["active_task"],"T10")
                        self.assertEqual(gates["active_status"],graph["T10"]["status"])
                        self.assertTrue((DOCS/"T10/FROZEN_SCOPE.md").exists())
                        self.assertTrue((DOCS/"T10/TASK_PACKET.md").exists())
                        registry10=next(w for w in load_json(DOCS/"WORKSTREAM_REGISTRY.json")["workstreams"] if w["task_id"]=="T10")
                        owner10=next(w for w in load_json(DOCS/"PATH_OWNERSHIP.json")["active_owners"] if w["task_id"]=="T10")
                        expected10=("world-transformation-builder","havenline/T10-world-transformation",gates["active_base_integration_commit"])
                        self.assertEqual((registry10["owner"],registry10["branch"],registry10["base_commit"]),expected10)
                        self.assertEqual((owner10["owner"],owner10["branch"],owner10["base_commit"]),expected10)
                        self.assertEqual(registry10["owned_paths"],["@reservation:T10"])
                        self.assertEqual(owner10["paths_alias"],"@reservation:T10")
                else:
                    self.assertEqual(gates["active_task"],"T09")
                    self.assertEqual(gates["active_status"],graph["T09"]["status"])
                    if graph["T09"]["status"] != "LOCKED":
                        registry9=next(w for w in load_json(DOCS/"WORKSTREAM_REGISTRY.json")["workstreams"] if w["task_id"]=="T09")
                        owner9=next(w for w in load_json(DOCS/"PATH_OWNERSHIP.json")["active_owners"] if w["task_id"]=="T09")
                        expected=("harvesting-acquisition-builder","havenline/T09-harvesting","7492074e40a0b061f31d8c32602b7a581b2610f3")
                        self.assertEqual((registry9["owner"],registry9["branch"],registry9["base_commit"]),expected)
                        self.assertEqual((owner9["owner"],owner9["branch"],owner9["base_commit"]),expected)
                        self.assertEqual(registry9["owned_paths"],["@reservation:T09"])
                        self.assertEqual(owner9["paths_alias"],"@reservation:T09")
                        self.assertEqual(gates["active_base_integration_commit"],expected[2])
                        self.assertTrue((DOCS/"T09/FROZEN_SCOPE.md").exists())
                        self.assertTrue((DOCS/"T09/TASK_PACKET.md").exists())
                self.assertEqual(set(graph["T09"]["critics"]),{"C2","C3","C4","C5","C6"})
        else:
            self.assertEqual(gates["active_task"],"T07")
            self.assertEqual(gates["active_status"],t7["status"])
            self.assertEqual(gates["approved_tasks"],["T01","T02","T03","T04","T05","T06"])
        self.assertTrue((DOCS/"T07/FROZEN_SCOPE.md").exists())
        self.assertTrue((DOCS/"T07/TASK_PACKET.md").exists())

if __name__=="__main__":unittest.main()
