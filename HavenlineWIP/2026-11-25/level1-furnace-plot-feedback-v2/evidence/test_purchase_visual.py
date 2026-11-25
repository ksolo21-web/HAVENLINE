from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import unittest

from purchase_visual import Marker, ObservedMount, PAYMENT, MOTION_DEADLINE
SCENE = "fixture-scene"
POSE = (1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0)
# Synthetic tokens are unit-test inputs only. They are not claims of real game nodes.
OBS = tuple(ObservedMount(source, obj, POSE, True) for source, obj in
            zip(("wood-a", "wood-b", "wood-c"), (101, 102, 103)))

class TestPlotOnly(unittest.TestCase):
    def stage(self, m, *, tick=10, grounded=True, observations=OBS):
        self.assertTrue(m.approach(tick, True, grounded=grounded, observations=observations))

    def pay(self, m, *, tick=10, live=True):
        self.assertTrue(m.publish_paid(tick, deepcopy(PAYMENT), SCENE, live_commit=live))
        self.assertTrue(m.view().show_committed_furnace and m.view().show_committed_camp)

    def blocked(self, m):
        v = m.view()
        self.assertEqual((v.state, v.visible, v.near_edge_fill, v.fill_target), ("done", False, 0, 0))
        self.assertTrue(v.show_committed_camp and v.show_committed_furnace)
        self.assertFalse(m.arrive(999, SCENE, 1, 101))

    def test_same_tick_success_immediate_furnace_and_camp_through_entire_effect(self):
        m = Marker(SCENE)
        self.assertEqual(m.view().corners, "white")
        self.stage(m)
        self.assertEqual(m.view().corners, "lime")
        self.assertEqual(m.view().near_edge_fill, 0)
        self.assertFalse(m.view().show_committed_furnace)
        self.pay(m)
        self.assertEqual(m.view().state, "paying")
        for index, (tick, subject) in enumerate(((11, 103), (21, 101), (31, 102))):
            self.assertTrue(m.advance_to(tick - 1))
            self.assertEqual(m.view().fill_target, Fraction(index, 3))
            self.assertTrue(m.arrive(tick, SCENE, 1, subject))
            self.assertEqual(m.view().fill_target, Fraction(index + 1, 3))
            self.assertLess(m.view().near_edge_fill, m.view().fill_target)
            self.assertTrue(m.advance_to(tick+4))
            self.assertEqual(m.view().near_edge_fill, m.view().fill_target)
            self.assertEqual(m.view().text, "3 WOOD")
            self.assertTrue(m.view().show_committed_camp and m.view().show_committed_furnace)
        self.assertEqual(m.view().state, "full_hold")
        self.assertTrue(m.advance_to(41))
        self.assertEqual((m.view().state, m.view().marker_scale), ("exit", Fraction(7, 8)))
        self.assertTrue(m.view().show_committed_furnace)
        self.assertTrue(m.advance_to(48))
        self.blocked(m)

    def test_stale_hover_old_or_one_tick_ago_paid_but_never_plays(self):
        for now in (11, 10010):
            with self.subTest(now=now):
                m = Marker(SCENE)
                self.stage(m)
                self.assertTrue(m.advance_to(now))
                self.assertEqual((m.view().state, m.view().corners), ("idle", "white"))
                self.pay(m, tick=now)
                self.blocked(m)

    def test_stock_baseline_missing_observed_identities_fail_closed_at_0_1_2(self):
        for n in range(3):
            with self.subTest(n=n):
                m = Marker(SCENE)
                self.stage(m, observations=OBS[:n])
                self.pay(m)
                self.blocked(m)

    def test_grounded_source_lineage_node_ownership_and_unique_finite_pose_required(self):
        malformed_sets = (OBS[:-1]+(replace(OBS[2], source_id="wood-a"),),
                          OBS[:-1]+(replace(OBS[2], native_id=101),),
                          OBS[:-1]+(replace(OBS[2], is_owned_and_visible=False),),
                          OBS[:-1]+(replace(OBS[2], world_affine=(float("nan"),)+POSE[1:]),),
                          OBS[:-1]+(replace(OBS[2], world_affine=(0,)*12),),
                          OBS[:-1]+(replace(OBS[2], source_id="storage-A"),))
        for observations in malformed_sets:
            m = Marker(SCENE)
            self.stage(m, observations=observations)
            self.pay(m)
            self.blocked(m)
        m = Marker(SCENE)
        self.stage(m, grounded=False)
        self.pay(m)
        self.blocked(m)

    def test_same_tick_lost_overlap_does_not_reuse_old_armed_sample(self):
        m = Marker(SCENE)
        self.stage(m)
        self.assertTrue(m.approach(10, False, grounded=True, observations=OBS))
        self.pay(m)
        self.blocked(m)

    def test_save_failure_wrong_receipt_fields_and_wrong_scene_no_paid_or_fill(self):
        m = Marker(SCENE)
        self.stage(m)
        for wrong in (None, {}, {**PAYMENT, "revision": True}, {**PAYMENT, "typed_debit": {"wood": 4}}):
            self.assertFalse(m.publish_paid(10, wrong, SCENE, live_commit=True))
        self.assertFalse(m.publish_paid(10, PAYMENT, "foreign", live_commit=True))
        self.assertFalse(m.arrive(10, SCENE, 1, 101))
        self.assertEqual((m.view().state, m.view().fill_target), ("armed", 0))
        self.assertFalse(m.view().show_committed_furnace or m.view().show_committed_camp)

    def test_same_tick_duplicate_delayed_or_unowned_arrivals_do_not_fill(self):
        m = Marker(SCENE)
        self.stage(m)
        self.pay(m)
        self.assertFalse(m.publish_paid(10, PAYMENT, SCENE, live_commit=True))
        self.assertTrue(m.arrive(12, SCENE, 1, 101))
        for tick, scene, revision, ident in ((12, SCENE, 1, 101), (13, SCENE, 1, 222),
                (13, "stale", 1, 102), (13, SCENE, 2, 102), (11, SCENE, 1, 102),
                (55, SCENE, 1, 102), (100, SCENE, 1, 103)):
            self.assertFalse(m.arrive(tick, scene, revision, ident))
            self.assertEqual(m.view().fill_target, Fraction(1, 3))
        self.assertTrue(m.advance_to(55))  # Deadline: never claim full green on timeout.
        self.blocked(m)

    def test_restored_paid_snapshot_never_replays_even_with_fresh_observation(self):
        for m in (Marker(SCENE, deepcopy(PAYMENT)), Marker(SCENE)):
            if not m.view().show_committed_furnace:
                self.stage(m)
                self.pay(m, live=False)
            self.blocked(m)
            self.assertFalse(m.publish_paid(10000, PAYMENT, SCENE, live_commit=True))

    def test_rapid_arrivals_only_ramp_to_confirmed_total(self):
        m = Marker(SCENE)
        self.stage(m)
        self.pay(m)
        self.assertTrue(m.arrive(11, SCENE, 1, 101))
        self.assertTrue(m.advance_to(12))
        p = m.view().near_edge_fill
        self.assertEqual(p, Fraction(1,12))
        self.assertTrue(m.arrive(12, SCENE, 1, 102))
        self.assertTrue(m.arrive(12, SCENE, 1, 103))
        self.assertEqual(m.view().near_edge_fill, p)
        self.assertTrue(m.view().show_committed_furnace and m.view().show_committed_camp)
        self.assertTrue(m.advance_to(16))
        self.assertEqual(m.view().near_edge_fill, 1)

if __name__ == "__main__":
    unittest.main()
