import unittest

from performance_protocol import (
    COUNTERBALANCED_ORDER, EQUAL_WARMUP_SECONDS, REPEAT_STABILITY_LIMIT,
    repeat_mean, repeat_spread, summarize_rss, valid_warmup_record,
    validate_counterbalanced_order,
)


class CounterbalancedPerformanceTests(unittest.TestCase):
    def test_equal_warmup_uses_the_same_counterbalanced_order(self):
        self.assertEqual(EQUAL_WARMUP_SECONDS, 30)
        self.assertTrue(validate_counterbalanced_order(COUNTERBALANCED_ORDER))
        self.assertFalse(validate_counterbalanced_order(("baseline-a", "baseline-b", "candidate-a", "candidate-b")))

    def test_warmup_record_must_have_real_elapsed_samples(self):
        valid = {
            "requested_seconds": 30, "retained_seconds": 30.0, "samples": 1800,
            "native_dimensions_and_scale_maintained": True, "fixed_timestep_used": False,
        }
        self.assertTrue(valid_warmup_record(valid))
        for key, bad_value in (
            ("retained_seconds", 0), ("samples", 0),
            ("native_dimensions_and_scale_maintained", False), ("fixed_timestep_used", True),
        ):
            changed = dict(valid)
            changed[key] = bad_value
            self.assertFalse(valid_warmup_record(changed), key)

    def test_stable_counterbalanced_means_and_ratio(self):
        result = summarize_rss([2040.0, 2060.0], [2000.0, 2020.0])
        self.assertEqual(result["candidate_mean"], 2050.0)
        self.assertEqual(result["baseline_mean"], 2010.0)
        self.assertTrue(result["stable"])
        self.assertAlmostEqual(result["candidate_to_baseline_ratio"], 2050.0 / 2010.0)

    def test_diagnostic_baseline_spread_is_rejected_as_unstable(self):
        result = summarize_rss([2103940.0, 2058904.0], [2147728.0, 1982800.0])
        self.assertGreater(result["baseline_spread"], REPEAT_STABILITY_LIMIT)
        self.assertFalse(result["stable"])

    def test_spread_is_range_over_mean(self):
        self.assertAlmostEqual(repeat_spread([95.0, 105.0]), 0.1)
        self.assertEqual(repeat_mean([95.0, 105.0]), 100.0)

    def test_requires_exactly_two_positive_finite_values(self):
        for values in ([1.0], [1.0, 2.0, 3.0], [0.0, 1.0], [float("nan"), 1.0]):
            with self.assertRaises(ValueError):
                repeat_mean(values)


if __name__ == "__main__":
    unittest.main()
