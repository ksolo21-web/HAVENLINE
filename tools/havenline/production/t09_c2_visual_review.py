#!/usr/bin/env python3
"""Independent exact-source C2 visual review for T09 harvesting evidence.

This runs only in a separate review job. It never edits the candidate, retries a
completed low judgment, or averages away a failed resource/view group. Final
C2 dimension scores are the minimum applicable raw score across all reviewed
boards, and any visual defect is blocking.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SOURCE = os.environ["EXPECTED_SOURCE"]
ROOT = Path(os.environ.get("EVIDENCE_ROOT", "task09-evidence"))
OUT = Path(os.environ.get("REVIEW_OUTPUT", "t09-c2-review"))
CACHE = Path.home() / ".cache/havenline-t01-qwen35"
SEED = int(os.environ.get("REVIEW_SEED", "20260992"))
TIMEOUT = int(os.environ.get("REVIEW_TIMEOUT_SECONDS", "1200"))
VIEWS = ["front", "front-right", "right", "rear-right", "rear", "rear-left", "left", "front-left", "overhead", "detail"]
RESOURCES = ["wood", "stone", "fuel"]
DIMS = ["geometry_contact", "clipping_seams", "intentional_gap_integrity", "cross_view_integrity"]
OUT.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def evidence(path: str) -> Path:
    p = ROOT / path
    if not p.is_file():
        raise SystemExit("missing exact-source evidence: " + path)
    return p


def validate_source() -> None:
    assert len(SOURCE) == 40
    summary = json.loads(evidence("capture-summary.json").read_text())
    tests = json.loads(evidence("tests.json").read_text())
    manifest = json.loads(evidence("candidate-manifest.json").read_text())
    assert summary["candidate"] == tests["source"] == manifest["candidate_commit"] == SOURCE
    assert summary["reports"] == 71 and summary["in_hand_views"] == 30 and summary["isolated_tool_turntables"] == 30
    assert tests["all_passed"] is True
    for resource in RESOURCES:
        for view in VIEWS:
            evidence(f"captures/tool-{resource}-{view}/tool-{resource}-{view}.png")
            report = json.loads(evidence(f"captures/tool-{resource}-{view}/capture-report.json").read_text())
            assert report["candidate"] == SOURCE and report["mode"] == "tool"
            final = report["final_harvest"]
            assert final["contact_alignment_valid"] is True
            assert final["grip_error_m"] <= 0.025 and final["impact_error_m"] <= 0.025 and final["secondary_grip_error_m"] <= 0.045
    for resource in ("wood", "stone", "metal", "fuel"):
        evidence(f"captures/sequence-{resource}/{resource}-committed-contact.png")


def fit(source: Image.Image, box: tuple[int, int]) -> Image.Image:
    image = source.copy().convert("RGB")
    image.thumbnail(box, Image.Resampling.LANCZOS)
    return image


def make_board(resource: str) -> Path:
    board = Image.new("RGB", (1664, 1200), (20, 28, 38))
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default(size=19)
    title = ImageFont.load_default(size=24)
    draw.text((18, 12), f"T09 C2 exact-source in-hand review — {resource}", fill="white", font=title)
    cell_w, cell_h = 328, 545
    for index, view in enumerate(VIEWS):
        row, col = divmod(index, 5)
        x, y = 12 + col * cell_w, 54 + row * cell_h
        draw.text((x + 4, y), view, fill="white", font=font)
        source = Image.open(evidence(f"captures/tool-{resource}-{view}/tool-{resource}-{view}.png"))
        image = fit(source, (cell_w - 16, cell_h - 38))
        board.paste(image, (x + (cell_w - image.width) // 2, y + 28 + (cell_h - 38 - image.height) // 2))
    path = OUT / f"board-{resource}.jpg"
    board.save(path, quality=95, subsampling=0)
    return path


def make_contact_board() -> Path:
    board = Image.new("RGB", (1664, 1050), (20, 28, 38))
    draw = ImageDraw.Draw(board)
    title = ImageFont.load_default(size=24)
    font = ImageFont.load_default(size=20)
    draw.text((18, 12), "T09 C2 authoritative committed-contact review", fill="white", font=title)
    for index, resource in enumerate(("wood", "stone", "metal", "fuel")):
        row, col = divmod(index, 2)
        x, y = 16 + col * 816, 60 + row * 485
        draw.text((x, y), resource, fill="white", font=font)
        source = Image.open(evidence(f"captures/sequence-{resource}/{resource}-committed-contact.png"))
        image = fit(source, (790, 440))
        board.paste(image, (x + (790 - image.width) // 2, y + 28 + (440 - image.height) // 2))
    path = OUT / "board-committed-contact.jpg"
    board.save(path, quality=95, subsampling=0)
    return path


def make_probe() -> Path:
    specs = [
        ("A", evidence("captures/tool-wood-front/tool-wood-front.png"), True),
        ("B", evidence("captures/asset-wood-front/asset-axe-front.png"), False),
        ("C", evidence("captures/tool-fuel-front/tool-fuel-front.png"), True),
        ("D", evidence("captures/asset-fuel-front/asset-salvage_pry_tool-front.png"), False),
    ]
    board = Image.new("RGB", (960, 960), (20, 28, 38))
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default(size=28)
    for i, (label, path, _) in enumerate(specs):
        row, col = divmod(i, 2)
        image = fit(Image.open(path), (450, 405))
        x, y = col * 480 + (480 - image.width) // 2, row * 480 + 50 + (405 - image.height) // 2
        board.paste(image, (x, y))
        draw.text((col * 480 + 16, row * 480 + 12), label, fill="white", font=font)
    path = OUT / "blind-vision-probe.jpg"
    board.save(path, quality=94)
    (OUT / "blind-vision-expected.json").write_text(json.dumps({k: v for k, _, v in specs}, indent=2) + "\n")
    return path


def model_runtime() -> tuple[dict, Path]:
    manifest = json.loads((CACHE / "manifest.json").read_text())
    assert manifest["publisher"] == "unsloth/Qwen3.5-9B-GGUF"
    assert manifest["base_model"] == "Qwen/Qwen3.5-9B"
    for item in manifest["files"]:
        assert sha256(CACHE / item["filename"]) == item["sha256"]
    servers = list((CACHE / "runtime").rglob("llama-server"))
    assert len(servers) == 1
    return manifest, servers[0]


def request_image(path: Path, prompt: str, schema: dict, name: str, seed: int) -> tuple[dict, dict]:
    image = Image.open(path).convert("RGB")
    image.thumbnail((1664, 1664), Image.Resampling.LANCZOS)
    buffer = io.BytesIO(); image.save(buffer, format="JPEG", quality=92)
    payload = {
        "model": "T09-C2-independent",
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()}},
            {"type": "text", "text": prompt},
        ]}],
        "max_tokens": 1200,
        "temperature": 0.15,
        "top_p": 0.9,
        "seed": seed,
        "repeat_penalty": 1.12,
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": {"type": "json_object", "schema": schema},
        "cache_prompt": False,
    }
    request_path = OUT / f"{name}-request.json"
    request_path.write_text(json.dumps({"seed": seed, "prompt": prompt, "schema": schema, "source_image": path.name, "source_image_sha256": sha256(path)}, indent=2) + "\n")
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        raw = response.read()
    raw_path = OUT / f"{name}-raw.json"; raw_path.write_bytes(raw)
    envelope = json.loads(raw)
    content = envelope["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    answer_path = OUT / f"{name}-answer.json"; answer_path.write_text(json.dumps(parsed, indent=2) + "\n")
    return parsed, {"request": request_path.name, "request_sha256": sha256(request_path), "raw": raw_path.name, "raw_sha256": sha256(raw_path), "answer": answer_path.name, "answer_sha256": sha256(answer_path)}


def group_schema(dimensions: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "scores": {"type": "object", "properties": {d: {"type": "number", "minimum": 0, "maximum": 10} for d in dimensions}, "required": dimensions, "additionalProperties": False},
            "defects": {"type": "array", "items": {"type": "string"}},
            "coverage_complete": {"type": "boolean"},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "summary": {"type": "string"},
        },
        "required": ["scores", "defects", "coverage_complete", "confidence", "summary"],
        "additionalProperties": False,
    }


def prompt(group: str, dimensions: list[str]) -> str:
    rubric = {
        "geometry_contact": "Hands must visibly seat on the authored grip(s); tool head/contact end must align convincingly with the source at committed contact. No hovering, buried head, or visibly unreachable grip.",
        "clipping_seams": "Reject any visible tool-through-head/torso/limb/source clipping, broken limb/tool intersection, or obvious mesh seam/opening caused by the interaction.",
        "intentional_gap_integrity": "Hand spacing, handle spacing, tool-to-source offset, and any visible gap must look intentional and physically plausible, not like detached hands or floating contact.",
        "cross_view_integrity": "Across the shown meaningful angles, the same grip/contact configuration must remain coherent; a clean front view cannot hide a broken side/rear/detail view.",
    }
    return (
        f"You are independent Havenline critic C2 reviewing exact-source T09 harvesting pixels for {group}. "
        "Judge only what is visible. This is a strict production gate, not a style preference exercise. "
        "A score of 9.0 does NOT pass; release requires every applicable raw dimension strictly above 9.0 and zero defects. "
        "Do not average away one bad angle. If any shown view has a real contact/clipping/gap defect, list it and score the affected dimension accordingly. "
        "Do not invent problems outside the shown evidence. " + " ".join(f"{d}: {rubric[d]}" for d in dimensions) +
        " Return only the requested JSON object."
    )


def main() -> None:
    validate_source()
    manifest, server = model_runtime()
    input_paths = []
    for resource in RESOURCES:
        input_paths.extend(evidence(f"captures/tool-{resource}-{view}/tool-{resource}-{view}.png") for view in VIEWS)
    input_paths.extend(evidence(f"captures/sequence-{r}/{r}-committed-contact.png") for r in ("wood", "stone", "metal", "fuel"))
    input_manifest = {"task": "T09", "candidate": SOURCE, "critic_id": "C2", "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in input_paths}}
    manifest_path = OUT / "input-manifest.json"; manifest_path.write_text(json.dumps(input_manifest, indent=2, sort_keys=True) + "\n")

    environment = dict(os.environ)
    environment["LD_LIBRARY_PATH"] = str(server.parent) + ":" + environment.get("LD_LIBRARY_PATH", "")
    log = (OUT / "inference.log").open("w")
    command = [str(server), "-m", str(CACHE / manifest["model_file"]), "--mmproj", str(CACHE / manifest["projector_file"]), "--host", "127.0.0.1", "--port", "8080", "-c", "8192", "-t", "4", "-tb", "4", "-ngl", "0", "--no-mmproj-offload", "--parallel", "1", "--jinja", "--image-min-tokens", "1024", "--image-max-tokens", "2048"]
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=environment)
    raw_index = []
    judgments = []
    try:
        for _ in range(150):
            if process.poll() is not None: raise RuntimeError("independent reviewer runtime exited")
            try:
                if json.load(urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=3)).get("status") == "ok": break
            except Exception: pass
            time.sleep(2)
        else: raise RuntimeError("independent reviewer runtime not ready")

        probe_schema = {"type": "object", "properties": {k: {"type": "boolean"} for k in "ABCD"}, "required": list("ABCD"), "additionalProperties": False}
        probe, files = request_image(make_probe(), "Panels A-D are shown. For each panel return true only if a visible human character is present; return false when the panel shows only the isolated tool/asset without a human. Return only JSON.", probe_schema, "competency", SEED)
        expected = json.loads((OUT / "blind-vision-expected.json").read_text())
        assert probe == expected, (probe, expected)
        raw_index.append({"group": "competency", **files})

        for offset, resource in enumerate(RESOURCES):
            dims = DIMS
            result, files = request_image(make_board(resource), prompt(resource, dims), group_schema(dims), f"review-{resource}", SEED + 101 * (offset + 1))
            assert set(result["scores"]) == set(dims)
            judgments.append({"group": resource, "dimensions": dims, **result})
            raw_index.append({"group": resource, **files})

        contact_dims = DIMS[:3]
        result, files = request_image(make_contact_board(), prompt("authoritative committed-contact states", contact_dims), group_schema(contact_dims), "review-committed-contact", SEED + 707)
        assert set(result["scores"]) == set(contact_dims)
        judgments.append({"group": "committed-contact", "dimensions": contact_dims, **result})
        raw_index.append({"group": "committed-contact", **files})
    finally:
        process.terminate()
        try: process.wait(timeout=15)
        except subprocess.TimeoutExpired: process.kill()
        log.close()

    final_scores = {dim: min(float(j["scores"][dim]) for j in judgments if dim in j["scores"]) for dim in DIMS}
    defects = [f"{j['group']}: {defect}" for j in judgments for defect in j.get("defects", [])]
    confidence_values = [j.get("confidence") for j in judgments]
    coverage = all(j.get("coverage_complete") is True for j in judgments)
    confidence = "high" if all(v == "high" for v in confidence_values) else ("medium" if all(v in ("medium", "high") for v in confidence_values) else "low")
    passed = coverage and confidence in ("medium", "high") and not defects and all(score > 9.0 for score in final_scores.values())
    raw_index_path = OUT / "raw-output-index.json"; raw_index_path.write_text(json.dumps({"candidate": SOURCE, "critic_id": "C2", "judgments": judgments, "files": raw_index}, indent=2) + "\n")
    record = {
        "critic_id": "C2", "provider": "local-checksum-pinned-public-model", "model": manifest["base_model"],
        "request_or_run_id": ":".join((os.environ.get("GITHUB_RUN_ID", "local"), os.environ.get("GITHUB_JOB", "local"), "T09-C2")),
        "candidate_hash": SOURCE, "input_manifest_hash": sha256(manifest_path),
        "raw_output_path": str(raw_index_path), "raw_output_hash": sha256(raw_index_path),
        "scores": final_scores, "defects": defects, "coverage_complete": coverage, "confidence": confidence,
        "independent_runtime": True, "task_approved": False, "passed": passed,
        "strict_rule": ">9.0 unrounded; zero unresolved defects; group minima, no averaging",
    }
    (OUT / "critic-record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
