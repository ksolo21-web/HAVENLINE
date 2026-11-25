import hashlib,json,math,subprocess,sys
from pathlib import Path
p=Path(sys.argv[1])
h=hashlib.sha256()
with p.open('rb') as f:
    for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
assert h.hexdigest()=='4c9051cbea6df0efa3e7288b13b6d17da46e857274869b0b43d2f96ff6cc79d2'
# Exact PTS decoded in order, not average FPS or thumbnail seek labels.
frames=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp','-of','json',str(p)]))['frames']
notes={
967:'No individually legible leading log; white forest effect and moving exterior red actors',
968:'Small brown fragment next to foliage effect, ambiguous as an individual wood piece',
969:'First unambiguous detached brown log airborne in exterior forest; blue avatar separate',
972:'Airborne log has shifted right toward rear marker after pan correction',
975:'Likely lead brown piece close to fence line; trajectory visible, exact identity not algorithmically tracked',
976:'Brown silhouette projects onto the marker; physical contact not distinguishable from raised projection',
977:'Clearly visible low row segment near front of marker; first visually seated silhouette',
978:'First row segment remains marker-locked during pan; another airborne silhouette projects onto marker',
979:'More deposited silhouettes; continuous first-arrival evidence, not count or last arrival',
982:'More silhouettes visible at marker during continued flights',
986:'Established low row; no completion boundary guaranteed',
1014:'Later exterior airborne wood is again visible with loaded marker; cannot isolate an overall final landing',
1017:'Overlapping wood motion/row; no unambiguous end-of-batch',
1023:'Loaded row remains later in same camera pan, not proof of final settled piece',
}
reference={967:'27.274844',968:'27.307856',969:'27.341156',972:'27.442044',975:'27.542078',976:'27.575478',977:'27.608878',978:'27.642611',979:'27.675767',982:'27.775644',986:'27.909222',1014:'28.845211',1017:'28.945244',1023:'29.147256'}
raw={k:int(frames[k]['best_effort_timestamp']) for k in notes}
s={k:raw[k]/90000 for k in notes}
assert all(abs(s[k]-float(reference[k]))<(.001 if k==1023 else .0000006) for k in reference)
# Hand-read points on temporary decoded 384w full-source proxy, with y origin
# shifted by 185 px for readability. North cusp of dark rear plot used as
# the common origin, not player camera-lock or a moving gate/actor.
A={'log_center_xy':[129,69],'rear_marker_north_tip_xy':[270,126],'blue_avatar_head_to_boot_px':38}
B={'log_center_xy':[232,145],'rear_marker_north_tip_xy':[232,98],'blue_avatar_head_to_boot_px':37}
d=lambda a,b:[a[0]-b[0],a[1]-b[1]]
a,b=[d(row['log_center_xy'],row['rear_marker_north_tip_xy']) for row in [A,B]]
rawdisp=d(B['log_center_xy'],A['log_center_xy']); stabilized=d(b,a)
mag=math.hypot(*stabilized); hmean=(A['blue_avatar_head_to_boot_px']+B['blue_avatar_head_to_boot_px'])/2
print(json.dumps({
 'source_sha256':h.hexdigest(),'timestamp_base':'1/90000','frames':[{'zero_based':k,'raw_pts':raw[k],'pts_s':s[k],'observation':v} for k,v in notes.items()],
 'first_clear_airborne_to_first_visually_seated_s':(raw[977]-raw[969])/90000,
 'possible_ordering_interval_s_from_ambiguity_frames_not_claimed_release_time':[(raw[976]-raw[969])/90000,(raw[977]-raw[968])/90000],
 'first_airborne_actual_exit_time_known':False,'first_contact_physics_precisely_observable':False,'last_visually_seated_identifiable':False,
 'source_continuity':'Exterior-forest to rear marker imagery in continuous pan, not instant cut to an already loaded pad. Brown piece starts among trees/red helpers; cannot identify precise individual source or detect simulated/real custody. Blue avatar is elsewhere and not the source in the followed flight.',
 'screen_measurement':{'measurement_only':True,'proxy_width_px':384,'proxy_y_origin_px':185,'frame_969':A,'frame_977':B,'raw_screen_chord_px':rawdisp,'estimated_pan_from_marker_tip_px':d(B['rear_marker_north_tip_xy'],A['rear_marker_north_tip_xy']),'marker_relative_chord_px':stabilized,'marker_relative_chord_length_px':mag,'same_shot_blue_avatar_mean_height_px':hmean,'approx_avatar_heights':mag/hmean,'rough_reading_range_avatar_heights':[4.2,5.3],'note':'Hand-estimated screen chord, approximately framed and body-height-normalized, not physical distance, arc length or world m/s.'},
 'target_disposition':'Do not inherit .300/.875 customer-counter timings for Character 1 rear storage. The rear reference supports visible in-air wood followed by a legible low deposit, not its player custody, total duration, precise last landing, counts, route, or capacity.'},sort_keys=True,indent=2))
