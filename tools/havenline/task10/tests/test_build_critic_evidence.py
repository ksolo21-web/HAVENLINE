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

class CompactEvidenceTests(unittest.TestCase):
 def test_all_required_progression_checks_preserved(self):
  import sys
  sys.path.insert(0,str(Path(__file__).parents[1]))
  from validate_progression import REQUIRED
  report=dict(passed=True,executed=True,suites=[dict(suite=k,checks=len(v),required_checks=sorted(v),passed=True) for k,v in REQUIRED.items()])
  text=m.compact_progression(report)
  for names in REQUIRED.values():
   for name in names:self.assertIn(name,text)
  report['suites'][0]['required_checks'].pop()
  with self.assertRaises(AssertionError):m.compact_progression(report)
 def test_all_scope_rules_and_prompt_limits(self):
  import tempfile
  for i in range(1,15):self.assertIn('R'+str(i).zfill(2),m.SCOPE_SYNOPSIS)
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);p=root/'brief.txt';p.write_text(m.SCOPE_SYNOPSIS)
   manifest=dict(critic_id='C3',groups=[dict(id='fixture',items=[dict(path='brief.txt',kind='text',category='task_scope',description=''),dict(path='x.png',kind='image')])])
   self.assertEqual([],m.prompt_errors(manifest,root))
   p.write_text('x'*2801);self.assertTrue(m.prompt_errors(manifest,root))
   p.write_text('x'*14001);self.assertTrue(m.prompt_errors(manifest,root))

class BenchmarkEvidenceTests(unittest.TestCase):
 def fixture(self):
  values=[16.667]*360
  def stats(v):return dict(count=360,mean=v,p95=v,p99=v,max=v,first_half_mean=v,last_half_mean=v,half_drift=0)
  phases=[]
  for cycle in range(3):
   for state in ('idle','committing'):
    phases.append(dict(state=state,cycle=cycle,warmup_frames=120,samples=360,elapsed_seconds=6.00012,
       frame_interval_ms=stats(16.667),process_proxy_ms=stats(1),raw_frame_interval_ms=values.copy(),raw_process_proxy_ms=[1]*360,
       rss_start_mb=700,rss_end_mb=701,rss_endpoint_peak_mb=701,static_start_mb=100,static_end_mb=101,static_peak_mb=101,
       node_min=15,node_max=15,draw_min=9,draw_max=9,primitive_min=2200,primitive_max=2200,texture_min_mb=170,texture_max_mb=170,
       visual_build_count=1,visual_node_count=4,visual_apply_delta=0))
  return dict(passed=True,task_id='T10',candidate_commit='a'*40,engine='4.7.2.stable.official.ed1daf0bf',renderer='mobile/llvmpipe',resolution=[3840,2160],render_scale=1,cycles=3,frame_cap=60,fixed_fps=False,measurement_io=False,physical_certification=False,phases=phases,active_seconds=18.00036,idle_seconds=18.00036,active_duty_fraction=.5,active_minus_idle=[dict(cycle=i,frame_mean_ms=0,process_mean_ms=0) for i in range(3)])
 def test_finite_repeated_measurement(self):self.assertEqual([],m.benchmark_errors(self.fixture(),'a'*40))
 def test_missing_stale_nonphysical_and_forged_metrics_reject(self):
  for key,value in [('passed',False),('renderer','mobile/forged-hardware'),('render_scale',True),('active_seconds','bad'),('candidate_commit','b'*40),('physical_certification',True),('measurement_io',True),('resolution',[1280,720]),('active_duty_fraction',1)]:
   row=self.fixture();row[key]=value;self.assertTrue(m.benchmark_errors(row,'a'*40))
  for change in ('missing','short','nonfinite','growth','statistics','duration','warmup'):
   row=self.fixture();p=row['phases'][0]
   if change=='missing':row['phases'].pop()
   elif change=='short':p['samples']=10
   elif change=='nonfinite':p['raw_process_proxy_ms'][0]=float('nan')
   elif change=='growth':p['node_max']=200
   elif change=='statistics':p['frame_interval_ms']['p99']=1
   elif change=='duration':p['elapsed_seconds']=2
   else:p['warmup_frames']=0
   with self.subTest(change=change):self.assertTrue(m.benchmark_errors(row,'a'*40))

 def test_memory_plateau_cannot_hide_growth_with_low_peak(self):
  row=self.fixture();row['phases'][0].update(static_start_mb=100,static_end_mb=10000,static_peak_mb=1)
  self.assertTrue(m.benchmark_errors(row,'a'*40))
  row=self.fixture();row['phases'][0]['rss_endpoint_peak_mb']=1
  self.assertTrue(m.benchmark_errors(row,'a'*40))
