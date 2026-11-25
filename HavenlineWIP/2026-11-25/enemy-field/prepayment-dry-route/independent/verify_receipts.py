#!/usr/bin/env python3
"""Independent offline cross-check of the original stage/run packets; no engine or writes."""
import hashlib
import json
from pathlib import Path
import re
import sys

stage, run = map(Path, sys.argv[1:3])
def content(directory, file):
    return (directory / file).read_bytes()
def digest(directory, file):
    return hashlib.sha256(content(directory, file)).hexdigest()
assert digest(stage, "SHA256SUMS") == "4bbb73b8fc5c527fc1c9ee660ca9a42b27fe98ecd46b6677ea4d282b74eb21eb"
for line in content(stage, "SHA256SUMS").decode().splitlines():
    expected, file = line.split("  ", maxsplit=1)
    assert digest(stage, file) == expected, file
assert digest(run, "prepayment.log") == "b3caf2ae0b9a4ce2ad6f58b79e7b068fc3e6b986922f8fc4565166c2886ad5b6"
assert content(run, "status").decode().splitlines() == [
    "import exit=0 diagnostic_count=18", "prepayment exit=0 diagnostic_count=0"]
assert content(run, "source-before.txt") == content(run, "source-after.txt") == b"tracked_git_blobs 126 private_fixture 1\n"
assert content(run, "prepayment.scan") == content(run, "save-artifacts.txt") == b""
assert content(stage, "import-warnings-author-expected.txt") == content(run, "import-warnings-observed.txt")
log = content(run, "prepayment.log").decode().splitlines()
points = [json.loads(s.split(" ", 1)[1]) for s in log if s.startswith("PREPAY_POINT ")]
result, = [json.loads(s.split(" ", 1)[1]) for s in log if s.startswith("PREPAY_RESULT ")]
passed = [int(re.search(r" tick=(\d+)$", s)[1]) for s in log if s.startswith("PASS ")]
assert len(passed) == result["checks"] == 19 and result["failed"] == 0
assert passed[-1] - passed[1] == 202
for k in ("grounded_dry", "ledger_unchanged", "camp_inactive"):
    assert result[k] == result["observed"] == 202
assert all(p["gap_m"] < .08 for p in points) and len(points) == 4
assert result["min_wood_c_m"] > .68
print(json.dumps({"verdict":"matched scoped unpaid field reachability receipts", "result":result, "points":points}, sort_keys=True))
