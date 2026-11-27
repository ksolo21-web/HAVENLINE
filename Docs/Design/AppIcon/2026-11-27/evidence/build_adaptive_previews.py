#!/usr/bin/env python3
"""Mechanical platform scaling/padding and launcher-view evidence only.

Pillow/NumPy read pixel values for measurement; only ImageMagick writes
images. No color, transparency threshold or creative geometry is edited.
"""
from pathlib import Path
import hashlib,json,math,shlex,subprocess
from PIL import Image
import numpy as np

PACKAGE=Path(__file__).resolve().parent.parent
OUT=PACKAGE/'evidence/adaptive-r3'
OUT.mkdir(exist_ok=True)
(OUT/'previews').mkdir(exist_ok=True)
ASSETS=PACKAGE/'assets'
ASSETS.mkdir(exist_ok=True)
SOURCE=PACKAGE/'sources/named-foreground-r3.png'
FOREGROUND=ASSETS/'havenline-adaptive-foreground-432.png'
BACKGROUND=ASSETS/'havenline-adaptive-background-432.png'
COMMANDS=[]
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def run(cmd):
    cmd=[str(a) for a in cmd]
    COMMANDS.append(shlex.join(cmd))
    return subprocess.run(cmd,check=True,capture_output=True,text=True).stdout

def identity(path):
    b=path.read_bytes()
    return {'path':str(path.relative_to(PACKAGE)), 'bytes':len(b),
            'sha256':hashlib.sha256(b).hexdigest(),
            'git_blob_sha':hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()}

def alpha_metrics(path,center):
    a=np.array(Image.open(path).convert('RGBA'))[:,:,3]
    results={}
    for threshold in (1,2,8,128,255):
        y,x=np.where(a>=threshold)
        r=np.hypot(x+.5-center[0],y+.5-center[1])
        results[str(threshold)]={'pixels':len(x),'bbox_inclusive':[int(x.min()),int(y.min()),int(x.max()),int(y.max())],
            'maximum_radius_pixels':float(r.max()),'outside_radius_130':int((r>130).sum()),'outside_radius_132':int((r>132).sum())}
    return {'size':[int(a.shape[1]),int(a.shape[0])], 'min_alpha':int(a.min()),'max_alpha':int(a.max()),
            'transparent_pixels':int((a==0).sum()),'fully_opaque_pixels':int((a==255).sum()),
            'center':center,'alpha_greater_equal':results}

before=identity(SOURCE)
a=np.array(Image.open(SOURCE).convert('RGBA'))[:,:,3]
y,x=np.where(a>=2)
center=[float((x.min()+x.max()+1)/2),float((y.min()+y.max()+1)/2)]
max_radius=float(np.hypot(x+.5-center[0],y+.5-center[1]).max())
side=int(math.floor(a.shape[1]*130/max_radius))
attempts=[]
while True:
    scaled_side=side
    scale=scaled_side/a.shape[1]
    offsets=[round(216-center[0]*scale),round(216-center[1]*scale)]
    assert offsets[0]>=0 and offsets[1]>=0 and offsets[0]+side<=432 and offsets[1]+side<=432
    resized=OUT/'previews'/f'foreground-uniform-{side}.png'
    run(['magick',SOURCE,'-filter','Lanczos','-resize',f'{side}x{side}!',resized])
    run(['magick','-size','432x432','xc:none',resized,'-geometry',f'+{offsets[0]}+{offsets[1]}','-compose','Over','-composite',FOREGROUND])
    metrics=alpha_metrics(FOREGROUND,[216,216])
    attempts.append({'resized_side':side,'offset':offsets,'metrics':metrics})
    if metrics['alpha_greater_equal']['2']['outside_radius_130']==0:
        break
    side-=1
    assert side>300, 'Unexpected padding failure; stop rather than hide the issue'

run(['magick','-size','432x432','xc:#06163d','-alpha','off','PNG24:'+str(BACKGROUND)])
composite=OUT/'composite-432.png'
run(['magick',BACKGROUND,FOREGROUND,'-compose','Over','-composite',composite])
viewport=OUT/'viewport-72dp-288px.png'
run(['magick',composite,'-crop','288x288+72+72','+repage',viewport])

