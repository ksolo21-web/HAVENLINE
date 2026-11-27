from pathlib import Path
import json,hashlib,collections
ROOT=Path('/workspace/scratch/9c51da47f878')
OUT=ROOT/'havenline-missing-renders-2026-11-27/audit/world'
TASK=ROOT/'havenline-missing-renders-2026-11-27'
BASE='d70fbfac21a852f99cc46b06b1944faf11ec7901'
TREE=json.loads((TASK/'source-records/baseline-tree.json').read_text())
PATHS={x['path']:x for x in TREE['tree'] if x['type']=='blob'}
PRIOR=json.loads((OUT/'source-selected-status.json').read_text())
OLD={x['id']:x for x in PRIOR['entries']}
BOARDS={}
expected={'18600.png':'e372bf74be027cb63a0f83c4247a7843a8195a9c579e75a415ddcf3c0052eaec','18607.png':'d71d77c6e200b7ef8d225e573474ad99c2d466954d05c29eabd142f4901bbc0c','18609.png':'68d2fb572cc5370a9746c7130f661438197ce36ac495a3b4ffeeaa4528d81ce7','Havenline: Frostbound World Atlas.png':'5a9f9592d2e8a32b3ae0c4117c2d851496d49023e2768c491dc1b211b7865edf'}
for name,sha in expected.items():
 p=TASK/'source-records/original-boards'/name;b=p.read_bytes();got=hashlib.sha256(b).hexdigest();assert got==sha
 BOARDS[name]={'local_path':str(p.relative_to(ROOT)),'sha256':got,'bytes':len(b),'pixels_inspected':True,'baseline_selected_render':False,'role':'user source board recovered with exact prior-audit hash; not new generated artwork'}
F={}
def family(id,name,variants,scope,notes=''):
 F[id]={'id':id,'name':name,'source_variants_to_cover':variants,'variant_count':len(variants),'gap_class':scope,'why_distinct':notes,'source_occurrences':[],'existing_coverage':[],'proposed_reference_format':'Family sheet(s) with readable opposing three-quarter views for each distinct form, plus use/open-state or material/detail panels where meaningful. Split into multiple sheets when variants become too small. No mandatory eight-angle repetition per form.','status':'MISSING_DEDICATED_SELECTED_REFERENCE_AT_BASELINE'}
