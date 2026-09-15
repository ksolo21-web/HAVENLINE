#!/usr/bin/env python3
from __future__ import annotations
import fnmatch, hashlib, json, os, pathlib, subprocess, sys
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "Docs" / "Production"

def load_json(path: str | pathlib.Path):
    p = pathlib.Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return json.loads(p.read_text(encoding="utf-8"))

def sha256_file(path: str | pathlib.Path) -> str:
    p = pathlib.Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def git(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()

def current_commit() -> str:
    return git("rev-parse", "HEAD")

def current_branch() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD")

def changed_files(base: str, head: str = "HEAD") -> list[str]:
    out = git("diff", "--name-only", f"{base}..{head}")
    return [line.strip() for line in out.splitlines() if line.strip()]

def expand_alias(value, ownership: dict) -> list[str]:
    if isinstance(value, str):
        value = [value]
    result = []
    for item in value:
        if item.startswith("@"):
            result.extend(ownership["aliases"].get(item, []))
        else:
            result.append(item)
    return result

def matches(path: str, pattern: str) -> bool:
    # pathlib PurePath.match has surprising ** behavior at root; fnmatch is
    # intentionally used for repository-relative POSIX paths.
    return fnmatch.fnmatch(path, pattern)

def any_match(path: str, patterns: Iterable[str]) -> bool:
    return any(matches(path, p) for p in patterns)

def json_dump(path: pathlib.Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")

def fail(message: str, code: int = 2):
    print(message, file=sys.stderr)
    raise SystemExit(code)

def ensure_score_strictly_above_nine(scores: dict) -> list[str]:
    errors = []
    for name, value in scores.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{name}: non-numeric score")
        elif not value > 9.0:
            errors.append(f"{name}: {value} is not strictly > 9.0")
    return errors
