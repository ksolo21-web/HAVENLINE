#!/usr/bin/env python3
"""Exact-source independent C1/C2 review for the integrated T05 station kit.

Each execution owns one formal critic role. Completed low judgments are never
retried here; the workflow applies the repository's isolated-dissent policy.
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
SEED = int(os.environ.get("REVIEW_SEED", "20260951"))
ROOT = Path(os.environ.get("EVIDENCE_ROOT", "task05-evidence"))
OUT = Path(os.environ.get("REVIEW_OUTPUT", "task05-station-review"))
CACHE = Path.home() / ".cache/havenline-t01-qwen35"
OUT.mkdir(parents=True, exist_ok=True)

assert len(SOURCE) == 40
assert ROLE in ("C1", "C2")
RUN_ID = os.environ.get("GITHUB_RUN_ID", "local")
RUN_ATTEMPT = os.environ.get("GITHUB_RUN_ATTEMPT", "0")
RUN_JOB = os.environ.get("GITHUB_JOB", "local")

DIMS = {
    "C1": ["reference_fidelity", "visual_language", "cross_view_consistency"],
    "C2": ["geometry_contact", "clipping_seams", "intentional_gap_integrity", "cross_view_integrity"],
}

VIEWS = ["front", "rear", "left", "right", "three-quarter", "detail"]


def family_files(*families: str) -> list[str]:
    return [f"families/family-{family}-{view}.png" for family in families for view in VIEWS]


FILES = {
    "core-families": family_files("hearth", "counters", "pads"),
    "loop-families": family_files("fishing", "processing", "defense"),
    "resources-and-details": family_files("resources") + [
        "component/close-hearth-front.png",
        "component/close-counter-reverse.png",
        "component/close-fishing-side.png",
        "component/close-processing-front.png",
        "component/close-defense-reverse.png",
        "component/camp-day-front.png",
        "component/camp-day-reverse.png",
        "component/lakeshore-day-front.png",
        "component/lakeshore-day-reverse.png",
        "component/camp-night-front.png",
        "component/camp-blizzard-side.png",
        "component/lakeshore-night-front.png",
    ],
    "shipping-device-and-tracking": [
        "gameplay/aspect-phone-16-9.png",
        "gameplay/aspect-phone-20-9.png",
        "gameplay/aspect-tablet-16-10.png",
        "gameplay/aspect-tablet-4-3.png",
        "gameplay/aspect-foldable-outer.png",
        "gameplay/aspect-foldable-inner.png",
        "gameplay/direction-north.png",
        "gameplay/direction-east.png",
        "gameplay/direction-south.png",
        "gameplay/direction-west.png",
        "gameplay/target-inclusion-storage.png",
        "gameplay/target-release-damped.png",
        "gameplay/resize-fold-inner-safe.png",
        "gameplay/resize-fold-inner-settled.png",
    ],
    "shipping-contexts-and-native": [
        "gameplay/gameplay-camp.png",
        "gameplay/gameplay-lakeshore.png",
        "gameplay/gameplay-west-gate.png",
        "gameplay/condition-day.png",
        "gameplay/condition-night.png",
        "gameplay/condition-blizzard.png",
        "native4k/native-gameplay-camp.png",
        "native4k/native-gameplay-lakeshore.png",
        "native4k/native-gameplay-east-river-gate.png",
    ],
}

GROUPS = [name for name in os.environ.get("REVIEW_GROUPS", ",".join(FILES)).split(",") if name]
assert GROUPS and set(GROUPS) <= set(FILES)

NOTES = {
    "core-families": "Inspect every angle of the heated vessel, counters and six distinct pads. Pads may share a family language, but their silhouettes/trim/icon sockets must remain distinguishable without HUD text.",
    "loop-families": "Inspect fishing, processing and defense fixtures from all six required angles. T05 supplies static visual foundations and sockets only; later fishing, conveyor, processing and firing behavior is explicitly outside this task.",
    "resources-and-details": "Inspect all reusable resource props, close details, camp/lakeshore arrangements and night/blizzard conditions. Judge authored finish, grounding, legibility and cross-view consistency, not future moving-stack behavior.",
    "shipping-device-and-tracking": "Inspect the exact integrated shipping call site across landscape phone/tablet/foldable and tracking/target states. Grade T05 station visibility, scale, contact and obstruction only; T04 camera behavior is already approved.",
    "shipping-contexts-and-native": "Inspect normal camp/lakeshore/gate use, day/night/blizzard and all three 3840x2160 scale-1 frames. Preserve T01-T04; report only defects caused by T05 assets or placement.",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


provenance = json.loads((ROOT / "provenance.json").read_text())
tests = json.loads((ROOT / "tests.json").read_text())
component = json.loads((ROOT / "component/capture.json").read_text())
families = json.loads((ROOT / "families/capture.json").read_text())
gameplay = json.loads((ROOT / "gameplay/capture.json").read_text())
native = json.loads((ROOT / "native4k/capture.json").read_text())
assert provenance["source"] == tests["source"] == SOURCE
assert provenance["actual_images"] == 77
assert provenance["family_view_contract_complete"] is True
assert provenance["shipping_main_call_site_exercised"] is True
assert provenance["cheap_pixel_gate_passed"] is True
assert provenance["cheap_performance_gate_passed"] is True
assert tests["all_passed"] is True and tests["suite_count"] == 18 and tests["total_checks"] >= 1117
assert component["task"] == families["task"] == "T05-station-kit-v1"
assert len(component["captures"]) == 12 and len(families["captures"]) == 42
assert gameplay["shipping_main_call_site_exercised"] is True
assert native["shipping_main_call_site_exercised"] is True
assert len(gameplay["captures"]) == 20 and len(native["captures"]) == 3
for name, expected in provenance["captures"].items():
    assert digest(ROOT / name) == expected, "changed evidence " + name

all_review_files = [name for names in FILES.values() for name in names]
assert len(all_review_files) == 77
assert len(set(all_review_files)) == 77
assert set(all_review_files) == set(provenance["captures"])

reference = ROOT / "reference-ground.webp"
assert digest(reference) == "3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb"


def validate_reference_coverage() -> tuple[bool, str | None, dict[str, list[Path]]]:
    """Require actual authoritative pixels for every T05 family before C1 can pass."""
    coverage_path = ROOT / "reference/coverage.json"
    if not coverage_path.is_file():
        return False, "missing reference/coverage.json with family-complete authoritative video frames", {}
    try:
        coverage = json.loads(coverage_path.read_text())
        required = {"hearth", "counters", "pads", "fishing", "processing", "defense", "resources"}
        locked_path = Path("Docs/Design/ReferenceVideoLock/reference-video-sources.json")
        locked = json.loads(locked_path.read_text())
        if coverage.get("source_manifest_sha256") != digest(locked_path):
            return False, "reference coverage is not bound to the locked source manifest", {}
        locked_sources = {source["id"]: source for source in locked["sources"]}
        extraction_path = ROOT / "reference/extraction-report.json"
        if not extraction_path.is_file() or coverage.get("extraction_report_sha256") != digest(extraction_path):
            return False, "reference coverage lacks its checksum-bound extraction report", {}
        extraction = json.loads(extraction_path.read_text())
        if extraction.get("source_manifest_sha256") != digest(locked_path) or extraction.get("extracted_sample_count") != 44:
            return False, "reference extraction report is not the complete locked 44-frame set", {}
        if {row.get("id"): row.get("sha256") for row in extraction.get("sources", [])} != {key: value["sha256"] for key, value in locked_sources.items()}:
            return False, "reference extraction report source hashes do not match the lock", {}
        expected_extractions = {
            (source_id, timestamp)
            for source_id, source in locked_sources.items()
            for timestamp in source["selected_seek_seconds"]
        }
        extracted = {(row.get("source"), row.get("requested_seek_seconds")): row for row in extraction.get("samples", [])}
        if len(extraction.get("samples", [])) != len(expected_extractions) or set(extracted) != expected_extractions:
            return False, "reference extraction report does not contain the exact locked source/timestamp set", {}
        items = coverage.get("items", [])
        present = {item.get("family") for item in items}
        if coverage.get("authoritative_user_video_pixels") is not True or present != required:
            return False, "authoritative reference pixels do not cover every T05 station/prop family", {}
        paths: dict[str, list[Path]] = {}
        identities = set()
        relative_paths = set()
        pixel_hashes = set()
        for item in items:
            source = locked_sources.get(item.get("source_id"))
            timestamp = item.get("seek_seconds")
            identity = (item.get("source_id"), timestamp)
            if source is None or item.get("source_video_sha256") != source["sha256"] or timestamp not in source["selected_seek_seconds"]:
                return False, "reference frame lacks original-video hash/timestamp provenance", {}
            sample = extracted.get(identity)
            if sample is None or sample.get("filename") != Path(item.get("path", "")).name or sample.get("extracted_png_sha256") != item.get("sha256"):
                return False, "reference frame is not bound to its locked-video extraction record", {}
            if identity in identities or item.get("path") in relative_paths or item.get("sha256") in pixel_hashes:
                return False, "reference families must use unique locked frames, paths and pixel hashes", {}
            identities.add(identity)
            relative_paths.add(item.get("path"))
            pixel_hashes.add(item.get("sha256"))
            path = ROOT / item["path"]
            if not path.is_file() or digest(path) != item.get("sha256"):
                return False, "reference coverage contains a missing or changed frame: " + item.get("path", "<unknown>"), {}
            with Image.open(path) as frame:
                if frame.size != (source["width"], source["height"]):
                    return False, "reference coverage frame is not an original-resolution locked frame", {}
                frame.verify()
            paths.setdefault(item["family"], []).append(path)
        return True, None, paths
    except Exception as error:
        return False, "invalid reference coverage manifest: " + str(error), {}


reference_scope_complete, reference_scope_error, reference_frames = validate_reference_coverage()
if ROLE == "C1" and not reference_scope_complete:
    blocked = {
        "task": "T05", "source": SOURCE, "candidate_hash": SOURCE,
        "critic_id": ROLE, "attempt": ATTEMPT, "groups": GROUPS, "reviews": [],
        "competency_passed": False, "error": reference_scope_error, "passed": False,
        "reference_scope_complete": False, "reference_scope_error": reference_scope_error,
        "independent_runtime": False, "strict_rule": ">9.0 unrounded",
        "task_approved": False, "physical_4k60_verified": False,
    }
    (OUT / "review-result.json").write_text(json.dumps(blocked, indent=2) + "\n")
    (OUT / "provenance.json").write_text(json.dumps({
        "source": SOURCE, "critic_id": ROLE, "attempt": ATTEMPT, "seed": SEED,
        "evidence_provenance_sha256": digest(ROOT / "provenance.json"),
        "reference_sha256": digest(reference), "blocked_before_inference": True,
        "blocker": reference_scope_error,
    }, indent=2) + "\n")
    print(json.dumps(blocked), flush=True)
    raise SystemExit(2)
manifest = json.loads((CACHE / "manifest.json").read_text())
assert manifest["publisher"] == "unsloth/Qwen3.5-9B-GGUF"
assert manifest["base_model"] == "Qwen/Qwen3.5-9B"
for item in manifest["files"]:
    assert digest(CACHE / item["filename"]) == item["sha256"], "bad reviewer runtime bytes"
servers = list((CACHE / "runtime").rglob("llama-server"))
assert len(servers) == 1
server = servers[0]


def build_probe() -> Path:
    ref = Image.open(reference).convert("RGB")
    left = ref.crop((0, 0, ref.width // 2, ref.height))
    right = ref.crop((ref.width // 2, 0, ref.width, ref.height))
    specs = [
        ("A", left, True),
        ("B", right, False),
        ("C", Image.open(ROOT / "component/close-fishing-side.png").convert("RGB"), True),
        ("D", Image.open(ROOT / "component/close-hearth-front.png").convert("RGB"), False),
    ]
    board = Image.new("RGB", (960, 960), (20, 29, 38))
    draw = ImageDraw.Draw(board)
    sources = []
    for index, (label, source, expected) in enumerate(specs):
        source.thumbnail((450, 410), Image.Resampling.LANCZOS)
        x = (index % 2) * 480 + (480 - source.width) // 2
        y = (index // 2) * 480 + 45 + (410 - source.height) // 2
        board.paste(source, (x, y))
        draw.text(((index % 2) * 480 + 16, (index // 2) * 480 + 12), label, fill="white")
        sources.append({"panel": label, "expected": expected})
    path = OUT / "blind-competency.jpg"
    board.save(path, quality=94)
    (OUT / "competency-sources.json").write_text(json.dumps(sources, indent=2))
    return path


def build_boards(group: str) -> tuple[list[Path], Path]:
    """Build small review boards without shrinking authoritative pixels into a contact sheet."""
    group_families = {
        "core-families": ("hearth", "counters", "pads"),
        "loop-families": ("fishing", "processing", "defense"),
        "resources-and-details": ("resources", "hearth", "counters", "fishing", "processing", "defense"),
        "shipping-device-and-tracking": ("hearth", "counters", "pads", "fishing", "processing", "defense", "resources"),
        "shipping-contexts-and-native": ("hearth", "counters", "pads", "fishing", "processing", "defense", "resources"),
    }[group]
    refs: list[tuple[str, Path]] = []
    if reference_scope_complete:
        for family in group_families:
            for path in reference_frames.get(family, []):
                refs.append(("REFERENCE " + family + ": " + path.name, path))
    else:
        refs.append(("LIMITED REFERENCE — fishing/hearth only", reference))

    candidates = FILES[group]
    slice_count = max(math.ceil(len(candidates) / 2), len(refs))
    boards: list[Path] = []
    board_rows = []
    for index in range(slice_count):
        start = index * len(candidates) // slice_count
        end = (index + 1) * len(candidates) // slice_count
        candidate_names = candidates[start:end]
        ref_label, ref_path = refs[index % len(refs)]

        board = Image.new("RGB", (1600, 1200), (20, 29, 38))
        draw = ImageDraw.Draw(board)
        draw.text((18, 14), f"T05 {group} — slice {index + 1}/{slice_count}", fill="white")
        draw.text((18, 40), ref_label, fill="white")
        ref_image = Image.open(ref_path).convert("RGB")
        ref_image.thumbnail((420, 1080), Image.Resampling.LANCZOS)
        ref_position = (18 + (420 - ref_image.width) // 2, 78 + (1080 - ref_image.height) // 2)
        board.paste(ref_image, ref_position)

        candidate_rows = []
        cell_height = 550 if len(candidate_names) == 2 else 1100
        for candidate_index, name in enumerate(candidate_names):
            y0 = 58 + candidate_index * cell_height
            draw.text((468, y0), "SOURCE-BOUND CANDIDATE: " + name, fill="white")
            candidate = Image.open(ROOT / name).convert("RGB")
            candidate.thumbnail((1120, cell_height - 42), Image.Resampling.LANCZOS)
            position = (468 + (1120 - candidate.width) // 2, y0 + 32 + (cell_height - 42 - candidate.height) // 2)
            board.paste(candidate, position)
            candidate_rows.append({"path": name, "display_size": list(candidate.size), "position": list(position)})

        path = OUT / f"{group}-board-{index + 1:02d}.jpg"
        board.save(path, quality=95, subsampling=0)
        boards.append(path)
        board_rows.append({
            "path": path.name, "sha256": digest(path), "canvas_size": list(board.size),
            "reference_path": str(ref_path.relative_to(ROOT)),
            "reference_display_size": list(ref_image.size), "reference_position": list(ref_position),
            "candidates": candidate_rows,
        })

    manifest = OUT / f"{group}-board-manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": 2, "task": "T05", "source": SOURCE, "group": group,
        "layout_contract": {
            "canvas_size": [1600, 1200], "maximum_model_input": [1664, 1664],
            "minimum_reference_display_width": 420, "minimum_candidate_display_height": 480,
            "maximum_candidates_per_board": 2, "all_group_candidates_present_once": True,
            "all_group_references_present_at_least_once": True,
        },
        "slices": board_rows,
    }, indent=2, sort_keys=True) + "\n")
    return boards, manifest


def query(image_path: Path, prompt: str, schema: dict, name: str, max_tokens: int) -> tuple[dict, float]:
    image = Image.open(image_path).convert("RGB")
    original = image.size
    image.thumbnail((1664, 1664), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    payload = buffer.getvalue()
    request = {
        "model": "T05-" + ROLE + "-" + ATTEMPT,
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
        "source_image_path": image_path.name, "source_image_sha256": digest(image_path),
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


def write_input_manifest(group: str, board_manifest: Path) -> tuple[str, str]:
    candidate_inputs = {name: digest(ROOT / name) for name in FILES[group]}
    board_payload = json.loads(board_manifest.read_text())
    reference_names = {row["reference_path"] for row in board_payload["slices"]}
    reference_inputs = {name: digest(ROOT / name) for name in sorted(reference_names)}
    payload = {
        "candidate_commit": SOURCE,
        "critic_id": ROLE,
        "attempt": ATTEMPT,
        "seed": SEED,
        "group": group,
        "evidence_provenance_sha256": digest(ROOT / "provenance.json"),
        "reference_sha256": digest(reference), "board_sha256": digest(board_manifest),
        "inputs": candidate_inputs,
        "pixel_manifest": {
            "candidate_inputs": candidate_inputs,
            "reference_inputs": reference_inputs,
            "reference_coverage_sha256": digest(ROOT / "reference/coverage.json") if reference_scope_complete else None,
            "reference_extraction_sha256": digest(ROOT / "reference/extraction-report.json") if reference_scope_complete else None,
            "board_sha256": digest(board_manifest),
            "board_inputs": {
                row["path"]: row["sha256"]
                for row in board_payload["slices"]
            },
        },
    }
    path = OUT / (group + "-input-manifest.json")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path.name, digest(path)


role_prompt = {
    "C1": "Judge reference fidelity, bright polished sculpted Havenline visual language, normal-scale readability and consistency across all supplied views.",
    "C2": "Judge grounding/contact, clipping, seams, sockets/bounds implied by visible construction, deliberate openings versus defects and cross-view technical integrity.",
}[ROLE]
base_prompt = f"""You are an independent visual critic reviewing only Havenline Task T05: the production station and prop kit at exact integrated source {SOURCE}. Each board presents one large checksum-bound frame from the authoritative user recordings beside no more than two labelled exact source-bound candidate renders. T05 is a static authored visual/socket foundation. Fishing, processing, conveyor motion, customer service, payments, combat, upgrades, actors and animations are later tasks and MUST NOT be scored as missing T05 behavior. Preserve approved T01-T04 environment and camera. Judge only T05 assets and their integration: heated vessel; counters; build/upgrade/input/output/stock/payment pads; fishing fixtures; intake/cooker/conveyor fixtures; defense platform; wood/stone/metal/fuel/fish/cooked-food/money/crate props; coherent blue/orange/yellow timber/metal snow-aware art; stable readable silhouettes; grounding; route/camera compatibility. Primitive-looking unfinished art, default/debug materials, visible penetrations, floating contact, broken silhouettes, indistinguishable pad variants or inconsistent cross-views are defects. {role_prompt} Inspect every labelled panel. Every mandatory score is 0-10. PASS requires each score strictly above 9.0 unrounded, zero defects, complete coverage and medium/high confidence. Do not average, round, or excuse a visible defect. Return JSON only."""

score_properties = {name: {"type": "number", "minimum": 0, "maximum": 10} for name in DIMS[ROLE]}
schema = {
    "type": "object",
    "properties": {
        "observations": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 6},
        "defects": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
        "coverage_complete": {"type": "boolean"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "scores": {"type": "object", "properties": score_properties, "required": DIMS[ROLE], "additionalProperties": False},
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
        "properties": {key: {"type": "boolean"} for key in "ABCD"},
        "required": list("ABCD"), "additionalProperties": False,
    }
    answers, elapsed = query(
        build_probe(),
        "Four panels are labelled A-D. For each panel, return true if the image visibly contains at least three long, thin, roughly parallel yellow poles. Return false when it instead shows a large round station or vessel without three yellow poles. Return only the JSON object.",
        probe_schema, "competency", 180,
    )
    expected = {"A": True, "B": False, "C": True, "D": False}
    competent = answers == expected
    (OUT / "competency.json").write_text(json.dumps({"answers": answers, "expected": expected, "passed": competent, "elapsed_seconds": elapsed}, indent=2))
    assert competent, "blind image competency failed; do not grade"

    for group in GROUPS:
        boards, board_manifest = build_boards(group)
        raw_path = OUT / (group + "-raw-bundle.json")
        input_manifest_path, input_manifest_hash = write_input_manifest(group, board_manifest)
        row = {
            "task": "T05", "source": SOURCE, "candidate_hash": SOURCE,
            "critic_id": ROLE, "group": group, "attempt": ATTEMPT, "seed": SEED,
            "provider": "local-checksum-pinned-public-model", "model": manifest["base_model"],
            "model_revision": manifest["revision"], "runtime_release_sha256": digest(server),
            "request_or_run_id": ":".join((RUN_ID, RUN_ATTEMPT, RUN_JOB, ROLE, ATTEMPT, group)),
            "input_manifest_path": input_manifest_path, "input_manifest_hash": input_manifest_hash,
            "board_path": board_manifest.name,
            "independent_execution": False, "passed": False,
            "reference_scope_complete": reference_scope_complete if ROLE == "C1" else True,
            "reference_scope_error": reference_scope_error if ROLE == "C1" else None,
        }
        try:
            slice_reviews = []
            for slice_index, board in enumerate(boards, 1):
                name = f"{group}-slice-{slice_index:02d}"
                review, elapsed = query(
                    board,
                    base_prompt + f"\nCurrent evidence group: {group}; board slice {slice_index}/{len(boards)}. "
                    + NOTES[group] + " Grade every candidate panel on this slice against the large authoritative reference panel.",
                    schema, name, 760,
                )
                slice_reviews.append({
                    "slice": slice_index, "board_path": board.name, "board_sha256": digest(board),
                    "raw_output_path": name + "-raw.json", "raw_output_sha256": digest(OUT / (name + "-raw.json")),
                    "request_path": name + "-request.json", "request_sha256": digest(OUT / (name + "-request.json")),
                    "answer_path": name + "-answer.json", "answer_sha256": digest(OUT / (name + "-answer.json")),
                    "elapsed_seconds": elapsed, "review": review,
                })
            confidence_order = {"low": 0, "medium": 1, "high": 2}
            review = {
                "observations": list(dict.fromkeys(item for part in slice_reviews for item in part["review"]["observations"])),
                "defects": list(dict.fromkeys(item for part in slice_reviews for item in part["review"]["defects"])),
                "coverage_complete": all(part["review"]["coverage_complete"] is True for part in slice_reviews),
                "confidence": min((part["review"]["confidence"] for part in slice_reviews), key=confidence_order.get),
                "scores": {dimension: min(part["review"]["scores"][dimension] for part in slice_reviews) for dimension in DIMS[ROLE]},
            }
            elapsed = round(sum(part["elapsed_seconds"] for part in slice_reviews), 3)
            raw_path.write_text(json.dumps({
                "schema_version": 2, "task": "T05", "source": SOURCE, "critic_id": ROLE,
                "attempt": ATTEMPT, "seed": SEED, "group": group,
                "aggregation": "minimum score; union defects; all slices require coverage; lowest confidence",
                "slices": slice_reviews, "aggregate_review": review,
            }, indent=2, sort_keys=True) + "\n")
            scores = review["scores"]
            assert set(scores) == set(DIMS[ROLE])
            assert all(not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 10 for value in scores.values())
            assert isinstance(review["defects"], list) and isinstance(review["coverage_complete"], bool)
            row.update({
                "independent_execution": True, "review": review, "minimum": min(scores.values()),
                "elapsed_seconds": elapsed, "board_sha256": digest(board_manifest),
                "raw_output_path": raw_path.name, "raw_output_sha256": digest(raw_path), "error": None,
            })
            row["passed"] = (
                row["minimum"] > 9.0 and review["defects"] == []
                and review["coverage_complete"] is True and review["confidence"] in ("medium", "high")
                and row["reference_scope_complete"] is True
            )
        except Exception as error:
            row["error"] = str(error)
        rows.append(row)
        (OUT / (group + "-review.json")).write_text(json.dumps(row, indent=2))
        print(json.dumps(row), flush=True)
except Exception as error:
    failure = str(error)
finally:
    result = {
        "task": "T05", "source": SOURCE, "critic_id": ROLE, "attempt": ATTEMPT,
        "groups": GROUPS, "reviews": rows, "competency_passed": competent,
        "error": failure, "passed": competent and failure is None and len(rows) == len(GROUPS) and all(row["passed"] for row in rows),
        "provider": "local-checksum-pinned-public-model", "model": manifest["base_model"],
        "model_revision": manifest["revision"], "runtime_release_sha256": digest(server),
        "request_or_run_id": ":".join((RUN_ID, RUN_ATTEMPT, RUN_JOB, ROLE, ATTEMPT)),
        "candidate_hash": SOURCE, "independent_runtime": True,
        "reference_scope_complete": reference_scope_complete if ROLE == "C1" else True,
        "reference_scope_error": reference_scope_error if ROLE == "C1" else None,
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
