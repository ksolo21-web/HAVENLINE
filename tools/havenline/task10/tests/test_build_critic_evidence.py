import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('t10build',Path(__file__).parents[1]/'build_critic_evidence.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MotionEvidenceTests(unittest.TestCase):
 def rows(self):
  states=['ready','blocked','preview','committing','complete','replay']
  return states,[dict(state=s,start_frame=i*32+2,end_frame=i*32+32) for i,s in enumerate(states)],dict(r_frame_rate='30/1',nb_frames='194')
 def test_complete_ordered_cycle(self):self.assertEqual([],m.motion_errors(*self.rows()))
 def test_missing_state_rejects(self):
  s,r,v=self.rows();r.pop();self.assertTrue(m.motion_errors(s,r,v))
 def test_short_pulse_or_overlap_rejects(self):
  for field,value in [('end_frame',110),('start_frame',60)]:
   s,r,v=self.rows();r[3][field]=value;self.assertTrue(m.motion_errors(s,r,v))
 def test_false_framerate_or_truncated_video_rejects(self):
  for field,value in [('r_frame_rate','2/1'),('nb_frames','170')]:
   s,r,v=self.rows();v[field]=value;self.assertTrue(m.motion_errors(s,r,v))
