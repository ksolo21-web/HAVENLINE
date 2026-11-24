import hashlib
import json
from pathlib import Path

ROOT = Path('/workspace/scratch/fc906e16b0fb')
OUT = ROOT / 'havenline-resource-expansion'
contract = json.loads((OUT / 'acceptance-contract.json').read_text())
REPO = 'https://github.com/ksolo21-web/HAVENLINE'
ART_SHA = '08ec81f4668e5285d09172d790554b2f0ae009a5'
RUNTIME_SHA = 'f74a84a2a288ab3d3935fba7a6cb9b975c2df239'
COOKER_SHA = '5abfc29f1c3c51bef99247641cf1131581899942'


def code_source(id, commit, path, evidence, lines=None):
    result = {'id': id, 'kind': 'repository_source', 'commit': commit,
              'path': path, 'url': f'{REPO}/blob/{commit}/{path}', 'evidence': evidence}
    if lines:
        result['line_range'] = lines
    return result


sources = [
    code_source('runtime-kinds', RUNTIME_SHA, 'HavenlineGodot/scripts/simulation.gd',
                'KINDS and inventory/stored dictionaries contain wood, stone, metal and fuel. Deposit transfers raw resources to stored; furnace level/warmth upgrades do not manufacture a new inventory item.', [8, 16]),
    code_source('runtime-transfers', RUNTIME_SHA, 'HavenlineGodot/scripts/simulation.gd',
                'Gather/deposit/repair transitions account for raw resource units. No cooking, drying, milling, smelting or tanning recipe table was found.', [238, 281]),
    code_source('runtime-customers', RUNTIME_SHA, 'HavenlineGodot/scripts/npc_population.gd',
                'Customer resource orders use the same raw KINDS. Service consumes resource units for credits; it is not proof of a food conversion.'),
    code_source('resource-registry', ART_SHA, 'Docs/Production/RESOURCE_ACTION_REGISTRY.json',
                'Wood and stone resolved; metal is frozen ore and fuel is frozen salvage. Fish T16 and wheat T19 require freeze and have production_ready=false.', [17, 94]),
    code_source('locked-video-chain', ART_SHA, 'Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md',
                'Reference A fish acquisition -> staffed processor -> cooked output -> counter, plus wheat/mechanized harvest -> blue/orange processing -> bread-like output. Explicitly forbids inventing an unshown exact recipe.', [29, 39]),
    code_source('station-kit', ART_SHA, 'HavenlineGodot/assets/stations_v2/catalog.json',
                'Visual kit lists fishing_rack, intake_machine, conveyor_straight, cooker_processor, processing_counter, service_counter, hearth_vessel and resource props. runtime_logic_included=false and visual_approval_claimed=false.', [1030, 1032]),
    code_source('station-scope', ART_SHA, 'Docs/Production/T05/FROZEN_SCOPE.md',
                'T05 supplies visual/attachment foundations; recipes, processing behavior, production rates, economy and inventory are outside its scope.'),
    code_source('construction-fixtures', ART_SHA, 'HavenlineGodot/data/world_transform_recipes.json',
                'prebuild_fixtures=true. Seed/foundation/reinforced debit wood, stone and metal for construction; these are not material processing recipes.'),
    code_source('primary-board-authority', ART_SHA, 'Docs/Production/T05/NEWEST_USER_RENDER_AUTHORITY_20260927.json',
                'Binds 18607 earlycamp utility/art language, 18600 earlycamp assets and Furnace_b080906_4K heavy-station language; newer direct renders supersede older boards on conflict.'),
    code_source('progression-board-binding', COOKER_SHA, 'Docs/Production/T05/R10D_COOKER_REBUILD_20260927.md',
                'Names 18607 earlycamp board, 18609 continuity board and 18608 late-game polish ceiling. No 18611/18613 binding was found in inspected repository documents.'),
    code_source('cooker-crop-receipt', COOKER_SHA, 'Docs/Production/T05/NeuralTrials/R37_components/source/receipt.json',
                'raw_meat_crate crop is from 32451.jpg; finished_food_tray crop is from 32450.jpg. source_view_only=true, hidden_geometry_verified=false, T05_critic_approved=false.'),
]

