#!/usr/bin/env python3
"""Pure counterbalanced C6 repeat calculations."""
from __future__ import annotations

import math


REPEAT_STABILITY_LIMIT = 0.05
COUNTERBALANCED_ORDER = ("baseline-a", "candidate-a", "candidate-b", "baseline-b")
EQUAL_WARMUP_SECONDS = 30


def validate_counterbalanced_order(labels: list[str] | tuple[str, ...]) -> bool:
    return tuple(labels) == COUNTERBALANCED_ORDER


def valid_warmup_record(record: dict) -> bool:
    return (
        record.get("requested_seconds") == EQUAL_WARMUP_SECONDS
        and isinstance(record.get("retained_seconds"), (int, float))
        and not isinstance(record.get("retained_seconds"), bool)
        and record["retained_seconds"] >= EQUAL_WARMUP_SECONDS
        and isinstance(record.get("samples"), int)
        and not isinstance(record.get("samples"), bool)
        and record["samples"] > 0
        and record.get("native_dimensions_and_scale_maintained") is True
        and record.get("fixed_timestep_used") is False
    )


def repeat_mean(values: list[float]) -> float:
    if len(values) != 2 or any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("exactly two finite positive repeat values are required")
    return sum(values) / 2


def repeat_spread(values: list[float]) -> float:
    average = repeat_mean(values)
    return (max(values) - min(values)) / average


def summarize_rss(candidate: list[float], baseline: list[float]) -> dict:
    candidate_mean = repeat_mean(candidate)
    baseline_mean = repeat_mean(baseline)
    return {
        "candidate_mean": candidate_mean,
        "baseline_mean": baseline_mean,
        "candidate_spread": repeat_spread(candidate),
        "baseline_spread": repeat_spread(baseline),
        "candidate_to_baseline_ratio": candidate_mean / baseline_mean,
        "stable": repeat_spread(candidate) <= REPEAT_STABILITY_LIMIT and repeat_spread(baseline) <= REPEAT_STABILITY_LIMIT,
    }