family('defense_platform','Modular defense platform',['platform with mount, supply and repair interfaces'],'PRIOR_FROZEN_BLOCKED_SLOT','The only unfilled slot in prior69-slot contract. Ballista tower already exists, but platform/service interfaces have no selected PNG.')
family('cookhouse','Cookhouse',['early open-front cookhouse','expanded cookhouse'],'SOURCE_BOARD_BUILDING_FAMILY','Early18600 cooking shelter and expanded18609 form differ; do not substitute existing open cookfire.')
family('greenhouse','Greenhouse / warm grow hut',['glass framed grow hut'],'SOURCE_BOARD_BUILDING_FAMILY','Enclosed glass growing building is named on18609; crops, yields and recipes remain undefined.')
family('workshop','Workshop',['workshop level1','improved workshop'],'SOURCE_BOARD_BUILDING_FAMILY','18600 open-front workshop is an earlier illustration of the basic workshop family, not a third confirmed identity.')
family('wheat_harvester','Mechanized wheat harvester',['field-mounted rotary harvesting assembly'],'LOCKED_VIDEO_MACHINE_FAMILY','Stationary silver curved rotary heads, blue collection frame/rails; not a tractor.')
family('wheat_processor','Wheat food processor',['blue processor with wheat inlet and bread-like output tray'],'LOCKED_VIDEO_MACHINE_FAMILY','Distinct sourceA machine. Do not invent flour intermediate or exact recipe.')
family('herbs','Herbs',['gathered herb resource'],'ATLAS_RESOURCE_NOUN','Additional explicit atlas noun beyond existing33 bounded resource concepts; no medicinal effect or recipe established.')
family('crystal','Crystal',['crystal resource cluster'],'ATLAS_RESOURCE_NOUN','Additional explicit atlas noun beyond existing33 bounded resource concepts; no power/element/drop table established.')
family('camp_tiles','Physical camp foundation and tile kit',['camp center tile','walkway tile','snow tile','storage pad'],'SOURCE_BOARD_MODULAR_VARIANTS','Existing storage/purchase plots are flat marked interaction zones; these are sculpted timber/stone/snow modules.')
family('survivor_tents','Survivor shelter tents',['beginner tent','survivor shelter tent with stove/chimney'],'SOURCE_BOARD_UPGRADE_VARIANTS','Compact early A-frame and larger midcamp insulated shelter are different visible forms; stove tent is not a medical tent.')
family('cabins','Residential cabins',['wooden hut','upgraded cabin'],'SOURCE_BOARD_UPGRADE_VARIANTS','Both residential forms are absent from equipment and storehouse selections.')
family('bunkhouse','Bunkhouse',['bunkhouse'],'SOURCE_BOARD_BUILDING_FAMILY','Multi-room/multi-bed residence is a distinct named building, not a storage house.')
family('stockpile_shelter','Stockpile shelter',['blue-roof open stockpile shelter'],'SOURCE_BOARD_BUILDING_FAMILY','Roofed open shelter with accessible stacked materials differs from enclosed general storehouse and loose crates.')
family('medical_facilities','Clinic, medical huts and hospital concepts',['clinic / medic tent','basic green-roof medical hut','reinforced medical hut','atlas hospital example1','atlas hospital example2','atlas hospital example3'],'SOURCE_BOARD_AND_ATLAS_VARIANTS','Three early/midcamp forms plus three distinct atlas field-hospital forms. Atlas rows are examples, not six frozen numerical upgrade tiers.')
family('dog_kennels','Dog kennel upgrades',['dog kennel level1','kennel level2'],'SOURCE_BOARD_UPGRADE_VARIANTS','Animal companion references do not supply kennel buildings.')
family('cold_storage_shed','Cold storage shed',['arched insulated cold storage shed'],'SOURCE_BOARD_BUILDING_FAMILY','Round-topped industrial shed with snowflake identity differs from latest gable-roof general storehouse. No refrigeration mechanic or capacity established.')
family('bridges','Camp crossing bridges',['rope bridge','reinforced bridge'],'SOURCE_BOARD_UPGRADE_VARIANTS','The bridge-builder cart is a separate mobile tool; it does not cover either actual crossing.')
family('reinforced_palisades','Reinforced timber palisades',['short reinforced palisade','tall reinforced palisade'],'SOURCE_BOARD_UPGRADE_VARIANTS','Current approved fence has cream ropes and warm timber;18609 forms have blue metal straps and distinct heights.18600 metal-banded variant belongs to this family.')
family('improved_gatehouse','Improved gatehouse',['twin-tower timber gatehouse'],'SOURCE_BOARD_BUILDING_FAMILY','Current double swing gate has posts but no flanking roofed towers; source18609 gatehouse is distinct.')
family('fish_hut','Fish hut over ice',['raised fishing hut with ice access'],'SOURCE_BOARD_BUILDING_FAMILY','Existing ice fishing spot/rack/winch do not cover the elevated enclosing hut.')
family('spike_barricade','Timber spike barricade',['small crossed timber spike barricade'],'SOURCE_VISIBLE_UNLABELLED_PROP','18600 depicts a distinct grounded cluster of pointed timber stakes. This is an editorial working name, not a canonical source label or real construction plan.')
family('late_furnaces','Late camp furnace forms',['level51–70 form','level71–90 form','level91–100 form'],'ATLAS_LATE_RANGE_VARIANTS','Existing ten furnace sheets cover named levels1–50. They do not cover the three additional late-stage forms shown by atlas.')
family('fortress_walls','Fortress wall upgrade examples',['atlas wall example1','atlas wall example2','atlas wall example3'],'ATLAS_FUTURE_VARIANTS','Stone/metal walls in atlas are distinct from timber palisades; three depicted examples, not an exhaustive future wall catalogue.')
family('fortress_gates','Fortress gate upgrade examples',['atlas gate example1','atlas gate example2','atlas gate example3'],'ATLAS_FUTURE_VARIANTS','Stone/metal piers and gate panels differ from existing rope posts/swing gate and midcamp timber gatehouse.')
family('fortress_watchtowers','Fortress watchtower upgrade examples',['atlas watchtower example1','atlas watchtower example2','atlas watchtower example3'],'ATLAS_FUTURE_VARIANTS','Three stone/metal tower forms differ from already-approved timber watchtower/guard tower.')
family('archer_towers','Archer tower upgrade examples',['atlas archer tower example1','atlas archer tower example2','atlas archer tower example3'],'ATLAS_FUTURE_VARIANTS','Atlas explicitly names this family separately from watchtower and cannon tower; existing ballista is a different asset.')
family('cannon_towers','Cannon tower upgrade examples',['atlas cannon tower example1','atlas cannon tower example2','atlas cannon tower example3'],'ATLAS_FUTURE_VARIANTS','Three source-labelled fantasy game defensive tower forms; no real firing mechanism, ammunition recipe or runtime attack behavior inferred.')
family('worker_huts','Worker hut upgrade examples',['atlas worker hut example1','atlas worker hut example2','atlas worker hut example3'],'ATLAS_FUTURE_VARIANTS','Atlas names worker hut separately from workshop; these are authored lodging/worker-building appearances, not new job mechanics.')
family('atlas_storage','Atlas storage building alternatives',['atlas storage example1','atlas storage example2','atlas storage example3'],'ATLAS_FUTURE_VISUAL_ALTERNATIVES','Latest three-stage gable storehouse fully covers its approved contract. Atlas flat-roof fortified forms with barrel annexes are additional visual alternatives; do not replace current storehouse or imply its approval failed.')
family('biome_vignettes','Future biome visual references',['pine forest','frozen lake','ice canyon','snow cliffs','abandoned mines'],'ATLAS_FUTURE_REGION_CONCEPTS','Five labelled atlas thumbnails define broad scene concepts, not a complete terrain mesh/node/prop list or playable world. Existing native environment captures are not dedicated approved versions of these five concept vignettes.')
ROWS=[]
STORAGE='Docs/Design/StructureReferences/2026-11-26/upgradeable-storage-house/selected/storage-house-starter.png'
FENCE='Docs/Design/StructureReferences/2026-11-25/selected/fence-cardinal.png'
GATE='Docs/Design/StructureReferences/2026-11-25/selected/gates-cardinal.png'
# Resolve canonical selected aliases from exact baseline rather than infer a path.
for p in PATHS:
 if '/StructureReferences/2026-11-25/selected/' in p and p.endswith('fence-cardinal.png'):FENCE=p
 if '/StructureReferences/2026-11-25/selected/' in p and p.endswith('gates-cardinal.png'):GATE=p
