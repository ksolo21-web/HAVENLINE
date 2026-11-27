"""Negative integrity tests for a concrete plan; these do not test the game."""
import copy
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import completeness as cp
import device_matrix as dm


class CompletenessIntegrity(unittest.TestCase):
    def test_exact_complete_plan_and_preserved_task_mapping(self):
        result=cp.validate()
        self.assertTrue(result['passed'],result['errors'])
        self.assertFalse(result['runtime_approval_allowed'])
        self.assertFalse(result['runtime_tested'])
        self.assertIsNone(result['game_score'])
        rows=cp.crosswalk()['rows']
        self.assertEqual([r['task_id'] for r in rows],cp.TASKS+cp.UNDEFINED)
        self.assertTrue(all(r['status']=='SOURCE_NOT_FOUND' for r in rows[70:]))

    def test_missing_or_false_completion_rejected(self):
        probes=[
          ('missing pet',lambda c,a,e,t,s:a['all_pets_attack_contract']['species'].pop()),
          ('support-only owl',lambda c,a,e,t,s:a['all_pets_attack_contract']['species'][3].update(attack_required=False)),
          ('wrong attack',lambda c,a,e,t,s:a['all_pets_attack_contract']['species'][0].update(attack_profile='owl_attack')),
          ('no real scenario',lambda c,a,e,t,s:a['all_pets_attack_contract']['species'][0].update(mandatory_combat_scenario='')),
          ('level omitted',lambda c,a,e,t,s:e['progression_goals'].pop()),
          ('duplicate outcome',lambda c,a,e,t,s:e['progression_goals'][2].update(outcome=e['progression_goals'][1]['outcome'])),
          ('fake runtime receipt',lambda c,a,e,t,s:e['progression_goals'][1].update(exact_producer_receipt_binding='APPROVED')),
          ('unknown region',lambda c,a,e,t,s:e['region_designs'].pop()),
          ('enemy role omitted',lambda c,a,e,t,s:e['enemy_roster_recommendation'].pop()),
          ('reserve silently activated',lambda c,a,e,t,s:e['enemy_roster_recommendation'][3].update(disposition='SELECTED_LAUNCH_HOSTILE_FOR_FORWARD_IMPLEMENTATION')),
          ('missing resource',lambda c,a,e,t,s:e['resource_value_decisions'].pop()),
          ('currency multiplied',lambda c,a,e,t,s:e['resource_value_decisions'][17].update(id='pocket_wallet')),
          ('art concept omitted',lambda c,a,e,t,s:e['resource_value_decisions'][2].update(aliases=[])),
          ('worker capacity downgraded',lambda c,a,e,t,s:c['selected_policy'].update(survivor_logical_capacity='SIX_SMALL_SLOTS')),
          ('boundary omitted',lambda c,a,e,t,s:t['rows'].pop()),
          ('unrun test passed',lambda c,a,e,t,s:t['rows'][0].update(runtime_test_status='PASS')),
          ('fake game approval',lambda c,a,e,t,s:c.update(runtime_approval_allowed=True)),
          ('missing gap',lambda c,a,e,t,s:c['requirements'].pop()),
          ('undefined source closed',lambda c,a,e,t,s:c['requirements'][-1].update(specification_status='CLOSED')),
          ('old decision forgotten',lambda c,a,e,t,s:c['prior_decision_dispositions'].pop()),
          ('old source selected',lambda c,a,e,t,s:s.update(selected_branch='alfred/level-1-replacement')),
          ('stale observed head',lambda c,a,e,t,s:s.update(observed_head=cp.GAME)),
          ('ownership reassigned',lambda c,a,e,t,s:s.update(ownership_reassignment_allowed=True)),
        ]
        for name,mutate in probes:
            with self.subTest(name=name):
                data=copy.deepcopy(cp.load());mutate(*data)
                self.assertTrue(cp.validate_data(*data),name)

    def test_source_omission_rejected(self):
        original=cp.read
        def missing(root,rel):
            result=original(root,rel)
            if rel.endswith('SOURCE_BINDINGS.json'):result['sources']=[]
            return result
        with patch.object(cp,'read',side_effect=missing):
            result=cp.validate()
        self.assertFalse(result['passed'])
        self.assertIn('exact source universe omitted, duplicated or changed',result['errors'])

    def test_latest_reported_evidence_does_not_become_runtime_approval(self):
        note=cp.read(cp.ROOT,cp.PACKAGE+'LATEST_SOURCE_DELTA.json')
        self.assertEqual(cp.validate_latest_source(note),[])
        for mutate in [lambda n:n.update(fixed_review_cutoff=cp.GAME),
                       lambda n:n['approval'].update(runtime_approved=True),
                       lambda n:n['reported_build13'].update(all_values_are_reported_not_reexecuted=False),
                       lambda n:n['source_file_pairs'].pop(),
                       lambda n:n['reference_custody'].update(media_downloaded_or_played_back_by_this_audit=True)]:
            changed=copy.deepcopy(note);mutate(changed)
            self.assertTrue(cp.validate_latest_source(changed))

    def test_task_projection_routes_actual_gaps_without_task_invention(self):
        for task,ids in {'T23':['CG02','CG03','CG06'], 'T26':['CG01','CG05'],
                         'T27':['CG01','CG05'], 'T33':['CG09','CG10'],
                         'T43':['CG12','CG20'], 'T58':['CG17','CG18'], 'T70':['CG23','CG24']}.items():
            text=cp.task_section(task)
            for identity in ids:self.assertIn(identity,text)
            self.assertIn('not new dependency edges',text)
        with self.assertRaises(ValueError):cp.task_section('T71')


class LayoutFixtureIntegrity(unittest.TestCase):
    def matrix(self):return cp.read(cp.ROOT,cp.DOCS+'DEVICE_LAYOUT_MATRIX.json')

    def test_actual_six_states_and_native_tablet_rounding(self):
        matrix=self.matrix()
        self.assertEqual(dm.validate_layout_definition(matrix),[])
        self.assertEqual(matrix['states'][0]['logical_size'],[1920,1080])
        self.assertEqual(matrix['states'][1]['logical_size'],[2400,1080])
        self.assertEqual(matrix['states'][3]['logical_size'],[2732,2048])

    def test_old_duplicate_aspect_and_omission_fail(self):
        probes=[lambda m:m['states'][0].update(logical_size=[2400,1080]),
                lambda m:m['states'].pop(),
                lambda m:m['states'][1].update(id='phone_16_9'),
                lambda m:m['states'][0].update(logical_size=[1080,1920]),
                lambda m:m['states'][0].update(logical_size=[1920,0]),
                lambda m:m['states'][0].update(logical_size=[True,1080]),
                lambda m:m.update(landscape_required=False),
                lambda m:m.update(checks=[])]
        for mutate in probes:
            matrix=self.matrix();mutate(matrix)
            self.assertTrue(dm.validate_layout_definition(matrix))


if __name__=='__main__':unittest.main()
