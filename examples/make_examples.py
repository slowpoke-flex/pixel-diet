"""Generate tiny synthetic examples for the README and the tests of the CLI."""

from pathlib import Path

import numpy as np
from PIL import Image

here = Path(__file__).parent
rng = np.random.default_rng(7)
h = w = 256
y, x = np.mgrid[0:h, 0:w]
base = np.stack([(x / w), (y / h), 0.35 + 0.25 * np.sin(x / 18.0)], axis=2)
noise = rng.normal(0.0, 0.01, base.shape)
a = np.clip(base + noise, 0, 1)

b = a.copy()
b[70:120, 80:150] = np.array([0.95, 0.35, 0.15])  # a new object
b[180:200, 40:90] = np.clip(b[180:200, 40:90] * 0.7, 0, 1)  # a local darkening

Image.fromarray((a * 255).astype(np.uint8)).save(here / "a.png")
Image.fromarray((b * 255).astype(np.uint8)).save(here / "b.png")

gt = np.zeros((h, w), dtype=np.uint8)
gt[60:190, 60:190] = 1
pred = gt.copy()
pred[60:150, 60:150] = 0
pred[150:190, 120:190] = 0
Image.fromarray(gt * 255).save(here / "mask_gt.png")
Image.fromarray(pred * 255).save(here / "mask_pred.png")

depth = (1.0 + 0.5 * np.sin(x / 30.0) + 0.3 * np.cos(y / 40.0)).astype(np.float32)
np.save(here / "depth_gt.npy", depth)
np.save(here / "depth_pred.npy", depth * 1.02)

print("wrote a.png, b.png, mask_gt.png, mask_pred.png, depth_gt.npy, depth_pred.npy")
