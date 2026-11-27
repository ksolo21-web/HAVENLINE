"""Build the root-review draft catalog; this script never invokes image generation."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
MATRIX_PATH = ROOT / 'audit/world/world-gap-matrix.json'
matrix = json.loads(MATRIX_PATH.read_text())
families = {row['id']: row for row in matrix['family_gap_matrix']}
assert len(families) == 30 and sum(row['variant_count'] for row in families.values()) == 65

def fact(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    result = {'local_path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
              'git_blob_sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}
    with Image.open(path) as im:
        result.update(dimensions=list(im.size), actual_format=im.format)
        im.verify()
    return result

board_dir = ROOT / 'source-records/original-boards'
sources = {
    'early': {'path': board_dir / '18607.png', 'role': 'Original user early-camp board; object identity and source-visible forms.'},
    'original': {'path': board_dir / '18600.png', 'role': 'Original user unlabeled camp-prop board; object identity and source-visible forms.'},
    'mid': {'path': board_dir / '18609.png', 'role': 'Original user mid-camp board; object identity and source-visible forms.'},
    'atlas': {'path': board_dir / 'Havenline: Frostbound World Atlas.png', 'role': 'Original user world atlas; only the explicitly identified family/column/row is identity authority.'},
    'wheat': {'path': ROOT / 'audit/world/inputs/A-wheat-sequence.png', 'role': 'Exact locked source-A contact sheet, thirteen samples spanning 37–43 seconds; machine appearance evidence, not recipe or performance evidence.'},
    'style': {'path': ROOT / 'renders/defense-platform-turnaround-r2.png', 'role': 'Reviewed Havenline material and rendering style ONLY: broad sculpted bevels, warm timber, blue steel, restrained snow, pale studio background. Do not copy the defense platform geometry.'},
    'fence': {'path': ROOT.parent / 'havenline-structures-2026-11-25/renders/fence-oblique-r2.png', 'role': 'Existing approved basic rope-bound fence identity; preserve it exactly in the supplemental corner assembly, separate from reinforced upgrades.'},
}
for key, row in sources.items():
    row.update(fact(row.pop('path')))
    if key in {'early', 'original', 'mid', 'atlas'}:
        recorded = matrix['source_boards'][Path(row['local_path']).name]
        assert row['sha256'] == recorded['sha256'] and row['bytes'] == recorded['bytes']

STYLE = (
    'Create a premium HAVENLINE sculpted 3D game-asset reference sheet. Match the supplied Havenline style reference: '
    'confident chunky silhouettes, broad clean bevels, subtly carved warm timber, convincing blue or dark steel, bronze fasteners where the source shows them, '
    'pale stone and selective clean snow on exposed ledges. Keep source-specific roof, canvas, glass and metal colors. '
    'Use refined animated-feature/PBR-like rendering, soft studio illumination, crisp useful detail, and quiet contact shadows. '
    'Use a pale warm-gray studio background, generous gutters and complete uncropped objects. Avoid photoreal grime, painterly noise, glossy toy-plastic flattening, '
    'extra characters, decorative piles, fake UI, promotional badges, and crowded copied-board graphics. '
    'This is deliberate production reference art with clear geometry and a small clean sans-serif heading.'
)
CONSISTENCY = (
    'The two opposing three-quarter views of a form must show ONE fixed design from front-left and rear-right; rotate the camera around it, do not mirror the image. '
    'Keep doors, windows, chimneys, pipe runs, roof pitch, support posts, snow patches, planks, handles, annexes and material assignments in the same physical positions. '
    'Preserve the distinct source silhouettes; do not make variants by recoloring one duplicated model. '
    'The source boards mostly show one side, so rear faces and any opened interiors are restrained concept interpretations. '
    'Add the short footer SOURCE-BASED CONCEPT · UNSEEN SURFACES INTERPRETED. '
    'Do not print invented levels, costs, capacities, rates, recipes, unlocks, dimensions or gameplay claims. '
    'Source-visible props remain aesthetic context; no new production chain, crop list, animal drop, weapon mechanism or runtime behavior is established.'
)

drafts = []

def build_views(variants, labels, mode='pairs', details=None, extra=None, open_state=False):
    views = []
    for i, (variant, label) in enumerate(zip(variants, labels)):
        for camera in ['FRONT-LEFT', 'REAR-RIGHT']:
            views.append({'source_variant': variant, 'variant_display_label': label,
                          'camera': camera + ' THREE-QUARTER', 'state': 'OPEN' if open_state else 'SOURCE FORM',
                          'panel_label': label + ' / ' + ('OPEN ' if open_state else '') + camera,
                          'purpose': 'Opposing geometry and identity reference',
                          'interpretation_boundary': 'Source-hidden surfaces interpreted; source-visible identity retained.'})
    if mode == 'single4':
        assert len(variants) == 1 and details and len(details) == 2
        for label, camera, purpose in details:
            views.append({'source_variant': variants[0], 'variant_display_label': labels[0],
                          'camera': camera, 'state': 'DETAIL / INTERPRETED OPEN STATE',
                          'panel_label': label, 'purpose': purpose,
                          'interpretation_boundary': 'Any source-hidden interior or use state is a visual interpretation only.'})
    if extra:
        views.extend(extra)
    return views

def add(family_id, refs, direction, *, suffix=None, title=None, variant_indexes=None, labels=None,
        mode='pairs', details=None, extra=None, layout=None, checks=None, dependency=None, open_state=False):
    family = families[family_id]
    indexes = list(range(family['variant_count'])) if variant_indexes is None else variant_indexes
    variants = [family['source_variants_to_cover'][i] for i in indexes]
    labels = labels or [variant.upper() for variant in variants]
    assert len(labels) == len(variants)
    ident = 'world-' + (suffix or family_id.replace('_', '-'))
    future = (family['gap_class'].startswith('ATLAS_') and family_id not in {'herbs', 'crystal'}) or (family_id == 'medical_facilities' and all(i >= 3 for i in indexes))
    title = title or family['name'].upper()
    if future:
        title = 'FUTURE CONCEPT | ' + title
    views = build_views(variants, labels, mode, details, extra, open_state)
    if layout is None:
        if len(views) == 4:
            layout = 'Four large panels in a 2-column by 2-row landscape sheet. For a two-form sheet each row is one form: front-left then rear-right. For a single-form sheet the top row is the opposing exterior pair and the bottom row is the two specified detail/use views.'
        elif len(views) == 6:
            layout = 'Six large panels in a 3-column by 2-row landscape sheet. Each column is one source form: front-left above its matching rear-right view. Use the source form order given below.'
        elif len(views) == 8:
            layout = 'Eight panels in a 4-column by 2-row landscape sheet. Each column is one tile type: front-left above its matching rear-right view. Keep a clear gap around each complete tile.'
        else:
            raise AssertionError((ident, len(views)))
    ordered = [dict(order=i+1, source_key=key, **sources[key]) for i, key in enumerate(refs)]
    assert len(ordered) <= 5
    ref_lines = '\n'.join('Reference ' + str(row['order']) + ': ' + Path(row['local_path']).name + ' — ' + row['role'] for row in ordered)
    occurrences = family['source_occurrences']
    if family_id == 'medical_facilities':
        occurrences = [o for o in occurrences if ('Atlas.png' in o['source']) == all(i >= 3 for i in indexes)]
    elif family_id == 'biome_vignettes':
        occurrences = [o for o in occurrences if o['label'].lower() in variants]
    anchors = '\n'.join('- ' + occurrence['source'] + ': ' + occurrence['label'] + ('; ' + occurrence['region'] if occurrence['region'] else '') for occurrence in occurrences)
    panels = '\n'.join('- ' + v['panel_label'] + ': ' + v['purpose'] for v in views)
    prompt = (STYLE + '\n\nREFERENCES IN ACTUAL ORDER\n' + ref_lines + '\n\n'
              'SUBJECT: ' + title + '.\n' + direction + '\n\nSOURCE ANCHORS\n' + anchors + '\n\n'
              'SHEET\nSmall heading: HAVENLINE | ' + title + '. Requested landscape canvas 1536 × 1024, with detail large enough to judge. '
              + layout + '\nRequired panels:\n' + panels + '\n\n' + CONSISTENCY)
    if future:
        prompt += '\nThis sheet is an atlas future visual concept. Label example forms A/B/C by their source row, never as invented numerical upgrade tiers. It does not replace an existing approved asset or claim a playable region.'
    if family_id == 'late_furnaces':
        prompt += '\nThe printed furnace range labels 51–70, 71–90 and 91–100 are copied from the source atlas header. They are source identifiers here, not invented individual level models or progression rules.'
    row = {'id': ident, 'recommended_render_id': ident + '-r1', 'status': 'DRAFT_REQUIRES_ROOT_REVIEW',
           'family_id': family_id, 'source_form_indexes_zero_based': indexes, 'source_variants': variants,
           'source_form_count_on_sheet': len(variants), 'future_visual_concept': future,
           'source_occurrences': occurrences, 'source_scope_reason': family['why_distinct'],
           'ordered_reference_inputs': ordered, 'required_views': views, 'requested_layout': layout,
           'source_interpretation_boundary': 'Only source-visible silhouettes/materials are observed; unseen rear/interior/open-state geometry is explicitly interpreted.',
           'acceptance_checks': [
               'Every listed source form is represented by both required opposing views.',
               'Source-visible identity and silhouette match the correct board region; source variants remain distinct.',
               'Fixed geometry, face assignments and props remain coherent across views; no mirror substitution.',
               'Complete objects, readable labels and material detail; no cropped supports or hidden required interface.',
               'Rear/interior interpretation and any future-concept status remain explicit; no gameplay or numerical invention.'
           ] + (checks or []),
           'ready_after_root_review': dependency is None, 'depends_on_sheet_ids': [dependency] if dependency else [],
           'draft_arguments': {'prompt': prompt, 'referenced_image_paths': [x['local_path'] for x in ordered], 'transparent_background': False}}
    if dependency:
        row['ready_after_root_review'] = False
        row['required_additional_reference'] = {'order': len(ordered)+1, 'approved_sheet_id': dependency,
            'local_path': None, 'sha256': None, 'instruction': 'Bind the exact independently approved closed-state native PNG before creating the real invocation.'}
        row['deferred_argument_template'] = row.pop('draft_arguments')
        row['deferred_argument_template']['prompt'] += '\n\nMANDATORY DEPENDENCY: Reference 3 must be the exact independently approved closed-state fortress-gate sheet from this batch. Keep all three gate designs identical to that reference while opening their actual gate panels coherently. Do not invoke this draft without that third reference. If the closed design does not establish a visually coherent opening arrangement, repair/review that ambiguity before generating the open-state sheet.'
        row['draft_arguments'] = None
    drafts.append(row)

add('cookhouse', ['original','mid','style'],
    'Render the two distinct cookhouses. EARLY: the small open-front timber kitchen in 18600 row 1 far right, with blue roof, chimney, hanging utensils and the source-visible cooking pot/counter. EXPANDED: the broader 18609 second-row cookhouse with its blue roof, brick/metal chimneys, orange front awning and glowing oven opening. Preserve their different footprints and roof silhouettes. Show the working front clearly in the first angle; show coherent chimney placement and structural rear in the opposing angle. Keep them buildings, separate from the already-covered open cookfire.',
    labels=['EARLY COOKHOUSE','EXPANDED COOKHOUSE'], checks=['The early open kitchen and expanded oven/awning building remain visibly distinct.'])
add('greenhouse', ['mid','style'],
    'Reconstruct the 18609 top-right GREENHOUSE / WARM GROW HUT: a compact framed glass building with curved/arched roof panes, warm timber structure, blue base/corner fittings and a readable entrance. Preserve transparent glazing and the source silhouette. Use a few generic leafy growing beds visible through glass; no named crops, extra agricultural machine or heating-system schematic. The interior view is a restrained visual interpretation with a usable central access strip.',
    labels=['WARM GROW HUT'], mode='single4', details=[('OPEN ENTRY / INTERIOR','FRONT THREE-QUARTER WITH DOOR OPEN','Show entrance clearance, glass framing and generic beds through the same building.'),('FRAME / GLAZING DETAIL','CLOSE THREE-QUARTER','Readable junction of roof glass, timber frame and blue base; no dimensions.')],
    checks=['Glazing remains legible instead of becoming opaque blue roofing.', 'Door and interior access remain physically plausible.'])
add('workshop', ['early','mid','original','style'],
    'Render BASIC WORKSHOP from 18607 lower building row (supported by the open-front tool workshop in 18600 row 1) and IMPROVED WORKSHOP from 18609 top buildings. Preserve the compact basic blue-gabled timber workshop with visible bench/tools and the larger reinforced midcamp building with its source-visible roofline, fittings and front work area. The earlier 18600 illustration supports the basic family; do not create a third workshop. Keep tool silhouettes legible and rear wall/chimney placement coherent. No invented crafting recipes or industrial process chain.',
    labels=['BASIC WORKSHOP','IMPROVED WORKSHOP'])
add('wheat_harvester', ['wheat','style'],
    'Use the source-A 37–43 second contact sheet for identity. Render the FIELD-MOUNTED ROTARY HARVESTER: stationary silver curved rotary heads above the wheat rows, connected with the source-visible low blue collection frame/rails and blue collection belt. It is not a tractor or a vehicle. Reproduce the strongly readable source arrangement of curved heads and repeated blue collector sections on one compact field demonstration patch. Keep a short boundary of uncut golden wheat so the harvest-facing side reads; no whole game map, floating cash, workers, interface icons or invented crop stage. The overhead panel must resolve the same physical arrangement seen in both three-quarter views.',
    labels=['ROTARY WHEAT HARVESTER'], mode='single4', details=[('OVERHEAD / FIELD LAYOUT','TOP','Show curved heads, wheat strip and blue collection structure in a coherent spatial relationship.'),('COLLECTOR INTERFACE','CLOSE THREE-QUARTER','Show the blue collection-side end and physically connected support/rail relationship; no recipe diagram.')],
    checks=['Stationary field assembly, silver curved heads and blue collectors match source A.', 'No tractor cab/wheels or unsourced flour-processing machinery.'])
add('wheat_processor', ['wheat','style'],
    'Use source A frames around 40.5–43 seconds for the separate BLUE/ORANGE WHEAT FOOD PROCESSOR. Preserve its rounded blue housing, two orange top caps and the red/dark front roller/opening, a wheat-side blue intake connection on its right and a front tray for the rounded orange bread-like output pieces visible in the source. Give the short intake connection and front output tray clear physical support. Treat the orange pieces as the source-visible food form; do not add flour sacks, a milling stage, baking recipe labels, throughput values or extra ovens. Show one compact machine, not the whole camp chain.',
    labels=['WHEAT FOOD PROCESSOR'], mode='single4', details=[('WHEAT-SIDE CONNECTION','RIGHT-SIDE CLOSE THREE-QUARTER','Show the supported intake opening and short blue connector without hiding its join.'),('FRONT FOOD TRAY','FRONT CLOSE THREE-QUARTER','Show the source-like front opening and a few rounded food pieces in the tray, without flow numbers or recipe labels.')],
    checks=['Right intake and front food tray stay on the same sides in every panel.', 'No invented flour intermediate or exact production claim.'])
add('herbs', ['atlas','style'],
    'Create one gathered HERBS resource matching the small green leafy resource icon in the atlas bottom-left resource row. A compact readable leafy tuft/bundle with the same simple source silhouette, natural green folds and a modest stem/root base. Keep it an identifiable collected resource, not a potted plant, potion, flower bouquet or medicine kit. Use the same leaf arrangement in the opposing views; add a top view and a leaf/stem material close-up. No species, medical effect, recipe or quantity label.',
    labels=['HERBS'], mode='single4', details=[('TOP','TOP','Show the same compact leaf arrangement from above.'),('LEAF / STEM DETAIL','CLOSE THREE-QUARTER','Show leaf edges, folds and stem junction without adding a new resource variant.')])
add('crystal', ['atlas','style'],
    'Create one CRYSTAL resource cluster matching the atlas resource-row icon: a small grouped cluster of cool lavender/blue-gray angular mineral points with clear faceted tips and a stable rough base. Keep facets readable, with subtle mineral translucency and restrained highlights. Use the same point count and arrangement in every view. No runes, magical aura, electrical power, named element, gemstone tiers or new mining node. The close-up explains material and base, not gameplay.',
    labels=['CRYSTAL'], mode='single4', details=[('TOP','TOP','Show the same point arrangement from above.'),('FACETS / BASE DETAIL','CLOSE THREE-QUARTER','Show the mineral facet transitions and compact supporting base.')])
add('camp_tiles', ['early','original','style'],
    'Create exactly FOUR physical camp modules from 18607 upper-right CAMP FOUNDATIONS & TILES: CAMP CENTER TILE with its distinct inset timber center/stone-edged base, WALKWAY TILE with straight timber planks, SNOW TILE as a clean thick sculpted snowy square, and STORAGE PAD as a slightly raised framed timber platform with corner structure. Use 18600 snow/plank tile views as supporting material reference only. These are actual sculpted 3D tile objects, not dashed purchase-zone decals. Each type must receive opposing three-quarter views. Keep edge thickness, plank direction, corners and snow distribution coherent. No crates/buildings placed on them, no price text and no implied grid dimensions.',
    labels=['CAMP CENTER TILE','WALKWAY TILE','SNOW TILE','STORAGE PAD'],
    checks=['Exactly four tile identities and eight panels; each type has its opposing pair.', 'Physical edge thickness and sculpted form remain distinct from existing marked interaction zones.'])
add('survivor_tents', ['early','mid','original','style'],
    'Render the compact BEGINNER TENT from 18607 (supported by the blue/beige A-frame tent in 18600) and the larger SURVIVOR SHELTER TENT from 18609 second row. The beginner is a small blue canvas A-frame with simple timber poles and rope anchors. The survivor shelter is larger and insulated, with the source-visible stove/chimney, blue canvas, warm entrance fabric and stronger anchoring. Preserve the distinct roof/tent shape and the fixed chimney side. Show front opening and opposite rear without inventing a medical role, occupancy number or heating mechanic.',
    labels=['BEGINNER TENT','SURVIVOR SHELTER'])
add('cabins', ['early','mid','style'],
    'Render WOODEN HUT from 18607 middle building row and UPGRADED CABIN from 18609 top buildings. Preserve the simple compact blue-gabled log/timber hut and the larger more developed residential cabin with its source roofline, chimney, warm windows and entry detail. Keep residential identity distinct from workshop, kennel and storage buildings. Windows, doors and roof ridges must stay in fixed positions through each opposing pair. Do not assign new numerical levels or resident counts.',
    labels=['WOODEN HUT','UPGRADED CABIN'])
add('bunkhouse', ['mid','style'],
    'Reconstruct the 18609 BUNKHOUSE as a broader timber residence with its distinctive extended blue roof, source-visible chimneys, windows and entrance arrangement. It must read as the named bunkhouse, not an enlarged crate shed. The interpreted open-front/interior panel may show a restrained shared sleeping arrangement and a clear access aisle while preserving the exterior footprint; bed count is illustrative and must not be labeled as capacity. Keep all source-visible roof and door positions coherent.',
    labels=['BUNKHOUSE'], mode='single4', details=[('OPEN FRONT / INTERIOR','FRONT THREE-QUARTER CUTAWAY','Show an interpreted shared sleeping interior within the same footprint, with no capacity claim.'),('ROOF / WALL DETAIL','CLOSE THREE-QUARTER','Show roof eave, wall framing, snow and chimney transition.')])
add('stockpile_shelter', ['early','style'],
    'Reconstruct the STOCKPILE shelter in 18607 middle building row: a blue-gabled timber roof over an openly accessible material bay, with timber logs and a few existing crate/barrel forms visible below. Preserve its open-front storage-shelter identity and supporting posts; it is not the approved enclosed general storehouse. Keep clear entry to the pile and a believable support base. Show the rear structure coherently and avoid filling every opening with decorative goods.',
    labels=['STOCKPILE SHELTER'], mode='single4', details=[('OPEN STOCKPILE BAY','FRONT THREE-QUARTER CLOSE VIEW','Show the accessible front bay and restrained existing material props.'),('POST / ROOF SUPPORT','REAR CLOSE THREE-QUARTER','Show coherent roof support, wall edge and plinth detail.')])
add('medical_facilities', ['early','original','mid','style'],
    'Render exactly the THREE EARLY/MIDCAMP medical forms. CLINIC TENT: cream A-frame medic canvas with the green cross from 18607 lower building row. BASIC MEDICAL HUT: the small green-roof timber hut with source white/green medical marks from 18600 row 2 left. REINFORCED MEDICAL HUT: the blue-roof strengthened timber building with orange/white medical sign from 18609 second row. Preserve canvas-versus-building identity, roof colors and entrance/symbol placement. Do not blend them into one roof recolored three times. No patients, injuries, treatment equipment inventory, healthcare claims or invented numerical upgrade levels.',
    suffix='medical-early', title='EARLY MEDICAL FORMS', variant_indexes=[0,1,2], labels=['CLINIC TENT','BASIC MEDICAL HUT','REINFORCED MEDICAL HUT'],
    checks=['Cream canvas tent, green-roof hut and reinforced blue-roof hut remain three distinct source designs.'])
add('medical_facilities', ['atlas','style'],
    'Render the THREE forms in the atlas HOSPITAL column, top/middle/bottom rows, as future field-hospital concept examples A/B/C. Preserve each source roof/canvas silhouette, green/tan/cream palette, timber support/base, entrance and medical-cross placement. These are the three atlas hospital appearances, separate from the early clinic tent and two early/midcamp huts. Keep their distinct source masses and awnings; do not turn them into modern glass hospitals or invent machinery. No patients, clinical claims, bed capacities or numerical tiers.',
    suffix='medical-atlas', title='ATLAS HOSPITAL EXAMPLES', variant_indexes=[3,4,5], labels=['ATLAS EXAMPLE A','ATLAS EXAMPLE B','ATLAS EXAMPLE C'],
    checks=['Top/middle/bottom Hospital-column forms remain distinct.', 'Explicit future visual concept; no invented tier numbers.'])
add('dog_kennels', ['early','mid','style'],
    'Render DOG KENNEL from 18607 lower building row and the larger KENNEL LEVEL 2 from 18609 second row. Preserve the compact blue-gabled open-arch dog house with its source bowl, then the more substantial blue-roof timber kennel building with its source door/frontage. Keep canine-scale shelter proportions and fixed bowl/door placement. No dog is needed, and no additional companion design or breeding/training mechanic should be invented. Source labels may distinguish BASIC KENNEL and IMPROVED KENNEL without adding any new level schedule.',
    labels=['BASIC KENNEL','IMPROVED KENNEL'])
add('cold_storage_shed', ['mid','style'],
    'Reconstruct the 18609 COLD STORAGE SHED: an arched blue insulated metal roof/body on a compact foundation, gray front double doors, source white snowflake identity, warm small entry accents and the restrained exterior fittings visible in the source. Keep the arched silhouette distinct from the approved gable-roof general storehouse. The opened-door view shows a simple interpreted lined storage interior with a few neutral crates and a usable entry. Do not depict a new refrigeration engine, temperatures, capacities or food recipes.',
    labels=['COLD STORAGE SHED'], mode='single4', details=[('DOORS OPEN / INTERIOR','FRONT THREE-QUARTER WITH DOORS OPEN','Keep the same door hinges/leaf proportions and show a restrained interpreted storage interior.'),('ARCH / REAR DETAIL','REAR CLOSE THREE-QUARTER','Show insulated curved body, end wall, roof bands and source-style fittings.')])
add('bridges', ['early','mid','style'],
    'Render the source ROPE BRIDGE from 18607 and REINFORCED BRIDGE from 18609. The rope bridge has a modest sagging plank deck between four heavy timber posts with rope rails and stone feet. The reinforced bridge has a broader sturdier framed timber deck, blue capped/fitted posts, rope side lines and stone abutments as shown by the source. Keep each on two small snowy bank/abutment pieces with a narrow gap so both approaches, supported deck ends and underside read. No floating entrance, disconnected landing, unsupported deck or invented real-world engineering specification. This is the crossing itself, not the existing bridge-builder cart.',
    labels=['ROPE BRIDGE','REINFORCED BRIDGE'],
    extra=[{'source_variant':'rope bridge','variant_display_label':'ROPE BRIDGE','camera':'LOW THREE-QUARTER','state':'SUPPORT DETAIL','panel_label':'ROPE BRIDGE / APPROACH + SUPPORT','purpose':'Show deck-to-bank contact, anchored posts and the readable underside.','interpretation_boundary':'Visual support interpretation, not an engineered load-bearing plan.'},
           {'source_variant':'reinforced bridge','variant_display_label':'REINFORCED BRIDGE','camera':'LOW THREE-QUARTER','state':'SUPPORT DETAIL','panel_label':'REINFORCED BRIDGE / APPROACH + SUPPORT','purpose':'Show both a deck-end support connection and the source-style framed underside.','interpretation_boundary':'Visual support interpretation, not an engineered load-bearing plan.'}],
    layout='Six panels in a 3-column by 2-row landscape sheet. Top row: rope bridge front-left, rear-right, approach/support detail. Bottom row: reinforced bridge front-left, rear-right, approach/support detail.',
    checks=['Both ends have readable approaches and supporting contact with their banks.', 'The reinforced crossing is distinct from the lighter suspended rope bridge.'])
add('reinforced_palisades', ['mid','original','fence','style'],
    'Render SHORT and TALL reinforced palisade modules from 18609 third row, using the blue steel straps and distinct post heights in that board; 18600 metal-banded palisade is supporting source. Keep the two upgrades distinct from the existing cream-rope basic fence. Add ONE supplemental assembly shown twice: a 90-degree corner using the EXACT approved basic rope-bound fence identity in reference 3, matching the corner arrangement visible at 18600 row 2 right. This corner is an additional view of an existing family, not a new wall tier. Show outside and inside so the corner-post relationship and rope joins read without interpenetration. Do not replace the base fence with blue bands.',
    labels=['SHORT REINFORCED','TALL REINFORCED'],
    extra=[{'source_variant':None,'supplemental_existing_identity':'basic_palisade_corner_join','variant_display_label':'BASIC FENCE CORNER','camera':'OUTSIDE THREE-QUARTER','state':'90-DEGREE ASSEMBLY','panel_label':'BASIC FENCE CORNER / OUTSIDE','purpose':'Show the approved basic fence forming a coherent right-angle corner.','interpretation_boundary':'New assembly view of an existing approved identity; no new family or tier.'},
           {'source_variant':None,'supplemental_existing_identity':'basic_palisade_corner_join','variant_display_label':'BASIC FENCE CORNER','camera':'INSIDE OPPOSING THREE-QUARTER','state':'90-DEGREE ASSEMBLY','panel_label':'BASIC FENCE CORNER / INSIDE','purpose':'Reveal the same corner post, rope join and plank junction from inside.','interpretation_boundary':'New assembly view of an existing approved identity; no new family or tier.'}],
    layout='Six panels in a 3-column by 2-row landscape sheet. Columns: short reinforced module, tall reinforced module, existing basic-fence corner. Top row: front-left/front-left/outside. Bottom row: matching rear-right/rear-right/inside views.',
    checks=['Both reinforced forms retain blue metal straps and distinct heights.', 'Basic corner uses the existing approved cream-rope fence unchanged.', 'Outside/inside views show one coherent corner post and join, without overlapping logs.'])
add('improved_gatehouse', ['mid','style'],
    'Reconstruct the 18609 IMPROVED GATEHOUSE: two roofed timber towers with blue gabled roofs flank the central timber gate, on restrained stone bases. Preserve both tower silhouettes and the source-visible roof/flag/wood/metal arrangement. This is distinct from the earlier gate with simple posts. Show the coherent closed gate from opposing angles, then an interpreted open gate with a clear continuous walk-through. Keep gate leaves attached to readable supported hinges and keep towers/roofs fixed. Show join detail, without a drawbridge, hidden engine or numerical fortification claim.',
    labels=['TIMBER GATEHOUSE'], mode='single4', details=[('GATE OPEN','FRONT THREE-QUARTER OPEN STATE','Show the same gate leaves opening into clear space with an uninterrupted path.'),('HINGE / TOWER JOIN','CLOSE THREE-QUARTER','Show readable attached hinges, post/stone contact and tower-side structure.')],
    checks=['Both roofed flanking towers are present and stable across views.', 'Open leaves remain attached; the entrance is clear and physically coherent.'])
add('fish_hut', ['mid','style'],
    'Reconstruct FISH HUT OVER ICE from 18609 third row: a small raised timber fishing hut with blue roof, supported stilt/platform structure, safe-looking entry step/deck, and source-visible fishing/ice-access details. Preserve its elevated enclosing hut identity, distinct from a bare ice hole or standalone winch. Use only a small localized ice/snow base; show where the supports meet ice and where the fishing access opening sits. The open entry/interior is an interpreted view of the same hut, not a new fishing machine or catch-rate system.',
    labels=['FISH HUT OVER ICE'], mode='single4', details=[('OPEN ENTRY / ICE ACCESS','FRONT THREE-QUARTER WITH ENTRY OPEN','Show a clear entry and a readable fishing access location within the same footprint.'),('STILTS / ICE CONTACT','LOW REAR THREE-QUARTER','Show every support contacting the base and a coherent underside/deck.')],
    checks=['Raised supports and the localized ice access are visible, not buried under snow.', 'No floating hut or disconnected entry platform.'])
add('spike_barricade', ['original','style'],
    'Recreate the small unlabelled crossed timber stake cluster visible in 18600 row 3, between the torch and the ground tiles. Working label TIMBER BARRICADE. Keep the source squat radial/crossed arrangement of chunky timber points, dark stylized caps and cream rope lashings on a stable snow-dusted base. Treat it as a fantasy-game prop; preserve broad readable shapes. Do not create a large wall, explosive device, realistic fabrication blueprint or injury scene. The top and detail panels clarify the same arrangement, with no dimensions or construction steps.',
    labels=['TIMBER BARRICADE'], mode='single4', details=[('TOP','TOP','Show the fixed crossed/radial arrangement and compact footprint.'),('MATERIAL / LASHING DETAIL','CLOSE THREE-QUARTER','Show sculpted timber, capped tips and source-style rope material without a construction diagram.')])
add('late_furnaces', ['atlas','style'],
    'Render the LAST THREE furnace forms from the atlas top CAMP / FURNACE UPGRADE PROGRESSION strip, labelled in the source 51–70, 71–90, 91–100. Preserve their increasingly developed central hot furnace bodies, raised metal/stone bases, upper flame stacks, surrounding blue/bronze service forms and distinct overall silhouettes as actually pictured. Do not reuse one existing level-50 furnace with a changed number. Retain a clear source-like warm glow without engulfing the structure or obscuring its rear geometry. Interpret unseen rear plumbing conservatively, with physically attached runs and no new technical specification.',
    labels=['SOURCE RANGE 51–70','SOURCE RANGE 71–90','SOURCE RANGE 91–100'],
    checks=['All three actual atlas source ranges are represented; no invented individual levels.', 'Three source massing/silhouette changes remain readable in both angles.'])
add('fortress_walls', ['atlas','style'],
    'Use only the atlas WALLS column, top/middle/bottom examples, as three future wall concepts A/B/C. Preserve the light block-and-pier first form, the heavier developed stone/blue-accent middle form, and the darker metal-armored lower form with its visible warm metal fasteners/top accents. Reproduce their actual source panel silhouettes and end piers rather than inventing three new palisades. Show both the outside face and consistent supported rear in the opposing angle. No combat statistics, invented upgrade levels or expanded fortress scene.',
    labels=['ATLAS EXAMPLE A','ATLAS EXAMPLE B','ATLAS EXAMPLE C'])
add('fortress_gates', ['atlas','style'],
    'Render the three atlas GATE-column examples, top/middle/bottom, CLOSED, as future concepts A/B/C. Preserve the source stone/metal piers, arch/lintel shapes, visible grille or door panel, blue fittings and restrained warm highlights. They are separate from the timber midcamp gatehouse. Show each closed gate in opposing front-left and rear-right three-quarter views. Keep an identifiable fixed front/rear and make source-compatible panel attachment/support legible enough that an open-state interpretation can later retain the same design. No invented drawbridge, siege engine, hidden machinery or upgrade numbers.',
    suffix='fortress-gates-closed', title='FORTRESS GATES | CLOSED', labels=['ATLAS EXAMPLE A','ATLAS EXAMPLE B','ATLAS EXAMPLE C'],
    checks=['Closed gate identities and attached panels are stable and readable from both sides.', 'Approve this exact native sheet before generating the matching open-state sheet.'])
add('fortress_gates', ['atlas','style'],
    'Create the OPEN-STATE companion to the exact approved closed fortress-gate sheet that must be supplied as reference 3. Preserve all three source A/B/C gate identities, including piers, lintels, panel counts, materials, hardware and snow. Open only the existing panels in a visibly coherent supported arrangement, with a clear passage and no wall/leaf collision. Do not change a hinged leaf into a sliding grille or invent a new lifting machine; use the opening arrangement established by the approved closed design. Show each gate open from front-left and rear-right three-quarter views. These open states are explicitly interpreted static visual studies, not implemented mechanisms.',
    suffix='fortress-gates-open', title='FORTRESS GATES | OPEN STUDIES', labels=['ATLAS EXAMPLE A','ATLAS EXAMPLE B','ATLAS EXAMPLE C'],
    dependency='world-fortress-gates-closed', open_state=True,
    checks=['Every open gate remains byte-referenced to the approved closed source sheet at invocation.', 'Only panel state changes; fixed structure and gate identity remain the same.', 'Supported panels and unobstructed walk-through; no clipping or unexplained detached grille.'])
add('fortress_watchtowers', ['atlas','style'],
    'Render the three WATCH TOWER column forms in the atlas, top/middle/bottom, as future observation-tower examples A/B/C. Preserve their source stone/metal masses, platform/cap silhouettes, observation openings, ladders or entry details where visible, and blue/warm trim. Keep the observation role visually distinct from the separate archer and cannon columns; no newly mounted weapon or new guard character. Rear supports and access are restrained interpretations of the same tower, not a different second design.',
    labels=['ATLAS EXAMPLE A','ATLAS EXAMPLE B','ATLAS EXAMPLE C'])
add('archer_towers', ['atlas','style'],
    'Render the three ARCHER TOWER column forms in the atlas, top/middle/bottom, as future archer-tower examples A/B/C. Preserve the source raised stone/metal structure, upper guarded firing platform/openings, each distinct roof/parapet silhouette and visible torch accents. Keep them distinct from watch towers and the existing ballista tower. No mounted ballista, cannon, extra archers, arrows in flight or invented attack mechanism. Source-hidden rear access and supports must be coherent, modest interpretations.',
    labels=['ATLAS EXAMPLE A','ATLAS EXAMPLE B','ATLAS EXAMPLE C'])
add('cannon_towers', ['atlas','style'],
    'Render the three CANNON TOWER column forms in the atlas, top/middle/bottom, as future fantasy defensive-tower examples A/B/C. Follow the visible source tower bodies, chunky stylized barrel/turret forms where shown, upper ledges, blue metal and warm torch details. Preserve the actual source silhouette differences and the placement/count of visible source weapon-like shapes. No firing action, ammunition cross-section, explosive recipe, weapon internals or realistic mechanism diagram. Rear tower structure is interpreted consistently with the source front.',
    labels=['ATLAS EXAMPLE A','ATLAS EXAMPLE B','ATLAS EXAMPLE C'])
add('worker_huts', ['atlas','style'],
    'Render the atlas WORKER HUT column examples A/B/C from its top/middle/bottom rows. Preserve the rustic timber first hut, the reinforced gray/metal intermediate appearance, and the more developed blue/dark-metal lower appearance, with their distinct source roof/entry silhouettes. These are the worker-building appearances named separately from WORKSHOP. Do not merge in a workshop bench, new job station, worker character or employment/capacity mechanic. Keep source windows, chimneys and annexes fixed across opposing views.',
    labels=['ATLAS EXAMPLE A','ATLAS EXAMPLE B','ATLAS EXAMPLE C'])
add('atlas_storage', ['atlas','style'],
    'Render the three atlas STORAGE-column appearances, top/middle/bottom, as additional future visual ALTERNATIVES A/B/C. Preserve their flat/fortified upper silhouettes, compact enclosed bodies, source-visible loading doors, and large barrel annex on the same physical side through both views. Reproduce the timber/stone/armored distinctions from the source rows. Do not replace or restyle the already approved three-stage gable storehouse, and do not invent storage tiers, capacities or conveyor recipes. No duplicated barrel annex on the opposite side.',
    title='ATLAS STORAGE ALTERNATIVES', labels=['ATLAS ALTERNATIVE A','ATLAS ALTERNATIVE B','ATLAS ALTERNATIVE C'],
    checks=['These remain visibly separate alternatives to the approved gable storehouse.', 'Barrel annex side and body silhouette stay coherent across both views.'])
add('biome_vignettes', ['atlas','style'],
    'Create two compact future-region terrain vignettes from the atlas BIOME VARIANTS thumbnails: PINE FOREST and FROZEN LAKE. Forest: snow-covered pine groupings, a readable snowy floor and restrained natural rock variation matching the source atmosphere. Lake: a shallow-looking blue frozen-water/ice basin within snow banks and rocks, matching the source thumbnail palette. Render each as one bounded tabletop terrain chunk with clean supporting edges, then rotate the same chunk for the opposing view. Keep the silhouettes, tree/rock placements and shore contours fixed. No camp buildings, enemy camps, collectible placement, routes, UI markers or claim of a playable level.',
    suffix='biomes-forest-lake', title='PINE FOREST + FROZEN LAKE', variant_indexes=[0,1], labels=['PINE FOREST','FROZEN LAKE'],
    checks=['Forest and lake are distinct compact vignettes with fixed layouts through both angles.', 'Future concept status is explicit; no implied terrain asset completeness.'])
add('biome_vignettes', ['atlas','style'],
    'Create two compact future-region terrain vignettes from the atlas thumbnails: ICE CANYON and SNOW CLIFFS. Canyon: a narrow icy passage/channel between tall cold blue-gray rock/ice sides with snow caps, following the source thumbnail. Cliffs: a broader sheer stepped rock/snow escarpment and plateau, visibly distinct from the canyon. Use bounded tabletop terrain chunks with readable rear faces and consistent topography through opposing views. Preserve source-like stylized rock planes and selective snow; no invented cave network, traversal mechanic, route markers, buildings or playable-world claim.',
    suffix='biomes-canyon-cliffs', title='ICE CANYON + SNOW CLIFFS', variant_indexes=[2,3], labels=['ICE CANYON','SNOW CLIFFS'],
    checks=['The narrow canyon and open cliff escarpment remain different source concepts.', 'Rear/topography corresponds to the same terrain chunk, without mirrored random rock swaps.'])
add('biome_vignettes', ['atlas','style'],
    'Create the ABANDONED MINES future vignette from the atlas final biome thumbnail: a timber-framed dark mine entrance embedded in snow-covered blue-gray rock, with the source-like muted warm entrance structure and restrained abandoned exterior details. Keep it one compact bounded terrain-and-portal chunk. Opposing views show the same rock mass and structural supports; add an entrance close-up and an upper/rear structure view. Only the portal and a shallow dark threshold need be visible; do not invent a full underground level, new ore type, extraction machine, minecart system, loot rewards or quest.',
    suffix='biomes-mines', title='ABANDONED MINES', variant_indexes=[4], labels=['ABANDONED MINES'], mode='single4',
    details=[('MINE PORTAL','FRONT CLOSE THREE-QUARTER','Show the source-like entrance silhouette, timber support and shallow dark threshold.'),('ROCK / REAR STRUCTURE','HIGH REAR THREE-QUARTER','Show a coherent snow-capped rock mass and interpreted rear support structure.')],
    checks=['The vignette remains a portal concept, not an invented underground playable level.'])

assert len(drafts) == 33
assert len({row['id'] for row in drafts}) == 33
covered = {(row['family_id'], variant) for row in drafts for variant in row['source_variants']}
expected = {(family['id'], variant) for family in families.values() if family['id'] != 'defense_platform' for variant in family['source_variants_to_cover']}
assert covered == expected and len(expected) == 64
assert sum(row['draft_arguments'] is None for row in drafts) == 1
assert all(len(row['ordered_reference_inputs']) + bool(row.get('required_additional_reference')) <= 5 for row in drafts)
assert all(any(v['source_variant'] == variant and v['camera'] == 'FRONT-LEFT THREE-QUARTER' for v in row['required_views']) and
           any(v['source_variant'] == variant and v['camera'] == 'REAR-RIGHT THREE-QUARTER' for v in row['required_views'])
           for row in drafts for variant in row['source_variants'])

raw = MATRIX_PATH.read_bytes()
matrix_sha = hashlib.sha256(raw).hexdigest()
snapshot = ROOT / 'drafts/catalog-inputs' / ('world-gap-matrix--' + matrix_sha + '.json')
snapshot.parent.mkdir(parents=True, exist_ok=True)
assert not snapshot.exists() or snapshot.read_bytes() == raw
if not snapshot.exists():
    shutil.copyfile(MATRIX_PATH, snapshot)
catalog = {
    'schema_version': 1, 'status': 'DRAFT_FOR_ROOT_REVIEW_NOT_INVOKED', 'author_agent': '/root/missing_archive',
    'task_date': '2026-11-27', 'source_matrix': {'path': str(MATRIX_PATH), 'snapshot_path': str(snapshot), 'sha256': matrix_sha, 'schema_version': matrix['schema_version']},
    'scope': 'Thirty-source-family census planning. Two defense sheets are already produced separately. This catalog plans thirty-three additional world sheets covering the other sixty-four depicted source forms plus the existing basic-fence corner detail.',
    'counts': {'census_families': 30, 'census_depicted_forms': 65, 'existing_defense_family_excluded': 1,
               'planned_additional_world_sheets': len(drafts), 'planned_non_defense_families': len({r['family_id'] for r in drafts}),
               'unique_non_defense_source_forms_covered': len(covered), 'planned_view_panels': sum(len(r['required_views']) for r in drafts),
               'independent_sheets_after_root_review': 32, 'dependency_blocked_sheets': 1},
    'generation_boundary': 'No image generation invoked by this catalog builder; no final requirements edits. Root must review prompt and exact ordered inputs, then save the actual invocation independently.',
    'interpretation_policy': 'Observed source-facing identity remains authoritative. Rear faces, interiors, terrain back faces and open states are explicitly interpreted concept art. Atlas examples A/B/C are source-row labels, not invented numeric tiers. Only printed late-furnace source ranges carry their source numbers.',
    'existing_approval_boundary': 'Earlier selected assets and the three-stage general storehouse remain intact. Future atlas alternatives are additive visual concepts, not failed replacements or runtime activation.',
    'render_quality_gate': 'Separate critic must inspect actual whole sheets and relevant native close-ups. Target 10, minimum selected-art score 9.5 with every mandatory check passed; missing or untested evidence blocks selection.',
    'source_bindings': sources,
    'coverage_check': {'all_64_non_defense_forms_have_opposing_views': True, 'uncovered': [], 'unexpected_families': [],
                       'supplemental_existing_identity_detail': 'basic_palisade_corner_join',
                       'fortress_gate_open_state_repeats_same_three_forms': True},
    'sheets': drafts,
}
target = ROOT / 'world-render-catalog.json'
assert not target.exists(), 'Root must review the first draft before any replacement'
target.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'path': str(target), 'status': catalog['status'], 'counts': catalog['counts'], 'source_matrix_sha256': matrix_sha}, indent=2))
