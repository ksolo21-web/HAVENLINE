import unittest

from performance_protocol import REPEAT_STABILITY_LIMIT, repeat_mean, repeat_spread, summarize_rss


class CounterbalancedPerformanceTests(unittest.TestCase):
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
