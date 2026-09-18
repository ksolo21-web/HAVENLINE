import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('readiness', ROOT / 'tools/havenline/task10/validate_critic_readiness.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AuthorityReadinessTests(unittest.TestCase):
    def records(self):
        return [
            {'candidate': 'a' * 40},
            {'candidate': 'a' * 40, 'fixture_simulation_only': False, 'real_t09_adapter_bound': True},
            *[{'candidate': 'a' * 40, 'real_t09_adapter_bound': True, 'exact_debit_verified': True, 'fixture_only': False} for _ in range(2)]
        ]

    def test_bound_source_passes(self):
        self.assertEqual([], module.authority_errors(*self.records(), 'a' * 40))

    def test_each_stale_source_rejects(self):
        for index in range(4):
            rows = self.records()
            rows[index]['candidate'] = 'b' * 40
            self.assertTrue(module.authority_errors(*rows, 'a' * 40))

    def test_fixture_or_missing_debit_rejects(self):
        for index, field in [(1, 'real_t09_adapter_bound'), (2, 'exact_debit_verified'), (3, 'real_t09_adapter_bound')]:
            rows = self.records()
            rows[index][field] = False
            self.assertTrue(module.authority_errors(*rows, 'a' * 40))

class PackageBindingTests(unittest.TestCase):
    def package(self,root):
        import hashlib,json,sys
        sys.path.insert(0,str(ROOT/'tools/havenline/task10'))
        import build_critic_evidence as build
        from validate_progression import REQUIRED
        from critic_profile import resolve_critic
        fixture_spec=importlib.util.spec_from_file_location('benchmark_fixture',Path(__file__).with_name('test_build_critic_evidence.py'))
        fixture=importlib.util.module_from_spec(fixture_spec);fixture_spec.loader.exec_module(fixture)
        candidate='a'*40
        def write(name,value):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value if isinstance(value,str) else json.dumps(value))
        def item(name,category,kind='json',description=''):
            return dict(path='critic-input/'+name,category=category,kind=kind,description=description,sha256=hashlib.sha256((root/name).read_bytes()).hexdigest())
        required=['FROZEN_SCOPE.md','recipes.json','progression.json','domain-tests.json','integration-tests.json','review-summary.json','motion-timeline.json','save-matrix/save-matrix.json','benchmark/manifest.json','performance.json']
        for name in required:write(name,{})
        progression=dict(passed=True,executed=True,suites=[dict(suite=k,checks=len(v),required_checks=sorted(v),passed=True) for k,v in REQUIRED.items()])
        write('progression.json',progression);write('benchmark/manifest.json',fixture.BenchmarkEvidenceTests().fixture())
        write('scope-brief.txt',build.SCOPE_SYNOPSIS)
        write('progression-brief.txt',build.compact_progression(progression)+'\nRaw critic-input/progression.json SHA256 '+build.digest(root/'progression.json')+'\n')
        write('review-output-contract.txt',build.REVIEW_OUTPUT_CONTRACT)
        images=['native4k/'+state+'-front.png' for state in module.REQUIRED_STATES]+['capture/motion-000.png','device-layout/phone/blocked-front.png','device-layout/phone/complete-front.png']
        for name in images:write(name,'pixel fixture')
        execution=json.loads((ROOT/'Docs/Production/CRITIC_EXECUTION.json').read_text());matrix=json.loads((ROOT/'Docs/Production/CRITIC_MATRIX.json').read_text())
        preserved=[item(name,'preserved_raw') for name in required]
        for cid in ('C3','C4','C6','C7'):
            if cid in ('C3','C4'):
                categories=sorted(resolve_critic('T10',cid,execution,matrix)[0]['required_categories'])
                items=[item(name,categories[i%len(categories)],'motion_frame' if name.startswith('capture/') else 'image') for i,name in enumerate(images)]
                items += [item('scope-brief.txt','task_scope','text'),item('review-output-contract.txt','task_scope','text',build.REVIEW_OUTPUT_DESCRIPTION)]
            elif cid=='C7':
                categories=resolve_critic('T10',cid,execution,matrix)[0]['required_categories']
                items=[item('domain-tests.json',category) for category in categories]
            else:items=[item('performance.json','quantitative_budgets')]
            write(cid+'-manifest.json',dict(candidate_commit=candidate,critic_id=cid,task_id='T10',preserved_sources=preserved,groups=[dict(id='fixture',items=items)]))
        write('evidence-index.json',dict(candidate=candidate,files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}))
        return candidate

    def test_real_transported_consumer_and_mutations(self):
        import hashlib,json,sys,tempfile
        from unittest.mock import patch
        sys.path.insert(0,str(ROOT/'tools/havenline/task10'))
        import build_critic_evidence as build
        for change in ('valid','content','contract_hash','path','order','duplicate','missing','index'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as t:
                root=Path(t)/'arbitrary-package-name';root.mkdir();candidate=self.package(root)
                manifest_path=root/'C3-manifest.json';manifest=json.loads(manifest_path.read_text());items=manifest['groups'][0]['items']
                index=json.loads((root/'evidence-index.json').read_text())
                if change=='content':
                    (root/'review-output-contract.txt').write_text('changed')
                    h=hashlib.sha256(b'changed').hexdigest();index['files']['review-output-contract.txt']=h
                    for cid in ('C3','C4'):
                        p=root/(cid+'-manifest.json');d=json.loads(p.read_text());d['groups'][0]['items'][-1]['sha256']=h;p.write_text(json.dumps(d));index['files'][p.name]=build.digest(p)
                    manifest=json.loads(manifest_path.read_text())
                elif change=='contract_hash':items[-1]['sha256']='0'*64
                elif change=='path':items[-1]['path']='review-output-contract.txt'
                elif change=='order':items.reverse()
                elif change=='duplicate':items.append(copy.deepcopy(items[-1]))
                elif change=='missing':items.pop()
                elif change=='index':index['files']['review-output-contract.txt']='0'*64
                manifest_path.write_text(json.dumps(manifest));index['files'][manifest_path.name]=build.digest(manifest_path)
                (root/'evidence-index.json').write_text(json.dumps(index))
                if change in ('index','contract_hash','path'):
                    with patch.object(build,'prompt_errors',side_effect=AssertionError('normalization must not run before canonical integrity')) as prompt:
                        errors=module.package_errors(root,candidate);prompt.assert_not_called()
                else:errors=module.package_errors(root,candidate)
                if change=='valid':self.assertEqual([],errors)
                else:self.assertTrue(errors)

    def test_missing_or_tampered_raw_package_rejects(self):
        import hashlib,json,sys,tempfile
        sys.path.insert(0,str(ROOT/'tools/havenline/task10'))
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);raw=root/'progression.json';raw.write_text('{}')
            index=dict(candidate='a'*40,files={'progression.json':hashlib.sha256(raw.read_bytes()).hexdigest()})
            (root/'evidence-index.json').write_text(json.dumps(index))
            raw.write_text('{"tampered":true}')
            errors=module.package_errors(root,'a'*40)
            self.assertTrue(any('indexed raw digest mismatch' in e for e in errors))
            raw.unlink()
            self.assertTrue(module.package_errors(root,'a'*40))
            self.assertTrue(module.package_errors(root,'b'*40))
