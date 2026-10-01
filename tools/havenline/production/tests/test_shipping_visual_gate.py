import json, pathlib, sys, unittest
PROD=pathlib.Path(__file__).resolve().parents[1]
ROOT=pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0,str(PROD))
import shipping_visual_gate

class ShippingVisualGateTests(unittest.TestCase):
    def test_policy_forbids_builtin_visible_primitives_and_materials(self):
        p=shipping_visual_gate.policy()
        for token in ("BoxMesh","PlaneMesh","SphereMesh","CylinderMesh","CapsuleMesh","PrismMesh","QuadMesh","PrimitiveMesh"):
            self.assertIn(token,p["forbidden_render_types"])
        for token in ("StandardMaterial3D","ORMMaterial3D"):
            self.assertIn(token,p["forbidden_material_types"])
        self.assertEqual([3840,2160],p["human_visual_gate"]["minimum_internal_resolution"])
        self.assertEqual(60,p["human_visual_gate"]["minimum_capture_fps"])
        self.assertTrue(p["human_visual_gate"]["explicit_user_visual_approval_required"])

    def test_known_approved_primitive_debt_is_explicitly_invalidated(self):
        inv=shipping_visual_gate.invalidations()
        active={r["task_id"] for r in inv["records"] if r.get("status")=="ACTIVE"}
        self.assertTrue({"T08","T09","T10","T11"}.issubset(active))
        report=shipping_visual_gate.audit_effective_approvals()
        self.assertTrue(report["passed"],report)
        rows={r["task_id"]:r for r in report["rows"]}
        for task in ("T08","T09","T10","T11"):
            self.assertTrue(rows[task]["invalidation_active"])
            self.assertFalse(rows[task]["effective_approved"])
        self.assertEqual(0, rows["T08"]["finding_count"], rows["T08"])
        for task in ("T09","T10","T11"):
            self.assertGreater(rows[task]["finding_count"], 0, rows[task])

    def test_t11_is_not_effectively_approved_until_visual_repair(self):
        out=shipping_visual_gate.effective_approval("T11")
        self.assertFalse(out["passed"],out)
        self.assertTrue(out["historical_approved"])
        self.assertGreater(out["primitive_audit"]["finding_count"],0)

if __name__=="__main__":
    unittest.main(verbosity=2)
