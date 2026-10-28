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
        with self.assertRaisesRegex(ValueError,"No glTF mesh primitives"):
            m.gltf_slots(glb([{"name":"wood"}],[]),".glb")

    def test_real_glb_texture_slot_channels_are_source_bound(self):
        data=glb([{"name":"wood","pbrMetallicRoughness":{"baseColorTexture":{"index":0}},
            "normalTexture":{"index":1},"occlusionTexture":{"index":2}}],[0],
            textures=[{"source":0},{"source":1},{"source":2}])
        p=m.gltf_slots(data,".glb")["material_slots"][0]
        self.assertEqual(["albedo","normal","occlusion"],p["texture_channels_bound"])

    def test_variant_only_material_is_real_used_surface_not_discarded(self):
        doc={"asset":{"version":"2.0"},
             "materials":[{"name":"HL_wood"},{"name":"HL_snow"}],
             "extensions":{"KHR_materials_variants":{"variants":[{"name":"winter"}]}},
             "meshes":[{"primitives":[{"attributes":{"POSITION":0},"material":0,
                 "extensions":{"KHR_materials_variants":{"mappings":[
                     {"material":1,"variants":[0]}]}}}]}]}
        data=json.dumps(doc).encode()
        data+=b" "*((-len(data))%4)
        blob=struct.pack("<I4s",len(data),b"JSON")+data
        wrapped=struct.pack("<4sII",b"glTF",2,len(blob)+12)+blob
        result=m.gltf_slots(wrapped,".glb")
        self.assertEqual(2,result["material_slot_count"])
        self.assertEqual(0,result["unused_authored_slots"])
        self.assertEqual(["winter"],result["material_slots"][1]["glTF_variant_names"])

    def test_invalid_variant_material_binding_is_rejected(self):
        doc={"asset":{"version":"2.0"},"materials":[{"name":"wood"}],
             "extensions":{"KHR_materials_variants":{"variants":[{"name":"winter"}]}},
             "meshes":[{"primitives":[{"attributes":{"POSITION":0},"material":0,
                "extensions":{"KHR_materials_variants":{"mappings":[{"material":3,"variants":[0]}]}}}]}]}
        data=json.dumps(doc).encode()
        data+=b" "*((-len(data))%4)
        blob=struct.pack("<I4s",len(data),b"JSON")+data
        with self.assertRaisesRegex(ValueError,"Variant references out-of-range"):
            m.gltf_slots(struct.pack("<4sII",b"glTF",2,len(blob)+12)+blob,".glb")

    def test_invalid_glb_texture_binding_fails_closed(self):
        data=glb([{"name":"wood","normalTexture":{"index":3}}],[0],
                 textures=[{"source":0}])
        with self.assertRaisesRegex(ValueError,"Invalid texture index"):
            m.gltf_slots(data,".glb")

    def _runtime_obj_fixture(self):
        from tempfile import TemporaryDirectory
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root=pathlib.Path(temp.name)
        script_path="HavenlineGodot/scripts/transfer_feedback.gd"
        shader_path="HavenlineGodot/assets/transfer_feedback_v2/transfer_feedback_v2.gdshader"
        mesh_path="HavenlineGodot/assets/transfer_feedback_v2/transfer_arrow_sigil.obj"
        for rel in (script_path,shader_path,mesh_path):
            (root/rel).parent.mkdir(parents=True,exist_ok=True)
        (root/mesh_path).write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
        (root/shader_path).write_text("shader_type spatial;\nvoid fragment() { ALBEDO = vec3(1.0); }\n")
        (root/script_path).write_text('''
const FEEDBACK_MESHES := {
  "arrow": "res://assets/transfer_feedback_v2/transfer_arrow_sigil.obj"
}
const FEEDBACK_SHADER := "res://assets/transfer_feedback_v2/transfer_feedback_v2.gdshader"
func _feedback_material(color,role):
 var material := ShaderMaterial.new()
 material.shader = load(FEEDBACK_SHADER)
func _make_feedback_instances(kind,color,capacity,role):
 var instances := MultiMesh.new()
 instances.mesh = mesh
 result.multimesh = instances
 result.material_override = material
func _make_arrows(color):
 return _make_feedback_instances("arrow", color, 42, 1.0)
func _ensure_trails():
 gather_arrows = _make_arrows(Color("5deaff"))
 destination_arrows = _make_arrows(Color("ffb548"))
''')
        return root,mesh_path,script_path,shader_path

    def test_runtime_obj_has_placeholder_until_real_script_shader_binding(self):
        raw=b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
        row=m.obj_slots(raw)
        self.assertEqual("STATIC_OBJ_RUNTIME_MATERIAL_BINDING_REQUIRED",row["status"])
        self.assertTrue(row["runtime_override_required"])
        self.assertEqual(1,row["primitive_count"])
        self.assertFalse(row["material_slots"][0]["used_in_render_mesh"])

    def test_real_runtime_shader_script_binding_yields_two_unapproved_color_variants(self):
        root,mesh,script,shader=self._runtime_obj_fixture()
        result=m.resolve_obj_runtime_shader_binding(root,mesh,[script])
        self.assertEqual("arrow",result["effect_kind"])
        self.assertEqual(2,len(result["runtime_material_variants"]))
        self.assertEqual(["runtime:source_to_actor","runtime:actor_to_destination"],
                         result["runtime_color_variants"])
        self.assertEqual(1.0,result["role"])
        self.assertFalse(result["native_Godot_runtime_visual_checked"])
        c=m.inspect_sources({"source_items":[
            {"shipping_path":mesh,"source_class":"mesh_or_geometry"},
            {"shipping_path":script,"source_class":"code_created_or_modified_material"},
            {"shipping_path":shader,"source_class":"shader_or_material"}],
            "identified_visual_source_paths":3},root=root)
        self.assertEqual(2,c["glTF_and_OBJ_material_slots_known"])
        self.assertEqual(0,c["unresolved_mesh_source_count"])
        self.assertFalse(c["all_materials_reviewed"])

    def test_runtime_obj_without_shader_or_colors_cannot_be_assumed_valid(self):
        root,mesh,script,shader=self._runtime_obj_fixture()
        (root/shader).unlink()
        with self.assertRaisesRegex(ValueError,"shader missing/invalid"):
            m.resolve_obj_runtime_shader_binding(root,mesh,[script])
        (root/shader).write_text("shader_type spatial;")
        (root/script).write_text((root/script).read_text().replace('Color("ffb548")','Color("ff0000")'))
        with self.assertRaisesRegex(ValueError,"two-direction"):
            m.resolve_obj_runtime_shader_binding(root,mesh,[script])

    def test_obj_without_faces_or_usemtl_is_not_valid_geometry(self):
        with self.assertRaisesRegex(ValueError,"neither material assignment nor mesh faces"):
            m.obj_slots(b"v 0 0 0\n")
    
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