if FENCE not in PATHS:
 FENCE=next(p for p in PATHS if '/StructureReferences/2026-11-25/' in p and p.endswith('/fence-cardinal-r1.png'))
if GATE not in PATHS:
 GATE=next(p for p in PATHS if '/StructureReferences/2026-11-25/' in p and p.endswith('/gates-cardinal-r2.png'))
CARGO='Docs/Design/ResourceTurnarounds/2026-11-23/reviewed-concepts/12-cargo.png'
def row(source,label,family_id=None,existing=None,status=None,notes='',region=''):
 r={'source':source,'source_label':label,'source_region':region,'gap_family_id':family_id,'status':status or ('GAP' if family_id else 'COVERED'),'existing_selected':[],'notes':notes}
 if existing:
  for e in (existing if isinstance(existing,list) else [existing]):
   if e in OLD:
    t=OLD[e];r['existing_selected'].append({'id':e,'path':t['selected_path'],'status':t['status'],'score':t['score'],'sha256':t['sha256']})
   else:
    assert e in PATHS,e;r['existing_selected'].append({'path':e,'status':'PRIOR_SELECTED_REFERENCE','git_blob_sha':PATHS[e]['sha']})
 if family_id:F[family_id]['source_occurrences'].append({'source':source,'label':label,'region':region})
 ROWS.append(r)
