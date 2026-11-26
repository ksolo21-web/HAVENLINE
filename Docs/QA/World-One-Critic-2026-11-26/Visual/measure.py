"""Measure game and reference pixels at their original display resolution."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def read_roi(path, bounds):
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB").crop(bounds), dtype=float)
    return rgb


def summarize(path, bounds, green=False):
    rgb = read_roi(path, bounds)
    luma = rgb @ np.array([0.2126, 0.7152, 0.0722])
    fields = {"source_file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "crop_left_top_right_bottom": bounds, "pixel_count": int(luma.size),
              "median_rgb": np.median(rgb, axis=(0, 1)).tolist(),
              "luma_rec709_display_mean": float(luma.mean()),
              "luma_rec709_display_p10_median_p90": np.percentile(luma, [10, 50, 90]).tolist()}
    if green:
        red, green_channel, blue = (rgb / 255.0).transpose(2, 0, 1)
        for name, red_gap, blue_gap in [("strong_green", .16, .15), ("green_tint", .045, .025)]:
            selected = ((green_channel - red > red_gap) & (green_channel - blue > blue_gap))
            fields[name] = {"pixels": int(selected.sum()), "coverage": float(selected.mean())}
    return fields


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--unpaid", required=True, type=Path)
    args.add_argument("--built", type=Path)
    args.add_argument("--source-pad", required=True, type=Path)
    args.add_argument("--source-snow", required=True, type=Path)
    args.add_argument("--source-court", required=True, type=Path)
    args.add_argument("--output", required=True, type=Path)
    p = args.parse_args()
    result = {"source_plot": summarize(p.source_pad, [59, 138, 177, 222], True),
              "game_plot": summarize(p.unpaid, [647, 188, 850, 311], True),
              "source_snow": summarize(p.source_snow, [48, 204, 144, 231]),
              "game_snow": summarize(p.unpaid, [505, 435, 936, 588]),
              "source_court": summarize(p.source_court, [139, 181, 163, 194])}
    if p.built:
        result["game_court"] = summarize(p.built, [787, 366, 829, 402])
    p.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
