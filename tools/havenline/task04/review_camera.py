#!/usr/bin/env python3
"""Source-bound local visual review for the T04 shipping camera.

One execution owns one formal critic role and may cover one or more evidence
groups. Returned low scores are evidence, never retried here. The closeout
workflow separately invokes two fresh supplemental executions only when a
valid primary judgment dissents, then resolves that row by 2-of-3 quorum
without averaging scores.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw


SOURCE = os.environ["EXPECTED_SOURCE"]
ROLE = os.environ["REVIEW_ROLE"]
ATTEMPT = os.environ.get("REVIEW_ATTEMPT", "primary")
SEED = int(os.environ.get("REVIEW_SEED", "20260923"))
ROOT = Path(os.environ.get("EVIDENCE_ROOT", "task04-evidence"))
OUT = Path(os.environ.get("REVIEW_OUTPUT", "task04-camera-review"))
CACHE = Path.home() / ".cache/havenline-t01-qwen35"
OUT.mkdir(parents=True, exist_ok=True)

assert len(SOURCE) == 40
assert ROLE in ("C1", "C2")

DIMS = {
    "C1": ["reference_fidelity", "visual_language", "cross_view_consistency"],
    "C2": ["geometry_contact", "clipping_seams", "intentional_gap_integrity", "cross_view_integrity"],
}
FILES = {
    "device-matrix": [
        "gallery/aspect-phone-16-9.png", "gallery/aspect-phone-20-9.png",
        "gallery/aspect-tablet-16-10.png", "gallery/aspect-tablet-4-3.png",
        "gallery/aspect-foldable-outer.png", "gallery/aspect-foldable-inner.png",
    ],
    "tracking-and-target": [
        "gallery/direction-north.png", "gallery/direction-east.png",
        "gallery/direction-south.png", "gallery/direction-west.png",
        "gallery/target-inclusion-storage.png", "gallery/target-release-damped.png",
        "gallery/resize-fold-inner-safe.png", "gallery/resize-fold-inner-settled.png",
    ],
    "contexts-and-native": [
        "gallery/gameplay-camp.png", "gallery/gameplay-lakeshore.png",
        "gallery/gameplay-west-gate.png", "gallery/condition-day.png",
        "gallery/condition-night.png", "gallery/condition-blizzard.png",
        "native4k/native-gameplay-camp.png", "native4k/native-gameplay-lakeshore.png",
        "native4k/native-gameplay-east-river-gate.png",
    ],
}
GROUPS = [x for x in os.environ.get("REVIEW_GROUPS", ",".join(FILES)).split(",") if x]
assert GROUPS and set(GROUPS) <= set(FILES)

NOTES = {
    "device-matrix": "Judge automatic landscape composition across all six labelled phone, tablet and foldable aspects. Wider views may reveal more world; actor scale must remain readable and the active interaction must remain present.",
    "tracking-and-target": "Judge facing/movement look-ahead, stable lead anchoring, nearby target inclusion and release, plus the safe and settled fold resize states. These are deterministic state samples, not an animation storyboard.",
    "contexts-and-native": "Judge normal camp, gate and lakeshore gameplay under day/night/blizzard plus three actual 3840x2160 scale-1 frames. Environment content itself is approved T01-T03 scope; grade only camera-caused framing or integrity defects.",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


provenance = json.loads((ROOT / "provenance.json").read_text())
tests = json.loads((ROOT / "tests.json").read_text())
gallery = json.loads((ROOT / "gallery/capture.json").read_text())
native = json.loads((ROOT / "native4k/capture.json").read_text())
assert provenance["source"] == tests["source"] == SOURCE
assert provenance["actual_images"] == 23 and provenance["automated_framing_gate_passed"] is True
assert tests["all_passed"] is True and tests["suite_count"] == 17 and tests["total_checks"] == 852
assert gallery["shipping_main_call_site_exercised"] is True
assert native["shipping_main_call_site_exercised"] is True
assert gallery["candidate_component_applied_directly_because_main_is_integration_only"] is False
assert native["candidate_component_applied_directly_because_main_is_integration_only"] is False
for name, expected in provenance["captures"].items():
    assert digest(ROOT / name) == expected, "changed evidence " + name

reference = ROOT / "reference-ground.webp"
assert digest(reference) == "3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb"
manifest = json.loads((CACHE / "manifest.json").read_text())
assert manifest["publisher"] == "unsloth/Qwen3.5-9B-GGUF"
assert manifest["base_model"] == "Qwen/Qwen3.5-9B"
for item in manifest["files"]:
    assert digest(CACHE / item["filename"]) == item["sha256"], "bad model/runtime bytes"
servers = list((CACHE / "runtime").rglob("llama-server"))
assert len(servers) == 1
server = servers[0]


def build_probe() -> Path:
    specs = [
        ("A", "gallery/gameplay-camp.png", (0.39, 0.48, 0.61, 0.91), "human_character"),
        ("B", "gallery/gameplay-lakeshore.png", (0.12, 0.28, 0.88, 0.72), "blue_river"),
        ("C", "gallery/gameplay-camp.png", (0.14, 0.17, 0.43, 0.57), "wooden_cabin"),
        ("D", "gallery/gameplay-camp.png", (0.08, 0.46, 0.36, 0.94), "snow_tree"),
    ]
    board = Image.new("RGB", (960, 960), (20, 29, 38))
    draw = ImageDraw.Draw(board)
    sources = []
    for index, (label, name, ratios, expected) in enumerate(specs):
        image = Image.open(ROOT / name).convert("RGB")
        w, h = image.size
        box = tuple(int(value * (w if i % 2 == 0 else h)) for i, value in enumerate(ratios))
        crop = image.crop(box)
        crop.thumbnail((450, 410), Image.Resampling.LANCZOS)
        x = (index % 2) * 480 + (480 - crop.width) // 2
        y = (index // 2) * 480 + 45 + (410 - crop.height) // 2
        board.paste(crop, (x, y))
        draw.text(((index % 2) * 480 + 16, (index // 2) * 480 + 12), label, fill="white")
        sources.append({"panel": label, "source": name, "crop": list(box), "expected": expected})
    path = OUT / "blind-competency.jpg"
    board.save(path, quality=94)
    (OUT / "competency-sources.json").write_text(json.dumps(sources, indent=2))
    return path


def build_board(group: str) -> Path:
    ref = Image.open(reference).convert("RGB")
    ref.thumbnail((1500, 300), Image.Resampling.LANCZOS)
    tiles = []
    for name in FILES[group]:
        image = Image.open(ROOT / name).convert("RGB")
        image.thumbnail((500, 285), Image.Resampling.LANCZOS)
        tiles.append((name, image))
    columns = 3
    rows = math.ceil(len(tiles) / columns)
    board = Image.new("RGB", (1560, 370 + rows * 330), (20, 29, 38))
    draw = ImageDraw.Draw(board)
    draw.text((18, 12), "AUTHORITATIVE USER VIDEO REFERENCE — visual-language context", fill="white")
    board.paste(ref, ((1560 - ref.width) // 2, 42))
    draw.text((18, 342), "SOURCE-BOUND T04 SHIPPING CAMERA EVIDENCE: " + group, fill="white")
    for index, (name, image) in enumerate(tiles):
        column, row = index % columns, index // columns
        x0, y0 = column * 520, 385 + row * 330
        draw.text((x0 + 10, y0), name, fill="white")
        board.paste(image, (x0 + (520 - image.width) // 2, y0 + 28))
    path = OUT / (group + "-board.jpg")
    board.save(path, quality=93)
    return path


def query(image_path: Path, prompt: str, schema: dict, name: str, max_tokens: int) -> tuple[dict, float]:
    image = Image.open(image_path).convert("RGB")
    original = image.size
    image.thumbnail((1664, 1664), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    payload = buffer.getvalue()
    request = {
        "model": "T04-" + ROLE + "-" + ATTEMPT,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(payload).decode()}},
            {"type": "text", "text": prompt},
        ]}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "top_p": 0.9,
        "seed": SEED,
        "repeat_penalty": 1.12,
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": {"type": "json_object", "schema": schema},
        "cache_prompt": False,
    }
    (OUT / (name + "-request.json")).write_text(json.dumps({
        "model": request["model"], "prompt": prompt, "schema": schema,
        "image_sha256": hashlib.sha256(payload).hexdigest(),
        "original_size": original, "input_size": image.size, "seed": SEED,
    }, indent=2, default=list))
    began = time.monotonic()
    call = urllib.request.Request(
        "http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(request).encode(), headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(call, timeout=1800) as response:
        raw = json.load(response)
    (OUT / (name + "-raw.json")).write_text(json.dumps(raw, indent=2))
    choice = raw["choices"][0]
    assert choice["finish_reason"] == "stop", "truncated " + name
    parsed = json.loads(choice["message"]["content"])
    (OUT / (name + "-answer.json")).write_text(json.dumps(parsed, indent=2))
    return parsed, round(time.monotonic() - began, 3)


role_prompt = {
    "C1": "Judge reference fidelity, the close oblique near-orthographic visual language, and consistency across the supplied views.",
    "C2": "Judge only camera-caused contact/clipping/seam ambiguity, intentional crops versus defects, and cross-view technical integrity.",
}[ROLE]
base_prompt = """You are an independent visual critic reviewing only Havenline Task T04: the automatic shipping gameplay camera. The top strip is the authoritative user-video reference; the labelled candidate panels are exact source-bound renders from the shipping main.gd call site. Preserve the already-approved T01-T03 environment and do not invent defects in its art, fences, river, paths, characters or lighting. T04 succeeds when the selected lead remains a stable readable anchor, movement/facing look-ahead shows useful action space, an in-range interaction target remains composed, and landscape phone/tablet/foldable views adapt without stretching, unsafe crops, snapping, oscillation or distant-diagram scale. Do not demand identical world coverage across different aspect ratios. Wider displays are expected to reveal more world. Night and blizzard may change illumination, and lakeshore/gate contexts intentionally show different parts of the map. A frame-edge crop is a defect only if the camera cuts away the active lead or target, creates misleading contact, or makes gameplay unreadable. Actual native frames prove pixels and scale only, not physical FPS. Every score at or below 9.0 must cite a concise actionable T04 camera defect visible in the supplied pixels. Forward approval requires every score strictly greater than 9.0 unrounded, no unresolved defects, complete coverage and medium/high confidence. If no actionable defect exists, defects must be [] exactly. Return JSON only."""
base_prompt += "\nFormal role: " + ROLE + ". " + role_prompt

schema = {
    "type": "object",
    "properties": {
        "observations": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
        "defects": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "coverage_complete": {"type": "boolean"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "scores": {"type": "object", "properties": {key: {"type": "number", "minimum": 0, "maximum": 10} for key in DIMS[ROLE]}, "required": DIMS[ROLE], "additionalProperties": False},
    },
    "required": ["observations", "defects", "coverage_complete", "confidence", "scores"],
    "additionalProperties": False,
}

environment = dict(os.environ)
environment["LD_LIBRARY_PATH"] = str(server.parent) + ":" + environment.get("LD_LIBRARY_PATH", "")
log = (OUT / "inference.log").open("w")
command = [
    str(server), "-m", str(CACHE / manifest["model_file"]), "--mmproj", str(CACHE / manifest["projector_file"]),
    "--host", "127.0.0.1", "--port", "8080", "-c", "8192", "-t", "4", "-tb", "4",
    "-ngl", "0", "--no-mmproj-offload", "--parallel", "1", "--jinja",
    "--image-min-tokens", "1024", "--image-max-tokens", "2048",
]
process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=environment)
rows = []
failure = None
competent = False
try:
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError("local reviewer runtime exited")
        try:
            if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=3)).get("status") == "ok":
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        raise RuntimeError("local reviewer runtime not ready")

    probe_schema = {
        "type": "object",
        "properties": {key: {"type": "string", "enum": ["human_character", "blue_river", "wooden_cabin", "snow_tree", "other_or_unclear"]} for key in "ABCD"},
        "required": list("ABCD"), "additionalProperties": False,
    }
    answers, elapsed = query(
        build_probe(),
        "Four panels are labelled A-D. Identify the prominent subject in each as human_character, blue_river, wooden_cabin, snow_tree, or other_or_unclear. Return only the JSON object.",
        probe_schema, "competency", 180,
    )
    expected = {"A": "human_character", "B": "blue_river", "C": "wooden_cabin", "D": "snow_tree"}
    competent = answers == expected
    (OUT / "competency.json").write_text(json.dumps({"answers": answers, "expected": expected, "passed": competent, "elapsed_seconds": elapsed}, indent=2))
    assert competent, "blind image competency failed; do not grade"

    for index, group in enumerate(GROUPS):
        row = {"task": "T04", "source": SOURCE, "critic_id": ROLE, "group": group, "attempt": ATTEMPT, "seed": SEED, "independent_execution": False, "passed": False}
        try:
            review, elapsed = query(
                build_board(group),
                base_prompt + "\nCurrent evidence group: " + group + ". " + NOTES[group] + " Inspect every labelled candidate panel.",
                schema, group, 650,
            )
            scores = review["scores"]
            assert set(scores) == set(DIMS[ROLE])
            assert all(not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 10 for value in scores.values())
            assert isinstance(review["defects"], list) and isinstance(review["coverage_complete"], bool)
            row.update({"independent_execution": True, "review": review, "minimum": min(scores.values()), "elapsed_seconds": elapsed, "board_sha256": digest(OUT / (group + "-board.jpg"))})
            row["passed"] = row["minimum"] > 9.0 and review["defects"] == [] and review["coverage_complete"] is True and review["confidence"] in ("medium", "high")
        except Exception as error:
            row["error"] = str(error)
        rows.append(row)
        (OUT / (group + "-review.json")).write_text(json.dumps(row, indent=2))
        print(json.dumps(row), flush=True)
except Exception as error:
    failure = str(error)
finally:
    result = {
        "task": "T04", "source": SOURCE, "critic_id": ROLE, "attempt": ATTEMPT,
        "groups": GROUPS, "reviews": rows, "competency_passed": competent,
        "error": failure, "passed": competent and failure is None and len(rows) == len(GROUPS) and all(row["passed"] for row in rows),
        "provider": "local-checksum-pinned-public-model", "model": manifest["base_model"],
        "model_revision": manifest["revision"], "independent_runtime": True,
        "strict_rule": ">9.0 unrounded", "score_averaging": False,
        "task_approved": False, "physical_4k60_verified": False,
    }
    (OUT / "review-result.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "provenance.json").write_text(json.dumps({
        "source": SOURCE, "critic_id": ROLE, "attempt": ATTEMPT, "seed": SEED,
        "evidence_provenance_sha256": digest(ROOT / "provenance.json"),
        "reference_sha256": digest(reference), "script_sha256": digest(Path(__file__)),
        "completed_low_scores_retried": False, "score_averaging": False,
    }, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
    log.close()
raise SystemExit(0 if result["error"] is None and result["competency_passed"] else 1)
