import unittest

import numpy as np

from vision_eval.metrics import depth_metrics, diff_metrics, mask_metrics, psnr, ssim


class MetricsTest(unittest.TestCase):
    def test_identical_image(self):
        a = np.zeros((16, 16, 3), dtype=np.float32)
        self.assertIsNone(psnr(a, a))
        self.assertAlmostEqual(ssim(a, a), 1.0, places=5)
        r = diff_metrics(a, a)
        self.assertEqual(r["changed_pct"], 0.0)
        self.assertEqual(r["max_abs"], 0.0)

    def test_one_pixel_diff(self):
        a = np.zeros((16, 16, 3), dtype=np.float32)
        b = a.copy()
        b[4, 5] = 1.0
        r = diff_metrics(a, b)
        self.assertGreater(r["max_abs"], 0.9)
        self.assertGreater(r["changed_pct"], 0.0)
        self.assertEqual(len(r["regions"]), 1)
        self.assertEqual(r["regions"][0]["kind"], "speck")

    def test_psnr_known(self):
        a = np.zeros((4, 4, 3), dtype=np.float32)
        b = np.ones((4, 4, 3), dtype=np.float32)
        self.assertAlmostEqual(psnr(a, b), 0.0, places=4)

    def test_mask_iou(self):
        pred = np.array([[0, 1], [1, 1]], dtype=np.int32)
        gt = np.array([[0, 1], [0, 1]], dtype=np.int32)
        r = mask_metrics(pred, gt, [1])
        self.assertAlmostEqual(r["mean_iou"], 2 / 3, places=5)
        self.assertAlmostEqual(r["classes"][0]["dice"], 0.8, places=5)

    def test_depth(self):
        gt = np.array([[1.0, 2.0], [4.0, 8.0]], dtype=np.float32)
        r = depth_metrics(gt, gt)
        self.assertEqual(r["abs_rel"], 0.0)
        self.assertEqual(r["delta1"], 1.0)
        r2 = depth_metrics(gt * 1.3, gt)
        self.assertGreater(r2["abs_rel"], 0.0)
        self.assertLess(r2["delta1"], 1.0)


if __name__ == "__main__":
    unittest.main()
