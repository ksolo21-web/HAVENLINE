"""Measure complete, source-verified trials from the public Running Biomechanics Data Set v5. Downloads source data when executed."""

from pathlib import Path
import json, io, hashlib, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd

directory = Path(__file__).resolve().parents[1]
catalog = json.load(
    urllib.request.urlopen(
        "https://api.figshare.com/v2/articles/4543435/versions/5", timeout=30
    )
)
files = [f for f in catalog["files"] if f["name"].endswith("T45markers.txt")]
markers = [
    "Heel.Bottom",
    "MT1",
    "MT5",
    "ASIS",
    "PSIS",
    "Thigh.Top.Lateral",
    "Thigh.Top.Medial",
    "Thigh.Bottom.Lateral",
    "Thigh.Bottom.Medial",
]


def subject(file):
    raw = urllib.request.urlopen(file["download_url"], timeout=60).read()
    assert hashlib.md5(raw).hexdigest() == file["computed_md5"], file["name"]
    cols = ["R." + k + axis for k in markers for axis in "XYZ"] + [
        "L." + k + axis for k in ("ASIS", "PSIS") for axis in "XYZ"
    ]
    d = pd.read_csv(io.BytesIO(raw), usecols=["Time"] + cols, sep="\t")
    point = lambda k: d[["R." + k + axis for axis in "XYZ"]].to_numpy() / 1000
    a, b = point("ASIS"), point("PSIS")
    left_a = d[["L.ASIS" + axis for axis in "XYZ"]].to_numpy() / 1000
    left_b = d[["L.PSIS" + axis for axis in "XYZ"]].to_numpy() / 1000
    forward = np.nanmedian((a - b + left_a - left_b) * 0.5, axis=0)
    forward[1] = 0
    forward /= np.linalg.norm(forward)
    heel = point("Heel.Bottom")
    toes = 0.5 * (point("MT1") + point("MT5"))
    pelvis = (a + b) * 0.5
    femur = (
        point("Thigh.Bottom.Lateral")
        + point("Thigh.Bottom.Medial")
        - point("Thigh.Top.Lateral")
        - point("Thigh.Top.Medial")
    ) * 0.5
    sole = np.minimum(heel[:, 1], toes[:, 1])
    threshold = np.nanpercentile(sole, 5) + 0.035
    land = np.flatnonzero((sole[:-1] > threshold) & (sole[1:] <= threshold)) + 1
    valid = [(a, b) for a, b in zip(land, land[1:]) if 70 < b - a < 160]
    if len(valid) < 5:
        return (file["name"], len(valid), None, None)
    kinematics = {
        "thigh_marker_pitch_degrees": np.degrees(
            np.arctan2(femur @ forward, -femur[:, 1])
        ),
        "heel_forward_of_pelvis_m": (heel - pelvis) @ forward,
        "heel_above_forefoot_m": heel[:, 1] - toes[:, 1],
        "heel_y_m": heel[:, 1],
    }
    summary = {
        key: np.nanmedian(
            [
                np.interp(np.linspace(a, b, 101), np.arange(len(d)), curve)
                for a, b in valid
            ],
            axis=0,
        )
        for key, curve in kinematics.items()
    }
    if not all(np.isfinite(v).all() for v in summary.values()):
        return (file["name"], len(valid), None, None)
    crossings = np.flatnonzero(
        (summary["heel_forward_of_pelvis_m"][:-1] < 0)
        & (summary["heel_forward_of_pelvis_m"][1:] >= 0)
    )
    return (
        file["name"],
        len(valid),
        int(crossings[-1]) + 1 if len(crossings) else None,
        summary,
    )


with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(subject, files))
excluded = [r[0] for r in results if r[3] is None]
results = [r for r in results if r[3] is not None]
group = {
    key: np.median([r[3][key] for r in results], axis=0).round(6).tolist()
    for key in results[0][3]
}
out = {
    "dataset_doi": "10.6084/m9.figshare.4543435.v5",
    "released_subject_files": 39,
    "raw_files_at_4p5_m_s": len(files),
    "source_metadata_url": catalog["url_public_api"],
    "excluded_incomplete_marker_records": excluded,
    "source_hz": 150,
    "excluded_source_ids_without_4p5_m_s_recording": [
        "031",
        "033",
        "034",
        "035",
        "036",
        "037",
        "038",
        "039",
    ],
    "method": "Each subject contributes one median of complete right-leg strides. Start at a downward crossing 35 mm above the 5th percentile of the trial’s lower heel/metatarsal marker height. Use bilateral horizontal PSIS-to-ASIS direction as forward. The thigh angle is an observed marker-cluster pitch to world vertical, including mounting offset. Align the 101 samples by the subject’s own stride duration. The group result is the median across subject files.",
    "contributing_subjects": [
        {"file": r[0], "strides": r[1], "heel_repasses_pelvis_cycle_percent": r[2]}
        for r in results
    ],
    "median": group,
}
(directory / "Human-running-markers.json").write_text(json.dumps(out, indent=2) + "\n")
print(
    len(results),
    sum(r[1] for r in results),
    np.percentile([r[2] for r in results if r[2]], [10, 50, 90]),
    min(group["thigh_marker_pitch_degrees"]),
    max(group["thigh_marker_pitch_degrees"]),
)