#18607: all32 readable asset labels; the arrangement vignette is separately a composition.
for level in [1,5,10,15,25]:row('18607.png','Furnace level '+str(level),existing='furnace_level_'+str(level).zfill(2),region='upper-left furnace evolution')
for label in ['Camp center tile','Walkway tile','Snow tile','Storage pad']:row('18607.png',label,'camp_tiles',region='upper-right camp foundations & tiles')
for label,f in [('Beginner tent','survivor_tents'),('Wooden hut','cabins'),('Stockpile','stockpile_shelter')]:row('18607.png',label,f,region='middle building row')
for label,e in [('Cookfire','cookfire'),('Butcher table','butcher_table'),('Drying rack','mixed_drying_rack'),('Fishing spot','ice_fishing_spot')]:row('18607.png',label,existing=e,region='middle equipment row')
row('18607.png','Rope bridge','bridges',region='middle right')
row('18607.png','Saw station',existing='saw_station',region='lower building row')
for label,f in [('Workshop (LVL1)','workshop'),('Clinic / Medic tent','medical_facilities'),('Dog kennel (LVL1)','dog_kennels')]:row('18607.png',label,f,region='lower building row')
row('18607.png','Storage crates',existing=CARGO,notes='Cargo sheet visually inspected: wooden braced green-lid crate exactly covers this prop family; arrangement of multiple crates does not create a new identity.',region='lower building row')
row('18607.png','Spiked palisade',existing=FENCE,region='lower right defenses')
row('18607.png','Tall fence post',existing=GATE,status='COVERED_COMPONENT',notes='Tall rope-bound snowcapped outer post is covered within current gate reference. No separate confirmed new identity required.',region='lower right defenses')
row('18607.png','Gate',existing=GATE,region='lower right defenses')
for label,e in [('Watchtower','watchtower'),('Torch post','torch_post')]:row('18607.png',label,existing=e,region='lower right defenses')
for label,e in [('Hand-push snowplow','hand_push_snowplow'),('Chopping station','chopping_station'),('Fishing winch','fishing_winch'),('Sled hauler','sled_hauler'),('Rescue beacon','rescue_beacon')]:row('18607.png',label,existing=e,region='bottom early assistance machines')
#18609: all31 readable asset labels.
for level in [26,30,34,42,50]:row('18609.png','Furnace '+str(level),existing='furnace_level_'+str(level).zfill(2),region='upper-left furnace evolution')
for label,f in [('Upgraded cabin','cabins'),('Bunkhouse','bunkhouse'),('Improved workshop','workshop'),('Greenhouse / Warm grow hut','greenhouse')]:row('18609.png',label,f,region='top buildings')
for label,f in [('Expanded cookhouse','cookhouse'),('Reinforced medical hut','medical_facilities')]:row('18609.png',label,f,region='second row')
for label,e in [('Lumber mill','lumber_mill'),('Quarry drill station','quarry_drill_station')]:row('18609.png',label,existing=e,region='second row')
for label,f in [('Cold storage shed','cold_storage_shed'),('Survivor shelter tent','survivor_tents'),('Kennel level2','dog_kennels')]:row('18609.png',label,f,region='second row')
for label,f in [('Reinforced palisade wall (short)','reinforced_palisades'),('Reinforced palisade wall (tall)','reinforced_palisades'),('Improved gatehouse','improved_gatehouse')]:row('18609.png',label,f,region='third row')
for label,e in [('Guard tower','guard_tower'),('Ballista tower','ballista_tower'),('Hunting blind','hunting_blind')]:row('18609.png',label,existing=e,region='third row')
for label,f in [('Fish hut over ice','fish_hut'),('Reinforced bridge','bridges')]:row('18609.png',label,f,region='third row')
for label,e in [('Steam saw','steam_saw'),('Cargo sled','cargo_sled'),('Pulley crane','pulley_crane'),('Ice drill','ice_drill'),('Snow-cat utility','snow_cat_utility'),('Bridge-builder cart','bridge_builder_cart'),('Supply sorting table','supply_sorting_table')]:row('18609.png',label,existing=e,region='bottom assistance machines')
#18600: unlabelled isolated visual forms; names below are descriptive, not canonical labels.
for label,e in [('stone firepit','cookfire'),('small heated vessel','hearth_vessel'),('larger heated vessel','hearth_vessel')]:row('18600.png',label,existing=e,status='COVERED_FAMILY',notes='Unlabelled source variant; covered heater/cookfire family, not additional named numerical tier.',region='row1')
for label,f in [('blue/beige A-frame shelter','survivor_tents'),('open-front tool workshop','workshop'),('open-front cooking shelter','cookhouse')]:row('18600.png',label,f,region='row1')
row('18600.png','green-roof medical hut','medical_facilities',region='row2')
row('18600.png','green-roof storage hut',existing=STORAGE,status='COVERED_FAMILY_NEWER_DESIGN',notes='Current user-requested three-tier storehouse supplies the general storage-building family. The green-roof early illustration is an older visual alternative; no claim of exact geometry reproduction.',region='row2')
row('18600.png','timber lookout tower',existing='watchtower',region='row2')
row('18600.png','rope-bound palisade',existing=FENCE,region='row2')
row('18600.png','metal-banded palisade','reinforced_palisades',region='row2')
row('18600.png','palisade corner',existing=FENCE,status='COVERED_FAMILY_JOIN_VARIANT',notes='Same basic fence family; current reference has adjacent-module join detail. Right-angle assembly is a layout variant, not separate material identity.',region='row2')
for label,e in [('timber gate',GATE),('axe in chopping stump','chopping_stump'),('meat/hide drying rack','mixed_drying_rack'),('green-lidded metal-braced cargo crate',CARGO),('torch post','torch_post')]:row('18600.png',label,existing=e,region='row3')
row('18600.png','crossed timber spike barricade','spike_barricade',region='row3')
for label in ['snow ground tile','plank floor tile']:row('18600.png',label,'camp_tiles',region='row3')
#Atlas upperhalf.
AT='Havenline: Frostbound World Atlas.png'
for label,ids in [('Level1–10',['furnace_level_01','furnace_level_05','furnace_level_10']),('Level11–20',['furnace_level_15']),('Level21–30',['furnace_level_25','furnace_level_26','furnace_level_30']),('Level31–50',['furnace_level_34','furnace_level_42','furnace_level_50'])]:row(AT,label,existing=ids,status='COVERED_RANGE_FAMILY',notes='Existing named level selections cover this level range; not a claim that each thumbnail silhouette is an exact duplicate.',region='camp / furnace upgrade progression')
for label in ['Level51–70','Level71–90','Level91–100']:row(AT,label,'late_furnaces',region='camp / furnace upgrade progression')
for name,f in [('Walls','fortress_walls'),('Gate','fortress_gates'),('Watch tower','fortress_watchtowers'),('Archer tower','archer_towers'),('Cannon tower','cannon_towers'),('Worker hut','worker_huts'),('Storage','atlas_storage'),('Hospital','medical_facilities')]:
 for i in [1,2,3]:row(AT,name+' example'+str(i),f,status='GAP_FUTURE_SOURCE_EXAMPLE',notes='One of three depicted source examples. No exact level, production recipe, upgrade cost or exhaustive family count is established.',region='upgrade examples (some of many), '+name+' column, row'+str(i))