for shape,power in [('circle',2),('squircle',4)]:
    mask=OUT/'previews'/f'{shape}-288-mask.png'
    expression=f'pow(abs((i+0.5-144)/144),{power})+pow(abs((j+0.5-144)/144),{power})<=1?1:0'
    run(['magick','-size','288x288','xc:black','-fx',expression,mask])
    masked=OUT/'previews'/f'viewport-{shape}-288.png'
    run(['magick',viewport,mask,'-alpha','off','-compose','CopyOpacity','-composite',masked])
    for size in (96,64,48,32):
        run(['magick',masked,'-filter','Lanczos','-resize',f'{size}x{size}!',OUT/'previews'/f'viewport-{shape}-{size}.png'])

for theme,bg,fg in [('dark','#131b2d','#f7f5ec'),('light','#edf0f5','#15203b')]:
    cmd=['magick','-size','700x620',f'xc:{bg}','-font',FONT,'-fill',fg,
         '-pointsize','21','-annotate','+24+32','Adaptive color: actual launcher viewport',
         '-pointsize','13','-annotate','+24+58','432px / 108dp layers; central 288px / 72dp visible viewport.',
         '-pointsize','13','-annotate','+24+80','Uniform source scale and padding only; no source-art edits.',
         '-pointsize','16','-annotate','+265+114','Circle','-annotate','+460+114','Squircle']
    for size,yy in [(96,185),(64,330),(48,445),(32,540)]:
        cmd+=['-pointsize','16','-annotate',f'+24+{yy+6}',f'{size}px']
        for shape,xx in [('circle',290),('squircle',490)]:
            cmd += [OUT/'previews'/f'viewport-{shape}-{size}.png','-geometry',f'+{xx-size//2}+{yy-size//2}','-compose','Over','-composite']
    cmd += [OUT/f'native-launcher-{theme}.png']
    run(cmd)

overlay=OUT/'safe-circle-overlay-432.png'
run(['magick',composite,'-fill','none','-stroke','#5ad1ff','-strokewidth','1',
     '-draw','rectangle 72,72 360,360','-stroke','#69ff80','-strokewidth','1',
     '-draw','circle 216,216 348,216','-stroke','#ffe95c','-draw','circle 216,216 346,216',overlay])
run(['magick','-size','880x520','xc:#edf0f5','-font',FONT,'-fill','#15203b','-pointsize','21',
     '-annotate','+20+30','Adaptive color: exact 432px layer and safe-circle evidence',
     overlay,'-geometry','+20+62','-compose','Over','-composite','-pointsize','14',
     '-annotate','+480+90','Green: 264px safe circle',
     '-annotate','+480+120','Yellow: 260px protected circle',
     '-annotate','+480+150','Blue: 288px visible viewport',
     '-annotate','+480+210','All alpha >= 2 lies inside yellow.',
     '-annotate','+480+240','Alpha = 1 haze is reported separately.',
     '-annotate','+480+300','No source pixels intentionally removed.',
     '-annotate','+480+330','No color or lettering edits.',
     '-annotate','+480+390','Simulation, not device certification.',
     OUT/'safe-circle-explanation.png'])

assert before==identity(SOURCE)
bg_arr=np.array(Image.open(BACKGROUND).convert('RGBA'))
assert np.all(bg_arr==np.array([6,22,61,255]))
data={
    'builder':'/root/icon_source_audit','scope':'Mechanical adaptive export and mask simulation; not independent approval',
    'source':before,'source_unchanged':True,
    'substantive_alpha_definition':'alpha >= 2 of255; alpha=1 haze is retained and reported separately, never stripped',
    'source_content_center':center,'source_content_max_radius':max_radius,
    'uniform_resized_canvas_side':side,'uniform_scale':side/a.shape[1],
    'integer_translation_on_432_canvas':offsets,'source_canvas_fully_inside_output':True,
    'no_alpha_thresholding_or_creative_edit':True,'attempts':attempts,
    'final_foreground':identity(FOREGROUND),'final_foreground_metrics':metrics,
    'background':identity(BACKGROUND),'background_pixel_rgba':[6,22,61,255],'background_uniform_opaque_check':True,
    'safe_circle_radius_pixels':132,'substantive_margin_radius_pixels':130,
    'launcher_viewport':{'canvas_dp':108,'visible_dp':72,'canvas_pixels':432,'viewport_crop':'288x288+72+72'},
    'outputs':[identity(p) for p in sorted(OUT.rglob('*.png'))],
    'device_run':False,
}
(OUT/'adaptive-export-metrics.json').write_text(json.dumps(data,indent=2)+'\n')
(OUT/'commands.txt').write_text('\n'.join(COMMANDS)+'\n')
print(json.dumps({k:data[k] for k in ['source','uniform_resized_canvas_side','uniform_scale','integer_translation_on_432_canvas','final_foreground','final_foreground_metrics','background']},indent=2))
