#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tarfile
import time
import urllib.error
import urllib.request

from lib import DOCS, load_json

LOCK_PATH = pathlib.Path(__file__).with_name("critic_runtime_lock.json")


def digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_lock() -> dict:
    return json.loads(LOCK_PATH.read_text())


def validate_runtime_lock(lock: dict | None = None) -> dict:
    lock = lock or load_lock()
    errors: list[str] = []
    if lock.get("schema_version") != 1:
        errors.append("runtime lock schema_version must be 1")
    revision = str(lock.get("revision", ""))
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision.lower()):
        errors.append("runtime lock revision must be an exact 40-character commit")
    files = lock.get("files", [])
    if len(files) != 3:
        errors.append("runtime lock must contain exactly model, projector and runtime archive")
    names = [str(row.get("filename", "")) for row in files]
    if len(names) != len(set(names)):
        errors.append("runtime lock filenames must be unique")
    for row in files:
        name = row.get("filename")
        sha = str(row.get("sha256", ""))
        url = str(row.get("url", ""))
        if not name:
            errors.append("runtime lock file is missing filename")
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha.lower()):
            errors.append(f"runtime lock SHA-256 invalid for {name}")
        if not url.startswith("https://"):
            errors.append(f"runtime lock URL must be HTTPS for {name}")
    if lock.get("model_file") not in names:
        errors.append("model_file must be present in locked files")
    if lock.get("projector_file") not in names:
        errors.append("projector_file must be present in locked files")
    cache_policy = lock.get("cache_validation", {})
    if cache_policy.get("network_required_on_valid_cache") is not False:
        errors.append("valid cache must not require network access")
    if cache_policy.get("verify_every_file_sha256") is not True:
        errors.append("every cached runtime file must be SHA-256 verified")
    return {"passed": not errors, "errors": errors, "file_count": len(files)}


def _manifest_expected(lock: dict, records: list[dict]) -> dict:
    return {
        "publisher": lock["publisher"],
        "revision": lock["revision"],
        "base_model": lock["base_model"],
        "model_file": lock["model_file"],
        "projector_file": lock["projector_file"],
        "runtime_release": lock["runtime_release"],
        "files": records,
        "purpose": "Havenline independent C1/C2/C3/C4/C5/C7/C8/C10/C11 review",
        "paid_inference": False,
        "pinned_revision_enforced": True,
        "offline_cache_validation": True,
    }


def validate_cached_runtime(root: pathlib.Path, lock: dict | None = None) -> dict:
    lock = lock or load_lock()
    errors: list[str] = []
    lock_report = validate_runtime_lock(lock)
    if not lock_report["passed"]:
        errors.extend(lock_report["errors"])
        return {"passed": False, "errors": errors, "files": []}

    manifest_path = root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as exc:
        return {"passed": False, "errors": [f"manifest unavailable/invalid: {exc}"], "files": []}

    for key in ("publisher", "revision", "base_model", "model_file", "projector_file", "runtime_release"):
        if manifest.get(key) != lock.get(key):
            errors.append(f"manifest {key} mismatch")

    manifest_files = {row.get("filename"): row for row in manifest.get("files", []) if isinstance(row, dict)}
    verified: list[dict] = []
    for expected in lock["files"]:
        name = expected["filename"]
        cached = root / name
        recorded = manifest_files.get(name, {})
        if recorded.get("sha256") != expected["sha256"]:
            errors.append(f"manifest SHA-256 mismatch for {name}")
        if not cached.is_file():
            errors.append(f"cached file missing: {name}")
            continue
        actual = digest(cached)
        if actual != expected["sha256"]:
            errors.append(f"cached SHA-256 mismatch for {name}: {actual}")
        verified.append({"filename": name, "sha256": actual, "bytes": cached.stat().st_size})

    servers = list((root / "runtime").rglob("llama-server")) if (root / "runtime").exists() else []
    if len(servers) != 1 or not servers[0].is_file():
        errors.append(f"expected one extracted llama-server, found {len(servers)}")

    return {
        "passed": not errors,
        "errors": errors,
        "files": verified,
        "server": str(servers[0]) if len(servers) == 1 else None,
    }


