#!/usr/bin/env python3
"""Build Havenline's 15-sheet static-art pack from exact reviewed PNG files.

No source raster is cropped, retouched, recompressed or overwritten. The PDF
places each original in full; the ZIP carries byte-identical originals.
Run freeze only after the root owner confirms final static selections.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

RES = 'Docs/Design/ResourceTurnarounds/2026-11-27-industrial/selected'
MAC = 'Docs/Design/ProcessingMachines/2026-11-27/selected'
RESOURCE_MANIFEST = 'Docs/Design/ResourceTurnarounds/2026-11-27-completion/RESOURCE_SELECTED_MANIFEST.json'
CHAIN = 'Docs/Production/VehicleEconomy/2026-11-27/RESOURCE_CHAINS.json'
PDF_NAME = 'Havenline_Resources_and_Processing_Machines.pdf'
ZIP_NAME = 'Havenline_Resource_Machine_Render_Pack.zip'

RESOURCE_ROWS = [
    ('iron_bars', 'iron-bars', 'Iron bars', 'Ore and coal become bars for metalworking, steel production and machine frames.'),
    ('sheet_metal', 'sheet-metal', 'Sheet metal', 'Formed from iron bars for vehicle panels, garage doors and machinery casings.'),
    ('mechanical_parts', 'mechanical-parts', 'Mechanical parts', 'Shared parts stock for pumps, shutters, refining and vehicle assemblies.'),
    ('drive_assembly', 'drive-assembly', 'Drive assembly', 'A complete drive unit built from steel, mechanical parts and sheet metal.'),
    ('traction_kit', 'mobility-assembly', 'Mobility assembly', 'A mobility module built from steel, mechanical parts and planks.'),
    ('crude_oil', 'crude-oil', 'Crude oil', 'Collected by the manual outside-camp pump, then processed into fuel.'),
    ('blocks', 'stone-blocks', 'Stone blocks', 'Processed stone for foundations, defense bases, docks and equipment supports.'),
    ('premium_gems', 'gems', 'Gems', 'Optional currency. Gems are not a mined industrial product or factory output.'),
    ('relay_component', 'relay-component', 'Relay component', 'A finite project object for the final relay connection; no factory recipe is selected.'),
]
MACHINE_ROWS = [
    ('coal_smelter', '01-coal-smelter', 'Iron smelter', 'Iron ore + coal -> iron bars. Separate ore, coal and finished-bar interfaces.'),
    ('hand_metal_bench', '02-metalworking-bench', 'Metalworking bench', 'Iron bars -> sheet metal OR mechanical parts. Two recipes share one producer.'),
    ('steel_forge', '03-steel-forge', 'Steel forge', 'Iron bars + coal -> steel. This is a separate producer from the central camp hearth.'),
    ('assembly_bench', '04-assembly-bench', 'Assembly bench', 'Makes drive and mobility assemblies using distinct combinations of existing processed goods.'),
    ('manual_oil_pump', '05-manual-oil-pump', 'Manual oil pump', 'A reachable outside-camp crude deposit -> crude oil. No engine fuel is required.'),
    ('coal_refinery', '06-coal-refinery', 'Fuel refinery', 'Crude oil + coal -> fuel. The first fuel can be made without owning a fueled vehicle.'),
]
EXPECTED = [
    {'id': rid, 'stem': stem, 'title': title, 'caption': caption,
     'category': category, 'source_path': f'{base}/{stem}.png',
     'pack_path': f'{category}/{stem}.png'}
    for category, base, rows in [('resources', RES, RESOURCE_ROWS), ('machines', MAC, MACHINE_ROWS)]
    for rid, stem, title, caption in rows
]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

def inspect_sources(repo: Path) -> list[dict]:
    missing = [x['source_path'] for x in EXPECTED if not (repo / x['source_path']).is_file()]
    if missing:
        raise ValueError(f'Final export blocked: {len(missing)} of 15 selected sheets missing: ' + ', '.join(missing))
    rm = json.loads((repo / RESOURCE_MANIFEST).read_text())
    approved_resources = {x['selected']['path']: x for x in rm['resources']}
    if len(approved_resources) != 9:
        raise ValueError('Expected exactly nine resource selections in the retained resource manifest')
    result = []
    for row in EXPECTED:
        path = repo / row['source_path']
        digest = sha(path)
        with Image.open(path) as im:
            if im.format != 'PNG':
                raise ValueError(f'Expected an original PNG: {path}')
            dimensions = list(im.size)
            im.verify()
        if row['category'] == 'resources':
            existing = approved_resources[row['source_path']]
            if digest != existing['selected']['sha256']:
                raise ValueError(f'Resource selected hash changed: {row["id"]}')
            review = existing['fresh_review']
            if review['verdict'] != 'PASS_SCOPED_RASTER_CONCEPT' or not review['all_recorded_checks_passed']:
                raise ValueError(f'Resource does not have the retained scoped pass: {row["id"]}')
        result.append({**row, 'sha256': digest, 'bytes': path.stat().st_size,
                       'dimensions': dimensions, 'illustrated_views': 8})
    return result

def freeze(repo: Path, dest: Path, review_records: list[Path]) -> dict:
    assets = inspect_sources(repo)
    if not review_records:
        raise ValueError('Supply final machine review record(s); root must confirm their final selection before freezing')
    records = []
    for p in review_records:
        if not p.is_file():
            raise ValueError(f'Missing review record: {p}')
        try:
            rel = p.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError as e:
            raise ValueError('Review records must be retained in the source repository before final export') from e
        records.append({'source_path': rel, 'sha256': sha(p), 'bytes': p.stat().st_size})
    manifest = {
        'schema_version': 1,
        'scope': 'Selected static illustrated concept sheets; no native model, animation or runtime approval.',
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'selection_authority': 'Root final-selection notice; exporter does not independently judge visual approval.',
        'counts': {'resource_sheets': 9, 'machine_sheets': 6, 'total_sheets': 15, 'illustrated_views': 120},
        'assets': assets,
        'source_recipe_graph': {'source_path': CHAIN, 'sha256': sha(repo / CHAIN)},
        'source_resource_manifest': {'source_path': RESOURCE_MANIFEST, 'sha256': sha(repo / RESOURCE_MANIFEST)},
        'machine_review_records': records,
    }
    write_json(dest, manifest)
    return manifest

def validate_selection(repo: Path, selection: Path) -> dict:
    data = json.loads(selection.read_text())
    current = inspect_sources(repo)
    if len(data.get('assets', [])) != 15:
        raise ValueError('Final manifest must contain exactly 15 sheets')
    if [x['id'] for x in data['assets']] != [x['id'] for x in EXPECTED]:
        raise ValueError('Final manifest has a missing, duplicated, reordered or unknown sheet')
    for frozen, live in zip(data['assets'], current):
        for key in ['id', 'source_path', 'pack_path', 'sha256', 'bytes', 'dimensions']:
            if frozen[key] != live[key]:
                raise ValueError(f'Final selected input changed: {frozen["id"]} / {key}')
    evidence = data.get('machine_review_records', [])
    if not evidence:
        raise ValueError('Final machine review records are missing')
    for row in evidence + [data['source_recipe_graph'], data['source_resource_manifest']]:
        if sha(repo / row['source_path']) != row['sha256']:
            raise ValueError(f'Frozen evidence changed: {row["source_path"]}')
    return data

NAVY = HexColor('#081C2C')
PANEL = HexColor('#102B40')
WHITE = HexColor('#F6F8FB')
MUTED = HexColor('#B8CCD9')
BLUE = HexColor('#6AC5FF')
ORANGE = HexColor('#F8A443')
PAGE_W, PAGE_H = 864, 648

def fonts() -> None:
    root = Path('/usr/share/fonts/truetype/dejavu')
    pdfmetrics.registerFont(TTFont('HL', str(root / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('HLBold', str(root / 'DejaVuSans-Bold.ttf')))

def text(c: canvas.Canvas, value: str, x: float, y: float, size=11, color=WHITE, bold=False) -> None:
    c.setFillColor(color)
    c.setFont('HLBold' if bold else 'HL', size)
    c.drawString(x, y, value)

def paragraph(c: canvas.Canvas, value: str, x: float, top: float, width: float,
              size=11, color=MUTED, leading=None, bold=False) -> float:
    style = ParagraphStyle('p', fontName='HLBold' if bold else 'HL', fontSize=size,
                           leading=leading or size * 1.42, textColor=color)
    p = Paragraph(value, style)
    _, height = p.wrap(width, PAGE_H)
    p.drawOn(c, x, top - height)
    return height

def background(c: canvas.Canvas, page: int, label: str) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setStrokeColor(HexColor('#26475F'))
    c.setLineWidth(0.6)
    c.line(36, 27, 828, 27)
    text(c, 'HAVENLINE  /  STATIC CONCEPT COLLECTION', 36, 14, 7.5, MUTED)
    c.setFont('HL', 7.5)
    c.drawRightString(828, 14, f'{label}   {page:02d} / 18')

def fit_image(c: canvas.Canvas, path: Path, x: float, y: float, width: float, height: float) -> None:
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(width / iw, height / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(str(path), x + (width - dw) / 2, y + (height - dh) / 2,
                width=dw, height=dh, preserveAspectRatio=True, mask='auto')

def build_pdf(repo: Path, assets: list[dict], dest: Path) -> None:
    fonts()
    c = canvas.Canvas(str(dest), pagesize=(PAGE_W, PAGE_H), pageCompression=1, invariant=1)
    c.setTitle('Havenline - Resources and Processing Machines')
    c.setAuthor('Havenline visual development')
    c.setSubject('15 selected static concept sheets, production routes and review scope')
    background(c, 1, 'COLLECTION')
    text(c, 'VISUAL DEVELOPMENT  /  27 NOV 2026', 52, 611, 10, BLUE, True)
    text(c, 'HAVENLINE', 52, 552, 43, WHITE, True)
    text(c, 'Resources &', 52, 502, 36, WHITE, True)
    text(c, 'Processing Machines', 52, 458, 36, WHITE, True)
    c.setStrokeColor(ORANGE)
    c.setLineWidth(3)
    c.line(52, 434, 226, 434)
    paragraph(c, 'The selected industrial resources and the machines that turn them into useful goods.',
              52, 414, 735, 14, MUTED, 20)
    text(c, '09  RESOURCE SHEETS', 52, 348, 15, BLUE, True)
    text(c, '06  MACHINE SHEETS', 454, 348, 15, ORANGE, True)
    fit_image(c, repo / assets[0]['source_path'], 52, 91, 356, 237)
    fit_image(c, repo / assets[-1]['source_path'], 454, 91, 356, 237)
    text(c, '15 original sheets  /  120 illustrated directions', 52, 61, 11, WHITE, True)
    text(c, 'Static concept artwork. Native models and animation are separate implementation work.', 52, 42, 9, MUTED)
    c.showPage()

    for index, row in enumerate(assets, start=2):
        label = 'RESOURCES' if row['category'] == 'resources' else 'MACHINES'
        background(c, index, label)
        text(c, row['title'], 36, 616, 20, WHITE, True)
        text(c, f'{label}  /  EIGHT ILLUSTRATED VIEWS  /  ORIGINAL FULL SHEET', 36, 596, 8.5, BLUE)
        fit_image(c, repo / row['source_path'], 36, 55, 792, 528)
        paragraph(c, html.escape(row['caption']), 36, 47, 792, 8.3, MUTED, 10)
        c.showPage()

    background(c, 17, 'PRODUCTION ROUTES')
    text(c, 'How the materials connect', 36, 605, 26, WHITE, True)
    paragraph(c, 'Existing food and construction lines continue alongside the six new industrial producers.',
              36, 583, 780, 11, MUTED)
    rows = [
        ('Wood', 'Saw bench', 'Planks'),
        ('Stone', 'Quarry drill', 'Stone blocks'),
        ('Iron ore + coal', 'Iron smelter', 'Iron bars'),
        ('Iron bars', 'Metalworking bench', 'Sheet metal OR mechanical parts'),
        ('Iron bars + coal', 'Steel forge', 'Steel'),
        ('Steel + parts + sheet metal', 'Assembly bench', 'Drive assembly'),
        ('Steel + parts + planks', 'Assembly bench', 'Mobility assembly'),
        ('Reachable crude deposit', 'Manual oil pump', 'Crude oil'),
        ('Crude oil + coal', 'Fuel refinery', 'Fuel'),
        ('Meat', 'Camp cooker', 'Meal'),
        ('Whole fish', 'Fish-processing line', 'Cooked fish'),
        ('Wheat', 'Wheat food processor', 'Bread'),
    ]
    xs = [36, 322, 565]
    widths = [270, 227, 263]
    top = 544
    c.setFillColor(HexColor('#16374F'))
    c.roundRect(36, top - 29, 792, 29, 5, fill=1, stroke=0)
    for x, label in zip(xs, ['INPUT', 'PRODUCER', 'OUTPUT']):
        text(c, label, x + 12, top - 19, 9, BLUE, True)
    y = top - 29
    for i, row in enumerate(rows):
        bottom = y - 32
        c.setFillColor(PANEL if i % 2 == 0 else NAVY)
        c.rect(36, bottom, 792, 32, fill=1, stroke=0)
        for x, width, value in zip(xs, widths, row):
            paragraph(c, html.escape(value), x + 12, y - 8, width - 12, 10, WHITE, 12)
        y = bottom
    paragraph(c, 'Gems are optional currency. Relay components are finite project objects. Neither has a selected factory recipe.',
              36, y - 13, 792, 10, BLUE, 14)
    paragraph(c, 'No engine fuel is needed to build or operate the first material-processing chain. Recipe quantities remain unbalanced design fixtures; the original JSON is included in the download pack.',
              36, 87, 792, 9, MUTED, 13)
    text(c, 'SOURCE  VehicleEconomy/2026-11-27/RESOURCE_CHAINS.json + the selected whole-game resource map', 36, 40, 7.5, MUTED)
    c.showPage()

    background(c, 18, 'SCOPE & CUSTODY')
    text(c, 'What this collection establishes', 36, 605, 26, WHITE, True)
    paragraph(c, 'A complete selected static reference set for this industrial expansion.', 36, 581, 792, 12, BLUE)
    sections = [
        ('THE DELIVERABLE', 'Nine resource sheets and six machine sheets, each with eight illustrated directions. Every art page contains its original full sheet without cropping. The PNG download pack preserves the original bytes and dimensions.'),
        ('THE REVIEW BOUNDARY', 'The independent reviews cover the selected static designs, view coverage, defining landmarks, style and resource interfaces. Generated views are illustrations; they do not establish a shared 3D mesh, working mechanism or complete animation cycle.'),
        ('THE GAMEPLAY BOUNDARY', 'The machine roles follow the existing selected resource graph. This pack does not implement plots, recipes, resource consumption, saved transactions, collisions, destruction, rebuilding, conveyor behavior or device performance. Exact production amounts and timing still require playtests.'),
        ('EXISTING WORK IS RETAINED', 'The original wood, stone, ore, coal, steel, fuel, plank and food references continue to apply. Existing cooker, saw, quarry, wheat, storage and conveyor designs are preserved. Their historical reviews remain separate from these selected sheets.'),
        ('USING THE DOWNLOAD PACK', 'Open index.html after extracting the ZIP. Resources and machines have separate folders. selected-manifest.json binds every original PNG to its SHA-256 hash; proofs retain the selected review records and source recipe graph.'),
    ]
    y = 536
    for heading, body in sections:
        text(c, heading, 36, y, 10, ORANGE, True)
        h = paragraph(c, body, 36, y - 11, 792, 11, WHITE, 16)
        y -= h + 42
    text(c, 'Repository: ksolo21-web/HAVENLINE', 36, 47, 10, BLUE)
    c.save()

def make_readme(assets: list[dict]) -> str:
    resources = '\n'.join(f'- {r["title"]}: {r["caption"]}' for r in assets if r['category'] == 'resources')
    machines = '\n'.join(f'- {r["title"]}: {r["caption"]}' for r in assets if r['category'] == 'machines')
    return f'''# Havenline - resource and processing-machine render pack

15 original PNG sheets / 120 illustrated directions.

Open `index.html` after extracting this ZIP. The artbook PDF is delivered separately to keep this archive compact.

## Resources

{resources}

## Processing machines

{machines}

## Exact production graph

`proofs/RESOURCE_CHAINS.json` preserves the selected source recipe graph and build fixtures. Numerical recipes are unbalanced design fixtures, not final prices or physical quantities. The saved ore identifier remains `metal`; mobility assembly remains `traction_kit`.

The existing wood/plank, stone/block, meat/meal, fish/cooked-fish and wheat/bread routes remain. Existing food and equipment references were not replaced by this collection. The metalworking and assembly benches each support two recipes. Crude extraction is outside camp and manually reachable; the first fuel chain requires no engine fuel.

## Scope

These are selected static concept illustrations. The illustrated directions do not establish a shared native 3D model, rig, animation cycle, working recipe, game integration or device performance. All original PNGs are included without cropping, image editing or recompression. Gems are optional currency; relay components are finite project objects. No additional factory recipe is inferred for either.

## Custody

`selected-manifest.json` records the exact source paths, sizes, dimensions and SHA-256 hashes. `proofs/` retains source recipe and selected-review records. The source repository retains rejected attempts, prompts and detailed review history outside this compact pack.
'''

def make_html(assets: list[dict]) -> str:
    cards = []
    for row in assets:
        cards.append(f'''<article id="{html.escape(row['id'])}"><div class="cardhead"><span>{html.escape(row['category'])}</span><h2>{html.escape(row['title'])}</h2></div><a href="{html.escape(row['pack_path'])}"><img loading="lazy" src="{html.escape(row['pack_path'])}" alt="{html.escape(row['title'])}: original full eight-view Havenline concept sheet"></a><p>{html.escape(row['caption'])}</p><a class="download" href="{html.escape(row['pack_path'])}" download>Open original PNG</a></article>''')
    nav = ''.join(f'<a href="#{html.escape(x["id"])}">{html.escape(x["title"])}</a>' for x in assets)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Havenline - Resources and Processing Machines</title><style>
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#081c2c;color:#f6f8fb;font-family:system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.5}header,main,footer{max-width:1400px;margin:auto;padding:clamp(20px,4vw,52px)}header{padding-bottom:24px}.eyebrow{color:#6ac5ff;letter-spacing:.16em;font-size:.78rem;font-weight:800}h1{font-size:clamp(2rem,4.8vw,4.2rem);line-height:1.06;max-width:950px;margin:.35em 0}header p{color:#b8ccd9;max-width:900px}nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:24px}nav a{background:#102b40;color:#b8ccd9;border:1px solid #28485f;border-radius:100px;padding:7px 13px;text-decoration:none;font-size:.85rem}nav a:hover,nav a:focus{color:white;border-color:#6ac5ff}main{padding-top:0}article{margin:0 0 36px;border:1px solid #26475f;border-radius:14px;overflow:hidden;background:#102b40;scroll-margin-top:20px}.cardhead{padding:20px 24px 12px}.cardhead span{text-transform:uppercase;font-size:.7rem;letter-spacing:.17em;color:#6ac5ff;font-weight:800}h2{margin:.1em 0;font-size:1.5rem}img{display:block;width:100%;height:auto}article p{margin:20px 24px 10px;color:#c4d5e0}a.download{display:inline-block;margin:0 24px 24px;color:#f8a443}footer{padding-top:0;color:#b8ccd9;font-size:.9rem}footer a{color:#6ac5ff}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
    </style></head><body><header><div class="eyebrow">HAVENLINE / VISUAL DEVELOPMENT</div><h1>Resources &amp;<br>Processing Machines</h1><p>15 original sheets. 120 illustrated directions. The selected industrial resources and their processing machines, with every original image preserved in full.</p><p>Static concepts only. Native models, animation and gameplay integration remain separate implementation work.</p><nav aria-label="Sheet navigation">''' + nav + '</nav></header><main>' + ''.join(cards) + '''</main><footer><p>Recipe numbers in the source graph remain unbalanced design fixtures. Existing food, timber, stone and logistics references are preserved. Gems are optional currency; relay components are finite project objects.</p><p><a href="README.md">Read the collection notes</a> &nbsp; <a href="selected-manifest.json">Inspect the exact-file manifest</a></p></footer></body></html>'''

def build(repo: Path, selection: Path, output: Path) -> dict:
    data = validate_selection(repo, selection)
    output.mkdir(parents=True, exist_ok=True)
    pack = output / 'Havenline_Render_Pack'
    if pack.exists():
        raise ValueError('Pack directory already exists; use a new output directory to preserve previous artifacts')
    pack.mkdir()
    for row in data['assets']:
        dest = pack / row['pack_path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / row['source_path'], dest)
        if sha(dest) != row['sha256']:
            raise ValueError(f'Copied source mismatch: {row["id"]}')
    shutil.copyfile(selection, pack / 'selected-manifest.json')
    proofs = pack / 'proofs'
    proofs.mkdir()
    shutil.copyfile(repo / CHAIN, proofs / 'RESOURCE_CHAINS.json')
    shutil.copyfile(repo / RESOURCE_MANIFEST, proofs / 'RESOURCE_SELECTED_MANIFEST.json')
    for i, row in enumerate(data['machine_review_records'], start=1):
        p = repo / row['source_path']
        shutil.copyfile(p, proofs / f'machine-review-{i:02d}-{p.name}')
    resource_manifest = json.loads((repo / RESOURCE_MANIFEST).read_text())
    source_review = repo / resource_manifest['resources'][0]['fresh_review']['path']
    if sha(source_review) != resource_manifest['resources'][0]['fresh_review']['sha256']:
        raise ValueError('Retained resource review hash changed')
    shutil.copyfile(source_review, proofs / 'RESOURCE_SELECTED_FRESH_REVIEW.json')
    (pack / 'README.md').write_text(make_readme(data['assets']))
    (pack / 'index.html').write_text(make_html(data['assets']))
    pdf = output / PDF_NAME
    build_pdf(repo, data['assets'], pdf)
    zip_path = output / ZIP_NAME
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(pack.rglob('*')):
            if p.is_file():
                z.write(p, (Path(pack.name) / p.relative_to(pack)).as_posix())
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP CRC validation failed')
        for row in data['assets']:
            raw = z.read(f'{pack.name}/{row["pack_path"]}')
            if hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError(f'ZIP image bytes mismatch: {row["id"]}')
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    if len(reader.pages) != 18:
        raise ValueError(f'Unexpected PDF page count: {len(reader.pages)}')
    for i, row in enumerate(data['assets'], start=1):
        if row['title'] not in (reader.pages[i].extract_text() or ''):
            raise ValueError(f'Missing PDF sheet heading: {row["title"]}')
    result = {
        'status': 'BUILT_REQUIRES_RENDERED_LAYOUT_INSPECTION',
        'pdf': {'path': str(pdf), 'bytes': pdf.stat().st_size, 'sha256': sha(pdf), 'pages': 18},
        'zip': {'path': str(zip_path), 'bytes': zip_path.stat().st_size, 'sha256': sha(zip_path)},
        'selection_sha256': sha(selection),
        'checks': {'all_15_original_png_hashes_preserved': True, 'all_15_zip_png_hashes_preserved': True,
                   'zip_crc_valid': True, 'pdf_pages_18': True, 'all_15_pdf_sheet_headings_present': True},
        'visual_layout_review': 'PENDING',
    }
    write_json(output / 'BUILD_VALIDATION.json', result)
    return result

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['preflight', 'freeze', 'build'])
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--selection', type=Path)
    p.add_argument('--review-record', type=Path, action='append', default=[])
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        if args.action == 'preflight':
            assets = inspect_sources(args.repo)
            result = {'status': 'INPUTS_PRESENT_NOT_EXPORT_APPROVAL', 'selected_sheets': len(assets)}
        elif args.action == 'freeze':
            if not args.selection:
                raise ValueError('--selection is required')
            result = freeze(args.repo, args.selection, args.review_record)
            result = {'status': 'FROZEN_FOR_EXPORT', 'selection': str(args.selection), 'assets': len(result['assets'])}
        else:
            if not args.selection or not args.output:
                raise ValueError('--selection and --output are required')
            result = build(args.repo, args.selection, args.output)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, FileNotFoundError) as e:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(e)}, indent=2))
        return 2

if __name__ == '__main__':
    sys.exit(main())
