"""Meaningful regression checks for rules that can yield different k."""
import unittest
import numpy as np
from clustering_analysis import select_gap, dispersion


class SelectionTests(unittest.TestCase):
    def test_figure_approximation(self):
        gap = [.193, .340, .305, .286, .266, .252, .259, .248, .256, .274]
        se = [.030, .033, .033, .029, .028, .028, .026, .028, .030, .031]
        for rule in ['Tibs2001SEmax', 'firstSEmax', 'globalmax']:
            self.assertEqual(select_gap(gap, se, rule), 2)

    def test_rules_are_not_interchangeable(self):
        gap, se = [0, .1, .2, .3], [.01, .15, .01, .01]
        self.assertEqual(select_gap(gap, se), 1)
        self.assertEqual(select_gap(gap, se, 'firstSEmax'), 4)

    def test_boundary_and_equality(self):
        self.assertEqual(select_gap([0, 1, 2], [.1, .1, .1]), 3)
        self.assertEqual(select_gap([0, 1], [0, 1]), 1)

    def test_pairwise_dispersion(self):
        x = np.array([[0.], [2.], [10.], [14.]])
        labels = np.array([0, 0, 1, 1])
        self.assertAlmostEqual(dispersion(x, labels, 1), 1.5)
        self.assertAlmostEqual(dispersion(x, labels, 2), 5.)


if __name__ == '__main__':
    unittest.main()
