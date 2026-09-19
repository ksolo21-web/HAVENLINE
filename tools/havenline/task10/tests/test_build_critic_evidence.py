import copy,importlib.util,unittest,math,hashlib,tempfile
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
 def contract(self,root):
  p=root/m.REVIEW_OUTPUT_PATH;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(m.REVIEW_OUTPUT_CONTRACT)
  return dict(path=m.REVIEW_OUTPUT_PATH,kind='text',category='task_scope',description=m.REVIEW_OUTPUT_DESCRIPTION,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
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
   manifest=dict(critic_id='C3',groups=[dict(id='fixture',items=[dict(path='brief.txt',kind='text',category='task_scope',description=''),dict(path='x.png',kind='image'),self.contract(root)])])
   self.assertEqual([],m.prompt_errors(manifest,root))
   p.write_text('x'*2801);self.assertTrue(m.prompt_errors(manifest,root))
   p.write_text('x'*14001);self.assertTrue(m.prompt_errors(manifest,root))

 def test_contract_preserves_judgment_and_fits_existing_budget(self):
  self.assertEqual(423,len(m.REVIEW_OUTPUT_CONTRACT))
  self.assertEqual('e149bee5c4081d0d4d7d4ac68fc56e5e51d18e645225103ed4c11b8474af35e1',hashlib.sha256(m.REVIEW_OUTPUT_CONTRACT.encode()).hexdigest())
  self.assertIn('preserve your independent evidence judgment',m.REVIEW_OUTPUT_CONTRACT)
  self.assertIn('Do not omit defects or fields to fit.',m.REVIEW_OUTPUT_CONTRACT)
  for word in ('PASS','APPROVED','9.0','10.0'):
   self.assertNotIn(word,m.REVIEW_OUTPUT_CONTRACT)
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'brief.txt').write_text('x'*2150)
   for cid in ('C3','C4'):
    groups=[dict(id=g,items=[dict(path='brief.txt',kind='text',category='task_scope',description=''),dict(path=g+'.png',kind='image'),self.contract(root)]) for g in ('full-lifecycle','motion-0','motion-12','device-readability')]
    self.assertEqual([],m.prompt_errors(dict(critic_id=cid,groups=groups),root))

 def test_visual_groups_are_bounded_unique_and_complete(self):
  manifest=dict(critic_id='C4',groups=[dict(id='a',items=[dict(path=str(i)+'.png',kind='image') for i in range(6)]),dict(id='b',items=[dict(path=str(i)+'.png',kind='motion_frame') for i in range(6,12)])])
  self.assertEqual([],m.visual_group_errors(manifest))
  manifest['groups'][0]['items'].append(dict(path='12.png',kind='image'))
  self.assertTrue(m.visual_group_errors(manifest))
  manifest['groups'][0]['items'].pop();manifest['groups'][1]['items'][0]['path']='0.png'
  self.assertTrue(m.visual_group_errors(manifest))

 def test_c7_context_binds_roles_dimensions_and_selected_rows(self):
  candidate='a'*40
  # Independent fixtures: do not derive report rows from the selector table being tested.
  domain_names=[
   'view lifecycle contains all frozen states','view enters ready lifecycle','valid preview enters preview lifecycle',
   'prepared intent enters committing lifecycle','raw simulation receipt cannot complete before T10 accepts it','T10-accepted receipt completes lifecycle',
  ]
  integration_names=[
   'locked lifecycle hides response geometry','view exposes explicit blocked lifecycle','blocked world response preserves exact reasons and shortfalls',
   'same blocked state refreshes exact shortfall label','unaccepted receipt cannot stop pending flow or claim paid',
   'accepted receipt stops flow while retaining camera-lane maintenance',
   'real harvesting commits to carried inventory','real carried harvest cannot pay T10','real deposit conserves delivered resources',
   'real simulation exact stored debit','real insufficient stock cannot partially charge',
  ]
  domain=dict(candidate=candidate,passed=True,failures=[],checks=[dict(name=n,passed=True) for n in domain_names])
  integration=dict(candidate=candidate,passed=True,failures=[],checks=[dict(name=n,passed=True) for n in integration_names])
  text=m.c7_context(domain,integration,candidate,'1'*64,'2'*64)
  for i in range(1,15):self.assertIn('R'+str(i).zfill(2),text)
  for dimension in m.C7_DIMENSIONS:self.assertIn(dimension,text)
  self.assertIn('Requirement IDs R01-R14 are scope boundaries; they are not score dimensions.',text)
  self.assertIn('R05 truthful locked/ready/blocked/preview/committing/complete lifecycle',text)
  self.assertIn('R06 only physically delivered stored resources pay',text)
  self.assertIn('stable_evidence_ids_with_anchored_semantic_matchers',text)
  self.assertIn('R05_INTEGRATION_ACCEPTED_STOPS_FLOW',text)
  self.assertIn('accepted receipt stops flow while retaining camera-lane maintenance',text)
  for change in ('missing','duplicate','false','stale','failed'):
   d=copy.deepcopy(domain);i=copy.deepcopy(integration)
   if change=='missing':d['checks'].pop()
   elif change=='duplicate':d['checks'].append(copy.deepcopy(d['checks'][0]))
   elif change=='false':d['checks'][0]['passed']=False
   elif change=='stale':d['candidate']='b'*40
   else:i['failures']=['failure']
   with self.subTest(change=change),self.assertRaises(AssertionError):m.c7_context(d,i,candidate,'1'*64,'2'*64)

 def test_c7_selector_survives_nonsemantic_suffix_but_rejects_ambiguity_and_core_drift(self):
  candidate='a'*40
  domain_names=[
   'view lifecycle contains all frozen states','view enters ready lifecycle','valid preview enters preview lifecycle',
   'prepared intent enters committing lifecycle','raw simulation receipt cannot complete before T10 accepts it','T10-accepted receipt completes lifecycle',
  ]
  base=[
   'locked lifecycle hides response geometry','view exposes explicit blocked lifecycle','blocked world response preserves exact reasons and shortfalls',
   'same blocked state refreshes exact shortfall label','unaccepted receipt cannot stop pending flow or claim paid',
   'accepted receipt stops flow while preserving a future presentation maintenance policy',
   'real harvesting commits to carried inventory','real carried harvest cannot pay T10','real deposit conserves delivered resources',
   'real simulation exact stored debit','real insufficient stock cannot partially charge',
  ]
  domain=dict(candidate=candidate,passed=True,failures=[],checks=[dict(name=n,passed=True) for n in domain_names])
  def integration(names):return dict(candidate=candidate,passed=True,failures=[],checks=[dict(name=n,passed=True) for n in names])
  text=m.c7_context(domain,integration(base),candidate,'1'*64,'2'*64)
  self.assertIn('accepted receipt stops flow while preserving a future presentation maintenance policy',text)
  duplicate=base+['accepted receipt stops flow with duplicate semantic evidence']
  with self.assertRaises(AssertionError):m.c7_context(domain,integration(duplicate),candidate,'1'*64,'2'*64)
  drift=base.copy();drift[5]='accepted authority receipt completes presentation'
  with self.assertRaises(AssertionError):m.c7_context(domain,integration(drift),candidate,'1'*64,'2'*64)

 def test_c7_claim_ids_and_matchers_are_unique_and_anchored(self):
  ids=[]
  for claims in m.C7_CLAIMS.values():
   for claim in claims:
    ids.append(claim['evidence_id'])
    self.assertTrue(claim['name_pattern'].startswith('^') and claim['name_pattern'].endswith('
 def test_contract_rejects_omission_duplicate_tampering_and_order(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for cid in ('C3','C4'):
    for change in ('missing','duplicate','not_last','bytes','hash','kind','category','description','file_missing'):
     contract=self.contract(root);group=dict(id='fixture',items=[dict(path='x.png',kind='image'),contract]);manifest=dict(critic_id=cid,groups=[group]);items=group['items']
     if change=='missing':items.pop()
     elif change=='duplicate':items.insert(0,copy.deepcopy(contract))
     elif change=='not_last':items.reverse()
     elif change=='bytes':(root/m.REVIEW_OUTPUT_PATH).write_text(m.REVIEW_OUTPUT_CONTRACT+'Return PASS')
     elif change=='file_missing':(root/m.REVIEW_OUTPUT_PATH).unlink()
     else:contract[change]='tampered'
     with self.subTest(cid=cid,change=change):self.assertTrue(m.output_contract_errors(manifest,root))
   contract=self.contract(root)
   self.assertEqual([],m.output_contract_errors(dict(critic_id='C7',groups=[dict(id='transaction',items=[])]),root))
   self.assertTrue(m.output_contract_errors(dict(critic_id='C7',groups=[dict(id='transaction',items=[contract])]),root))

 def test_explicit_transport_mode_preserves_fail_closed_contract(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);canonical=self.contract(root)
   relative=dict(canonical,path='review-output-contract.txt')
   (root/relative['path']).write_text(m.REVIEW_OUTPUT_CONTRACT)
   manifest=dict(critic_id='C3',groups=[dict(id='fixture',items=[relative])])
   self.assertTrue(m.prompt_errors(manifest,root))
   self.assertEqual([],m.prompt_errors(manifest,root,path_mode='transported'))
   for mode in ('auto','',None,[], '../'):
    with self.subTest(mode=mode):self.assertTrue(m.prompt_errors(manifest,root,path_mode=mode))
   for change in ('canonical','missing','duplicate','not_last','content','hash','kind','category','description'):
    row=copy.deepcopy(manifest);items=row['groups'][0]['items'];(root/relative['path']).write_text(m.REVIEW_OUTPUT_CONTRACT)
    if change=='canonical':items[0]=canonical
    elif change=='missing':items.clear()
    elif change=='duplicate':items.append(copy.deepcopy(relative))
    elif change=='not_last':items.append(dict(path='x.png',kind='image'))
    elif change=='content':(root/relative['path']).write_text('changed')
    else:items[0][change]='changed'
    with self.subTest(change=change):self.assertTrue(m.output_contract_errors(row,root,path_mode='transported'))
   for mode in ('canonical','transported'):
    self.assertEqual([],m.output_contract_errors(dict(critic_id='C7',groups=[dict(id='transaction',items=[])]),root,path_mode=mode))

class BenchmarkEvidenceTests(unittest.TestCase):
 def fixture(self):
  values=[16.667]*360
  def stats(v):return dict(count=360,mean=v,p95=v,p99=v,max=v,first_half_mean=v,last_half_mean=v,half_drift=0)
  phases=[]
  for cycle in range(3):
   for state in ('hidden','frozen','pulse'):
    identity=dict(descriptor=dict(lifecycle='committing',target_revision=1),view_id=1,ring_mesh=2,ghost_mesh=3,ring_material=4,ghost_material=5,label_text='Applying',camera_transform='fixed',camera_size=8)
    motion=[]
    for i in range(360):
     t=(i/60)%10 if state=='pulse' else 0;pulse=1+math.sin(t*math.tau*1.4)*.18
     motion.append(dict(time=t,scale=[pulse]*3,y=.08+.75*pulse))
    phases.append(dict(raw_pulse_samples=motion,base_scale=[1,1,1],identity_before=identity,identity_after=copy.deepcopy(identity),view_visible=state!='hidden',pulse_enabled=state=='pulse',state=state,cycle=cycle,warmup_frames=120,samples=360,elapsed_seconds=6.00012,
       frame_interval_ms=stats(16.667),process_proxy_ms=stats(1),raw_frame_interval_ms=values.copy(),raw_process_proxy_ms=[1]*360,
       rss_start_mb=700,rss_end_mb=701,rss_endpoint_peak_mb=701,static_start_mb=100,static_end_mb=101,static_peak_mb=101,
       node_min=15,node_max=15,draw_min=9,draw_max=9,primitive_min=2200,primitive_max=2200,texture_min_mb=170,texture_max_mb=170,
       visual_build_count=1,visual_node_count=4,visual_apply_delta=0))
  conditioning=dict(method='fixed_all_controls',adaptive=False,sweeps=2,frames_per_control=360,buffer_count=9,samples_per_buffer=360,before_preallocation=dict(rss_mb=600,static_mb=90),after_preallocation=dict(rss_mb=610,static_mb=93),phases=[dict(sweep=c,state=state,frames=360,elapsed_seconds=60,before=dict(rss_mb=610,static_mb=93),after=dict(rss_mb=700,static_mb=100),identity_before=copy.deepcopy(identity),identity_after=copy.deepcopy(identity)) for c in range(2) for state in ('hidden','frozen','pulse')])
  return dict(conditioning=conditioning,passed=True,task_id='T10',candidate_commit='a'*40,engine='4.7.2-stable (official)',engine_version=dict(major=4,minor=7,patch=2,status='stable',build='official',hash='ed1daf0bf001b61586d9930840f2f1394092c079',string='4.7.2-stable (official)'),renderer='mobile/llvmpipe',resolution=[3840,2160],render_scale=1,cycles=3,frame_cap=60,fixed_fps=False,measurement_io=False,physical_certification=False,phases=phases,active_seconds=18.00036,idle_seconds=18.00036,active_duty_fraction=.5,isolated_update=dict(batches=20,calls_per_batch=100,raw_gross_usec_per_call=[1]*20,raw_empty_usec_per_call=[0]*20,gross_usec_per_call=dict(stats(1),count=20),empty_usec_per_call=dict(stats(0),count=20)),active_minus_idle=[dict(cycle=i,frame_mean_ms=0,process_mean_ms=0,presentation_frame_mean_ms=0,presentation_process_mean_ms=0) for i in range(3)])
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

 def test_structured_version_and_matched_controls_reject_forgery(self):
  for key,value in [('major',True),('minor',8),('patch',3),('build','custom'),('status','dev'),('hash','ed1daf0bf'),('string','fake')]:
   row=self.fixture();row['engine_version'][key]=value
   with self.subTest(key=key):self.assertTrue(m.benchmark_errors(row,'a'*40))
  for change in ('identity','visibility','processing','delta','cpu_missing','cpu_stats','cpu_short'):
   row=self.fixture()
   if change=='identity':row['phases'][2]['identity_after']['label_text']='different'
   elif change=='visibility':row['phases'][0]['view_visible']=True
   elif change=='processing':row['phases'][1]['pulse_enabled']=True
   elif change=='delta':row['active_minus_idle'][0]['presentation_frame_mean_ms']=8
   elif change=='cpu_missing':del row['isolated_update']
   elif change=='cpu_stats':row['isolated_update']['gross_usec_per_call']['p99']=9
   else:row['isolated_update']['calls_per_batch']=1
   with self.subTest(change=change):self.assertTrue(m.benchmark_errors(row,'a'*40))

 def test_controls_must_prove_actual_bounded_motion(self):
  for change in ('pulse_still','frozen_moves','range','time','base'):
   row=self.fixture()
   if change=='pulse_still':row['phases'][2]['raw_pulse_samples']=copy.deepcopy(row['phases'][1]['raw_pulse_samples'])
   elif change=='frozen_moves':row['phases'][1]['raw_pulse_samples']=copy.deepcopy(row['phases'][2]['raw_pulse_samples'])
   elif change=='range':row['phases'][2]['raw_pulse_samples'][3]['scale'][0]=2
   elif change=='time':row['phases'][2]['raw_pulse_samples'][3]['time']=float('nan')
   else:row['phases'][2]['base_scale']=[2,2,2]
   with self.subTest(change=change):self.assertTrue(m.benchmark_errors(row,'a'*40))

 def test_conditioning_is_fixed_complete_and_cold_cost_preserved(self):
  for change in ('missing','adaptive','short','buffers','nan','identity','allocation','sweeps','growth'):
   row=self.fixture();c=row['conditioning']
   if change=='missing':del row['conditioning']
   elif change=='adaptive':c['adaptive']=True
   elif change=='short':c['phases'][0]['frames']=120
   elif change=='buffers':c['buffer_count']=1
   elif change=='nan':c['before_preallocation']['rss_mb']=float('nan')
   elif change=='identity':c['phases'][0]['identity_after']['label_text']='changed'
   elif change=='allocation':c['after_preallocation']['static_mb']=90
   elif change=='sweeps':c['phases'].pop()
   else:row['phases'][-1].update(rss_start_mb=734,rss_end_mb=734,rss_endpoint_peak_mb=734)
   with self.subTest(change=change):self.assertTrue(m.benchmark_errors(row,'a'*40))
  # Startup cost remains visible; it never replaces or relaxes the measured limit.
  row=self.fixture();self.assertGreater(row['conditioning']['phases'][-1]['after']['rss_mb']-row['conditioning']['before_preallocation']['rss_mb'],32)
  self.assertEqual([],m.benchmark_errors(row,'a'*40))
))
  self.assertEqual(len(ids),len(set(ids)))

 def test_contract_rejects_omission_duplicate_tampering_and_order(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for cid in ('C3','C4'):
    for change in ('missing','duplicate','not_last','bytes','hash','kind','category','description','file_missing'):
     contract=self.contract(root);group=dict(id='fixture',items=[dict(path='x.png',kind='image'),contract]);manifest=dict(critic_id=cid,groups=[group]);items=group['items']
     if change=='missing':items.pop()
     elif change=='duplicate':items.insert(0,copy.deepcopy(contract))
     elif change=='not_last':items.reverse()
     elif change=='bytes':(root/m.REVIEW_OUTPUT_PATH).write_text(m.REVIEW_OUTPUT_CONTRACT+'Return PASS')
     elif change=='file_missing':(root/m.REVIEW_OUTPUT_PATH).unlink()
     else:contract[change]='tampered'
     with self.subTest(cid=cid,change=change):self.assertTrue(m.output_contract_errors(manifest,root))
   contract=self.contract(root)
   self.assertEqual([],m.output_contract_errors(dict(critic_id='C7',groups=[dict(id='transaction',items=[])]),root))
   self.assertTrue(m.output_contract_errors(dict(critic_id='C7',groups=[dict(id='transaction',items=[contract])]),root))

 def test_explicit_transport_mode_preserves_fail_closed_contract(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);canonical=self.contract(root)
   relative=dict(canonical,path='review-output-contract.txt')
   (root/relative['path']).write_text(m.REVIEW_OUTPUT_CONTRACT)
   manifest=dict(critic_id='C3',groups=[dict(id='fixture',items=[relative])])
   self.assertTrue(m.prompt_errors(manifest,root))
   self.assertEqual([],m.prompt_errors(manifest,root,path_mode='transported'))
   for mode in ('auto','',None,[], '../'):
    with self.subTest(mode=mode):self.assertTrue(m.prompt_errors(manifest,root,path_mode=mode))
   for change in ('canonical','missing','duplicate','not_last','content','hash','kind','category','description'):
    row=copy.deepcopy(manifest);items=row['groups'][0]['items'];(root/relative['path']).write_text(m.REVIEW_OUTPUT_CONTRACT)
    if change=='canonical':items[0]=canonical
    elif change=='missing':items.clear()
    elif change=='duplicate':items.append(copy.deepcopy(relative))
    elif change=='not_last':items.append(dict(path='x.png',kind='image'))
    elif change=='content':(root/relative['path']).write_text('changed')
    else:items[0][change]='changed'
    with self.subTest(change=change):self.assertTrue(m.output_contract_errors(row,root,path_mode='transported'))
   for mode in ('canonical','transported'):
    self.assertEqual([],m.output_contract_errors(dict(critic_id='C7',groups=[dict(id='transaction',items=[])]),root,path_mode=mode))

class BenchmarkEvidenceTests(unittest.TestCase):
 def fixture(self):
  values=[16.667]*360
  def stats(v):return dict(count=360,mean=v,p95=v,p99=v,max=v,first_half_mean=v,last_half_mean=v,half_drift=0)
  phases=[]
  for cycle in range(3):
   for state in ('hidden','frozen','pulse'):
    identity=dict(descriptor=dict(lifecycle='committing',target_revision=1),view_id=1,ring_mesh=2,ghost_mesh=3,ring_material=4,ghost_material=5,label_text='Applying',camera_transform='fixed',camera_size=8)
    motion=[]
    for i in range(360):
     t=(i/60)%10 if state=='pulse' else 0;pulse=1+math.sin(t*math.tau*1.4)*.18
     motion.append(dict(time=t,scale=[pulse]*3,y=.08+.75*pulse))
    phases.append(dict(raw_pulse_samples=motion,base_scale=[1,1,1],identity_before=identity,identity_after=copy.deepcopy(identity),view_visible=state!='hidden',pulse_enabled=state=='pulse',state=state,cycle=cycle,warmup_frames=120,samples=360,elapsed_seconds=6.00012,
       frame_interval_ms=stats(16.667),process_proxy_ms=stats(1),raw_frame_interval_ms=values.copy(),raw_process_proxy_ms=[1]*360,
       rss_start_mb=700,rss_end_mb=701,rss_endpoint_peak_mb=701,static_start_mb=100,static_end_mb=101,static_peak_mb=101,
       node_min=15,node_max=15,draw_min=9,draw_max=9,primitive_min=2200,primitive_max=2200,texture_min_mb=170,texture_max_mb=170,
       visual_build_count=1,visual_node_count=4,visual_apply_delta=0))
  conditioning=dict(method='fixed_all_controls',adaptive=False,sweeps=2,frames_per_control=360,buffer_count=9,samples_per_buffer=360,before_preallocation=dict(rss_mb=600,static_mb=90),after_preallocation=dict(rss_mb=610,static_mb=93),phases=[dict(sweep=c,state=state,frames=360,elapsed_seconds=60,before=dict(rss_mb=610,static_mb=93),after=dict(rss_mb=700,static_mb=100),identity_before=copy.deepcopy(identity),identity_after=copy.deepcopy(identity)) for c in range(2) for state in ('hidden','frozen','pulse')])
  return dict(conditioning=conditioning,passed=True,task_id='T10',candidate_commit='a'*40,engine='4.7.2-stable (official)',engine_version=dict(major=4,minor=7,patch=2,status='stable',build='official',hash='ed1daf0bf001b61586d9930840f2f1394092c079',string='4.7.2-stable (official)'),renderer='mobile/llvmpipe',resolution=[3840,2160],render_scale=1,cycles=3,frame_cap=60,fixed_fps=False,measurement_io=False,physical_certification=False,phases=phases,active_seconds=18.00036,idle_seconds=18.00036,active_duty_fraction=.5,isolated_update=dict(batches=20,calls_per_batch=100,raw_gross_usec_per_call=[1]*20,raw_empty_usec_per_call=[0]*20,gross_usec_per_call=dict(stats(1),count=20),empty_usec_per_call=dict(stats(0),count=20)),active_minus_idle=[dict(cycle=i,frame_mean_ms=0,process_mean_ms=0,presentation_frame_mean_ms=0,presentation_process_mean_ms=0) for i in range(3)])
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

 def test_structured_version_and_matched_controls_reject_forgery(self):
  for key,value in [('major',True),('minor',8),('patch',3),('build','custom'),('status','dev'),('hash','ed1daf0bf'),('string','fake')]:
   row=self.fixture();row['engine_version'][key]=value
   with self.subTest(key=key):self.assertTrue(m.benchmark_errors(row,'a'*40))
  for change in ('identity','visibility','processing','delta','cpu_missing','cpu_stats','cpu_short'):
   row=self.fixture()
   if change=='identity':row['phases'][2]['identity_after']['label_text']='different'
   elif change=='visibility':row['phases'][0]['view_visible']=True
   elif change=='processing':row['phases'][1]['pulse_enabled']=True
   elif change=='delta':row['active_minus_idle'][0]['presentation_frame_mean_ms']=8
   elif change=='cpu_missing':del row['isolated_update']
   elif change=='cpu_stats':row['isolated_update']['gross_usec_per_call']['p99']=9
   else:row['isolated_update']['calls_per_batch']=1
   with self.subTest(change=change):self.assertTrue(m.benchmark_errors(row,'a'*40))

 def test_controls_must_prove_actual_bounded_motion(self):
  for change in ('pulse_still','frozen_moves','range','time','base'):
   row=self.fixture()
   if change=='pulse_still':row['phases'][2]['raw_pulse_samples']=copy.deepcopy(row['phases'][1]['raw_pulse_samples'])
   elif change=='frozen_moves':row['phases'][1]['raw_pulse_samples']=copy.deepcopy(row['phases'][2]['raw_pulse_samples'])
   elif change=='range':row['phases'][2]['raw_pulse_samples'][3]['scale'][0]=2
   elif change=='time':row['phases'][2]['raw_pulse_samples'][3]['time']=float('nan')
   else:row['phases'][2]['base_scale']=[2,2,2]
   with self.subTest(change=change):self.assertTrue(m.benchmark_errors(row,'a'*40))

 def test_conditioning_is_fixed_complete_and_cold_cost_preserved(self):
  for change in ('missing','adaptive','short','buffers','nan','identity','allocation','sweeps','growth'):
   row=self.fixture();c=row['conditioning']
   if change=='missing':del row['conditioning']
   elif change=='adaptive':c['adaptive']=True
   elif change=='short':c['phases'][0]['frames']=120
   elif change=='buffers':c['buffer_count']=1
   elif change=='nan':c['before_preallocation']['rss_mb']=float('nan')
   elif change=='identity':c['phases'][0]['identity_after']['label_text']='changed'
   elif change=='allocation':c['after_preallocation']['static_mb']=90
   elif change=='sweeps':c['phases'].pop()
   else:row['phases'][-1].update(rss_start_mb=734,rss_end_mb=734,rss_endpoint_peak_mb=734)
   with self.subTest(change=change):self.assertTrue(m.benchmark_errors(row,'a'*40))
  # Startup cost remains visible; it never replaces or relaxes the measured limit.
  row=self.fixture();self.assertGreater(row['conditioning']['phases'][-1]['after']['rss_mb']-row['conditioning']['before_preallocation']['rss_mb'],32)
  self.assertEqual([],m.benchmark_errors(row,'a'*40))
