"""Hostile tests of the two previously rejected full-domain evidence paths."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from tools.havenline.task10.tests import test_verify_rendered_clearance as fixture

PATH = Path(__file__).parents[1] / 'verify_rendered_clearance_domain.py'
spec = importlib.util.spec_from_file_location('domain', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class DomainTests(unittest.TestCase):
    def make_manifest(self, root):
        helper = fixture.RenderedClearanceTests()
        records = helper.records(root)
        profile = 'fixture'
        digest = m.sha256(PATH)
        for row in records:
            state = row['state']
            row['projected_readability'].update(passed=True, placement_found=True)
            nonce = hashlib.sha256(f'{fixture.SOURCE}:{fixture.PROBE_SOURCE}:{state}:gameplay:{profile}'.encode()).hexdigest()
            layers = row['rendered_clearance_layers']
            layers['case_nonce'] = nonce
            for layer in layers['layer_records'].values():
                core = layer['core']
                core.update(domain_profile=profile, evidence_scale=1.0, case_nonce=nonce, probe_verifier_sha256=digest)
                layer['core_json'] = json.dumps(core, separators=(',', ':'))
                layer['core_sha256'] = hashlib.sha256(layer['core_json'].encode()).hexdigest()
        manifest = helper.manifest(records)
        manifest.update(domain_profile=profile,evidence_scale=1.0,passed=True)
        manifest['rendered_clearance_identity']['probe_verifier_sha256'] = digest
        return manifest

    def verify(self, root, manifest):
        path = root/'manifest.json'; path.write_text(json.dumps(manifest))
        with patch.dict(m.PROFILES, {'fixture':(tuple(fixture.LOGICAL_SIZE),tuple(fixture.CAPTURE_SIZE),1.0)}), \
             patch.object(m,'profile_cases',return_value={(s,'gameplay') for s in m.STATES}):
            return m.verify(root,path,root/'masks',fixture.SOURCE,fixture.PRODUCT_SHA,'candidate',
                            fixture.PROBE_SOURCE,fixture.CAPTURE_SHA,m.sha256(PATH),fixture.WORKFLOW_SHA,
                            fixture.RESOURCE_SHA,'fixture')

    def test_geometry_failure_retains_every_case_and_mask(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); manifest=self.make_manifest(root)
            self.assertTrue(self.verify(root,manifest)['passed'])
            manifest['passed']=False
            manifest['records'][0]['projected_readability'].update(passed=False,placement_found=False)
            report=self.verify(root,manifest)
            self.assertFalse(report['passed'])
            self.assertEqual(len(report['rows']),6)
            self.assertEqual(len(list((root/'masks').glob('*.png'))),24)
            self.assertEqual(report['failure_count'],1)

    def test_rehashed_normal_substitutions_are_rejected(self):
        for mutation in ('white','single_pixel','response_recolor','response_erase'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as d:
                root=Path(d); manifest=self.make_manifest(root)
                layer=manifest['records'][0]['rendered_clearance_layers']['layer_records']['normal']
                target=root/layer['file']
                if mutation=='white':
                    image=Image.new('RGB',tuple(fixture.CAPTURE_SIZE),'white')
                elif mutation=='response_erase':
                    image=Image.open(target).convert('RGB')
                    image.paste((16,24,32),(110,100,160,170))
                elif mutation=='response_recolor':
                    image=Image.open(target).convert('RGB')
                    image.putpixel((150,130),(255,0,0))
                else:
                    image=Image.open(root/'ready-gameplay-response-only.png').convert('RGB')
                    image.putpixel((140,50),(255,255,255))
                image.save(target); layer['sha256']=m.sha256(target)
                report=self.verify(root,manifest)
                self.assertFalse(report['passed'])
                self.assertFalse(report['rows'][0]['normal_correspondence']['passed'])

    def test_entirely_offscreen_label_retains_all_masks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); manifest=self.make_manifest(root)
            row=manifest['records'][0]
            layer=row['rendered_clearance_layers']['layer_records']['label_id']
            Image.new('RGB',tuple(fixture.CAPTURE_SIZE),'black').save(root/layer['file'])
            layer['sha256']=m.sha256(root/layer['file'])
            row['projected_readability'].update(passed=False,placement_found=False)
            manifest['passed']=False
            report=self.verify(root,manifest)
            self.assertFalse(report['passed'])
            self.assertEqual(len(report['rows']),6)
            self.assertEqual(len(list((root/'masks').glob('*.png'))),24)
            self.assertEqual(report['rows'][0]['label_mask_pixels'],0)

    def test_domain_is_exactly_650(self):
        keys={(p,s,a,geometry[2]) for p,geometry in m.PROFILES.items() for s,a in m.profile_cases(p)}
        self.assertEqual(len(keys),650)
        self.assertEqual(sum(s=='committing' for p,s,a,scale in keys),108)

if __name__=='__main__': unittest.main()
