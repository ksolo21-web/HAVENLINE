import pathlib
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from failure_intelligence import query_packet
from validate_architecture_v32_t10 import failure_delta_errors, FAILURE
import validate_architecture_release_lock as v31

class FailurePacketTests(unittest.TestCase):
    def test_actual_c0_packet_field_is_queried(self):
        with patch('failure_intelligence.query',return_value={}) as query:
            query_packet({'task_id':'T10','failed_logs':'distinct-root-cause-signature'})
            self.assertIn('distinct-root-cause-signature',query.call_args.args[2])
    def test_legacy_precedence_and_limit_unchanged(self):
        for packet,expected,absent in [({'logs':'legacy'},'legacy','missing'),({'failed_logs':'current','logs':'legacy'},'current','legacy'),({'failure_excerpt':'preferred','failed_logs':'current'},'preferred','current')]:
            with patch('failure_intelligence.query',return_value={}) as query:
                query_packet(packet,limit=3)
                text=query.call_args.args[2]
                self.assertIn(expected,text);self.assertNotIn(absent,text)
                self.assertEqual(query.call_args.kwargs['limit'],3)
    def test_exact_lock_delta_rejects_drift(self):
        accepted=v31._git('show',f'{v31.ACCEPTED_SOURCE}:{FAILURE}').stdout.decode()
        current=(v31.ROOT/FAILURE).read_text()
        self.assertEqual(failure_delta_errors(accepted,current),[])
        for broken in [current+'\n# drift\n',current.replace('len(overlap) * 5','len(overlap) * 4'),accepted]:
            self.assertTrue(failure_delta_errors(accepted,broken))
