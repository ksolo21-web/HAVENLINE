#!/usr/bin/env python3
from __future__ import annotations
import datetime, pathlib, sys
from lib import DOCS, ROOT, load_json, expand_alias

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: task_packet.py T04")
    task_id = sys.argv[1].upper()
    graph = load_json(DOCS / "DEPENDENCY_GRAPH.json")
    registry = load_json(DOCS / "WORKSTREAM_REGISTRY.json")
    ownership = load_json(DOCS / "PATH_OWNERSHIP.json")
    critics = load_json(DOCS / "CRITIC_MATRIX.json")
    if task_id not in graph["tasks"]:
        raise SystemExit(f"unknown task {task_id}")
    task = graph["tasks"][task_id]
    ws = next((w for w in registry["workstreams"] if w["task_id"] == task_id), None)
    owned = []
    protected = []
    branch = None
    base = None
    owner = None
    workstream = None
    if ws:
        owned = expand_alias(ws.get("owned_paths", []), ownership)
        protected = expand_alias(ws.get("protected_paths", []), ownership)
        branch = ws.get("branch")
        base = ws.get("base_commit")
        owner = ws.get("owner")
        workstream = ws.get("workstream_id")
    required_critics = critics["task_applicability"].get(task_id, [])
    gates = [f"G{i}" for i in range(1, 15)]
    text = f"""# Havenline frozen task packet — {task_id}

Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}

## Identity
- Task ID: {task_id}
- Task name: {task['name']}
- Workstream ID: {workstream or 'UNASSIGNED'}
- Owner: {owner or 'UNASSIGNED'}
- Isolated branch: {branch or 'UNASSIGNED'}
- Exact base integration commit: {base or 'UNASSIGNED'}

## Dependencies
Required APPROVED upstream tasks: {', '.join(task['dependencies']) or 'none'}

## Owned paths
"""
    text += "\n".join(f"- `{p}`" for p in owned) or "- UNASSIGNED"
    text += "\n\n## Protected paths\n"
    text += "\n".join(f"- `{p}`" for p in protected) or "- resolve from PATH_OWNERSHIP.json"
    text += "\n\n## Acceptance gates\n" + "\n".join(f"- {g}: REQUIRED unless task packet records explicit N/A rationale." for g in gates)
    text += "\n\n## Required critics\n" + ("\n".join(f"- {c}" for c in required_critics) or "- none")
    text += """

## Score rule
Every applicable mandatory reviewed dimension must be strictly >9.0 unrounded.
Target 10/10. No averaging and no unresolved mandatory defects.

## Evidence
Exact-source hashes, changed-file manifest, required deterministic engine views,
performance records, applicable save/device matrices, raw critic inputs/outputs,
known failures and final dispositions are mandatory before APPROVED.

## Scope
Use the authoritative task-specific frozen scope when present. This generated
packet does not expand runtime scope.
"""
    out = DOCS / "Evidence" / task_id / "TASK_PACKET.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out.relative_to(ROOT))

if __name__ == "__main__":
    main()
