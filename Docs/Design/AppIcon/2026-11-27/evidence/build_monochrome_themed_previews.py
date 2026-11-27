#!/usr/bin/env python3
"""Android themed-icon alpha tint simulation; delivered art is never altered."""
from pathlib import Path
import hashlib,json,shlex,subprocess

PACKAGE=Path(__file__).resolve().parent.parent
OUT=PACKAGE/'evidence/monochrome-r1'
ASSET=PACKAGE/'assets/havenline-monochrome-432.png'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
COMMANDS=[]
def run(cmd):
    cmd=[str(x) for x in cmd]
    COMMANDS.append(shlex.join(cmd))
    subprocess.run(cmd,check=True,capture_output=True)
def identity(p):
    b=p.read_bytes()
    return {'path':str(p.relative_to(PACKAGE)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
before=identity(ASSET)
alpha=OUT/'previews/themed-alpha-432.png'
run(['magick',ASSET,'-alpha','extract',alpha])
themes=[('dark','#b9cdf9','#1b2946','#131b2d','#f7f5ec'),('warm','#49341b','#ead6af','#f6f0e6','#15203b')]
for theme,ink,bg,sheet_bg,label in themes:
    tinted=OUT/'previews'/f'themed-{theme}-layer-432.png'
    run(['magick','-size','432x432',f'xc:{ink}',alpha,'-alpha','off','-compose','CopyOpacity','-composite',tinted])
    composite=OUT/f'themed-{theme}-composite-432.png'
    run(['magick','-size','432x432',f'xc:{bg}',tinted,'-compose','Over','-composite',composite])
    viewport=OUT/'previews'/f'themed-{theme}-viewport-288.png'
    run(['magick',composite,'-crop','288x288+72+72','+repage',viewport])
    for shape in ['circle','squircle']:
        masked=OUT/'previews'/f'themed-{theme}-{shape}-288.png'
        run(['magick',viewport,OUT/'previews'/f'{shape}-288-mask.png','-alpha','off','-compose','CopyOpacity','-composite',masked])
        for size in [96,64,48,32]:
            run(['magick',masked,'-filter','Lanczos','-resize',f'{size}x{size}!',OUT/'previews'/f'themed-{theme}-{shape}-{size}.png'])
    cmd=['magick','-size','700x620',f'xc:{sheet_bg}','-font',FONT,'-fill',label,
         '-pointsize','21','-annotate','+24+32',f'Monochrome candidate: {theme} theme',
         '-pointsize','13','-annotate','+24+58','432px / 108dp layers; central 288px / 72dp visible viewport.',
         '-pointsize','13','-annotate','+24+80','Preview tint uses delivered alpha; original export remains unchanged.',
         '-pointsize','16','-annotate','+265+114','Circle','-annotate','+460+114','Squircle']
    for size,yy in [(96,185),(64,330),(48,445),(32,540)]:
        cmd+=['-pointsize','16','-annotate',f'+24+{yy+6}',f'{size}px']
        for shape,xx in [('circle',290),('squircle',490)]:
            cmd += [OUT/'previews'/f'themed-{theme}-{shape}-{size}.png','-geometry',f'+{xx-size//2}+{yy-size//2}','-compose','Over','-composite']
    cmd += [OUT/f'native-themed-{theme}.png']
    run(cmd)
assert before==identity(ASSET)
(OUT/'themed-commands.txt').write_text('\n'.join(COMMANDS)+'\n')
(OUT/'themed-preview-metrics.json').write_text(json.dumps({'scope':'Unselected optional monochrome candidate review; alpha tint simulations only','asset':before,'asset_unchanged':True,'themes':themes,'outputs':[identity(p) for p in sorted(OUT.rglob('*themed*.png'))],'device_run':False},indent=2)+'\n')
print('Generated two actual-size themed preview sheets without changing source/export art.')
