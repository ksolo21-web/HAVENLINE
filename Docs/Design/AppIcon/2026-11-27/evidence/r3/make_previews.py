#!/usr/bin/env python3
"""Mechanical launch-size/mask evidence. Creative source pixels are never changed.

ImageMagick supplies only resize, alpha masking, background composition and
evidence labels. This script is not a source-art editor or an icon generator.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import shlex

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent.parent
SOURCES = {
    'previous': PACKAGE / 'sources/previous-field-icon.png',
    'named-r3': PACKAGE / 'sources/named-r3.png',
}
PREVIEWS = HERE / 'previews'
PREVIEWS.mkdir(exist_ok=True)
COMMANDS = []

def run(args):
    args = [str(a) for a in args]
    COMMANDS.append(shlex.join(args))
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

def digest(path):
    b = path.read_bytes()
    return {'path': str(path.relative_to(PACKAGE)), 'bytes': len(b),
            'sha256': hashlib.sha256(b).hexdigest()}

source_before = {k: digest(p) for k,p in SOURCES.items()}
fonts = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
for size in (32, 48, 64, 96, 256):
    for shape in ('circle', 'squircle'):
        mask = PREVIEWS / f'mask-{shape}-{size}.png'
        # Pixel-center superellipse equation; n=2 circle, n=4 squircle.
        power = 2 if shape == 'circle' else 4
        expression = f'pow(abs((i+0.5-{size}/2)/({size}/2)),{power})+pow(abs((j+0.5-{size}/2)/({size}/2)),{power})<=1?1:0'
        run(['magick', '-size', f'{size}x{size}', 'xc:black', '-fx', expression, mask])
    for name, source in SOURCES.items():
        square = PREVIEWS / f'{name}-square-{size}.png'
        run(['magick', source, '-filter', 'Lanczos', '-resize', f'{size}x{size}!', square])
        for shape in ('circle', 'squircle'):
            run(['magick', square, PREVIEWS/f'mask-{shape}-{size}.png',
                 '-alpha','off','-compose','CopyOpacity','-composite',
                 PREVIEWS/f'{name}-{shape}-{size}.png'])

for theme, background, text_color in [('dark','#131b2d','#f7f5ec'),('light','#edf0f5','#15203b')]:
    canvas = HERE / f'native-sizes-{theme}.png'
    args = ['magick','-size','1000x710',f'xc:{background}','-font',fonts,'-fill',text_color,
            '-pointsize','22','-annotate','+24+34','Havenline icon: actual pixel sizes',
            '-pointsize','14','-annotate','+24+59','No source-art edits. Circle and squircle are launcher-mask simulations.']
    columns = [('previous','square'),('previous','circle'),('previous','squircle'),
               ('named-r3','square'),('named-r3','circle'),('named-r3','squircle')]
    xs = [150,300,450,600,750,900]
    for x,(name,shape) in zip(xs,columns):
        label = ('OLD' if name=='previous' else 'NAMED R3') + ' / ' + shape
        args += ['-pointsize','11','-annotate',f'+{x-63}+91',label]
    rows = [(96,180),(64,340),(48,480),(32,600)]
    for size,y in rows:
        args += ['-pointsize','16','-annotate',f'+24+{y+6}',f'{size}px']
        for x,(name,shape) in zip(xs,columns):
            args += [PREVIEWS/f'{name}-{shape}-{size}.png','-geometry',f'+{x-size//2}+{y-size//2}',
                     '-compose','Over','-composite']
    args += ['-pointsize','13','-annotate','+24+674',
             'Inspect at 100% display zoom. Smaller rows are intentionally shown without enlargement.',canvas]
    run(args)

canvas = HERE / 'named-r3-mask-detail.png'
args = ['magick','-size','900x380','xc:#eceff5','-font',fonts,'-fill','#15203b',
        '-pointsize','20','-annotate','+24+30','Named R3: 256px launcher-shape comparison']
for x,shape in [(20,'square'),(322,'circle'),(624,'squircle')]:
    args += ['-pointsize','16','-annotate',f'+{x}+60',shape,
             PREVIEWS/f'named-r3-{shape}-256.png','-geometry',f'+{x}+80','-compose','Over','-composite']
args += ['-pointsize','12','-annotate','+24+367','The title and furnace are unchanged source art. Only launcher masks are simulated.',canvas]
run(args)

source_after = {k: digest(p) for k,p in SOURCES.items()}
assert source_before == source_after, 'Source images changed during mechanical preview generation'
identity = {
    'scope': 'Mechanical evidence generation, not independent acceptance',
    'source_images_unchanged': True,
    'sources': source_before,
    'source_metadata': {k:run(['magick','identify','-format','%wx%h %[channels] %[opaque]',p]).strip() for k,p in SOURCES.items()},
    'sizes_native_pixels': [96,64,48,32],
    'mask_shapes': {'circle':'superellipse exponent2', 'squircle':'superellipse exponent4'},
    'mask_note': 'Representative masks only; no actual Android launcher/device run.',
    'outputs': [digest(p) for p in sorted(HERE.rglob('*.png'))],
    'image_magick': run(['magick','-version']).splitlines()[0],
}
(HERE/'preview-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
(HERE/'commands.txt').write_text('\n'.join(COMMANDS)+'\n')
print(json.dumps({'sources_unchanged':True,'outputs':len(identity['outputs']),'sheets':[
    str(HERE/'native-sizes-dark.png'),str(HERE/'native-sizes-light.png'),str(canvas)]}))