for label in ['Pine forest','Frozen lake','Ice canyon','Snow cliffs','Abandoned mines']:row(AT,label,'biome_vignettes',status='GAP_FUTURE_REGION_CONCEPT',region='biome variants (future regions)')
#Atlas resource nouns; every label is mapped, ambiguous can stays ambiguous.
resource_paths={'Wood':'01-wood.png','Stone':'02-stone.png','Iron ore':'05-metal-ore.png','Coal':'13-coal.png','Meat':'07-meat.png'}
for label,f in resource_paths.items():row(AT,label,existing='Docs/Design/ResourceTurnarounds/2026-11-23/reviewed-concepts/'+f,region='resource types')
for label,f in [('Hide','19-hide.png'),('Fur','20-fur.png'),('Plank','17-timber-planks.png')]:row(AT,label,existing='Docs/Design/ResourceTurnarounds/2026-11-23-expansion/reviewed-concepts/'+f,region='resource types')
row(AT,'Herbs','herbs',region='resource types');row(AT,'Crystal','crystal',region='resource types')
row(AT,'OIEL (ambiguous can label)',existing='Docs/Design/ResourceTurnarounds/2026-11-23/reviewed-concepts/06-fuel.png',status='AMBIGUOUS_SOURCE_NOT_NEW_REFINED_RESOURCE',notes='Likely intended oil/fuel. Fuel can already covered; no distinct refined oil asset or recipe established.',region='resource types')
#Extra frozen/video evidence outside the source boards.
row('selected-status.json at '+BASE,'defense_platform','defense_platform',status='PRIOR_BLOCKED_GENERATION',notes='No output/selected PNG; still in prior69-slot roster.')
for label,f in [('Mechanized wheat harvesting','wheat_harvester'),('Blue/orange wheat processor','wheat_processor')]:row('referenceA37–43seconds',label,f,status='GAP_LOCKED_VIDEO_ASSET',notes='Source pixels in audit/world/inputs/A-wheat-sequence.png; actual hidden geometry interpreted.')
#Record related covered assets without counting them as substitutions.
related={'defense_platform':['ballista_tower','guard_tower'],'cookhouse':['cookfire','campfire_cooking_rack'],'stockpile_shelter':[STORAGE,CARGO],'cold_storage_shed':[STORAGE],'fish_hut':['ice_fishing_spot','fishing_winch'],'bridges':['bridge_builder_cart'],'reinforced_palisades':[FENCE],'improved_gatehouse':[GATE],'fortress_walls':[FENCE],'fortress_gates':[GATE],'fortress_watchtowers':['watchtower','guard_tower'],'archer_towers':['ballista_tower'],'atlas_storage':[STORAGE],'late_furnaces':['furnace_level_50']}
for f,ids in related.items():
 for item in ids:
  if item in OLD:F[f]['existing_coverage'].append({'id':item,'path':OLD[item]['selected_path'],'status':OLD[item]['status'],'score':OLD[item]['score'],'reason':'Related family or earlier tier only; does not close this source form.'})
  else:F[f]['existing_coverage'].append({'path':item,'status':'PRIOR_SELECTED_REFERENCE','reason':'Related approved family; new source form remains distinct.'})
