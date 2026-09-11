import pathlib, sys, unittest
HERE=pathlib.Path(__file__).resolve()
PROD=HERE.parents[1]
sys.path.insert(0,str(PROD))
from lib import DOCS, load_json, ensure_score_strictly_above_nine
from workstream import registry_errors
from change_impact import calculate

class GovernanceTests(unittest.TestCase):
    def test_strict_score_rule(self):
        self.assertTrue(ensure_score_strictly_above_nine({"x":9.0}))
        self.assertEqual(ensure_score_strictly_above_nine({"x":9.000001}),[])
    def test_exact_70_task_graph(self):
        g=load_json(DOCS/"DEPENDENCY_GRAPH.json")
        self.assertEqual(list(g["tasks"]),[f"T{i:02d}" for i in range(1,71)])
        self.assertEqual(g["tasks"]["T01"]["status"],"APPROVED")
        self.assertEqual(g["tasks"]["T02"]["status"],"APPROVED")
        self.assertEqual(g["tasks"]["T03"]["status"],"FIX_REQUIRED")
        self.assertTrue(all(g["tasks"][f"T{i:02d}"]["status"]=="LOCKED" for i in range(4,71)))
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
    def test_current_registry_checkpoint(self):
        r=load_json(DOCS/"WORKSTREAM_REGISTRY.json")
        t3=next(w for w in r["workstreams"] if w["task_id"]=="T03")
        self.assertEqual(t3["status"],"FIX_REQUIRED")
        self.assertEqual(t3["candidate_commit"],"6947849f581db9cfa53a17ff9202ecde1c0ee80c")
        self.assertEqual(t3["tests"]["checks"],807)

if __name__=="__main__":unittest.main()
