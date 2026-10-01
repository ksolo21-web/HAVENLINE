#!/usr/bin/env python3
"""One source-bound benchmark; distinguish phase progress from job-budget exhaustion."""
import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

from build_critic_evidence import benchmark_errors

ROOT = Path(__file__).resolve().parents[3]
JOB_SECONDS = 40 * 60
RETENTION_RESERVE_SECONDS = 120
STALL_SECONDS = 1800
EXPECTED = [(cycle, state) for cycle in range(3) for state in ("hidden", "frozen", "pulse")]


class EvidenceError(ValueError):
    pass


def job_binding(payload, run_id, attempt, job_name, candidate, wall, monotonic):
    if not math.isfinite(wall) or not math.isfinite(monotonic):
        raise EvidenceError("INVALID_CLOCK")
    if attempt != 1:
        raise EvidenceError("UNCHANGED_ATTEMPT_REJECTED")
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or payload.get("total_count") != len(jobs):
        raise EvidenceError("INCOMPLETE_JOB_METADATA")
    matches = [job for job in jobs if job.get("name") == job_name]
    if len(matches) != 1:
        raise EvidenceError("AMBIGUOUS_JOB_IDENTITY")
    job = matches[0]
    if (job.get("run_id") != run_id or job.get("run_attempt") != attempt
            or job.get("status") != "in_progress" or job.get("conclusion") is not None
            or type(job.get("id")) is not int or job["id"] <= 0):
        raise EvidenceError("INVALID_ACTIVE_JOB_IDENTITY")
    try:
        started = datetime.fromisoformat(job["started_at"].replace("Z", "+00:00"))
        if started.tzinfo is None:
            raise ValueError("timezone required")
        started = started.timestamp()
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise EvidenceError("INVALID_JOB_START") from exc
    if started > wall:
        raise EvidenceError("JOB_START_IN_FUTURE")
    remaining = started + JOB_SECONDS - RETENTION_RESERVE_SECONDS - wall
    return {
        "candidate_commit": candidate, "workflow_run_id": run_id, "run_attempt": attempt,
        "job_id": job["id"], "job_name": job_name, "job_started_at": job["started_at"],
        # PR API head and actual checkout merge source may legitimately differ.
        "api_head_sha": job.get("head_sha"), "job_cap_seconds": JOB_SECONDS,
        "retention_reserve_seconds": RETENTION_RESERVE_SECONDS,
        "observed_wall_seconds": wall, "observed_monotonic_seconds": monotonic,
        "benchmark_deadline_monotonic": monotonic + remaining,
        "benchmark_remaining_seconds": remaining, "stall_seconds": STALL_SECONDS,
    }


@dataclass
class ProgressGuard:
    started: float
    deadline: float
    last_progress: float = field(init=False)
    previous_clock: float = field(init=False)
    events: list = field(default_factory=list)

    def __post_init__(self):
        if not math.isfinite(self.started) or not math.isfinite(self.deadline):
            raise EvidenceError("INVALID_CLOCK")
        self.last_progress = self.previous_clock = self.started

    def check(self, now):
        if not math.isfinite(now):
            raise EvidenceError("INVALID_CLOCK")
        if now < self.previous_clock:
            raise EvidenceError("MONOTONIC_CLOCK_REGRESSION")
        self.previous_clock = now
        if now >= self.deadline:
            raise EvidenceError("JOB_BUDGET_EXHAUSTED")
        if now - self.last_progress >= STALL_SECONDS:
            raise EvidenceError("BENCHMARK_STALLED")

    def line(self, raw, now):
        self.check(now)
        try:
            value = json.loads(raw)
        except ValueError:
            if "completed_control" in raw:
                raise EvidenceError("MALFORMED_PROGRESS_EVENT")
            return
        if not isinstance(value, dict) or "completed_control" not in value:
            return
        if (set(value) != {"cycle", "completed_control"} or type(value["cycle"]) is not int
                or not isinstance(value["completed_control"], str)
                or len(self.events) >= len(EXPECTED)
                or (value["cycle"], value["completed_control"]) != EXPECTED[len(self.events)]):
            raise EvidenceError("INVALID_PROGRESS_SEQUENCE")
        self.events.append(dict(value, observed_elapsed_seconds=now - self.started))
        self.last_progress = now


def command(candidate, output):
    return ["xvfb-run", "-a", "-s", "-screen 0 3840x2160x24",
            "Godot_v4.7.2-stable_linux.x86_64", "--path", "HavenlineGodot",
            "--rendering-method", "mobile", "--rendering-driver", "vulkan",
            "--audio-driver", "Dummy", "--resolution", "3840x2160", "--script",
            str(ROOT / "tools/havenline/task10/benchmark_world_transform.gd"), "--",
            "--candidate=" + candidate, "--width=3840", "--height=2160", "--out=" + str(output)]


def completion_errors(returncode, events, manifest, candidate):
    errors = []
    if returncode != 0:
        errors.append("BENCHMARK_PROCESS_FAILED")
    if [(event["cycle"], event["completed_control"]) for event in events] != EXPECTED:
        errors.append("INCOMPLETE_PROGRESS_SEQUENCE")
    if not isinstance(manifest, dict):
        errors.append("MISSING_BENCHMARK_MANIFEST")
    else:
        errors.extend(benchmark_errors(manifest, candidate))
    return errors


def terminate_group(proc):
    if proc.poll() is not None:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            pass


