"""Write a compact selected readback without copying any raw imported mesh arrays."""
import json, re
from pathlib import Path
import hashlib

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def data(name): return json.loads((p/name).read_text())

p=Path(__file__).resolve().parent
baseline=bytes.fromhex('7825ba134e6b13ce6539e3cbab16899f64a2cd83de0e085a50e6443fc08d36b4').hex()
prep=[]
for variant in ("v1","v2","v3"):
    sub=p/f'native-{variant}'
    log=(sub/'route.log').read_text()
    matched = re.findall(r'^DOCKED_CENTER_ROUTE_RESULT checks=(\d+) failures=(\d+) no_image_stages=(\d+)$',log,re.M)
    fields=lambda tag:[json.loads(line[len(tag)+1:]) for line in log.splitlines() if line.startswith(tag+' ')]
    res={'variant': variant,'route_log_sha256':sha(sub/'route.log'),
         'route_totals':list(map(int,matched[0])) if matched else None,
         'script_failures':[line for line in log.splitlines() if line.startswith('FAIL ')],
         'native_exit_status':int((sub/'godot-status.txt').read_text()),
         'no_owner_save_pointer_or_stage':not (sub/'save-artifacts.txt').read_text().strip(),
         'stop_rows':fields('STOP_GUARD'),'angled_rows':fields('SHOULDER_ROUTE'),
         'cpu_pose_transforms':fields('CPU_SURFACE')+fields('CPU_STANCE')}
    if variant!='v2':
        g=data(f'native-{variant}-geometry.json')
        assert g['actual_donor_dump_sha256']==baseline,variant
        res['same_donor_geometry_hash_as_old_clip']=True
        res['geometry_summary_sha256']=sha(p/f'native-{variant}-geometry.json')
        res['geometry_clear']=g['tested_geometry_clear']
        res['triangles_by_sample']={key:{
              'strict_entire_donor_pairs':sum(s['all_counter_intersections'] for s in r['surfaces']),
              'strict_worktop_pairs':sum(s['worktop_intersections'] for s in r['surfaces']),
              'conservative_matched_y_slab_signed_z_gap_m':r['signed_z_conservative_gap_m_in_20mm_y_slabs'],
              'raw_pose_dump_sha256':r['native_dump_sha256'],
              } for key,r in g['native_poses'].items()}
        assert not res['geometry_clear']  # do not silently promote the staged candidate
    prep.append(res)
out={'status':'HOLD: STAGED CENTER-ONLY GEOMETRY IMPROVEMENT, ADVERSE SITES REMAIN',
     'baseline_source_commit':'11c14a1c41971067c7dc97db69375f720a408f68',
     'baseline_level1_subtree':'d764a05246cbff96983aa27af17e2e919a946ae0',
     'original_donor_sha256':'a62f900f8587008fc0349782b4aa7da3d1a8ebcaa9847569d2b9fa67a47dd25c',
     'original_hero_sha256':'95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099',
     'basis':'counter-local',
     'supplemental_collision_box':{'center':[0,.475,0],'size':[3,.95,1.76]},
     'native_existing_origins_preserved':True,
     'known_old_center_worktop_pairs_inboard_outboard':[1283,1277],
     'known_old_center_full_donor_pairs_inboard_outboard':[6926,5769],
     'run_readback':prep,'rendered_images':False,'new_service_interaction':False,'game_changed':False}
print(json.dumps(out,indent=2,sort_keys=True))
