from pathlib import Path
from unittest.mock import patch
import unittest

from preflight import PINS, audit, glb_scene, git_blob

# Test execution deliberately resolves the supplied exact project outside this deliverable.
import os
PROJECT = Path(os.environ.get("EXACT_HVN_PROJECT", "../hvn-l1-paid-pine-renewal-v1/base/HavenlineLevel1"))

class TestPreflight(unittest.TestCase):
    def test_all_positive_counts_identical_custody_in_exact_opening(self):
        result = audit(PROJECT)
        rows = result["rows"]
        self.assertEqual([r["wood"] for r in rows], [0, 1, 2, 3])
        self.assertEqual([r["visible_representative_roots_if_install_succeeds"] for r in rows], [0, 1, 1, 1])
        self.assertEqual([r["visible_internal_mesh_parts"] for r in rows], [0, 6, 6, 6])
        self.assertEqual([r["affordable_by_count_only"] for r in rows], [False, False, False, True])
        self.assertEqual([r["source_bound_visual_units"] for r in rows], [0, 0, 0, 0])
        self.assertFalse(any(r["render_only_3_arrival_handoff_admitted"] for r in rows))

    def test_three_model_logs_present_and_never_mistaken_for_game_units(self):
        raw = (PROJECT / "assets/studio/wood_bundle_v3.glb").read_bytes()
        self.assertEqual(git_blob(raw), PINS["assets/studio/wood_bundle_v3.glb"])
        self.assertEqual(glb_scene(raw)[:3], ["Lower log | knot side", "Lower log | far side", "Crown log"])
        self.assertEqual(audit(PROJECT)["rows"][-1]["source_bound_visual_units"], 0)

    def test_tampered_stock_view_fails_before_any_model_admission(self):
        original = Path.read_bytes
        def changed(path):
            return original(path) + (b"\n# altered\n" if path.name == "wood_stock_view.gd" else b"")
        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(ValueError, "exact source pin failed"):
                audit(PROJECT)

    def test_invalid_glb_header_cannot_be_intaken(self):
        with self.assertRaisesRegex(ValueError, "invalid GLB header"):
            glb_scene(b"Not a GLB")

if __name__ == "__main__":
    unittest.main()
