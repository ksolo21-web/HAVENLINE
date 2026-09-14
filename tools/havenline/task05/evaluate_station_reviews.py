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
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from review_protocol import (
    BOARD_CANVAS_SIZE, CANDIDATE_PANEL_WIDTH, CANDIDATE_PANEL_X,
    FILES, GROUP_DISPLAY_NAMES, GROUP_FAMILIES, MAX_INVALID_RESPONSE_RETRIES,
    MIN_CANDIDATE_DISPLAY_HEIGHT, PROTOCOL, REFERENCE_FOCUS_BOXES,
    REFERENCE_PANEL_WIDTH, REFERENCE_PANEL_X, ROLE_DIMENSIONS,
    applicable_dimensions, build_review_prompt,
    build_review_schema, build_slice_contract, build_slice_plan, expected_request_settings,
    materialize_defect_summary, persist_model_response, review_exit_code, review_integrity_errors,
    slice_retry_seed, valid_slice_retry_seed, write_incomplete_group_bundle,
)


SOURCE = os.environ["EXPECTED_SOURCE"]
ROLE = os.environ["REVIEW_ROLE"]
ATTEMPT = os.environ.get("REVIEW_ATTEMPT", "primary")
SEED = int(os.environ.get("REVIEW_SEED", "20260951"))
ROOT = Path(os.environ.get("EVIDENCE_ROOT", "task05-evidence"))
OUT = Path(os.environ.get("REVIEW_OUTPUT", "task05-station-review"))
RESUME_ROOT = Path(os.environ["REVIEW_RESUME_ROOT"]) if os.environ.get("REVIEW_RESUME_ROOT") else None
RESUME_RUN_ID = os.environ.get("REVIEW_RESUME_RUN_ID")
CACHE = Path.home() / ".cache/havenline-t01-qwen35"
OUT.mkdir(parents=True, exist_ok=True)

assert len(SOURCE) == 40
assert ROLE in ("C1", "C2")
RUN_ID = os.environ.get("GITHUB_RUN_ID", "local")
RUN_ATTEMPT = os.environ.get("GITHUB_RUN_ATTEMPT", "0")
RUN_JOB = os.environ.get("GITHUB_JOB", "local")
TITLE_FONT = ImageFont.load_default(size=26)
LABEL_FONT = ImageFont.load_default(size=22)

DIMS = ROLE_DIMENSIONS