def download(url: str, path: pathlib.Path, max_tries: int = 3) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    aria = shutil.which("aria2c")
    if aria:
        subprocess.run(
            [
                aria,
                "--console-log-level=warn",
                "--summary-interval=20",
                "-x",
                "12",
                "-s",
                "12",
                "-k",
                "4M",
                "--file-allocation=none",
                f"--max-tries={max_tries}",
                "--retry-wait=3",
                "--connect-timeout=20",
                "--timeout=60",
                "--allow-overwrite=true",
                "--auto-file-renaming=false",
                "-d",
                str(path.parent),
                "-o",
                path.name,
                url,
            ],
            check=True,
        )
        return

    partial = path.with_name(path.name + ".partial")
    last_error: Exception | None = None
    for attempt in range(1, max_tries + 1):
        try:
            if partial.exists():
                partial.unlink()
            req = urllib.request.Request(url, headers={"User-Agent": "Havenline-independent-specialist-review"})
            with urllib.request.urlopen(req, timeout=120) as src, partial.open("wb") as dst:
                shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
            partial.replace(path)
            return
        except Exception as exc:
            last_error = exc
            if partial.exists():
                partial.unlink()
            if attempt < max_tries:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"download failed after {max_tries} attempts: {url}: {last_error}")


def _extract_runtime(root: pathlib.Path) -> pathlib.Path:
    runtime = root / "runtime"
    if runtime.exists():
        shutil.rmtree(runtime)
    runtime.mkdir(parents=True, exist_ok=True)
    with tarfile.open(root / "runtime.tar.gz") as archive:
        archive.extractall(runtime, filter="data")
    servers = list(runtime.rglob("llama-server"))
    if len(servers) != 1:
        raise RuntimeError(f"expected one llama-server after extraction, found {len(servers)}")
    servers[0].chmod(0o755)
    return servers[0]


def prepare_runtime(root: pathlib.Path, lock: dict | None = None) -> dict:
    lock = lock or load_lock()
    lock_report = validate_runtime_lock(lock)
    if not lock_report["passed"]:
        raise RuntimeError("invalid critic runtime lock: " + "; ".join(lock_report["errors"]))
    root.mkdir(parents=True, exist_ok=True)

    cached = validate_cached_runtime(root, lock)
    if cached["passed"]:
        return {
            "passed": True,
            "source": "verified_cache",
            "network_used": False,
            "cache": str(root),
            "publisher": lock["publisher"],
            "revision": lock["revision"],
            "runtime": lock["runtime_release"],
            "files": cached["files"],
        }

    max_tries = int(lock.get("cache_validation", {}).get("bounded_download_retries", 3))

    def ensure(item: dict) -> dict:
        target = root / item["filename"]
        valid = target.is_file() and digest(target) == item["sha256"]
        if not valid:
            if target.exists():
                target.unlink()
            download(item["url"], target, max_tries=max_tries)
        actual = digest(target)
        if actual != item["sha256"]:
            raise RuntimeError(f"hash mismatch {item['filename']}: {actual}")
        return {"filename": item["filename"], "sha256": actual, "bytes": target.stat().st_size}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(ensure, lock["files"]))

    _extract_runtime(root)
    (root / "manifest.json").write_text(json.dumps(_manifest_expected(lock, records), indent=2) + "\n")
    final = validate_cached_runtime(root, lock)
    if not final["passed"]:
        raise RuntimeError("critic runtime cache repair failed: " + "; ".join(final["errors"]))
    return {
        "passed": True,
        "source": "download_repair",
        "network_used": True,
        "cache": str(root),
        "publisher": lock["publisher"],
        "revision": lock["revision"],
        "runtime": lock["runtime_release"],
        "files": final["files"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or validate Havenline's checksum-pinned independent critic runtime")
    parser.add_argument("--validate-lock", action="store_true")
    parser.add_argument("--validate-cache", action="store_true")
    args = parser.parse_args()

    cfg = load_json(DOCS / "CRITIC_EXECUTION.json")["local_independent_runtime"]
    root = pathlib.Path(os.path.expanduser(cfg["cache_path"]))
    lock = load_lock()

    if cfg.get("provider") != lock.get("publisher") or cfg.get("model_revision") != lock.get("revision") or cfg.get("base_model") != lock.get("base_model"):
        raise SystemExit("CRITIC_EXECUTION runtime identity does not match critic_runtime_lock.json")

    if args.validate_lock:
        result = validate_runtime_lock(lock)
    elif args.validate_cache:
        result = validate_cached_runtime(root, lock)
    else:
        result = prepare_runtime(root, lock)
    print(json.dumps(result, indent=2))
    if not result.get("passed", False):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
