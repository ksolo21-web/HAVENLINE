#!/usr/bin/env python3
"""Read-only scope, source preservation, JSON and Markdown-link checks.

This validates a planning change only. It never approves gameplay or changes
candidate files. Run from the candidate root, or supply --root explicitly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

BASE = "9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c"
PACKAGE = "Docs/Production/GameplayDepth/2026-11-27/"
ALLOWED_TRACKED = {
    "BUILD_GAME.md", "REPOSITORY_INDEX.md",
    "Docs/Production/HAVENLINE_BUILD_PLAN_V2.md",
    "Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md",
    "Docs/Production/TASK_PACKET_TEMPLATE.md",
    "tools/havenline/production/task_packet.py",
}
ALLOWED_NEW = {
    "Docs/Production/GAMEPLAY_DEPTH_STANDARD.md",
    "Docs/Production/GAMEPLAY_DEPTH_CONTRACT.json",
    "tools/havenline/production/gameplay_depth.py",
    "tools/havenline/production/tests/test_gameplay_depth.py",
}
PRESERVED_PACKAGES = (
    "Docs/Production/ReferenceRefresh/2026-11-27/",
    "Docs/Production/AcceptanceTightening/2026-11-27/",
)
AUTHORITIES = (
    "DEPENDENCY_GRAPH.json", "WORKSTREAM_REGISTRY.json", "PATH_OWNERSHIP.json",
    "APPROVAL_INVALIDATIONS.json", "task-gates.json", "CRITIC_MATRIX.json",
    "REFERENCE_ACCEPTANCE_POLICY.json",
)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def markdown_targets(text, definitions_text=None):
    """Extract inline and defined reference links, excluding fenced code.

    An undefined ``[F1][F2]`` sequence is literal Markdown, not a broken
    reference link. These documents also use such text as source labels.
    Only a matching reference definition makes it a link under CommonMark.
    """
    def prose(value):
        lines = []; fence = None
        for line in value.splitlines():
            marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
            if marker:
                token = marker.group(1)[0]
                if fence is None: fence = token
                elif fence == token: fence = None
                continue
            if fence is None:
                lines.append(re.sub(r"`+[^`]*`+", "", line))
        return "\n".join(lines)
    body = prose(text); full = prose(definitions_text or text)
    definitions = {}
    for match in re.finditer(r"^\s{0,3}\[([^\]]+)\]:\s*(<[^>]+>|\S+)", full, re.M):
        definitions[match.group(1).strip().lower()] = match.group(2).strip("<>")
    targets = []
    for match in re.finditer(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", body):
        targets.append(match.group(1).strip("<>"))
    for match in re.finditer(r"!?\[([^\]\n]+)\]\[([^\]\n]*)\]", body):
        key = (match.group(2) or match.group(1)).strip().lower()
        if key in definitions:
            targets.append(definitions[key])
    # Check definitions introduced in the reviewed text as well.
    for match in re.finditer(r"^\s{0,3}\[([^\]]+)\]:\s*(<[^>]+>|\S+)", body, re.M):
        targets.append(match.group(2).strip("<>"))
    return sorted(set(targets))


def run(root, base):
    env = dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_NO_REPLACE_OBJECTS="1",
               GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    def git(*args, check=True):
        result = subprocess.run(["git", *args], cwd=root, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if check and result.returncode:
            raise ValueError("git " + " ".join(args[:2]) + ": " + result.stderr.decode(errors="replace").strip())
        return result
    git("cat-file", "-e", base + "^{commit}")
    base_rows = {}
    for row in git("ls-tree", "-r", "-z", base).stdout.split(b"\0"):
        if not row: continue
        metadata, name = row.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        base_rows[name.decode()] = {"mode": mode, "kind": kind, "oid": oid}
    changed = set(git("diff", "--name-only", "--no-renames", "-z", base).stdout.decode().split("\0")) - {""}
    untracked = set(git("ls-files", "--others", "--exclude-standard", "-z").stdout.decode().split("\0")) - {""}
    paths = sorted(changed | untracked)
    checks = []
    def check(name, passed, detail=None):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
    def cache_path(path):
        return "__pycache__" in PurePosixPath(path).parts or path.endswith(".pyc")
    def allowed(path):
        if cache_path(path): return False
        if path in base_rows: return path in ALLOWED_TRACKED
        return path in ALLOWED_NEW or path.startswith(PACKAGE)
    unexpected = [path for path in paths if not allowed(path)]
    check("only_explicitly_allowed_changes", not unexpected, unexpected)
    preserved_changes = sorted(path for path in changed if path in base_rows and path not in ALLOWED_TRACKED)
    check("all_other_tracked_files_unchanged", not preserved_changes, preserved_changes)
    deleted = [path for path in paths if not (root / path).is_file()]
    nonordinary = [path for path in paths if (root / path).is_symlink()]
    check("no_deletions_renames_or_symlink_substitution", not deleted and not nonordinary,
          {"missing_or_nonfile": deleted, "symlinks": nonordinary})
    mode_changes = []
    raw = git("diff", "--raw", "--no-renames", "-z", base).stdout.decode().split("\0")
    for index in range(0, len(raw) - 1, 2):
        metadata, path = raw[index], raw[index + 1]
        if not metadata: continue
        old_mode, new_mode, *_ = metadata.lstrip(":").split()
        if path in base_rows and old_mode != new_mode: mode_changes.append(path)
    check("existing_file_modes_preserved", not mode_changes, mode_changes)
    protected_prefixes = ("Havenline", "Docs/Design/", "Docs/RepositoryArchive/", ".github/")
    protected_changes = [p for p in paths if p.startswith(protected_prefixes)]
    check("no_runtime_asset_archive_or_workflow_changes", not protected_changes and not (root / ".github").exists(), protected_changes)

    def bytes_preserved(path):
        expected = base_rows.get(path)
        if expected is None: return False
        local = root / path
        if local.is_symlink(): return False
        if local.is_file():
            body = local.read_bytes()
            oid = hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
            return expected["kind"] == "blob" and oid == expected["oid"]
        # Sparse checkout omission is valid only if the checked-in HEAD object
        # is identical and this path has no staged/working-tree change.
        if path in changed: return False
        found = git("rev-parse", "HEAD:" + path, check=False)
        return found.returncode == 0 and found.stdout.decode().strip() == expected["oid"]

    for prefix in PRESERVED_PACKAGES:
        old_paths = sorted(p for p in base_rows if p.startswith(prefix))
        bad = [p for p in old_paths if not bytes_preserved(p)]
        check("preserved_package_" + prefix.rstrip("/").split("/")[-2], bool(old_paths) and not bad,
              {"files": len(old_paths), "changed_or_missing": bad})
    authority_paths = ["Docs/Production/" + p for p in AUTHORITIES]
    bad = [p for p in authority_paths if not bytes_preserved(p)]
    check("task_state_ownership_invalidation_and_acceptance_authorities_preserved", not bad, bad)
    packets = [p for p in base_rows if re.fullmatch(r"Docs/Production/(?:Evidence/)?T\d{2}/TASK_PACKET\.md", p)]
    bad = [p for p in packets if not bytes_preserved(p)]
    check("canonical_task_packets_preserved", not bad, {"files": len(packets), "changed_or_missing": bad})

    json_paths = [p for p in paths if p.endswith(".json") and (root / p).is_file()]
    json_errors = []
    for path in json_paths:
        try: strict_json((root / path).read_text(encoding="utf-8"))
        except (ValueError, UnicodeError, OSError) as exc: json_errors.append({"path": path, "error": str(exc)})
    check("changed_and_new_json_parse_strictly", not json_errors, {"files": len(json_paths), "errors": json_errors})

    md_paths = [p for p in paths if p.endswith(".md") and (root / p).is_file()]
    link_errors = []; link_checks = []; unresolved = []
    for path in md_paths:
        text = (root / path).read_text(encoding="utf-8")
        if path in base_rows:
            diff = git("diff", "--no-ext-diff", "--unified=0", base, "--", path).stdout.decode()
            reviewed_text = "\n".join(line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
        else: reviewed_text = text
        for target in markdown_targets(reviewed_text, text):
            if target.startswith("UNRESOLVED_REFERENCE:"):
                unresolved.append({"source": path, "target": target}); continue
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"): continue
            destination = posixpath.normpath(posixpath.join(str(PurePosixPath(path).parent), unquote(parsed.path)))
            if destination == ".." or destination.startswith("../"):
                link_errors.append({"source": path, "target": target, "reason": "escapes_repository"}); continue
            local = root / destination
            exists = local.exists()
            fallback = False
            if not exists:
                fallback = git("cat-file", "-e", "HEAD:" + destination, check=False).returncode == 0
            row = {"source": path, "target": target, "resolved_path": destination,
                   "exists": exists or fallback, "sparse_HEAD_fallback": fallback}
            link_checks.append(row)
            if not row["exists"]: link_errors.append(row)
    check("new_markdown_relative_link_targets_resolve", not link_errors and not unresolved,
          {"markdown_files": len(md_paths), "relative_targets_checked": len(link_checks),
           "errors": link_errors, "unresolved_references": unresolved,
           "sparse_HEAD_fallbacks": sum(r["sparse_HEAD_fallback"] for r in link_checks),
           "fragment_validation": False, "external_urls_not_rechecked": True})
    check("no_generated_python_cache_in_change", not any(cache_path(p) for p in paths))
    whitespace = git("diff", "--check", base, check=False)
    # Preserve exact source-audit bytes, including harmless terminal blank lines.
    # Git starts reporting these for new files only after they enter the index.
    # Keep the findings visible; all other whitespace diagnostics remain failures.
    diagnostics = whitespace.stdout.decode().splitlines()
    terminal_blank_lines = [line for line in diagnostics if re.fullmatch(r".+:\d+: new blank line at EOF\.", line)]
    substantive = [line for line in diagnostics if line not in terminal_blank_lines]
    diagnostic_status_known = whitespace.returncode == 0 or (whitespace.returncode == 2 and bool(terminal_blank_lines))
    check("no_substantive_diff_whitespace_errors", diagnostic_status_known and not substantive and not whitespace.stderr,
          {"blocking_diagnostics": substantive, "preserved_terminal_blank_line_advisories": terminal_blank_lines,
           "return_code": whitespace.returncode, "stderr": whitespace.stderr.decode().strip() or None})
    return {"schema_version": 1, "scope": "PLANNING_SOURCE_PRESERVATION_AND_LINKS_ONLY",
            "base_commit": base, "candidate_root": str(root), "passed": all(c["passed"] for c in checks),
            "checks_passed": sum(c["passed"] for c in checks), "checks_required": len(checks),
            "changed_or_new_files": len(paths), "allowed_tracked_edits": sorted(ALLOWED_TRACKED),
            "game_approval_allowed": False, "runtime_approval_allowed": False,
            "checks": checks, "changed_or_new_paths": paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", default=BASE)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.base): parser.error("--base requires exact lowercase40hex commit")
    try: report = run(args.root.resolve(), args.base)
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        report = {"schema_version": 1, "scope": "PLANNING_SOURCE_PRESERVATION_AND_LINKS_ONLY",
                  "passed": False, "game_approval_allowed": False, "runtime_approval_allowed": False,
                  "error": str(exc)}
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
