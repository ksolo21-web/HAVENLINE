#!/usr/bin/env python3
"""Recover timestamped visual-reference evidence. This is not a quality critic.

Requires Python 3.10+ and ffmpeg/ffprobe on PATH. Obtain the two original user
uploads through the conversation/Library tools; never substitute another video.
No files are downloaded and no player save or game asset is modified.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "Docs/Design/ReferenceVideoLock/reference-video-sources.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command(args: list[str], timeout: int = 120) -> str:
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{Path(args[0]).name} failed: {result.stderr[-3000:]}")
    return result.stdout


def verify_sources(manifest: dict[str, Any], source_dir: Path) -> list[dict[str, Any]]:
    sources = manifest.get("sources", [])
    if {source.get("id") for source in sources} != {"A", "B"} or len(sources) != 2:
        raise ValueError("Exactly the two pinned A/B sources are required")
    verified: list[dict[str, Any]] = []
    sample_count = 0
    for source in sources:
        name = source["filename"]
        if Path(name).name != name:
            raise ValueError("Source filename must be a basename")
        path = source_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing original reference: {name}")
        if path.stat().st_size != source["bytes"] or sha256(path) != source["sha256"]:
            raise ValueError(f"Source bytes/checksum mismatch: {name}")
        probe = json.loads(command([
            "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
        ]))
        videos = [s for s in probe["streams"] if s.get("codec_type") == "video"]
        if len(videos) != 1:
            raise ValueError(f"Expected one video stream: {name}")
        video = videos[0]
        if (video["width"], video["height"]) != (source["width"], source["height"]):
            raise ValueError(f"Video dimension mismatch: {name}")
        duration = float(probe["format"]["duration"])
        if abs(duration - float(source["duration_seconds"])) > 0.01:
            raise ValueError(f"Duration mismatch: {name}")
        has_audio = any(s.get("codec_type") == "audio" for s in probe["streams"])
        if has_audio != source["has_audio"]:
            raise ValueError(f"Audio stream-presence mismatch: {name}")
        timestamps = source["selected_seek_seconds"]
        if timestamps != sorted(set(timestamps)) or any(
            isinstance(t, bool) or not isinstance(t, (int, float)) or not 0 <= t < duration
            for t in timestamps
        ):
            raise ValueError(f"Invalid/duplicate timestamps: {name}")
        sample_count += len(timestamps)
        verified.append({
            "id": source["id"], "filename": name, "sha256": source["sha256"],
            "duration_seconds": duration, "width": video["width"], "height": video["height"],
            "has_audio": has_audio, "audio_reviewed": False,
        })
    if sample_count != manifest["sample_count"] or sample_count != 44:
        raise ValueError("Expected the 44 locked reference sample times")
    return verified


def extract_one(task: tuple[dict[str, Any], float, Path, Path]) -> dict[str, Any]:
    source, timestamp, source_dir, output_dir = task
    output = output_dir / f"{source['id']}-{timestamp:06.2f}.png"
    command([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-threads", "1",
        "-ss", str(timestamp), "-i", str(source_dir / source["filename"]),
        "-frames:v", "1", "-threads", "1", "-y", str(output),
    ])
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"No decoded frame: {output.name}")
    return {
        "source": source["id"], "requested_seek_seconds": timestamp,
        "filename": output.name, "bytes": output.stat().st_size,
        "extracted_png_sha256": sha256(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    for executable in ("ffmpeg", "ffprobe"):
        if shutil.which(executable) is None:
            raise RuntimeError(f"Required tool is missing: {executable}")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    verified = verify_sources(manifest, args.source_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "source_manifest_sha256": sha256(args.manifest), "sources": verified,
        "ffmpeg": command(["ffmpeg", "-version"]).splitlines()[0],
        "selection": "Accurate FFmpeg input seek; labels are requested recording timestamps",
        "samples": [], "verified_original_sources": len(verified),
        "independent_critic_execution": False, "game_quality_approved": False,
        "native_android_4k60_verified": False, "audio_reviewed": False,
    }
    if not args.verify_only:
        tasks = [
            (source, timestamp, args.source_dir, args.output_dir)
            for source in manifest["sources"] for timestamp in source["selected_seek_seconds"]
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            report["samples"] = list(pool.map(extract_one, tasks))
        if len(report["samples"]) != 44:
            raise RuntimeError("Incomplete extraction; do not present it as complete evidence")
    report["extracted_sample_count"] = len(report["samples"])
    temporary = args.output_dir / "extraction-report.json.tmp"
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output_dir / "extraction-report.json")
    print(f"Verified {len(verified)} originals; extracted {len(report['samples'])} frames. No quality or FPS approval.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"Reference evidence FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
