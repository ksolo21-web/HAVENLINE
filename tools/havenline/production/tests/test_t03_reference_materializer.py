"""Bounded T03 reference-art materialization does not reopen gameplay authority."""
from pathlib import Path
import json
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[4]


class T03ReferenceMaterializerTests(unittest.TestCase):
    def test_exact_branch_output_scope_and_trusted_authorization(self):
        path=ROOT/'.github/workflows/havenline-visual-repair-asset-materializer.yml'
        source=path.read_text();workflow=yaml.safe_load(source)
        t03=workflow['jobs']['materialize-t03'];t05=workflow['jobs']['materialize-t05']
        self.assertEqual(t03['if'],"github.ref_name == 'havenline/T03-reference-art-20260926'")
        self.assertEqual(t05['if'],"github.ref_name == 'havenline/T05-visual-repair-20260926'")
        self.assertEqual(t03['env'],t05['env'])
        steps='\n'.join(s.get('run','') for s in t03['steps'])
        self.assertIn("f'{integration}:Docs/Production/APPROVAL_INVALIDATIONS.json'",steps)
        self.assertIn("inv.get('historical_accepted_source')=='e1e7bb2d68d1d53025d1242011ad4c885f08c307'",steps)
        self.assertIn('git diff --cached --exit-code',steps)
        self.assertIn('git ls-files --others --exclude-standard',steps)
        self.assertIn('T03 materializer generated unauthorized path',steps)
        self.assertGreaterEqual(steps.count('test "$remote_head" = "$GITHUB_SHA"'),3)
        self.assertIn('HavenlineGodot/scripts/camp_boundary.gd',steps)
        self.assertIn('HavenlineGodot/scripts/river_geometry.gd',steps)
        self.assertIn('HavenlineGodot/scripts/camera_composition.gd',steps)
        self.assertIn('HavenlineGodot/assets/stations_v2',steps)
        self.assertNotIn('git add .',steps)
        self.assertNotIn('git push --force',steps)
        request=json.loads((ROOT/'Docs/Production/ChangeRequests/T03-reference-art-materializer.json').read_text())
        self.assertEqual(request['status'],'AUTHORIZED')
        self.assertEqual(request['allowed_generated_paths'],[
            'HavenlineGodot/assets/t03_boundary_v2/fence_panel.obj',
            'HavenlineGodot/assets/t03_boundary_v2/gate_post.obj',
            'HavenlineGodot/assets/t03_boundary_v2/gate_leaf.obj',
            'HavenlineGodot/assets/t03_boundary_v2/manifest.json',
        ])
        records=json.loads((ROOT/'Docs/Production/APPROVAL_INVALIDATIONS.json').read_text())['records']
        inv=next(r for r in records if r['task_id']=='T03' and r['status']=='ACTIVE')
        self.assertEqual(inv['repair_branch'],request['repair_branch'])
        self.assertEqual(inv['historical_accepted_source'],request['historical_accepted_source'])
        self.assertIs(inv['repair_candidate_allowed'],True)
        self.assertEqual(inv['repair_scope'],'VISUAL_ONLY')
        for authority in ['WORKSTREAM_REGISTRY.json','DEPENDENCY_GRAPH.json','task-gates.json']:
            self.assertNotIn('git add Docs/Production/'+authority,steps)


if __name__=='__main__':
    unittest.main()
