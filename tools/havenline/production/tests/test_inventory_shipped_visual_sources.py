import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import inventory_shipped_visual_sources as inv


class MaterialCensusTests(unittest.TestCase):
    def test_all_visual_source_categories_including_generated_material_code(self):
        self.assertEqual("mesh_or_geometry",inv.classify("HavenlineGodot/assets/cooker.glb"))
        self.assertEqual("image_or_texture",inv.classify("HavenlineGodot/textures/snow.png"))
        self.assertEqual("shader_or_material",inv.classify("HavenlineGodot/shaders/foam.gdshader"))
        self.assertEqual("scene_material_assignments",inv.classify("HavenlineGodot/scenes/main.tscn"))
        self.assertEqual("code_created_or_modified_material",inv.classify("HavenlineGodot/scripts/main.gd"))

    def test_real_git_tree_blob_inventory_and_exclusions(self):
        shas=["a"*40,"b"*40,"c"*40,"d"*40]
        paths=["HavenlineGodot/assets/cooker.glb","HavenlineGodot/scripts/main.gd",
               "HavenlineGodot/shaders/snow.gdshader","HavenlineGodot/tests/irrelevant.gd"]
        blob=b"".join(
            b"100644 blob "+sha.encode()+b"\t"+path.encode()+b"\0"
            for sha,path in zip(shas,paths))
        def fake_git(command,*args,**kwargs):
            return blob if "ls-tree" in command else "f"*40+"\n"
        with patch.object(inv.subprocess,"check_output",side_effect=fake_git), \
             patch.object(inv,"visual_style_paths",return_value=paths[:3]):
            out=inv.census()
        self.assertEqual(3,out["identified_visual_source_paths"])
        self.assertEqual(4,out["total_shipping_tracked_paths"]+1)
        self.assertFalse(out["complete_T70_C1_C2_critic_pass"])
        self.assertFalse(out["material_slot_count_known"])
        self.assertEqual({"code_created_or_modified_material":1,
                          "mesh_or_geometry":1,"shader_or_material":1},out["by_source_class"])

    def test_no_review_or_missing_shipping_material_fails_T70(self):
        stock={"source_items":[{"shipping_path":"HavenlineGodot/assets/a.glb"},
                               {"shipping_path":"HavenlineGodot/shaders/a.gdshader"}]}
        result=inv.compare_receipt(stock,{"source_paths_covered":["HavenlineGodot/assets/a.glb"]})
        self.assertFalse(result["passed"])
        self.assertEqual(["HavenlineGodot/shaders/a.gdshader"],result["missing_paths"])

    def test_synthetic_complete_paths_still_require_real_independent_C1_C2(self):
        stock={"source_items":[{"shipping_path":"HavenlineGodot/assets/a.glb"}]}
        report={"source_paths_covered":["HavenlineGodot/assets/a.glb"],
                "mode":"release","full_shipped_material_census_verified":True,
                "critic_ids_verified":["C1"],"real_visual_review_completed":True}
        self.assertFalse(inv.compare_receipt(stock,report)["passed"])
        report["critic_ids_verified"]=["C1","C2"]
        self.assertTrue(inv.compare_receipt(stock,report)["passed"])


if __name__=="__main__":
    unittest.main(verbosity=2)
