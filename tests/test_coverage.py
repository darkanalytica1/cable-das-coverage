import unittest
from dascov import Segment, coverage, sweep


class T(unittest.TestCase):
    def test_unrepeatered_limited_by_reach(self):
        c = coverage(Segment(250, 0, reach_km=171))
        self.assertAlmostEqual(c["heard_km"], 171)
        self.assertEqual(c["longest_deaf_km"], 79)

    def test_repeater_caps_reach(self):
        c = coverage(Segment(1375, 20, reach_km=171))
        self.assertAlmostEqual(c["heard_km"], 1375 / 21, places=1)

    def test_dual_ended_doubles(self):
        c = coverage(Segment(1375, 20, reach_km=171, dual_ended=True))
        self.assertAlmostEqual(c["fraction"], 2 / 21, places=4)
        self.assertAlmostEqual(c["longest_deaf_km"], 1375 * 19 / 21, places=1)

    def test_more_reach_does_not_pass_repeater(self):
        a = coverage(Segment(1375, 20, reach_km=171, dual_ended=True))
        b = coverage(Segment(1375, 20, reach_km=270.6, dual_ended=True))
        self.assertEqual(a["heard_km"], b["heard_km"])

    def test_multispan_full(self):
        c = coverage(Segment(1375, 20, reach_km=171, multispan=True))
        self.assertAlmostEqual(c["fraction"], 1.0)
        self.assertEqual(c["longest_deaf_km"], 0)

    def test_multispan_limited(self):
        c = coverage(Segment(1375, 20, reach_km=171, dual_ended=True, multispan=True, max_spans=3))
        self.assertAlmostEqual(c["fraction"], 6 / 21, places=4)

    def test_short_reach_inside_span(self):
        c = coverage(Segment(1000, 9, reach_km=50, multispan=True))
        self.assertAlmostEqual(c["heard_km"], 50)

    def test_explicit_spans(self):
        c = coverage(Segment(300, spans_km=(40, 200, 60), reach_km=171, dual_ended=True))
        self.assertAlmostEqual(c["heard_km"], 100)

    def test_bad_spans(self):
        with self.assertRaises(ValueError):
            Segment(300, spans_km=(100, 100)).spans()

    def test_sweep_shape(self):
        rows = sweep(1375, [40, 100], [50, 171])
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(0 < r["fraction"] <= 1 for r in rows))


if __name__ == "__main__":
    unittest.main()
