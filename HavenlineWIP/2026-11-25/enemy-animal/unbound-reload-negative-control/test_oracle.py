import copy
import unittest
from assert_unbound_reload import check

class SyntheticOracleControls(unittest.TestCase):
    def sample(self):
        s = dict(encounter_id='fixture', animal_id='fixture-animal', encounter_phase='live', encounter_active=True,
                 animal_active=True, binding_approved=False, binding_active=False,
                 cooldown=0, encounter_clock=11, animal_health=5, player_health=9, camp_condition=8,
                 damage_events=0,drop_events=0,completion_events=0,exit_events=0,
                 pending_custody={},reward_ledger={},exit_progress={})
        return dict(restored_before_ticks=copy.deepcopy(s),observed_after_ticks=copy.deepcopy(s),
                    ordinary_ticks_observed=3,in_contact_geometry_before_ticks=True)

    def test_control(self):
        self.assertEqual(check(self.sample()),[])

    def test_mutations(self):
        for field, value in dict(player_health=8, camp_condition=7, encounter_clock=10,
                                 encounter_active=False, animal_active=False, encounter_id='replacement',
                                 damage_events=1, drop_events=1, completion_events=1, exit_events=1,
                                 reward_ledger={'test':1},exit_progress={'test':True},
                                 pending_custody={'lost':True}, binding_active=True).items():
            with self.subTest(field=field):
                ev = self.sample()
                ev['observed_after_ticks'][field] = value
                self.assertTrue(check(ev))

    def test_requires_evidence(self):
        for field in ('observed_after_ticks','in_contact_geometry_before_ticks','ordinary_ticks_observed'):
            with self.subTest(field=field):
                ev = self.sample()
                del ev[field]
                self.assertTrue(check(ev))

    def test_cooldown_ready_on_restore(self):
        ev = self.sample()
        ev['restored_before_ticks']['cooldown'] = ev['observed_after_ticks']['cooldown'] = 1
        self.assertTrue(check(ev))