GROUPS = [name for name in os.environ.get("REVIEW_GROUPS", ",".join(FILES)).split(",") if name]
assert GROUPS and set(GROUPS) <= set(FILES)
SLICE_TIMEOUT_SECONDS = int(os.environ.get("REVIEW_SLICE_TIMEOUT_SECONDS", "900"))
assert 60 <= SLICE_TIMEOUT_SECONDS <= 1800

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
        draw.text(((index % 2) * 480 + 16, (index // 2) * 480 + 12), label, fill="white", font=TITLE_FONT)
        sources.append({"panel": label, "expected": expected})
    path = OUT / "blind-competency.jpg"
    board.save(path, quality=94)
    (OUT / "competency-sources.json").write_text(json.dumps(sources, indent=2))
    return path


def build_boards(group: str) -> tuple[list[Path], Path]:
    """Build protocol-v4 boards with local scope and checksum-bound reference focus."""
    reference_paths = {
        family: [str(path.relative_to(ROOT)) for path in reference_frames.get(family, [])]
        for family in GROUP_FAMILIES[group]
    }
    slice_plan = build_slice_plan(group, reference_paths)
    boards: list[Path] = []
    board_rows = []
    for index, scope in enumerate(slice_plan):
        candidate_names = scope["candidate_paths"]
        ref_path = ROOT / scope["reference_path"]
        family = scope["reference_family"]
        ref_label = "FOCUSED REFERENCE %s: %s" % (family, ref_path.name)

        board = Image.new("RGB", tuple(BOARD_CANVAS_SIZE), (20, 29, 38))
        draw = ImageDraw.Draw(board)
        draw.text((18, 10), f"T05 {GROUP_DISPLAY_NAMES[group]} — slice {index + 1}/{len(slice_plan)}", fill="white", font=TITLE_FONT)
        draw.text((18, 42), ref_label, fill="white", font=LABEL_FONT)
        ref_source = Image.open(ref_path).convert("RGB")
        crop_box = REFERENCE_FOCUS_BOXES[family]
        assert 0 <= crop_box[0] < crop_box[2] <= ref_source.width
        assert 0 <= crop_box[1] < crop_box[3] <= ref_source.height
        ref_source_artifact = OUT / f"reference-source-{family}.png"
        ref_source_artifact.write_bytes(ref_path.read_bytes())
        ref_focus_path = OUT / f"reference-focus-{family}.png"
        ref_source.crop(tuple(crop_box)).save(ref_focus_path)
        ref_image = Image.open(ref_focus_path).convert("RGB")
        ref_image.thumbnail((REFERENCE_PANEL_WIDTH, 1080), Image.Resampling.LANCZOS)
        ref_position = (
            REFERENCE_PANEL_X + (REFERENCE_PANEL_WIDTH - ref_image.width) // 2,
            78 + (1080 - ref_image.height) // 2,
        )
        board.paste(ref_image, ref_position)

        candidate_rows = []
        cell_height = 550 if len(candidate_names) == 2 else 1100
        for candidate_index, name in enumerate(candidate_names):
            y0 = 58 + candidate_index * cell_height
            draw.text((CANDIDATE_PANEL_X, y0), "SOURCE-BOUND CANDIDATE: " + name, fill="white", font=LABEL_FONT)
            candidate = Image.open(ROOT / name).convert("RGB")
            candidate.thumbnail((CANDIDATE_PANEL_WIDTH, cell_height - 42), Image.Resampling.LANCZOS)
            assert candidate.height >= MIN_CANDIDATE_DISPLAY_HEIGHT, f"candidate panel below strict resolution floor: {name}"
            position = (
                CANDIDATE_PANEL_X + (CANDIDATE_PANEL_WIDTH - candidate.width) // 2,
                y0 + 32 + (cell_height - 42 - candidate.height) // 2,
            )
            board.paste(candidate, position)
            candidate_rows.append({"path": name, "display_size": list(candidate.size), "position": list(position)})

        path = OUT / f"{group}-board-{index + 1:02d}.jpg"
        board.save(path, quality=95, subsampling=0)
        boards.append(path)
        board_rows.append({
            "path": path.name, "sha256": digest(path), "canvas_size": list(board.size),
            "reference_path": str(ref_path.relative_to(ROOT)),
            "reference_family": family,
            "reference_source_path": ref_source_artifact.name,
            "reference_source_sha256": digest(ref_source_artifact),
            "reference_focus_path": ref_focus_path.name,
            "reference_focus_sha256": digest(ref_focus_path),
            "reference_focus_crop_box": crop_box,
            "comparison_mode": scope["comparison_mode"],
            "unseen_assets_out_of_scope": True,
            "reviewed_candidate_paths": candidate_names,
            "reference_display_size": list(ref_image.size), "reference_position": list(ref_position),
            "candidates": candidate_rows,
        })

    manifest = OUT / f"{group}-board-manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": 4, "task": "T05", "source": SOURCE, "group": group,
        "protocol": PROTOCOL,
        "required_reference_families": list(GROUP_FAMILIES[group]),
        "reference_bindings": reference_paths,
        "layout_contract": {
            "canvas_size": BOARD_CANVAS_SIZE, "maximum_model_input": [1664, 1664],
            "minimum_reference_display_width": REFERENCE_PANEL_WIDTH,
            "minimum_candidate_display_height": MIN_CANDIDATE_DISPLAY_HEIGHT,
            "maximum_candidates_per_board": 2, "all_group_candidates_present_once": True,
            "all_required_reference_families_present_at_least_once": True,
            "coverage_complete_is_slice_local": True,
            "unlisted_assets_may_not_be_scored_as_missing": True,
        },
        "slices": board_rows,
    }, indent=2, sort_keys=True) + "\n")
    return boards, manifest