local_refs = [
    ('video-A-016', 'havenline-resource-reference-source/A-016.00.png', 'preservation_agent_direct_pixel_review',
     'Whole orange fish enters intake/conveyor. Cooked output retains whole-fish shape, golden/orange surface and broad dark roast bands; it is not evidence of a fillet intermediate.'),
    ('board-18607', 'havenline-primary-reference-source/18607.png', 'preservation_agent_direct_pixel_review',
     'Depicts furnace, cookfire, butcher table, drying rack, fishing spot, saw station, chopping station, workshop, stockpile, storage crates, fishing winch and sled hauler.'),
    ('board-18600', 'havenline-primary-reference-source/18600.png', 'preservation_agent_direct_pixel_review',
     'Depicts cooking, hung meat/drying rack, logs and workshop/wood-metal structures.'),
    ('board-18567', 'expanded-resource-references/18567.png', 'root_agent_direct_pixel_review',
     'Cooker/processor reference with red/brown rectangular meat output and broad cream fat cap.'),
    ('board-18603', 'expanded-resource-references/18603.png', 'root_agent_direct_pixel_review',
     'Depicts meat and fish drying-rack context; exact conversion recipe and finished item identity remain unspecified.'),
    ('board-18609', 'expanded-resource-references/18609.png', 'root_agent_direct_pixel_review',
     'Midcamp continuity board names lumber mill, quarry drill, steam saw, cookhouse and greenhouse; labels do not establish their recipes.'),
    ('world-atlas', 'expanded-resource-references/Havenline: Frostbound World Atlas.png', 'root_agent_direct_pixel_review',
     "Enlarged resource row reads WOOD, STONE, IRON ORE, COAL, MEAT, HIDE, HERBS, FUR, CRYSTAL and PLANK. A can has an ambiguous/garbled 'OIEL' label, likely intended oil/fuel. STEEL is not explicitly named. Resource labels do not establish production routes, species drops or recipe parameters."),
]
for id, rel, review, evidence in local_refs:
    p = ROOT / rel
    item = {'id': id, 'kind': 'supplied_reference_pixels', 'source_filename': p.name,
            'review_provenance': review, 'evidence': evidence}
    if p.is_file():
        data = p.read_bytes()
        item.update({'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    else:
        item['local_availability'] = 'not found at checkpoint; observation retained from prior review'
    sources.append(item)

sources.append({
    'id': 'prior-user-request', 'kind': 'explicit_user_request_and_prior_reviewed_concept',
    'evidence': 'The original user request explicitly included steel among the requested material renders. The prior 13-sheet set preserves a reviewed steel concept; this is not an atlas label or proof of a smelting recipe.',
    'prior_commit': contract['preserves']['commit'],
    'url': f"{REPO}/blob/{contract['preserves']['commit']}/Docs/Design/ResourceTurnarounds/2026-11-23/reviewed-concepts/04-steel.png"
})

sources.append({
    'id': 'cooker-visible-crops', 'kind': 'direct_pixel_review_with_repository_receipt',
    'receipt_ref': 'cooker-crop-receipt',
    'input': {'filename': '32451.jpg', 'sha256': '70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4', 'crop_bbox': [116, 661, 927, 1005], 'appearance': 'Irregular raw red meat with cream fat in timber crate.'},
    'output': {'filename': '32450.jpg', 'sha256': '5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719', 'crop_bbox': [486, 561, 1033, 796], 'appearance': 'Thick rounded rectangular red/brown meat portions with broad cream fat caps in metal tray.'},
    'boundary': 'Source-view appearance only; species, recipe, hidden geometry, processing temperature and runtime behavior are unverified.'
})

equipment = [
    {'id': 'furnace-hearth', 'equipment': ['furnace', 'hearth vessel'], 'status': 'confirmed_runtime', 'inputs': ['wood', 'stone', 'metal', 'fuel'], 'intermediate_outputs': [], 'final_outputs': ['camp warmth / furnace level upgrades (state changes, not new resource items)'], 'sources': ['runtime-kinds', 'runtime-transfers', 'station-kit'], 'recipe_boundary': 'No demonstrated ore -> steel, wood -> charcoal or fuel-refining conversion. Deposits and upgrades must not be relabelled smelting.'},
    {'id': 'fish-line', 'equipment': ['fishing rods/rack', 'intake machinery', 'conveyor', 'cooker/processor', 'processing counter', 'service counter'], 'status': 'locked_reference_design', 'inputs': ['whole fish'], 'intermediate_outputs': ['transported/stacked whole fish; no separately named prepared intermediate is frozen'], 'final_outputs': ['whole-fish-shaped cooked output', 'stocked counter items'], 'sources': ['locked-video-chain', 'video-A-016', 'resource-registry', 'station-kit', 'station-scope'], 'new_render_ids': ['cooked_fish', 'prepared_fish_fillet'], 'recipe_boundary': 'Cooked whole fish appearance is directly evidenced. Prepared fillet is an explicit art proposal. T16 fish freeze is still required; recipe quantities, fuel use, timing and yields are unspecified.'},
    {'id': 'meat-processor', 'equipment': ['cooker/processor', 'raw meat crate', 'finished food tray'], 'status': 'direct_visual_reference', 'inputs': ['irregular raw red meat portions'], 'intermediate_outputs': [], 'final_outputs': ['rounded rectangular red/brown meat portions with cream fat cap'], 'sources': ['cooker-visible-crops', 'cooker-crop-receipt', 'board-18567', 'station-scope'], 'new_render_ids': ['processed_meat_portion'], 'recipe_boundary': 'Visual input/output association is evidenced; exact species and runtime conversion are not.'},
    {'id': 'cookfire-cookhouse', 'equipment': ['cookfire', 'cookhouse'], 'status': 'direct_visual_reference', 'inputs': ['meat or fish proposed for art planning'], 'intermediate_outputs': [], 'final_outputs': ['cooked game meat proposed state'], 'sources': ['board-18607', 'board-18609'], 'new_render_ids': ['cooked_game_meat'], 'recipe_boundary': 'Equipment is depicted. No implemented generic cookhouse recipe, species eligibility or fuel requirement is established.'},
    {'id': 'drying-racks', 'equipment': ['meat drying rack', 'fish drying rack'], 'status': 'direct_visual_reference', 'inputs': ['hung meat', 'hung fish'], 'intermediate_outputs': [], 'final_outputs': ['dried meat proposed state', 'dried fish proposed state'], 'sources': ['board-18600', 'board-18603', 'board-18607'], 'new_render_ids': ['dried_meat', 'dried_fish'], 'recipe_boundary': 'Rack contents are visible; drying duration, recipe IDs, state transitions and yields are unspecified.'},
    {'id': 'wheat-food-line', 'equipment': ['wheat patch', 'mechanized harvester', 'blue/orange processing machinery'], 'status': 'locked_reference_design', 'inputs': ['wheat'], 'intermediate_outputs': ['unshown / unnamed'], 'final_outputs': ['bread-like cooked-food stack'], 'sources': ['locked-video-chain', 'resource-registry', 'station-scope'], 'reused_prior_render_ids': ['cooked_food'], 'recipe_boundary': 'T19 wheat freeze required. Do not invent a flour intermediate, mill recipe, baking recipe or greenhouse yield from the reference chain.'},
    {'id': 'saw-lumber', 'equipment': ['saw station', 'lumber mill', 'steam saw'], 'status': 'direct_visual_reference', 'inputs': ['timber/logs proposed pairing'], 'intermediate_outputs': ['unspecified'], 'final_outputs': ['PLANK is an explicit atlas resource; saw/lumber pairing is proposed'], 'sources': ['board-18607', 'board-18609', 'world-atlas'], 'new_render_ids': ['timber_planks'], 'recipe_boundary': 'No timber dimensions, conversion rate, machine tier or implemented plank recipe is established.'},
    {'id': 'chopping', 'equipment': ['chopping stump', 'chopping station'], 'status': 'direct_visual_reference', 'inputs': ['wood/logs'], 'intermediate_outputs': [], 'final_outputs': ['split firewood proposed visual state'], 'sources': ['board-18607', 'board-18600', 'resource-registry'], 'new_render_ids': ['split_firewood'], 'recipe_boundary': 'Chopping acquisition and equipment are evidenced; a distinct split-firewood inventory kind or recipe is not.'},
    {'id': 'animal-harvest-prep', 'equipment': ['butcher table', 'harvest/preparation context'], 'status': 'direct_visual_reference', 'inputs': ['wild-animal material; species eligibility undefined'], 'intermediate_outputs': ['unspecified'], 'final_outputs': ['HIDE', 'FUR', 'species meat concepts proposed'], 'sources': ['board-18607', 'world-atlas'], 'new_render_ids': ['hide', 'fur'] + [x['id'] for x in contract['animal_meat_concepts']], 'recipe_boundary': 'HIDE and FUR are explicit atlas nouns. No complete species drop table, skinning yields, edible roster or tanning route exists in inspected sources. Companions remain separate.'},
    {'id': 'stone-slate-quarry', 'equipment': ['mining nodes', 'quarry drill'], 'status': 'planned_or_depicted_equipment', 'inputs': ['stone/ore deposits; slate resource appearance in prior art set'], 'intermediate_outputs': ['unspecified'], 'final_outputs': ['raw stone/ore acquisition is supported; processed stone/slate output unspecified'], 'sources': ['runtime-kinds', 'resource-registry', 'board-18609'], 'reused_prior_render_ids': ['stone', 'slate', 'metal_ore'], 'recipe_boundary': 'A quarry drill is extraction equipment, not proof of cut blocks, bricks or finished slate tiles.'},
    {'id': 'steel-oil', 'equipment': ['specific conversion equipment unspecified'], 'status': 'request_concept_and_ambiguous_reference', 'inputs': ['unspecified'], 'intermediate_outputs': ['unspecified'], 'final_outputs': ['steel: explicitly user-requested prior concept, not an atlas label', "can likely intended as oil/fuel, with ambiguous atlas label 'OIEL'"], 'sources': ['prior-user-request', 'world-atlas', 'resource-registry', 'runtime-kinds'], 'reused_prior_render_ids': ['steel'], 'recipe_boundary': 'Neither the requested steel concept nor the ambiguous atlas can establishes an ore -> steel smelter or an oil/fuel refinery. The can is outside the current 20-sheet expansion; prior fuel and coal concepts do not establish conversion recipes.'},
    {'id': 'greenhouse', 'equipment': ['greenhouse'], 'status': 'planned_or_depicted_equipment', 'inputs': ['unspecified'], 'intermediate_outputs': ['unspecified'], 'final_outputs': ['unspecified'], 'sources': ['board-18609'], 'recipe_boundary': 'Depicted equipment only; no crop list or greenhouse-specific output is established.'},
    {'id': 'workshop', 'equipment': ['workshop'], 'status': 'planned_or_depicted_equipment', 'inputs': ['unspecified'], 'intermediate_outputs': ['unspecified'], 'final_outputs': ['unspecified'], 'sources': ['board-18600', 'board-18607'], 'recipe_boundary': 'No supported inventory list of nails, rods, plates, gears or other workshop outputs. Do not fabricate them.'},
    {'id': 'logistics', 'equipment': ['stockpile', 'storage crates', 'conveyor', 'fishing winch', 'sled hauler', 'service counter'], 'status': 'depicted_transport_storage_or_service', 'inputs': ['carried or stocked resources'], 'intermediate_outputs': ['same resources moved/stored'], 'final_outputs': ['same resource form; service payments where implemented'], 'sources': ['board-18607', 'station-kit', 'runtime-customers', 'locked-video-chain'], 'recipe_boundary': 'Transport, storage and service do not establish a new processed material.'},
]

render_map = []
for item in contract['animal_meat_concepts']:
    render_map.append({'id': item['id'], 'classification': 'art_proposal', 'scope_status': item['status'],
                       'equipment_coverage': ['animal-harvest-prep'], 'source_boundary': 'Wildlife roster association does not establish an implemented meat drop or food eligibility; exact roster provenance is separately recorded in wildlife-source-provenance.json.'})
for item in contract['processed_and_byproduct_concepts']:
    match = [e['id'] for e in equipment if item['id'] in e.get('new_render_ids', [])]
    classification = {'processed_meat_portion': 'direct_visual_output_concept', 'cooked_fish': 'locked_reference_output_concept', 'hide': 'explicit_atlas_resource_concept', 'fur': 'explicit_atlas_resource_concept', 'timber_planks': 'explicit_atlas_resource_with_proposed_equipment_mapping'}.get(item['id'], 'art_proposal')
    render_map.append({'id': item['id'], 'classification': classification, 'equipment_coverage': match, 'basis': item['basis']})

document = {
    'title': 'Havenline equipment and resource-output source coverage',
    'date_utc': '2026-11-23',
    'purpose': 'Source map for a bounded 20-sheet concept-art expansion; not a production recipe registry or runtime approval.',
    'status_legend': {
        'confirmed_runtime': 'Behavior is visible in the inspected runtime source at the named commit.',
        'locked_reference_design': 'Observed reference-video chain is required design; implementation is not implied.',
        'direct_visual_reference': 'Equipment or output shape is directly visible in supplied art; recipes are not implied.',
        'planned_or_depicted_equipment': 'Equipment exists as a label/depiction; conversion outputs remain unspecified.',
        'explicit_resource_nouns_only': 'Resource name is explicit, but its recipe and station association are not.',
        'request_concept_and_ambiguous_reference': 'A requested concept and a separately ambiguous source depiction; neither establishes a conversion recipe.',
        'art_proposal': 'New visual planning proposal, not an implemented drop/recipe claim.',
        'unspecified': 'No exact output/recipe evidence was found within the inspected scope.'
    },
    'inspection_scope': {
        'runtime_commit': RUNTIME_SHA,
        'reference_art_commit': ART_SHA,
        'newer_cooker_evidence_commit': COOKER_SHA,
        'prior_art_package_commit': contract['preserves']['commit'],
        'confirmed_runtime_resource_kinds': ['wood', 'stone', 'metal', 'fuel'],
        'complete_future_recipe_or_drop_registry_found': False,
        'production_implementation_approval_claimed': False,
        'unseen_source_boundary': 'No 18611/18613 repository binding found in inspected documents; no unseen higher-tier production chain is inferred.',
        'construction_boundary': 'world_transform_recipes.json is construction state/debit evidence, not material conversion evidence.'
    },
    'sources': sources,
    'equipment_chains': equipment,
    'new_render_coverage': render_map,
    'new_render_count': len(render_map),
    'reused_prior_outputs': ['steel', 'cooked_food (bread-like wheat output)'],
    'undefined_recipe_fields': ['exact species drops and food eligibility', 'quantities and yields', 'timings', 'fuel requirements', 'station tier bindings', 'recipe IDs', 'inventory kind IDs for proposed outputs', 'unshown intermediates'],
    'excluded_unestablished_outputs': ['flour', 'leather', 'canned meals', 'refined oil/fuel', 'steel plates', 'steel rods', 'charcoal', 'bricks', 'cut masonry blocks', 'workshop gears/nails'],
    'completeness_boundary': 'The 20 additions cover the agreed bounded art contract. This is not a claim that every future animal, biome, equipment tier or implemented processing recipe has been rendered; that requires a complete frozen recipe/drop specification.'
}
(OUT / 'source-equipment-coverage.json').write_text(json.dumps(document, indent=2) + '\n')

# Preserve a source-bound snapshot of the prior accepted package before new files are staged.
prior = json.loads((ROOT / 'havenline-resource-renders/package-file-manifest.json').read_text())
baseline_files = []
for file in prior['files']:
    path = Path(file['local_path'])
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    assert actual == file['sha256'], f'Prior package changed: {path}'
    baseline_files.append({key: file[key] for key in ['path', 'bytes', 'sha256', 'git_blob_sha']})
baseline = {'commit': contract['preserves']['commit'], 'prior_package_path': prior['package_path'],
            'verified_file_count': len(baseline_files), 'files': baseline_files}
(OUT / 'prior-package-preservation-baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
print(json.dumps({'source_coverage': str(OUT / 'source-equipment-coverage.json'), 'sources': len(sources), 'equipment_groups': len(equipment), 'new_render_mappings': len(render_map), 'prior_files_verified': len(baseline_files)}))