#No frozen scene/runtime or arithmetic claims from reference boards.
BOUNDARIES=['Static concept/reference art only; no native mesh, rig, motion, playable region or runtime approval.','Preserve original69-slot history, prior selected/rejected assets and current three-tier storehouse.','Atlas upgrade examples and future regions are explicit authored references, not implemented upgrade tables or an exhaustive future game catalogue.','No inferred recipes, crop lists, species drops, ammunition, powers, costs, capacity or exact world-unit dimensions.','Latest matching direct user design remains the identity authority; source-hidden rear/interior forms must be labelled interpreted.','Do not claim an existing family is absent merely because a board uses another visual variant. Covered-family rows name their exact coverage and limits.']
report={'schema_version':2,'date':'2026-11-27','agent':'/root/missing_world_audit','status':'REVISED_COMPLETE_NAMED_BOARD_CENSUS','supersedes':'world-gap-matrix-v1-superseded.json','correction':'V1 was a narrower equipment-chain audit and omitted many source-board building labels because original boards were unavailable. It was not a complete source-board census. V2 reopens its all-missing coverage conclusion.','baseline':{'repository':'ksolo21-web/HAVENLINE','branch':'art/conveyors-2026-11-26','commit':BASE,'tree_sha':TREE['sha'],'leaf_count':len(PATHS)},'source_boards':BOARDS,'source_occurrence_counts':dict(collections.Counter(r['source'] for r in ROWS)),'counts':{'source_occurrence_rows':len(ROWS),'distinct_missing_reference_families':len(F),'depicted_forms_to_cover_in_missing_families':sum(f['variant_count'] for f in F.values()),'family_counts_by_gap_class':dict(collections.Counter(f['gap_class'] for f in F.values()))},'family_gap_matrix':list(F.values()),'source_occurrence_matrix':ROWS,'covered_without_new_identity':['All51previous selected equipment sheets, including10furnacelevels1–50','All33previous bounded resource concepts','Original cargo crate/storage crates; exact green-lid crate pixel comparison inspected','Base rope-bound timber fence, tall gate posts and double gate','Current three-stage general storehouse contract','Previously approved conveyor/interface package','Existing two timber tower identities and ballista','All previously approved enemy/cast identities; lower-atlas cast census owned by independent cast auditor'], 'not_enumerated_as_physical_asset_requirements':[{'source':AT,'labels':['Heat radius','Buildings','Defenses','Workers','Storage','Tech & tools','Enemy difficulty'],'reason':'System improvement categories, not additional specific object designs.'},{'source':AT,'labels':['Your camp','Resource node','Enemy camp','Rescue survivor','Special location','Unlock gate','Expand path','Locked region'],'reason':'World-map legend categories and icons; not a complete specific location/prop identity catalogue.'},{'source':AT,'labels':['Infinite expansion','New biomes','Stronger enemies','New resources','Special events','Raider outposts','Hidden caves','Boss encounters'],'reason':'Feature promises, not a finite authored asset roster; named biome thumbnails are separately included.'},{'source':AT,'labels':['Blizzard','Wolf attack','Raider raid','Resource boom','Rescue call','Boss hunt'],'reason':'Event categories/icon examples; no separate physical object requirement or animation approval established.'},{'source':'18607.png /18600.png','labels':['How it fits together','assembled camp/palisade vignette'],'reason':'Arrangement of already listed parts, not an extra object identity.'}],'boundaries':BOUNDARIES,'source_scan_verification':{'all_existing_paths_resolve_in_fresh_baseline':all(c['path'] in PATHS for r in ROWS for c in r['existing_selected']),'all4_original_board_hashes_match_prior_evidence':True,'all3_named_boards_plus_atlas_upperhalf_and_resources_pixels_inspected':True,'covered_resource_crate_and_empty_plot_pixels_inspected':True,'new_generation_by_auditor':False,'native_runtime_modified':False},'navigation_sources_read':['AGENTS.md','BUILD_GAME.md','REPOSITORY_INDEX.md']}
assert report['source_scan_verification']['all_existing_paths_resolve_in_fresh_baseline']
(OUT/'world-gap-matrix.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'board-asset-census.json').write_text(json.dumps({'schema_version':2,'source_boards':BOARDS,'rows':ROWS},indent=2)+'\n')
lines=['# Havenline world render audit — revised complete source-board census','', '**V2 supersedes the narrower eight-asset checkpoint.** Original source boards are now recovered and pixel inspected. The earlier audit omitted readable building families and late atlas variants; those omissions are reopened here.','',f"Fresh immutable baseline: `{BASE}`; `{len(PATHS)}` leaves. All4recovered source hashes match prior evidence.",'',f"The audit records **{len(ROWS)}source occurrences**, mapping them to exact existing selected files or **{len(F)}missing reference families containing{sum(f['variant_count'] for f in F.values())}depicted forms**. Family grouping is for efficient render sheets, not a claim that all forms are one model.",'', '## Missing family coverage','', '| Family | Depicted forms | Source class | Why current selections do not close it |','|---|---|---|---|']
for f in F.values():lines.append('| '+f['name']+' | '+'; '.join(f['source_variants_to_cover'])+' | '+f['gap_class']+' | '+f['why_distinct']+' |')
lines+=['','## Every source occurrence','', '| Source | Label / visible form | Coverage | Existing selected IDs or new family |','|---|---|---|---|']
for r in ROWS:
 target=r['gap_family_id'] or '; '.join(x.get('id',x['path'].split('/')[-1]) for x in r['existing_selected'])
 lines.append('| '+r['source']+' | '+r['source_label']+' | '+r['status']+' | '+target+' |')
lines+=['','## Interpretation boundaries','']+['- '+x for x in BOUNDARIES]+['','The lower atlas cast/animal/raider census is separately owned by the independent cast auditor. Source context labels and event icons are listed in the JSON as non-object categories, rather than converted into invented physical asset counts.']
(OUT/'world-gap-audit.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(report['counts'],indent=2));print('source_counts',report['source_occurrence_counts']);print('all_existing_paths_resolve',report['source_scan_verification']['all_existing_paths_resolve_in_fresh_baseline'])
