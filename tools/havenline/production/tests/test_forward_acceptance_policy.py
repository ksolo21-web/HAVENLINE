"""Regression checks for stale/weak policy projections and historical custody."""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from lib import DOCS,ROOT
from validate_migration import forward_acceptance_errors,_strict_score_errors


class ForwardAcceptancePolicyTests(unittest.TestCase):
    def setUp(self):
        self.graph=json.loads((DOCS/'DEPENDENCY_GRAPH.json').read_text())
        self.matrix=json.loads((DOCS/'CRITIC_MATRIX.json').read_text())
        self.policy=json.loads((DOCS/'REFERENCE_ACCEPTANCE_POLICY.json').read_text())

    def test_current_forward_projections_agree(self):
        self.assertEqual([],forward_acceptance_errors(self.graph,self.matrix,self.policy))

    def test_execution_metadata_cannot_advertise_a_weaker_forward_rule(self):
        execution=json.loads((DOCS/'CRITIC_EXECUTION.json').read_text())
        self.assertEqual([],forward_acceptance_errors(self.graph,self.matrix,self.policy,execution))
        execution['forward_acceptance']['reference_sensitive_dimension_threshold']=9.5
        self.assertTrue(forward_acceptance_errors(self.graph,self.matrix,self.policy,execution))

    def test_legacy_forward_floor_cannot_masquerade_as_current(self):
        for projection,operator,threshold in (
            (self.graph['acceptance_rule'],'mandatory_dimension_operator','mandatory_dimension_threshold'),
            (self.matrix['forward_acceptance'],'dimension_operator','threshold'),
        ):
            original=copy.deepcopy(projection)
            projection.update({operator:'>',threshold:9.0})
            self.assertTrue(forward_acceptance_errors(self.graph,self.matrix,self.policy))
            projection.clear();projection.update(original)

    def test_missing_or_weakened_reference_contract_is_rejected(self):
        for key,value in (('reference_sensitive_dimension_threshold',9.5),('stricter_exact_visual_score',9.9),('unrounded',False),('no_average_waiver',False),('reference_sensitive_9_5_is_interim_only',False),('reference_sensitive_critic_ids',['C1'])):
            graph=copy.deepcopy(self.graph);graph['acceptance_rule'][key]=value
            with self.subTest(key=key):
                self.assertTrue(forward_acceptance_errors(graph,self.matrix,self.policy))

    def test_policy_cannot_lower_floor_even_when_projections_follow_it(self):
        policy=copy.deepcopy(self.policy);policy['final_acceptance']['reference_minimum_dimension_score']=9.5
        graph=copy.deepcopy(self.graph);graph['acceptance_rule']['reference_sensitive_dimension_threshold']=9.5
        matrix=copy.deepcopy(self.matrix);matrix['forward_acceptance']['reference_sensitive_dimension_threshold']=9.5
        self.assertTrue(forward_acceptance_errors(graph,matrix,policy))

    def test_historical_rule_still_rejects_invalid_numeric_data(self):
        for value in (True,None,'9.9',float('nan'),float('inf'),float('-inf'),10.01,9.0):
            with self.subTest(value=value):
                self.assertTrue(_strict_score_errors('historical',{'dimension':value}))
        self.assertEqual([],_strict_score_errors('historical',{'dimension':9.00001}))

    def test_historical_receipts_remain_byte_identical(self):
        receipts=self.policy['historical_preservation']['immutable_receipts']
        self.assertEqual(11,len(receipts))
        for row in receipts:
            with self.subTest(task=row['task_id']):
                self.assertEqual(row['sha256'],hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest())
        self.assertIs(False,self.policy['historical_preservation']['historical_validation_is_new_approval'])
        self.assertIs(False,self.policy['historical_preservation']['candidate_sha_alone_allows_bypass'])

    def test_task_identity_and_undefined_tasks_preserved(self):
        self.assertEqual([f'T{i:02d}' for i in range(1,71)],list(self.graph['tasks']))
        self.assertEqual(set(self.graph['tasks']),set(self.matrix['task_applicability']))
        self.assertNotIn('T71',self.graph['tasks'])

if __name__=='__main__':
    unittest.main()
