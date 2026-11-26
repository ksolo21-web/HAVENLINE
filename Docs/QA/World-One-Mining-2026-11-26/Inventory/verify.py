"""Check the two generated saves without installing or starting Havenline."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

root = Path(__file__).resolve().parent
def load(name):
    path = root / "Fixtures" / name
    raw = path.read_bytes()
    envelope = json.loads(raw)
    payload = envelope["payload"].encode()
    assert envelope["format"] == 1 and sha256(payload).hexdigest() == envelope["sha256"]
    state = json.loads(payload)
    total = Counter(state["collected"].values())
    for kind in state["carried"]:
        spent = sum(receipt.get(kind, 0) for receipt in state["paid"].values())
        assert total[kind] == state["stored"][kind] + state["carried"][kind] + spent
    return state, sha256(raw).hexdigest()
before, h2 = load("Generated-v2.json")
after, h3 = load("Generated-v3.json")
assert before["version"] == 2 and after["version"] == 3
assert len(before["build_order"]) == 8 and before["build_order"] == after["build_order"]
assert before["paid"] == after["paid"] and before["legacy_axes"] == after["legacy_axes"]
for old_kind in ("wood", "stone", "meat"):
    for column in ("carried", "stored"):
        assert before[column][old_kind] == after[column][old_kind]
assert all(after["collected"].get(token) == kind for token, kind in before["collected"].items())
new_tokens = Counter(kind for token, kind in after["collected"].items() if token not in before["collected"])
assert new_tokens == {"coal": 3, "slate": 4, "metal": 5}
for kind, count in new_tokens.items():
    assert after["carried"][kind] == 1 and after["stored"][kind] == count - 1
print(json.dumps({"before_sha256": h2, "after_sha256": h3,
                  "original_tokens": len(before["collected"]), "new_tokens": dict(new_tokens),
                  "all_eight_receipts_retained": True, "conservation_by_kind": True}, indent=2))
