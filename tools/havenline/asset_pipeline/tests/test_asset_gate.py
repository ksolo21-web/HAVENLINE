import copy
import json
import pathlib
import struct
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from asset_gate import run, get_file, parse_glb, plausible_baked_pixel, embedded_glb_normal_png

POLICY=pathlib.Path(__file__).resolve().parents[4]/"Docs/Production/GLOBAL_ASSET_AUTHORING_POLICY.json"
TEMPLATE=ROOT/"examples/T05-cooker-asset.json"

class AssetGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads(POLICY.read_text())
        cls.manifest=json.loads(TEMPLATE.read_text())
    def test_global_policy_scope(self):
        self.assertEqual(self.policy["scope"],"ALL_GAME_ART_ACROSS_ALL_TASKS_AND_FUTURE_BIOMES")
        self.assertEqual(self.policy["exact_style_scores"]["reference_fidelity"],10)
    def test_source_lint_is_not_approval(self):
        with tempfile.TemporaryDirectory() as workspace:
            result=run(self.manifest,self.policy,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"SOURCE_LINT_PASS_NOT_ASSET_APPROVAL")
        self.assertFalse(result["asset_released"])
    def test_incomplete_candidate_fails_closed(self):
        with tempfile.TemporaryDirectory() as workspace:
            result=run(self.manifest,self.policy,pathlib.Path(workspace),"candidate")
        self.assertEqual(result["result"],"FAIL")
        self.assertFalse(result["asset_released"])
        self.assertIn("owner_reference_pixels_sha256",[x["check"] for x in result["checks"] if not x["pass"]])
    def test_reference_style_cannot_be_lowered(self):
        p=copy.deepcopy(self.policy)
        p["exact_style_scores"]["reference_fidelity"]=9.5
        with tempfile.TemporaryDirectory() as workspace:
            result=run(self.manifest,p,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"FAIL")
    def test_exact_reference_mandatory(self):
        m=copy.deepcopy(self.manifest)
        m["owner_reference"]["binding"]="family_board"
        with tempfile.TemporaryDirectory() as workspace:
            result=run(m,self.policy,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"FAIL")
    def test_missing_limits_fails_closed(self):
        m=copy.deepcopy(self.manifest)
        del m["limits"]["texture_mib_max"]
        with tempfile.TemporaryDirectory() as workspace:
            result=run(m,self.policy,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"FAIL")
    def test_no_path_traversal(self):
        with tempfile.TemporaryDirectory() as workspace:
            with self.assertRaises(ValueError):get_file(pathlib.Path(workspace),"../other.png")
            with self.assertRaises(ValueError):get_file(pathlib.Path(workspace),"/tmp/secret")
    def test_invalid_glb_refused(self):
        with tempfile.TemporaryDirectory() as workspace:
            path=pathlib.Path(workspace)/"broken.glb"
            path.write_bytes(b"no glb")
            with self.assertRaises(ValueError):parse_glb(path)
    def test_embedded_normal_binding_and_bounds(self):
        # Pure stdlib synthetic GLB: prove payload selection, absent binding
        # rejection and out-of-bounds bufferView rejection.
        payload=b"PNG_BYTES_FOR_STRUCTURE_TEST"
        doc={
            "asset":{"version":"2.0"},
            "materials":[{"normalTexture":{"index":0}}],
            "textures":[{"source":0}],
            "images":[{"mimeType":"image/png","bufferView":0}],
            "bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":len(payload)}]
        }
        def write_glb(path,meta):
            json_chunk=json.dumps(meta,separators=(",",":")).encode()
            json_chunk+=b" " * ((-len(json_chunk))%4)
            binary=payload+bytes((-len(payload))%4)
            total=12+8+len(json_chunk)+8+len(binary)
            path.write_bytes(struct.pack("<4sII",b"glTF",2,total)+
                struct.pack("<I4s",len(json_chunk),b"JSON")+json_chunk+
                struct.pack("<I4s",len(binary),bytes((66,73,78,0)))+binary)
        with tempfile.TemporaryDirectory() as workspace:
            path=pathlib.Path(workspace)/"sample.glb"
            write_glb(path,doc)
            self.assertEqual(embedded_glb_normal_png(path,parse_glb(path)),payload)
            invalid=copy.deepcopy(doc)
            invalid["materials"]=[{}]
            write_glb(path,invalid)
            with self.assertRaises(ValueError):
                embedded_glb_normal_png(path,parse_glb(path))
            invalid=copy.deepcopy(doc)
            invalid["bufferViews"][0]["byteLength"]=len(payload)+1000
            write_glb(path,invalid)
            with self.assertRaises(ValueError):
                embedded_glb_normal_png(path,parse_glb(path))

    def test_release_never_inferred_from_technical_lint(self):
        with tempfile.TemporaryDirectory() as workspace:
            result=run(self.manifest,self.policy,pathlib.Path(workspace),"release")
        self.assertEqual(result["result"],"FAIL")
        self.assertFalse(result["asset_released"])
    def test_opaque_gray_normals_are_rejected(self):
        self.assertFalse(plausible_baked_pixel("normal",(128,128,128,255)))
        self.assertFalse(plausible_baked_pixel("normal",(230,26,217,255)))
        self.assertFalse(plausible_baked_pixel("normal",(128,128,255,0)))
        self.assertTrue(plausible_baked_pixel("normal",(128,128,255,255)))
    def test_opaque_black_ao_and_colored_sentinel_rejected(self):
        self.assertFalse(plausible_baked_pixel("ambient_occlusion",(0,0,0,255)))
        self.assertFalse(plausible_baked_pixel("ambient_occlusion",(230,26,217,255)))
        self.assertFalse(plausible_baked_pixel("ambient_occlusion",(255,255,255,0)))
        self.assertTrue(plausible_baked_pixel("ambient_occlusion",(240,240,240,255)))
    def test_lint_game_wide_future_biome(self):
        m=copy.deepcopy(self.manifest)
        m["asset_id"]="volcanic_region_shelter"
        m["task_id"]="T84"
        with tempfile.TemporaryDirectory() as workspace:
            result=run(m,self.policy,pathlib.Path(workspace),"lint")
        self.assertEqual(result["result"],"SOURCE_LINT_PASS_NOT_ASSET_APPROVAL")

if __name__=="__main__":unittest.main()
