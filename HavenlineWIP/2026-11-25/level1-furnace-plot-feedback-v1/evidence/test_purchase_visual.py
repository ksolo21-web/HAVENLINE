from copy import deepcopy
from fractions import Fraction
import unittest
from purchase_visual import Marker, PAYMENT, MOTION_DEADLINE, FILL_TICKS

SCENE = "volatile-scene-7"
PIECES = ("owned-wood-A", "owned-wood-B", "owned-wood-C")

class TestMarker(unittest.TestCase):
    def make_started(self):
        m = Marker(SCENE)
        self.assertTrue(m.approach(1, True))
        self.assertTrue(m.begin_after_live_commit(2, deepcopy(PAYMENT), SCENE, PIECES))
        return m

    def test_idle_hover_exit_without_filling(self):
        m = Marker(SCENE)
        self.assertEqual((m.view().state, m.view().corners, m.view().text), ("idle", "white", "3 WOOD"))
        self.assertTrue(m.approach(16, True))
        self.assertEqual((m.view().state, m.view().corners, m.view().near_edge_fill), ("armed", "lime", 0))
        self.assertFalse(m.view().show_committed_furnace)
        self.assertTrue(m.advance_to(600))
        self.assertEqual(m.view().near_edge_fill, 0)
        self.assertTrue(m.approach(601, False))
        self.assertEqual(m.view().state, "idle")

    def test_commit_and_arrivals_then_full_hold_shrink_reveal(self):
        m = self.make_started()
        self.assertEqual(m.view().near_edge_fill, 0)
        for idx, tick in enumerate((8, 18, 28)):
            self.assertTrue(m.advance_to(tick - 1))
            self.assertEqual(m.view().near_edge_fill, Fraction(idx, 3))
            self.assertTrue(m.arrive(tick, SCENE, 1, PIECES[idx]))
            self.assertEqual(m.view().near_edge_fill, Fraction(idx, 3))
            self.assertEqual(m.view().fill_target, Fraction(idx + 1, 3))
            self.assertTrue(m.advance_to(tick+1))
            self.assertEqual(m.view().near_edge_fill, Fraction(idx, 3) + Fraction(1, 3 * FILL_TICKS))
            self.assertTrue(m.advance_to(tick+FILL_TICKS))
            self.assertEqual(m.view().near_edge_fill, Fraction(idx + 1, 3))
            self.assertEqual(m.view().text, "3 WOOD")
            self.assertFalse(m.view().show_committed_furnace)
        self.assertEqual(m.view().state, "full_hold")
        self.assertTrue(m.advance_to(37))
        self.assertFalse(m.view().show_committed_furnace)
        self.assertTrue(m.advance_to(38))
        self.assertTrue(m.view().show_committed_furnace)
        self.assertEqual((m.view().state, m.view().marker_scale), ("exit", Fraction(7, 8)))
        self.assertTrue(m.advance_to(45))
        self.assertEqual((m.view().state, m.view().visible, m.view().text), ("done", False, ""))
        self.assertTrue(m.advance_to(20000))
        self.assertFalse(m.view().visible)

    def test_no_preview_without_eligibility_commit_or_actual_ids(self):
        m = Marker(SCENE)
        initial = dict(m.__dict__)
        self.assertFalse(m.begin_after_live_commit(100, PAYMENT, SCENE, PIECES))
        self.assertEqual(initial, m.__dict__)
        self.assertTrue(m.approach(1, True))
        armed = dict(m.__dict__)
        variants = (None, {}, {**PAYMENT, "revision": True}, {**PAYMENT, "typed_debit": {"wood": 3.0}},
                    {**PAYMENT, "typed_debit": {"wood": 2}}, {**PAYMENT, "grant": "storage"})
        for receipt in variants:
            self.assertFalse(m.begin_after_live_commit(100, receipt, SCENE, PIECES))
            self.assertEqual(armed, m.__dict__)
        for ids in (("a","a","c"), ("a","b",""), ("a","b"), list(PIECES)):
            self.assertFalse(m.begin_after_live_commit(100, PAYMENT, SCENE, ids))
            self.assertEqual(armed, m.__dict__)
        self.assertFalse(m.begin_after_live_commit(100, PAYMENT, "foreign", PIECES))
        self.assertEqual(armed, m.__dict__)

    def test_duplicates_out_of_order_cross_scene_stale_and_wrong_identity(self):
        m = self.make_started()
        for tick, scene, revision, ident in ((900, "foreign", 1, PIECES[0]),
                (900, SCENE, 2, PIECES[0]), (900, SCENE, True, PIECES[0]),
                (900, SCENE, 1, "storage-A"), (1, SCENE, 1, PIECES[0]),
                (3, SCENE, 1, PIECES[2])):
            initial = deepcopy(m.__dict__)
            self.assertFalse(m.arrive(tick, scene, revision, ident))
            self.assertEqual(initial, m.__dict__)
        self.assertTrue(m.arrive(3, SCENE, 1, PIECES[0]))
        initial = deepcopy(m.__dict__)
        self.assertFalse(m.arrive(5, SCENE, 1, PIECES[0]))
        self.assertFalse(m.begin_after_live_commit(12, PAYMENT, SCENE, PIECES))
        self.assertEqual(initial, m.__dict__)

    def test_missing_arrival_fails_to_authoritative_paid_display(self):
        m = self.make_started()
        self.assertTrue(m.arrive(3, SCENE, 1, PIECES[0]))
        self.assertTrue(m.advance_to(2+MOTION_DEADLINE-1))
        self.assertEqual(m.view().near_edge_fill, Fraction(1, 3))
        self.assertFalse(m.arrive(2+MOTION_DEADLINE, SCENE, 1, PIECES[1]))
        self.assertTrue(m.advance_to(2+MOTION_DEADLINE))
        self.assertFalse(m.view().visible)
        self.assertTrue(m.view().show_committed_furnace)
        self.assertFalse(m.arrive(2+MOTION_DEADLINE+1, SCENE, 1, PIECES[1]))

    def test_rapid_real_arrivals_do_not_jump_or_overtake_the_paid_total(self):
        m = self.make_started()
        self.assertTrue(m.arrive(10, SCENE, 1, PIECES[0]))
        self.assertTrue(m.advance_to(11))
        old = m.view().near_edge_fill
        self.assertEqual(old, Fraction(1, 12))
        self.assertTrue(m.arrive(11, SCENE, 1, PIECES[1]))
        self.assertEqual(m.view().near_edge_fill, old)
        self.assertTrue(m.arrive(11, SCENE, 1, PIECES[2]))
        self.assertEqual(m.view().near_edge_fill, old)
        self.assertFalse(m.view().show_committed_furnace)
        self.assertTrue(m.advance_to(14))
        self.assertTrue(old < m.view().near_edge_fill < 1)
        self.assertTrue(m.advance_to(15))
        self.assertEqual(m.view().near_edge_fill, 1)

    def test_exact_paid_restore_not_animation_and_replay_denied(self):
        m = Marker(SCENE, deepcopy(PAYMENT))
        self.assertEqual(m.view().state, "done")
        self.assertTrue(m.view().show_committed_furnace)
        self.assertFalse(m.approach(10, True))
        self.assertFalse(m.begin_after_live_commit(11, PAYMENT, SCENE, PIECES))
        self.assertFalse(m.arrive(12, SCENE, 1, PIECES[0]))
        self.assertTrue(m.advance_to(1000))
        self.assertEqual(m.view().state, "done")
        with self.assertRaises(ValueError):
            Marker(SCENE, {"revision": 1})

if __name__ == "__main__":
    unittest.main()
