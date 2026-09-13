#!/usr/bin/env python3
"""Pure counterbalanced C6 repeat calculations."""
from __future__ import annotations

import math


REPEAT_STABILITY_LIMIT = 0.05


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
