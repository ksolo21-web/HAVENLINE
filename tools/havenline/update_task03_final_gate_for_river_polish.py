#!/usr/bin/env python3
from pathlib import Path
p=Path('.github/workflows/havenline-task03-polish-final.yml')
s=p.read_text()
def rep(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new,1)
rep("report['task']=='T03-boundary-v1'","report['task']=='T03-boundary-v2'")
rep("assert abs(report['boundary']['gate_leaf_length']-1.35)<.0001 and abs(report['boundary']['fence_root_sink']-.08)<.0001 and abs(report['boundary']['visual_join_overlap']-.10)<.0001",
    "assert abs(report['boundary']['gate_leaf_length']-1.35)<.0001 and abs(report['boundary']['river_gate_leaf_length']-1.60)<.0001 and abs(report['boundary']['river_gate_open_angle']-1.43)<.0001 and abs(report['boundary']['river_apron_inset']-.55)<.0001 and abs(report['boundary']['fence_root_sink']-.08)<.0001 and abs(report['boundary']['visual_join_overlap']-.10)<.0001")
rep("'polish_revision':{'gate_leaf_length':1.35,'gate_open_angle':1.18,'fence_root_sink':.08,'visual_join_overlap':.10,'stronger_integrated_lane_contrast':True}",
    "'polish_revision':{'gate_leaf_length':1.35,'gate_open_angle':1.18,'river_gate_leaf_length':1.60,'river_gate_open_angle':1.43,'river_apron_inset':.55,'fence_root_sink':.08,'visual_join_overlap':.10,'stronger_integrated_lane_contrast':True,'river_threshold_aprons':True}")
rep('    timeout-minutes: 50\n    env:\n      EXPECTED_SOURCE:', '    timeout-minutes: 75\n    env:\n      EXPECTED_SOURCE:')
p.write_text(s)
print('Task 3 final gate aligned to v2 river-gate polish; 807-check threshold unchanged.')
