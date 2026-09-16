#!/usr/bin/env python3
"""Materialize exact-source T09 C3/C4/C5 specialist evidence.

C5 receives every captured motion frame for wood, stone and fuel, split into
source-ordered groups of at most 18 images so the independent specialist model
reviews the complete captured cycles rather than a sparse sample.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[3]
ALLOWED_KINDS = {"image", "motion_frame", "json", "text"}


def digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def copy_file(src_root: pathlib.Path, dst_root: pathlib.Path, out_name: str, rel: str) -> pathlib.Path:
    source = src_root / rel
    if not source.is_file():
        raise SystemExit("missing T09 evidence: " + rel)
    target = dst_root / out_name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def item(group: str, category: str, kind: str, path: pathlib.Path, description: str) -> dict:
    if kind not in ALLOWED_KINDS:
        raise ValueError(kind)
    return {
        "group": group,
        "category": category,
        "kind": kind,
        "path": str(path.relative_to(ROOT)),
        "description": description,
        "sha256": digest(path),
    }


def manifest(task: str, critic: str, candidate: str, rows: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        group = row.pop("group")
        groups.setdefault(group, []).append(row)
    return {
        "schema_version": 1,
        "task_id": task,
        "critic_id": critic,
        "candidate_commit": candidate,
        "groups": [{"id": group, "items": values} for group, values in groups.items()],
    }


def write_manifest(path: pathlib.Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--candidate", required=True)
    args = ap.parse_args()
    if len(args.candidate) != 40:
        raise SystemExit("candidate must be exact 40-char SHA")

    src = pathlib.Path(args.evidence_root).resolve()
    dst = pathlib.Path(args.out).resolve()
    if ROOT.resolve() not in dst.parents and dst != ROOT.resolve():
        raise SystemExit("output must stay inside repository")
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    static = {
        "device-impact.png": "captures/device-phone_16_9/device-phone_16_9-wood-impact-transfer-carry.png",
        "device-preimpact.png": "captures/device-phone_16_9/device-phone_16_9-wood-preimpact.png",
        "device-depleted.png": "captures/device-phone_16_9/device-phone_16_9-wood-depleted.png",
        "device-respawned.png": "captures/device-phone_16_9/device-phone_16_9-wood-respawned.png",
        "wood-report.json": "captures/sequence-wood/capture-report.json",
        "wood-focus.png": "captures/sequence-wood/wood-focus-acquired.png",
        "wood-contact.png": "captures/sequence-wood/wood-committed-contact.png",
        "wood-recovery.png": "captures/sequence-wood/wood-recovery.png",
        "wood-cancelled.png": "captures/sequence-wood/wood-cancelled.png",
        "wood-depleted.png": "captures/sequence-wood/wood-depleted.png",
        "wood-respawned.png": "captures/sequence-wood/wood-respawned.png",
        "stone-contact.png": "captures/sequence-stone/stone-committed-contact.png",
        "metal-contact.png": "captures/sequence-metal/metal-committed-contact.png",
        "fuel-contact.png": "captures/sequence-fuel/fuel-committed-contact.png",
        "wood-detail.png": "captures/tool-wood-detail/tool-wood-detail.png",
        "stone-detail.png": "captures/tool-stone-detail/tool-stone-detail.png",
        "fuel-detail.png": "captures/tool-fuel-detail/tool-fuel-detail.png",
    }
    files = {name: copy_file(src, dst, name, rel) for name, rel in static.items()}

    c3 = [
        item("gameplay", "gameplay_state", "image", files["device-impact.png"], "Phone gameplay state at authoritative harvest transfer/carry feedback."),
        item("controls", "control_state", "json", files["wood-report.json"], "Shipping T07/T09 action-state and authority trace across approach, focus, commit, recovery and reentry."),
        item("loop", "loop_evidence", "image", files["wood-focus.png"], "Focused contextual gather state."),
        item("loop", "loop_evidence", "image", files["wood-contact.png"], "Authoritative committed harvest contact."),
        item("loop", "loop_evidence", "image", files["wood-depleted.png"], "Visible depleted source state."),
        item("loop", "loop_evidence", "image", files["wood-respawned.png"], "Visible respawned source state."),
    ]
    c4 = [
        item("gameplay", "gameplay_state", "image", files["device-preimpact.png"], "Gameplay immediately before harvest impact."),
        item("feedback", "feedback_state", "image", files["device-impact.png"], "Impact plus transfer and carried-resource feedback."),
        item("feedback", "feedback_state", "image", files["device-depleted.png"], "Source depletion feedback."),
        item("feedback", "feedback_state", "image", files["device-respawned.png"], "Source respawn feedback."),
        item("feedback", "feedback_state", "image", files["wood-contact.png"], "Close authoritative harvest-contact feedback."),
    ]

    c5: list[dict] = []
    full_cycle_counts = {}
    for resource in ("wood", "stone", "fuel"):
        frame_root = src / f"captures/sequence-{resource}/frames"
        frames = sorted(frame_root.glob("frame-*.jpg"))
        if len(frames) < 80:
            raise SystemExit(f"{resource} full-cycle capture has only {len(frames)} frames")
        expected = list(range(len(frames)))
        actual = [int(path.stem.split("-")[-1]) for path in frames]
        if actual != expected:
            raise SystemExit(f"{resource} frame sequence is not contiguous")
        full_cycle_counts[resource] = len(frames)
        for index, source in enumerate(frames):
            target = dst / "full-cycle" / resource / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            group = f"{resource}-cycle-{index // 18 + 1:02d}"
            c5.append(item(group, "motion_cycle", "motion_frame", target, f"{resource} captured full-cycle frame {index + 1}/{len(frames)}."))

    c5.extend([
        item("transition", "motion_transition", "image", files["wood-focus.png"], "Focus-acquisition transition into harvesting."),
        item("transition", "motion_transition", "image", files["wood-recovery.png"], "Recovery state after committed contact."),
        item("transition", "motion_transition", "image", files["wood-cancelled.png"], "Movement-owned cancellation transition."),
        item("contact", "contact_detail", "image", files["wood-detail.png"], "Axe hand/tool contact detail."),
        item("contact", "contact_detail", "image", files["stone-detail.png"], "Pickaxe hand/tool contact detail."),
        item("contact", "contact_detail", "image", files["fuel-detail.png"], "Pry-tool hand/contact detail."),
        item("contact", "contact_detail", "image", files["wood-contact.png"], "Wood authoritative impact contact."),
        item("contact", "contact_detail", "image", files["stone-contact.png"], "Stone authoritative impact contact."),
        item("contact", "contact_detail", "image", files["metal-contact.png"], "Metal authoritative impact contact."),
        item("contact", "contact_detail", "image", files["fuel-contact.png"], "Fuel authoritative impact contact."),
    ])

    write_manifest(dst / "C3-manifest.json", manifest("T09", "C3", args.candidate, c3))
    write_manifest(dst / "C4-manifest.json", manifest("T09", "C4", args.candidate, c4))
    write_manifest(dst / "C5-manifest.json", manifest("T09", "C5", args.candidate, c5))
    summary = {
        "task": "T09",
        "candidate": args.candidate,
        "full_cycle_frame_counts": full_cycle_counts,
        "c5_group_count": len(json.loads((dst / "C5-manifest.json").read_text())["groups"]),
        "c5_uses_every_captured_frame": True,
        "max_visual_items_per_group": max(len(g["items"]) for g in json.loads((dst / "C5-manifest.json").read_text())["groups"]),
    }
    if summary["max_visual_items_per_group"] > 18:
        raise SystemExit("C5 group exceeds specialist runner visual-item limit")
    (dst / "input-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
