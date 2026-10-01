#!/usr/bin/env python3
"""Retry incomplete visual output and adjudicate split evidence groups only."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image

from evaluate_visual_quorum import ROLES, classify, load_reviews


SOURCE = os.environ["EXPECTED_SOURCE"]
REVIEWS = Path(os.environ.get("REVIEWS_ROOT", "original-reviews"))
OUT = Path(os.environ.get("SUPPLEMENT_OUT", "supplemental-review"))
OUT.mkdir(parents=True, exist_ok=True)
CACHE = Path.home() / ".cache/havenline-t01-qwen35"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def artifact_dir(role: str, group: str) -> Path:
    found = []
    for path in REVIEWS.rglob("shard-review.json"):
        shard = json.loads(path.read_text())
        if shard.get("role") == role and any(row.get("group") == group for row in shard.get("reviews", [])):
            found.append(path.parent)
    assert len(found) == 1, (role, group, found)
    return found[0]


def image_request(path: Path) -> tuple[bytes, tuple[int, int]]:
    image = Image.open(path).convert("RGB")
    original = image.size
    image.thumbnail((1664, 1664), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue(), original


manifest = json.loads((CACHE / "manifest.json").read_text())
assert manifest["publisher"] == "unsloth/Qwen3.5-9B-GGUF"
assert manifest["base_model"] == "Qwen/Qwen3.5-9B"
for item in manifest["files"]:
    assert digest(CACHE / item["filename"]) == item["sha256"]
servers = list((CACHE / "runtime").rglob("llama-server"))
assert len(servers) == 1
server = servers[0]


def query(image: Path, prompt: str, schema: dict, name: str, seed: int, expected_image_hash: str | None) -> dict:
    data, original = image_request(image)
    image_hash = hashlib.sha256(data).hexdigest()
    if expected_image_hash is not None:
        assert image_hash == expected_image_hash, (name, image_hash, expected_image_hash)
    last_error = None
    for attempt, max_tokens in enumerate((850, 1100), start=1):
        request = {
            "model": "T03-local-independent-adjudicator",
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(data).decode()}},
                {"type": "text", "text": prompt},
            ]}],
            "max_tokens": max_tokens,
            "temperature": .25,
            "top_p": .9,
            "seed": seed + attempt - 1,
            "repeat_penalty": 1.12,
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_object", "schema": schema},
            "cache_prompt": False,
        }
        stem = f"{name}-attempt-{attempt}"
        (OUT / f"{stem}-request.json").write_text(json.dumps({
            "prompt": prompt,
            "schema": schema,
            "image_sha256": image_hash,
            "original_size": original,
            "seed": request["seed"],
        }, indent=2))
        started = time.monotonic()
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8080/v1/chat/completions",
                data=json.dumps(request).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=1800) as response:
                raw = json.load(response)
            (OUT / f"{stem}-raw.json").write_text(json.dumps(raw, indent=2))
            choice = raw["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise ValueError(f"incomplete generation: {choice.get('finish_reason')}")
            review = json.loads(choice["message"]["content"])
            return {
                "review": review,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "image_sha256": image_hash,
                "seed": request["seed"],
                "attempt": attempt,
            }
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"focused review incomplete after two attempts: {last_error}")


def run_review(role: str, group: str, purpose: str, seed: int) -> dict:
    directory = artifact_dir(role, group)
    request = json.loads((directory / f"{group}-request.json").read_text())
    board = directory / f"{group}-comparison.jpg"
    prompt = request["prompt"]
    if purpose == "adjudication":
        prompt = re.sub(
            r"Role: [^\n]+",
            "Role: independent-adjudicator. Re-evaluate this evidence group without deference to either primary reviewer.",
            prompt,
            count=1,
        )
    result = query(board, prompt, request["schema"], f"{purpose}-{role}-{group}", seed, request["image_sha256"])
    output_role = "independent-adjudicator" if purpose == "adjudication" else role
    row = {
        "task": "T03-boundary-v2",
        "source": SOURCE,
        "role": output_role,
        "group": group,
        "purpose": purpose,
        "independent_execution": True,
        "review": result["review"],
        "lowest_score": min(result["review"]["scores"].values()),
        "elapsed_seconds": result["elapsed_seconds"],
        "comparison_sha256": digest(board),
        "request_image_sha256": result["image_sha256"],
        "seed": result["seed"],
        "attempt": result["attempt"],
        "error": None,
    }
    state, reasons = classify(row, SOURCE)
    row["classified_state"] = state
    row["classification_reasons"] = reasons
    (OUT / f"{purpose}-{role}-{group}-review.json").write_text(json.dumps(row, indent=2))
    print(json.dumps(row), flush=True)
    return row


base, structural_errors = load_reviews(REVIEWS, SOURCE)
assert not structural_errors, structural_errors
states = {key: classify(row, SOURCE)[0] for key, row in base.items()}
supplemental = []

environment = dict(os.environ)
environment["LD_LIBRARY_PATH"] = str(server.parent) + ":" + environment.get("LD_LIBRARY_PATH", "")
log = (OUT / "inference.log").open("w")
command = [
    str(server), "-m", str(CACHE / manifest["model_file"]), "--mmproj", str(CACHE / manifest["projector_file"]),
    "--host", "127.0.0.1", "--port", "8080", "-c", "8192", "-t", "4", "-tb", "4", "-ngl", "0",
    "--no-mmproj-offload", "--parallel", "1", "--jinja", "--image-min-tokens", "1024", "--image-max-tokens", "2048",
]
process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=environment)
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

    # Prove the focused reviewer can still distinguish the known visual subjects
    # before allowing either a retry or an adjudication vote.
    probe_directory = artifact_dir(*sorted(base)[0])
    probe_request = json.loads((probe_directory / "competency-request.json").read_text())
    probe = query(
        probe_directory / "blind-competency.png",
        probe_request["prompt"],
        probe_request["schema"],
        "competency",
        20261888,
        probe_request["image_sha256"],
    )
    expected_probe = {"A": "human_character", "B": "snow_tree", "C": "snow_tree", "D": "human_character"}
    assert probe["review"] == expected_probe, (probe["review"], expected_probe)
    (OUT / "competency.json").write_text(json.dumps({
        "answers": probe["review"],
        "expected": expected_probe,
        "passed": True,
        "seed": probe["seed"],
    }, indent=2))

    # Incomplete outputs are transport/tooling failures, so replace them once;
    # never retry a completed low score to improve its grade.
    for index, ((role, group), state) in enumerate(sorted(states.items())):
        if state == "INCOMPLETE":
            replacement = run_review(role, group, "retry", 20261900 + index * 10)
            supplemental.append(replacement)
            base[(role, group)] = replacement
            states[(role, group)] = classify(replacement, SOURCE)[0]

    groups = sorted({group for _, group in base})
    for index, group in enumerate(groups):
        group_states = {role: states.get((role, group)) for role in ROLES}
        dissent_roles = [role for role, state in group_states.items() if state == "DISSENT"]
        pass_roles = [role for role, state in group_states.items() if state == "PASS"]
        if len(dissent_roles) == 1 and len(pass_roles) == 1:
            adjudication = run_review(pass_roles[0], group, "adjudication", 20262900 + index * 10)
            supplemental.append(adjudication)
finally:
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
    log.close()

(OUT / "supplemental-reviews.json").write_text(json.dumps(supplemental, indent=2) + "\n")
(OUT / "provenance.json").write_text(json.dumps({
    "source": SOURCE,
    "model": manifest["base_model"],
    "model_revision": manifest["revision"],
    "original_reviews_root": str(REVIEWS),
    "completed_low_scores_retried": False,
    "incomplete_outputs_retried_once": True,
    "adjudication_scores_hidden": True,
    "strict_threshold": ">9.0 unrounded",
    "score_averaging": False,
}, indent=2) + "\n")