def run(candidate, output, context):
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        refusal = {"candidate_commit": candidate, "passed": False, "task_approved": False,
                   "errors": ["PREEXISTING_BENCHMARK_OUTPUT"], "benchmark_started": False}
        try:
            with (output / "supervisor-refused-existing-output.json").open("x") as stream:
                json.dump(refusal, stream)
        except FileExistsError:
            pass
        print(json.dumps(refusal))
        return 1
    result = {"candidate_commit": candidate, "task_approved": False, "passed": False,
              "errors": [], "progress": [], "single_attempt": True,
              "stage": "source_validation", "benchmark_started": False}
    proc = None
    guard = None
    returncode = 1
    try:
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        if actual != candidate:
            raise EvidenceError("CHECKOUT_SOURCE_MISMATCH")
        protected = ["HavenlineGodot", "tools/havenline/task10/benchmark_world_transform.gd"]
        subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *protected], cwd=ROOT, check=True)
        run_id, attempt = int(context["GITHUB_RUN_ID"]), int(context["GITHUB_RUN_ATTEMPT"])
        endpoint = f"repos/{context['GITHUB_REPOSITORY']}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100"
        result["stage"] = "job_metadata"
        raw_jobs = subprocess.check_output(["gh", "api", endpoint], cwd=ROOT, timeout=30)
        (output / "job-metadata.json").write_bytes(raw_jobs)
        wall, monotonic = time.time(), time.monotonic()
        binding = job_binding(json.loads(raw_jobs), run_id, attempt, context["GITHUB_JOB"], candidate, wall, monotonic)
        result.update(binding)
        result["job_metadata_sha256"] = hashlib.sha256(raw_jobs).hexdigest()
        result["benchmark_source_sha256"] = hashlib.sha256((ROOT / protected[1]).read_bytes()).hexdigest()
        result["stage"] = "budget_admission"
        guard = ProgressGuard(monotonic, binding["benchmark_deadline_monotonic"])
        guard.check(monotonic)
        argv = command(candidate, output)
        result["command"] = argv
        child_env = dict(context)
        child_env.pop("GH_TOKEN", None)
        child_env.pop("GITHUB_TOKEN", None)
        with (output / "benchmark.log").open("wb") as writer:
            proc = subprocess.Popen(argv, cwd=ROOT, env=child_env, stdout=writer,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            result["benchmark_started"] = True
            result["stage"] = "benchmark"
            with (output / "benchmark.log").open("rb") as reader, (output / "progress.jsonl").open("w") as progress:
                pending = b""
                while True:
                    now = time.monotonic()
                    guard.check(now)
                    returncode = proc.poll()
                    chunk = reader.read(65536)
                    pending += chunk
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        if len(line) > 65536:
                            raise EvidenceError("OVERSIZED_BENCHMARK_LOG_LINE")
                        previous = len(guard.events)
                        guard.line(line.decode("utf-8", errors="replace"), now)
                        if len(guard.events) != previous:
                            progress.write(json.dumps(guard.events[-1]) + "\n")
                            progress.flush()
                    if len(pending) > 65536:
                        raise EvidenceError("OVERSIZED_BENCHMARK_LOG_LINE")
                    # A terminated child can leave multiple unread chunks. Only
                    # finish after observing EOF following termination.
                    if returncode is not None and not chunk:
                        if pending:
                            guard.line(pending.decode("utf-8", errors="replace"), time.monotonic())
                        break
                    if returncode is None:
                        time.sleep(1)
        guard.check(time.monotonic())
        result["stage"] = "manifest_validation"
        manifest_path = output / "manifest.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else None
        result["errors"] = completion_errors(returncode, guard.events, manifest, candidate)
        raw_log = (output / "benchmark.log").read_text(errors="replace")
        if any(marker in raw_log for marker in ("SCRIPT ERROR", "Parse Error", "ObjectDB instances were leaked")):
            result["errors"].append("BENCHMARK_SCRIPT_ERROR")
        subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *protected], cwd=ROOT, check=True)
        guard.check(time.monotonic())
        result["passed"] = not result["errors"]
        result["stage"] = "complete" if result["passed"] else "validation_failed"
    except (EvidenceError, OSError, ValueError, KeyError, TypeError, AssertionError, subprocess.SubprocessError) as exc:
        result["errors"].append(str(exc))
        if str(exc) in {"JOB_BUDGET_EXHAUSTED", "BENCHMARK_STALLED"}:
            returncode = 124
        elif returncode is None:
            returncode = 1
    finally:
        if proc is not None:
            terminate_group(proc)
        if returncode is None:
            returncode = 1
        if guard is not None:
            result["progress"] = guard.events
            result["elapsed_seconds"] = time.monotonic() - guard.started
        result["exit_code"] = returncode
        result["child_exit_code"] = proc.poll() if proc is not None else None
        result["supervisor_exit_code"] = 0 if result["passed"] else ((128 - returncode if returncode < 0 else returncode) if returncode else 1)
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        (output / "supervisor.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"candidate_commit": candidate, "passed": result["passed"],
                          "errors": result["errors"], "completed_controls": len(result["progress"]),
                          "exit_code": returncode, "task_approved": False}))
    if result["passed"]:
        return 0
    return (128 - returncode if returncode < 0 else returncode) if returncode else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(run(args.candidate, args.output.resolve(), os.environ))
