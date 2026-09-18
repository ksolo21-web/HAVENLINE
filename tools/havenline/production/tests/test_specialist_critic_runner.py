import copy
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from specialist_critic_runner import response_schema, response_bounds_errors

class ResponseBoundsTests(unittest.TestCase):
    def test_t10_schema_preserves_scores_and_enforces_bounds(self):
        schema=response_schema('T10',['one','two'])
        self.assertEqual(schema['properties']['scores']['required'],['one','two'])
        self.assertEqual(schema['properties']['observations'],{'type':'array','items':{'type':'string','maxLength':160},'minItems':2,'maxItems':2})
        self.assertEqual(schema['properties']['defects']['maxItems'],5)
        self.assertEqual(schema['properties']['defects']['items']['maxLength'],160)
        self.assertFalse(schema['additionalProperties'])
    def test_other_tasks_unchanged(self):
        for task in ['T09','T11',None]:
            schema=response_schema(task,['a'])
            self.assertEqual(schema['properties']['observations'],{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':5})
            self.assertEqual(schema['properties']['defects'],{'type':'array','items':{'type':'string'},'maxItems':5})
            self.assertEqual(response_bounds_errors(task,{}),[])
    def test_hostile_response_bounds(self):
        valid={'observations':['a'*160,'b'],'defects':['c'*160]*5}
        self.assertEqual(response_bounds_errors('T10',valid),[])
        for field,values in [('observations',[]),('observations',['a']),('observations',['a']*3),('observations',['a'*161,'b']),('observations',[1,'b']),('observations',None),('defects',['a']*6),('defects',['a'*161]),('defects',[{}]),('defects','bad')]:
            broken=copy.deepcopy(valid);broken[field]=values
            self.assertTrue(response_bounds_errors('T10',broken),(field,values))
        self.assertTrue(response_bounds_errors('T10',{}))
