import json
import pathlib
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import inventory_shipped_material_slots as m


def glb(materials, primitive_ids, textures=None):
    doc={"asset":{"version":"2.0"},
         "materials":materials,
         "meshes":[{"primitives":[{"attributes":{"POSITION":0},
                 **({"material":k} if k is not None else {})} for k in primitive_ids]}]}
    if textures is not None:
        doc["textures"]=textures
    raw=json.dumps(doc).encode()
    raw+=b" "*((-len(raw))%4)
    chunk=struct.pack("<I4s",len(raw),b"JSON")+raw
    return struct.pack("<4sII",b"glTF",2,12+len(chunk))+chunk


class ActualModelMaterialSlotInventory(unittest.TestCase):
    def test_glb_counts_every_explicit_material_slot_not_one_per_model(self):
        mats=[{"name":"HL_wood"},{"name":"HL_snow"},{"name":"HL_metal"}]
        report=m.gltf_slots(glb(mats,[0,0,1,2]),".glb")
        self.assertEqual(3,report["material_slot_count"])
        self.assertEqual([2,1,1],[r["referencing_primitives"] for r in report["material_slots"]])
        self.assertEqual(["0:HL_wood","1:HL_snow","2:HL_metal"],
                         [r["slot_id"] for r in report["material_slots"]])
        self.assertFalse(report.get("all_materials_reviewed",False))

    def test_duplicate_names_do_not_hide_distinct_material_slots(self):
        mats=[{"name":"Identical"},{"name":"Identical"}]
        rows=m.gltf_slots(glb(mats,[0,1]),".glb")["material_slots"]
        self.assertEqual(["0:Identical","1:Identical"],[x["slot_id"] for x in rows])

    def test_implicit_glb_default_is_unapproved_and_not_silently_ignored(self):
        a=m.gltf_slots(glb([{"name":"paint"}],[0,None]),".glb")
        self.assertEqual(2,a["material_slot_count"])
        self.assertEqual(1,a["unassigned_primitives"])
        self.assertTrue(a["material_slots"][1]["implicit_default_must_be_replaced_before_visual_acceptance"])

    def test_bad_glb_header_is_fatal_not_an_empty_material_list(self):
        with self.assertRaisesRegex(ValueError,"Not a GLB"):
            m.gltf_slots(b"version https://git-lfs.github.com/spec/v1", ".glb")

    def test_out_of_bounds_glb_material_index_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"out-of-range"):
            m.gltf_slots(glb([{"name":"wood"}],[1]),".glb")

    def test_glb_empty_geometry_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"geometry"):
            m.gltf_slots(glb([{"name":"wood"}],[]),".glb")

    def test_real_glb_texture_slot_channels_are_source_bound(self):
        data=glb([{"name":"wood","pbrMetallicRoughness":{"baseColorTexture":{"index":0}},
            "normalTexture":{"index":1},"occlusionTexture":{"index":2}}],[0],
            textures=[{"source":0},{"source":1},{"source":2}])
        p=m.gltf_slots(data,".glb")["material_slots"][0]
        self.assertEqual(["albedo","normal","occlusion"],p["texture_channels_bound"])

    def test_invalid_glb_texture_binding_fails_closed(self):
        data=glb([{"name":"wood","normalTexture":{"index":3}}],[0],
                 textures=[{"source":0}])
        with self.assertRaisesRegex(ValueError,"Invalid texture index"):
            m.gltf_slots(data,".glb")

    def test_obj_material_names_are_not_a_render_approval(self):
        parsed=m.obj_slots(b"mtllib cooker.mtl\nusemtl Wood\nv 0 0 0\nusemtl Metal\nusemtl Wood\n")
        self.assertEqual(2,parsed["material_slot_count"])
        self.assertIn("NEEDS_GODOT",parsed["status"])

    def test_source_inventory_accounts_for_missing_and_real_model_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            path=root/"HavenlineGodot/assets/cooker.glb"
            path.parent.mkdir(parents=True)
            path.write_bytes(glb([{"name":"snow"},{"name":"steel"}],[0,1]))
            result=m.inspect_sources({"shipping_ref_commit":"a"*40,
                "identified_visual_source_paths":3,"source_items":[
                    {"shipping_path":"HavenlineGodot/assets/cooker.glb",
                     "source_class":"mesh_or_geometry"},
                    {"shipping_path":"HavenlineGodot/assets/missing.glb",
                     "source_class":"mesh_or_geometry"},
                    {"shipping_path":"HavenlineGodot/shaders/snow.gdshader",
                     "source_class":"shader_or_material"}]},root=root)
        self.assertEqual(2,result["glTF_and_OBJ_material_slots_known"])
        self.assertEqual(1,result["unresolved_mesh_source_count"])
        self.assertFalse(result["all_materials_reviewed"])
        self.assertEqual(2,result["mesh_source_count"])

    def test_native_viewer_is_still_required_for_all_static_material_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            path=root/"HavenlineGodot/assets/cooker.glb"
            path.parent.mkdir(parents=True)
            path.write_bytes(glb([{"name":"snow"}],[0]))
            result=m.inspect_sources({"identified_visual_source_paths":1,"source_items":[
                {"shipping_path":"HavenlineGodot/assets/cooker.glb",
                 "source_class":"mesh_or_geometry"}]},root=root)
        self.assertFalse(result["all_materials_reviewed"])
        self.assertFalse(result["models"][0]["native_Godot_material_render_verified"])
        self.assertFalse(result["models"][0]["actual_C1_C2_review_passed"])


if __name__=="__main__":
    unittest.main(verbosity=2)
