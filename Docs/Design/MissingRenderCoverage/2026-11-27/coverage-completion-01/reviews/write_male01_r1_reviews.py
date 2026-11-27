from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
b=Path('havenline-missing-renders-2026-11-27').resolve()
def bind(p):
 p=Path(p); raw=p.read_bytes(); return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def base(name):
 invp=b/'invocations'/f'{name}.json'; inv=json.loads(invp.read_text()); provp=b/'reviews/evidence'/f'{name}-crop-provenance.json'; prov=json.loads(provp.read_text())
 return {'schema_version':1,'review_id':name+'-independent','reviewer':'/root/missing_cast_critic','independent':True,'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'REPAIR REQUIRED — STATIC REFERENCE ONLY','score_method':'Minimum mandatory visual-area score; a failed mandatory check blocks approval irrespective of average.','reviewed_image':inv['output'],'requirements_at_generation':inv['requirements_at_generation'],'requirements_snapshot':bind(inv['requirements_snapshot_path']),'invocation':bind(invp),'exact_actual_prompt':bind(inv['exact_actual_prompt_file']['local_path']),'source_images_inspected':inv['ordered_reference_inputs'],'actual_full_native_png_inspected':True,'crop_provenance':bind(provp),'actual_native_crops_inspected':list(prov.get('crops',{})),'all_mandatory_visual_checks_passed':False,'native_mesh_rig_animation_runtime_approval':False,'pending_separate_evidence':['Corrected body and hand sheets and cross-sheet review','Full GitHub body/blob readback and independent archive gate'],'preserve':['Original failed PNG and exact invoked prompt','Existing approved relaxed eight-view character sheet and its previous approval','Bald face, body proportions, blue quilted puffer, orange trim, cream shearling and brown boots']}
def area(i,s,status,f,e=None):
 d={'id':i,'score':s,'status':status,'finding':f}
 if e:d['evidence']=e
 return d
r=base('customer-male-01-pose-r1'); r['score']=8.5
r['areas']=[
 area('source_identity_and_costume',9.6,'PASS','Same bald clean-shaven warm-brown customer with friendly round face, blue horizontal quilted puffer, orange trim, cream cuffs/collar, navy trousers and brown boots. No new accessories.'),
 area('style_materials',9.7,'PASS','Soft sculpted proportions, readable quilting, warm leather gloves, fleece and studio lighting fit the retained approved design.'),
 area('body_views_and_framing',9.6,'PASS','Four complete cardinal bodies with opposite profile directions, labels, head-to-sole visibility and uncropped spread hands in front and rear.'),
 area('front_and_rear_digit_counts',9.6,'PASS','Each frontal/rear hand shows four distinct fingers plus one splayed thumb, with clear background between digits. Five digits alone does not resolve the surface-orientation failure.'),
 area('rear_glove_surface',8.7,'FAIL_REPAIR_REQUIRED','Both REAR180 gloves repeat the padded palm surface visible in FRONT0 instead of showing dorsal finger seams/back surfaces. They cannot be the same unchanged palms-forward T-pose.', ['front-viewer-left-hand','front-viewer-right-hand','rear-viewer-left-hand','rear-viewer-right-hand']),
 area('profile_neutral_wrist_consistency',8.5,'FAIL_REPAIR_REQUIRED','LEFT90 and RIGHT270 near hands face the profile camera with fingers pointing downward, while frontal fingers extend laterally in the fixed T-pose. The visible wrists change orientation/bend rather than presenting the natural edge-on foreshortening of one neutral pose.', ['left-profile-hand','right-profile-hand']),
 area('lower_body_grounding',9.6,'PASS','Visible legs, knee alignment and complete boots are stable in the static pose, with soles at the floor. No motion or deformation approval is implied.')]
r['mandatory_defects_remaining']=[
 {'id':'CM01-P01','severity':'mandatory_pose_surface_consistency','panels':['REAR180'],'repair':'Keep the same neutral palms-forward T-pose. Show dorsal brown glove surfaces and finger-back seams in the rear; remove rear padded palm patches. Preserve five separated digits and the approved body.'},
 {'id':'CM01-P02','severity':'mandatory_wrist_rotation_consistency','panels':['LEFT90','RIGHT270'],'repair':'Keep arms, wrists and fingers in the same neutral orientation as FRONT0. From exact sides, outstretched arms/hands naturally foreshorten along the view direction; show a narrow edge-on glove profile without bending all fingers toward the floor or rotating a palm toward the camera.'}]
(b/'reviews/critic-customer-male-01-pose-r1.json').write_text(json.dumps(r,indent=2)+'\n')
r=base('customer-male-01-hands-r1'); r['score']=8.8
r['areas']=[
 area('source_sleeve_cuff_materials',9.7,'PASS','Blue quilted sleeve and cream shearling cuffs match the source; all four gloves share the same warm brown finish.'),
 area('digit_anatomy_and_separation',9.7,'PASS','All four large gloves each have four fingers plus an opposed thumb, clear intervening gaps and readable finger length hierarchy: 20 countable digits total.'),
 area('palm_dorsal_differentiation',9.7,'PASS','Top palms have soft padded centers; bottom dorsal views have lengthwise finger seams. Matching design is visible.'),
 area('anatomical_chirality_and_labels',8.8,'FAIL_REPAIR_REQUIRED','Every LEFT/RIGHT label is reversed. Fingers-up/wrist-down correct mapping is LEFT PALM thumb viewer-left, RIGHT PALM viewer-right, LEFT BACK viewer-right, RIGHT BACK viewer-left. The sheet uses the opposite map in all four panels.', ['left-palm-label-and-glove','right-palm-label-and-glove','left-back-label-and-glove','right-back-label-and-glove']),
 area('framing_and_readability',9.8,'PASS','Large uncropped gloves and labels, clean background, clear wrist/cuff joins and generous negative space.')]
r['mandatory_defects_remaining']=[{'id':'CM01-H01','severity':'mandatory_anatomical_label_mapping','panels':['LEFT PALM','RIGHT PALM','LEFT BACK','RIGHT BACK'],'observed_prompt_cause':'The exact invoked r1 prompt explicitly specifies the reversed viewer-side thumb map; the image follows that incorrect instruction. Preserve that failed prompt and image rather than rewriting history.','repair':'Use correct anatomical mapping with fingers up: LEFT PALM thumb viewer-left; RIGHT PALM viewer-right; LEFT BACK viewer-right; RIGHT BACK viewer-left. Correct labels or panel placement while preserving the already readable five-digit glove anatomy and materials.'}]
r['correct_chirality_map_fingers_up']={'LEFT PALM':'thumb viewer-left','RIGHT PALM':'thumb viewer-right','LEFT BACK':'thumb viewer-right','RIGHT BACK':'thumb viewer-left'}
(b/'reviews/critic-customer-male-01-hands-r1.json').write_text(json.dumps(r,indent=2)+'\n')
for n in ['customer-male-01-pose-r1','customer-male-01-hands-r1']:
 p=b/'reviews'/f'critic-{n}.json'; d=json.loads(p.read_text()); print(json.dumps({'review':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'score':d['score'],'image_sha256':d['reviewed_image']['sha256'],'crops':d['actual_native_crops_inspected']}))