def query(
    image_path: Path, prompt: str, schema: dict, name: str, max_tokens: int,
    request_contract: dict | None = None, request_seed: int | None = None,
) -> tuple[dict, float]:
    request_seed = SEED if request_seed is None else request_seed
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
        "seed": request_seed,
        "repeat_penalty": 1.12,
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": {"type": "json_object", "schema": schema},
        "cache_prompt": False,
    }
    request_settings = {
        "model": request["model"], "max_tokens": max_tokens,
        "temperature": request["temperature"], "top_p": request["top_p"], "seed": request["seed"],
        "repeat_penalty": request["repeat_penalty"], "chat_template_kwargs": request["chat_template_kwargs"],
        "response_format_type": request["response_format"]["type"], "cache_prompt": request["cache_prompt"],
    }
    (OUT / (name + "-request.json")).write_text(json.dumps({
        "model": request["model"], "prompt": prompt, "schema": schema,
        "request_contract": request_contract, "request_settings": request_settings,
        "source_image_path": image_path.name, "source_image_sha256": digest(image_path),
        "image_sha256": hashlib.sha256(payload).hexdigest(),
        "original_size": original, "input_size": image.size, "seed": request_seed,
        "inference_timeout_seconds": SLICE_TIMEOUT_SECONDS,
    }, indent=2, default=list))
    began = time.monotonic()
    call = urllib.request.Request(
        "http://127.0.0.1:8080/v1/chat/completions",
        data=json.dumps(request).encode(), headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(call, timeout=SLICE_TIMEOUT_SECONDS) as response:
        raw_bytes = response.read()
    parsed = persist_model_response(
        raw_bytes, OUT / (name + "-raw.json"), OUT / (name + "-answer.json"), name,
    )
    return parsed, round(time.monotonic() - began, 3)


def load_resume_prefix(group: str, boards: list[Path], board_payload: dict) -> list[dict]:
    """Reuse only a fully bound, valid prefix from an incomplete prior group artifact."""
    if RESUME_ROOT is None:
        return []
    raw_path = RESUME_ROOT / (group + "-raw-bundle.json")
    if not raw_path.is_file():
        return []
    bundle = json.loads(raw_path.read_text())
    assert bundle.get("schema_version") == 4
    assert bundle.get("execution_complete") is False
    assert bundle.get("source") == SOURCE and bundle.get("critic_id") == ROLE
    assert bundle.get("attempt") == ATTEMPT and bundle.get("seed") == SEED
    assert bundle.get("group") == group
    resumed = []
    for expected_index, part in enumerate(bundle.get("slices", []), 1):
        assert expected_index <= len(boards)
        board = boards[expected_index - 1]
        scope = board_payload["slices"][expected_index - 1]
        assert part.get("slice") == expected_index
        assert part.get("board_path") == board.name and part.get("board_sha256") == digest(board)
        assert part.get("reviewed_candidate_paths") == scope["reviewed_candidate_paths"]
        assert part.get("reference_family") == scope["reference_family"]
        assert part.get("reference_path") == scope["reference_path"]
        review = part.get("review")
        assert isinstance(review, dict)
        assert review.get("reviewed_candidate_paths") == scope["reviewed_candidate_paths"]
        assert review.get("reference_path_used") == scope["reference_path"]
        assert review.get("unseen_assets_out_of_scope_acknowledged") is True
        assert not review_integrity_errors(review, ROLE, scope["reviewed_candidate_paths"])
        part_seed = part.get("seed", SEED)
        assert valid_slice_retry_seed(SEED, part_seed)
        request_contract = build_slice_contract(SOURCE, ROLE, ATTEMPT, group, expected_index, len(boards), scope)
        request_schema = build_review_schema(ROLE, scope["reviewed_candidate_paths"], scope["reference_path"])
        copied = dict(part)
        for path_key, hash_key in (
            ("raw_output_path", "raw_output_sha256"),
            ("request_path", "request_sha256"),
            ("answer_path", "answer_sha256"),
        ):
            name = part.get(path_key)
            assert isinstance(name, str) and Path(name).name == name
            source_path = RESUME_ROOT / name
            assert source_path.is_file() and digest(source_path) == part.get(hash_key)
            shutil.copy2(source_path, OUT / name)
        request = json.loads((OUT / part["request_path"]).read_text())
        assert request.get("request_contract") == request_contract
        assert request.get("schema") == request_schema
        assert request.get("prompt") == build_review_prompt(SOURCE, ROLE, request_contract)
        assert request.get("request_settings") == expected_request_settings(ROLE, ATTEMPT, part_seed)
        assert request.get("seed") == part_seed
        raw_response = json.loads((OUT / part["raw_output_path"]).read_text())
        assert raw_response["choices"][0].get("finish_reason") == "stop"
        assert json.loads(raw_response["choices"][0]["message"]["content"]) == json.loads((OUT / part["answer_path"]).read_text())
        copied["seed"] = part_seed
        copied["resumed_from_run_id"] = RESUME_RUN_ID
        resumed.append(copied)
    return resumed


def preserve_invalid_attempt(name: str, retry_index: int, request_seed: int, error: Exception) -> dict:
    """Retain every invalid non-vote response before a fresh-seed retry."""
    prefix = f"{name}-invalid-{retry_index + 1:02d}"
    record = {"retry_index": retry_index, "seed": request_seed, "error": str(error)}
    for path_key, suffix in (
        ("raw_output_path", "-raw.json"),
        ("request_path", "-request.json"),
        ("answer_path", "-answer.json"),
    ):
        source_path = OUT / (name + suffix)
        if source_path.is_file():
            preserved_path = OUT / (prefix + suffix)
            source_path.replace(preserved_path)
            record[path_key] = preserved_path.name
            record[path_key.replace("path", "sha256")] = digest(preserved_path)
    return record


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
            "reference_bindings": board_payload["reference_bindings"],
            "slice_scopes": {
                row["path"]: {
                    "reference_family": row["reference_family"],
                    "reference_path": row["reference_path"],
                    "candidate_paths": row["reviewed_candidate_paths"],
                    "comparison_mode": row["comparison_mode"],
                    "unseen_assets_out_of_scope": row["unseen_assets_out_of_scope"],
                    "reference_source_path": row["reference_source_path"],
                    "reference_source_sha256": row["reference_source_sha256"],
                    "reference_focus_path": row["reference_focus_path"],
                    "reference_focus_sha256": row["reference_focus_sha256"],
                    "reference_focus_crop_box": row["reference_focus_crop_box"],
                }
                for row in board_payload["slices"]
            },
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
            "board_path": board_manifest.name, "board_sha256": digest(board_manifest),
            "independent_execution": False, "execution_complete": False, "passed": False,
            "reference_scope_complete": reference_scope_complete if ROLE == "C1" else True,
            "reference_scope_error": reference_scope_error if ROLE == "C1" else None,
        }
        slice_reviews = []
        failed_slice = None
        try:
            board_payload = json.loads(board_manifest.read_text())
            slice_reviews = load_resume_prefix(group, boards, board_payload)
            for resumed_part in slice_reviews:
                print(json.dumps({
                    "event": "slice_resumed", "critic_id": ROLE, "group": group,
                    "slice": resumed_part["slice"], "slice_count": len(boards),
                    "resume_run_id": RESUME_RUN_ID,
                }), flush=True)
            for slice_index, board in enumerate(boards, 1):
                if slice_index <= len(slice_reviews):
                    continue
                name = f"{group}-slice-{slice_index:02d}"
                scope = board_payload["slices"][slice_index - 1]
                request_contract = build_slice_contract(SOURCE, ROLE, ATTEMPT, group, slice_index, len(boards), scope)
                slice_schema = build_review_schema(ROLE, scope["reviewed_candidate_paths"], scope["reference_path"])
                slice_prompt = build_review_prompt(SOURCE, ROLE, request_contract)
                print(json.dumps({
                    "event": "slice_started", "critic_id": ROLE, "group": group,
                    "slice": slice_index, "slice_count": len(boards),
                    "timeout_seconds": SLICE_TIMEOUT_SECONDS,
                }), flush=True)
                invalid_attempts = []
                elapsed = 0.0
                for retry_index in range(MAX_INVALID_RESPONSE_RETRIES + 1):
                    request_seed = slice_retry_seed(SEED, retry_index)
                    assert expected_request_settings(ROLE, ATTEMPT, request_seed)["max_tokens"] == 1150
                    attempt_began = time.monotonic()
                    try:
                        review, _attempt_elapsed = query(
                            board, slice_prompt, slice_schema, name, 1150, request_contract,
                            request_seed=request_seed,
                        )
                        review, defect_summary_derived = materialize_defect_summary(review)
                        assert review["reviewed_candidate_paths"] == scope["reviewed_candidate_paths"], "reviewed candidate path acknowledgment mismatch"
                        assert review["reference_path_used"] == scope["reference_path"], "reference path acknowledgment mismatch"
                        assert review["unseen_assets_out_of_scope_acknowledged"] is True, "unseen-asset scope was not acknowledged"
                        integrity_errors = review_integrity_errors(review, ROLE, scope["reviewed_candidate_paths"])
                        assert not integrity_errors, "; ".join(integrity_errors)
                        elapsed += time.monotonic() - attempt_began
                        break
                    except Exception as error:
                        elapsed += time.monotonic() - attempt_began
                        invalid_attempts.append(preserve_invalid_attempt(name, retry_index, request_seed, error))
                        if retry_index < MAX_INVALID_RESPONSE_RETRIES:
                            print(json.dumps({
                                "event": "slice_invalid_retry", "critic_id": ROLE, "group": group,
                                "slice": slice_index, "slice_count": len(boards),
                                "retry_index": retry_index + 1,
                                "next_seed": slice_retry_seed(SEED, retry_index + 1),
                                "error": str(error),
                            }), flush=True)
                            continue
                        failed_slice = {
                            "slice": slice_index, "board_path": board.name, "board_sha256": digest(board),
                            "reviewed_candidate_paths": scope["reviewed_candidate_paths"],
                            "reference_family": scope["reference_family"], "reference_path": scope["reference_path"],
                            "seed": request_seed, "invalid_attempts": invalid_attempts, "error": str(error),
                        }
                        print(json.dumps({
                            "event": "slice_failed", "critic_id": ROLE, "group": group,
                            "slice": slice_index, "slice_count": len(boards), "error": str(error),
                        }), flush=True)
                        raise
                elapsed = round(elapsed, 3)
                slice_reviews.append({
                    "slice": slice_index, "board_path": board.name, "board_sha256": digest(board),
                    "reviewed_candidate_paths": scope["reviewed_candidate_paths"],
                    "reference_family": scope["reference_family"], "reference_path": scope["reference_path"],
                    "seed": request_seed, "invalid_attempts": invalid_attempts,
                    "raw_output_path": name + "-raw.json", "raw_output_sha256": digest(OUT / (name + "-raw.json")),
                    "request_path": name + "-request.json", "request_sha256": digest(OUT / (name + "-request.json")),
                    "answer_path": name + "-answer.json", "answer_sha256": digest(OUT / (name + "-answer.json")),
                    "elapsed_seconds": elapsed, "defect_summary_derived": defect_summary_derived,
                    "review": review,
                })
                write_incomplete_group_bundle(
                    raw_path, source=SOURCE, role=ROLE, attempt=ATTEMPT, seed=SEED,
                    group=group, slices=slice_reviews, failed_slice=None,
                )
                print(json.dumps({
                    "event": "slice_completed", "critic_id": ROLE, "group": group,
                    "slice": slice_index, "slice_count": len(boards),
                    "elapsed_seconds": elapsed, "checkpoint_path": raw_path.name,
                    "defect_summary_derived": defect_summary_derived,
                }), flush=True)
            confidence_order = {"low": 0, "medium": 1, "high": 2}
            unique_defect_evidence = []
            seen_defect_evidence = set()
            for part in slice_reviews:
                for evidence in part["review"]["defect_evidence"]:
                    key = json.dumps(evidence, sort_keys=True)
                    if key not in seen_defect_evidence:
                        seen_defect_evidence.add(key)
                        unique_defect_evidence.append(evidence)
            review = {
                "observations": list(dict.fromkeys(item for part in slice_reviews for item in part["review"]["observations"])),
                "defects": [evidence["description"] for evidence in unique_defect_evidence],
                "defect_evidence": unique_defect_evidence,
                "coverage_complete": all(part["review"]["coverage_complete"] is True for part in slice_reviews),
                "confidence": min((part["review"]["confidence"] for part in slice_reviews), key=confidence_order.get),
                "scores": {
                    dimension: min(
                        part["review"]["scores"][dimension]
                        for part in slice_reviews if dimension in part["review"]["scores"]
                    )
                    for dimension in DIMS[ROLE]
                },
            }
            elapsed = round(sum(part["elapsed_seconds"] for part in slice_reviews), 3)
            raw_path.write_text(json.dumps({
                "schema_version": 4, "task": "T05", "source": SOURCE, "critic_id": ROLE,
                "attempt": ATTEMPT, "seed": SEED, "group": group,
                "aggregation": "minimum score; union defects; all slices require coverage; lowest confidence",
                "execution_complete": True, "slices": slice_reviews, "aggregate_review": review,
            }, indent=2, sort_keys=True) + "\n")
            scores = review["scores"]
            assert set(scores) == set(DIMS[ROLE])
            assert all(not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 10 for value in scores.values())
            assert isinstance(review["defects"], list) and isinstance(review["defect_evidence"], list)
            assert isinstance(review["coverage_complete"], bool)
            row.update({
                "independent_execution": True, "execution_complete": True,
                "review": review, "minimum": min(scores.values()),
                "elapsed_seconds": elapsed,
                "raw_output_path": raw_path.name, "raw_output_sha256": digest(raw_path), "error": None,
            })
            row["passed"] = (
                row["minimum"] > 9.0 and review["defects"] == []
                and review["coverage_complete"] is True and review["confidence"] in ("medium", "high")
                and row["reference_scope_complete"] is True
            )
        except Exception as error:
            row["error"] = str(error)
            write_incomplete_group_bundle(
                raw_path, source=SOURCE, role=ROLE, attempt=ATTEMPT, seed=SEED,
                group=group, slices=slice_reviews, failed_slice=failed_slice,
            )
            row.update({"raw_output_path": raw_path.name, "raw_output_sha256": digest(raw_path)})
        rows.append(row)
        (OUT / (group + "-review.json")).write_text(json.dumps(row, indent=2))
        print(json.dumps(row), flush=True)
except Exception as error:
    failure = str(error)
finally:
    incomplete_groups = [row.get("group") for row in rows if row.get("execution_complete") is not True or row.get("error") is not None]
    execution_complete = competent and failure is None and len(rows) == len(GROUPS) and not incomplete_groups
    result = {
        "task": "T05", "source": SOURCE, "critic_id": ROLE, "attempt": ATTEMPT,
        "groups": GROUPS, "reviews": rows, "competency_passed": competent,
        "error": failure, "execution_complete": execution_complete,
        "incomplete_groups": incomplete_groups,
        "passed": execution_complete and all(row["passed"] for row in rows),
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
        "slice_timeout_seconds": SLICE_TIMEOUT_SECONDS,
        "completed_low_scores_retried": False, "score_averaging": False,
    }, indent=2) + "\n")
    print(json.dumps(result), flush=True)
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
    log.close()
raise SystemExit(review_exit_code(result["execution_complete"]))
