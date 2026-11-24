"""Extract unmodified reference pixels for read-only paid-plot state inspection."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/workspace/scratch/fc906e16b0fb')
SOURCE = ROOT / 'havenline-plot-reference-source/Media/Video-Misc'
OUT = ROOT / 'havenline-plot-renders/sources'
RAW = ROOT / 'havenline-plot-reference-source/extracted-frames'
VIDEOS = {'A': SOURCE / 'Screen_Recording_20260817_124839_YouTube.mp4', 'B': SOURCE / 'Screen_Recording_20260817_124510_YouTube.mp4'}
JOBS = [('A-paid', 'A', 9.0, 16.0), ('A-wheat', 'A', 37.0, 43.0), ('B-build', 'B', 2.0, 8.0), ('B-upgrade', 'B', 10.0, 16.0)]
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)


def extract(job):
    name, video, start, end = job
    folder = RAW / name
    folder.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(start), '-i', str(VIDEOS[video]), '-t', str(end-start+0.5), '-vf', 'fps=2', str(folder / '%03d.png')], check=True)
    files = sorted(folder.glob('*.png'))
    columns = 5
    width, height = 300, 525
    sheet = Image.new('RGB', (columns*width, ((len(files)+columns-1)//columns)*height), '#26323a')
    draw = ImageDraw.Draw(sheet)
    records = []
    for i, p in enumerate(files):
        im = Image.open(p)
        # Retain gameplay source pixels and omit phone/navigation and uploader bars.
        crop = im.crop((0, 273, 1080, 2073))
        crop.thumbnail((width, height-25))
        x, y = (i % columns)*width, (i // columns)*height
        sheet.paste(crop, (x, y+25))
        time = start+i*0.5
        draw.text((x+5, y+3), f'{video} {time:05.2f}s', font=font, fill='white')
        records.append({'video': video, 'requested_time_seconds': time, 'frame_path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    target = OUT / f'{name}-sequence.png'
    sheet.save(target)
    return {'sequence': name, 'source_filename': VIDEOS[video].name, 'source_sha256': hashlib.sha256(VIDEOS[video].read_bytes()).hexdigest(), 'contact_sheet': str(target), 'contact_sheet_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'gameplay_crop': [0, 273, 1080, 2073], 'frames': records}


with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(extract, JOBS))
(OUT / 'buy-plot-frame-extraction.json').write_text(json.dumps({'sampling': '2 fps; labels are requested sample times, not proven game timing. Source videos are unmodified. No audio audit.', 'sequences': results}, indent=2)+'\n')
print(json.dumps([{'sequence':r['sequence'], 'frames':len(r['frames']), 'contact_sheet':r['contact_sheet']} for r in results]))
