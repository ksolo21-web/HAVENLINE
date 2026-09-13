import pathlib, sys, unittest
HERE=pathlib.Path(__file__).resolve()
PROD=HERE.parents[1]
sys.path.insert(0,str(PROD))
from lib import DOCS, load_json, ensure_score_strictly_above_nine
from workstream import registry_errors, governance_only_drift
from change_impact import calculate

class GovernanceTests(unittest.TestCase):
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

if __name__=="__main__":unittest.main()
