"""Synthetic validator regression fixtures only; NOT game/device evidence."""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_gate as gate

class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = 'a' * 40
        self.status = {'required': {'placeholder_test_case': 'PASS_VERIFIED'}}
    def tearDown(self):
        self.temp.cleanup()
    def put(self, name, data):
        (self.root/name).write_bytes(data)
        return {'path':name, 'sha256':hashlib.sha256(data).hexdigest()}
    def trace(self, count=108001, end_ns=1800000000000, width=3840, height=2160, scale=1):
        stream=io.StringIO()
        writer=csv.writer(stream)
        writer.writerow(['presentation_ns','internal_width','internal_height','render_scale'])
        for i in range(count):
            writer.writerow([round(end_ns*i/(count-1)),width,height,scale])
        return stream.getvalue().encode()
    def manifest(self, **extra):
        data={'source_sha':self.source,'evidence_origin':'independently_executed',
              'apk':self.put('test-only.apk',b'NOT AN APK: synthetic test fixture'),
              'environment':{},'devices':[]}
        data.update(extra)
        (self.root/'release-evidence.json').write_text(json.dumps(data))
        return data
    def report(self):
        return gate.validate(self.root,self.source,self.status)
    def test_delivery_workflow_keeps_full_release_stage_scoped(self):
        workflow=(Path(__file__).resolve().parents[3]/'.github/workflows/havenline-device-release-gate.yml').read_text()
        for marker in [
            "ENFORCE_RELEASE_GATE:",
            "github.event_name == 'workflow_dispatch'",
            "github.ref == 'refs/heads/main'",
            "github.base_ref == 'main'",
            "startsWith(github.base_ref, 'release/')",
            "if: env.ENFORCE_RELEASE_GATE == 'true'",
            "python3 tools/havenline/release_gate.py",
            "validator regression tests remain mandatory",
        ]:
            self.assertIn(marker,workflow)
    def test_no_evidence_cannot_pass(self):
        self.assertFalse(self.report()['passed'])
    def test_missing_mandatory_game_check_rejected(self):
        self.manifest()
        self.assertTrue(any("Complete game requirement missing" in x for x in self.report()["errors"]))
    def test_empty_game_requirements_cannot_pass(self):
        self.manifest();self.status={'required':{}}
        self.assertIn('Complete game requirements are absent',self.report()['errors'])
    def test_stale_revision_rejected(self):
        self.manifest(source_sha='b'*40)
        self.assertIn('Evidence is stale or belongs to another source revision',self.report()['errors'])
    def test_synthetic_origin_rejected(self):
        self.manifest(evidence_origin='synthetic_fixture')
        self.assertIn('Evidence is not independently executed hardware/critic output',self.report()['errors'])
    def test_short_commit_rejected(self):
        self.manifest();self.source='abc'
        self.assertIn('Expected source must be an exact 40-character Git commit',self.report()['errors'])
    def test_local_pass_does_not_certify_gameplay(self):
        self.manifest();self.status['required']['placeholder_test_case']='PASS_LOCAL'
        self.assertTrue(any('PASS_LOCAL' in x for x in self.report()['errors']))
    def test_phone_alone_does_not_cover_tablet(self):
        self.manifest(devices=[{'case':'phone'}])
        self.assertTrue(any('tablet' in x for x in self.report()['errors']))
    def test_duplicate_views_rejected(self):
        self.manifest(environment={'views':[{'view':'mobile-render'}]*14})
        self.assertTrue(any('Fourteen unique' in x for x in self.report()['errors']))
    def test_score_nine_rejected(self):
        for score in [0,9,9.9,9.99,10.01,True,'NaN']:
            env={'source_sha':self.source,'apk_sha256':hashlib.sha256(b'NOT AN APK: synthetic test fixture').hexdigest()}
            r=dict(env,view='mobile-render',scores={name:score for name in gate.DIMENSIONS})
            self.manifest(environment=dict(env,views=[r]))
            self.assertTrue(any('10/10' in x or 'Boolean' in x or 'Non-finite' in x for x in self.report()['errors']))
    def test_emulator_is_not_physical(self):
        d={'case':'phone','source_sha':self.source,'apk_sha256':hashlib.sha256(b'NOT AN APK: synthetic test fixture').hexdigest(),'platform':'Android','physical_device':False}
        self.manifest(devices=[d]);self.assertTrue(any('Emulator/desktop' in x for x in self.report()['errors']))
    def test_missing_hash_rejected(self):
        with self.assertRaises(ValueError):gate.artifact(self.root,{'path':'absent'})
    def test_changed_artifact_rejected(self):
        p=self.put('frame',b'old');(self.root/'frame').write_bytes(b'new')
        with self.assertRaises(ValueError):gate.artifact(self.root,p)
    def test_empty_artifact_rejected(self):
        with self.assertRaises(ValueError):gate.artifact(self.root,self.put('empty',b''))
    def test_parent_escape_rejected(self):
        with self.assertRaises(ValueError):gate.artifact(self.root,{'path':'../escape','sha256':'a'*64})
    def test_absolute_path_rejected(self):
        with self.assertRaises(ValueError):gate.artifact(self.root,{'path':'/etc/passwd','sha256':'a'*64})
    def test_valid_artifact_bytes_retained(self):
        self.assertEqual(gate.artifact(self.root,self.put('bytes',b'actual bytes')),b'actual bytes')
    def test_synthetic_trace_calculation_is_not_physical_certification(self):
        r=gate.measure_presentations(self.trace())
        self.assertEqual(r['average_presented_fps'],60)
        self.assertEqual(r['duration_seconds'],1800)
        self.assertNotIn('physical_device_certified',r)
    def test_short_trace_fails(self):
        with self.assertRaisesRegex(ValueError,'30 sustained'):gate.measure_presentations(self.trace(1201,20000000000))
    def test_slow_trace_fails(self):
        with self.assertRaisesRegex(ValueError,'60 FPS'):gate.measure_presentations(self.trace(54001))
    def test_width_below_native_rejected(self):
        with self.assertRaisesRegex(ValueError,'native 4K'):gate.measure_presentations(self.trace(3,width=3839))
    def test_height_below_native_rejected(self):
        with self.assertRaisesRegex(ValueError,'native 4K'):gate.measure_presentations(self.trace(3,height=2159))
    def test_upscaling_rejected(self):
        with self.assertRaisesRegex(ValueError,'scaling'):gate.measure_presentations(self.trace(3,scale=.75))
    def test_duplicate_frame_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError,'increasing'):gate.measure_presentations(self.trace(3,end_ns=0))
    def test_empty_frame_trace_rejected(self):
        with self.assertRaisesRegex(ValueError,'No measured'):gate.measure_presentations(b'presentation_ns,internal_width,internal_height,render_scale\n')
    def test_unknown_thermal_rejected(self):
        data=[{'elapsed_seconds':0,'android_thermal_status':-1},{'elapsed_seconds':5,'android_thermal_status':0}]
        with self.assertRaises(ValueError):gate.check_thermal(json.dumps(data).encode(),1800)
    def test_severe_thermal_rejected(self):
        data=[{'elapsed_seconds':0,'android_thermal_status':3},{'elapsed_seconds':5,'android_thermal_status':0}]
        with self.assertRaises(ValueError):gate.check_thermal(json.dumps(data).encode(),1800)
    def test_short_thermal_trace_rejected(self):
        data=[{'elapsed_seconds':0,'android_thermal_status':0},{'elapsed_seconds':5,'android_thermal_status':0}]
        with self.assertRaisesRegex(ValueError,'full performance'):gate.check_thermal(json.dumps(data).encode(),1800)
    def test_complete_synthetic_thermal_trace(self):
        data=[{'elapsed_seconds':i,'android_thermal_status':0} for i in range(0,1801,5)]
        gate.check_thermal(json.dumps(data).encode(),1800)
    def test_missing_thermal_start_rejected(self):
        data=[{'elapsed_seconds':5,'android_thermal_status':0},{'elapsed_seconds':10,'android_thermal_status':0}]
        with self.assertRaisesRegex(ValueError,'session start'):gate.check_thermal(json.dumps(data).encode(),1800)
    def test_missing_thermal_middle_rejected(self):
        data=[{'elapsed_seconds':0,'android_thermal_status':0},{'elapsed_seconds':10,'android_thermal_status':0}]
        with self.assertRaisesRegex(ValueError,'incomplete'):gate.check_thermal(json.dumps(data).encode(),1800)
    def test_wrong_manifest_shape(self):
        (self.root/'release-evidence.json').write_text('[]');self.assertFalse(self.report()['passed'])
    def test_non_finite_and_boolean_numbers_rejected(self):
        for value in [True,False,float('inf'),'NaN']:
            with self.assertRaises(ValueError):gate.number(value)

if __name__=='__main__':unittest.main(verbosity=2)
