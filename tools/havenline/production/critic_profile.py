"""Task-scoped critic interpretation; applicability and thresholds are unchanged."""
from copy import deepcopy

T10_C7_DIMENSIONS = ["state_graph_integrity", "prerequisite_integrity", "transaction_ordering", "exact_once_replay", "recovery_integrity", "bounded_state"]


def resolve_critic(task, critic, execution, matrix):
    if critic == "C7" and task not in matrix["task_applicability"]:
        raise ValueError("C7 proof requires an explicit known task_id")
    spec = deepcopy(execution["critics"][critic])
    checks = list(matrix["critics"][critic]["checks"])
    if task == "T10" and critic == "C7":
        spec["dimensions"] = list(T10_C7_DIMENSIONS)
        spec["required_categories"] = ["progression_simulation", "transaction_state_graph", "recovery_evidence"]
        spec["deterministic_runner"] = "python3 tools/havenline/task10/validate_progression.py"
        spec["scope_profile"] = "T10_transaction_state_integrity_v1"
        checks = [
            "No implicit state skips, cycles or downgrades; reversible pairs are explicit and reciprocal.",
            "Prerequisites and exact delivered-resource costs gate every transition.",
            "Per-target revisions and source states remain continuous and ordered.",
            "Exact-once debit and advancement survive duplicates, stale requests and retries.",
            "Pending and completed JSON recovery is atomic, canonical and fail-closed.",
            "Targets, tags, identifiers and retained transaction state stay bounded.",
        ]
    return spec, checks
