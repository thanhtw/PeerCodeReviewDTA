import unittest
import numpy as np
from effort_profile_analysis import standardize, threshold_summary, label_high_effort


class EffortAnalysisTests(unittest.TestCase):
    def test_scaling_uses_training_data_only(self):
        train = np.array([[0., 2.], [2., 6.]])
        test = np.array([[100., 202.]])
        ztrain, ztest = standardize(train, test)
        np.testing.assert_allclose(ztrain.mean(axis=0), 0)
        np.testing.assert_allclose(ztrain.std(axis=0, ddof=1), 1)
        np.testing.assert_allclose(ztest, (test - train.mean(axis=0)) / train.std(axis=0, ddof=1))
        self.assertGreater(ztest.min(), 10)

    def test_threshold_keeps_equal_effort_together(self):
        score = np.array([1, 2, 2, 3])
        target = np.array([0, 0, 1, 1])
        result = threshold_summary(score, target)
        self.assertAlmostEqual(result['accuracy'], .75)
        self.assertNotEqual(result['example_threshold'], 2)

    def test_cluster_label_permutation_does_not_change_orientation(self):
        effort = np.array([1., 2., 10., 12.])
        a, _ = label_high_effort(np.array([0, 0, 1, 1]), effort)
        b, _ = label_high_effort(np.array([1, 1, 0, 0]), effort)
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(a, [0, 0, 1, 1])


if __name__ == '__main__':
    unittest.main()
