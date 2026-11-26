"""Pixel check of exact camera matched R17 paid frame, not a visual grade."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

prior, candidate = map(Path, sys.argv[1:])
images = [p / 'paid-first-frame.png' for p in (prior, candidate)]
for p, image in zip((prior, candidate), images):
    f = json.loads((p / 'frame-evidence.json').read_text())['frames']['paid-first-frame']
    assert hashlib.sha256(image.read_bytes()).hexdigest() == f['png_sha256']
    assert f['queued_tick'] == 357 and f['paid'] and not f['south_open'] and not f['east_open']
a, b = (np.asarray(Image.open(p).convert('RGB')).astype(np.int16) for p in images)
assert a.shape == b.shape == (720, 1280, 3)
rois = {
    'shadow_east_sample': (865, 442, 14, 18),
    'shadow_west_sample': (504, 155, 14, 18),
    'unchanged_furnace_sample': (718, 209, 30, 45),
    'unchanged_snow_sample': (854, 535, 90, 55),
}
results = {}
for name, (x, y, w, h) in rois.items():
    ar, br = (p[y:y+h, x:x+w] for p in (a, b))
    results[name] = dict(box=[x, y, w, h], before_mean_rgb=ar.mean((0,1)).round(3).tolist(),
                         after_mean_rgb=br.mean((0,1)).round(3).tolist(),
                         before_exact_black=int(np.count_nonzero(np.all(ar==0,axis=2))),
                         after_exact_black=int(np.count_nonzero(np.all(br==0,axis=2))),
                         altered_pixels=int(np.count_nonzero(np.any(ar!=br,axis=2))))
for label in ('unchanged_furnace_sample','unchanged_snow_sample'):
    assert results[label]['altered_pixels'] == 0
rows, cols = np.nonzero(np.any(a != b,axis=2))
assert len(rows)
print(json.dumps(dict(
    scope='Matched ordinary paid frame only; sampled patches are not full coverage or appearance approval',
    exact_pngs=[hashlib.sha256(p.read_bytes()).hexdigest() for p in images],
    total_altered_pixels=len(rows),
    altered_bounds_inclusive=[int(cols.min()),int(rows.min()),int(cols.max()),int(rows.max())],
    rois=results),indent=2))
